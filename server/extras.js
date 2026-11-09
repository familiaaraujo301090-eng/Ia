// Recursos extras: planos e limites de IA, hábitos, eventos que se repetem,
// senha (troca e recuperação), lembretes por notificação e painel de administração.
import crypto from 'node:crypto';
import { q } from './db.js';
import {
  hashPassword, verifyPassword, createSession, setSessionCookie, destroyOtherSessions, validPassword, adminSecretMatches,
  PASSWORD_MIN, PASSWORD_MAX,
} from './auth.js';
import { appUrl, hit, limitByIp, isAllowedPushEndpoint, underQuota, quotaGuard } from './security.js';
import { localDate, localDateTime, addDays, isValidDate } from './time.js';
import { vapidPublicKey, saveSubscription, removeSubscription, pushToUser } from './push.js';
import { sendMail } from './mail.js';

const str = (v, max = 5000) => (typeof v === 'string' ? v.trim().slice(0, max) : '');
const isDate = isValidDate;
const bad = (res, msg) => res.status(400).json({ error: msg });
const wrap = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

// ---------- planos e limites ----------
export const PLANS = {
  gratis: { name: 'Grátis', ai_per_day: () => Number(process.env.FREE_AI_PER_DAY || 30) },
  pro: { name: 'Pro', ai_per_day: () => Number(process.env.PRO_AI_PER_DAY || 300) },
};
const plan = (p) => (Object.hasOwn(PLANS, p) ? PLANS[p] : PLANS.gratis);

export function usage(user) {
  const used = q.get('SELECT count FROM ai_usage WHERE user_id = ? AND day = ?', user.id, localDate())?.count || 0;
  const p = plan(user.plan);
  const checkout = /^https:\/\/[^\s"'<>]+$/.test(process.env.PRO_CHECKOUT_URL || '') ? process.env.PRO_CHECKOUT_URL : null;
  return { plan: user.plan || 'gratis', plan_name: p.name, used, limit: p.ai_per_day(), checkout_url: checkout };
}

/** Devolve um uso de IA (pedido inválido ou falha da IA). */
export function refundAi(user) {
  q.run('UPDATE ai_usage SET count = MAX(count - 1, 0) WHERE user_id = ? AND day = ?', user.id, localDate());
}

/** Conta um uso de IA. Retorna mensagem de erro se o limite do dia acabou. */
export function consumeAi(user) {
  const u = usage(user);
  if (u.used >= u.limit) {
    return u.plan === 'gratis'
      ? `Você usou as ${u.limit} ações de IA de hoje no plano Grátis. Amanhã libera de novo, ou assine o Pro para usar muito mais.`
      : `Você atingiu o limite de ${u.limit} ações de IA de hoje. Amanhã libera de novo.`;
  }
  q.run(`INSERT INTO ai_usage (user_id, day, count) VALUES (?, ?, 1)
         ON CONFLICT(user_id, day) DO UPDATE SET count = count + 1`, user.id, localDate());
  return null;
}

// ---------- hábitos ----------
const weekdayOf = (ymd) => new Date(`${ymd}T12:00:00Z`).getUTCDay();

/** Cria as tarefas de hoje para os hábitos ativos que valem para este dia da semana. */
export function ensureHabitTasks(userId, day = localDate()) {
  const wd = String(weekdayOf(day));
  const habits = q.all('SELECT * FROM habits WHERE user_id = ? AND active = 1', userId);
  for (const h of habits) {
    if (!h.days.includes(wd)) continue;
    if (q.get('SELECT id FROM tasks WHERE habit_id = ? AND due_date = ?', h.id, day)) continue;
    q.run(`INSERT INTO tasks (user_id, goal_id, habit_id, title, detail, due_date, minutes, source) VALUES (?, ?, ?, ?, '', ?, ?, 'habito')`,
      userId, h.goal_id, h.id, h.title, day, h.minutes);
  }
}

function habitStreak(habitId, days) {
  const done = new Set(q.all('SELECT due_date d FROM tasks WHERE habit_id = ? AND done = 1', habitId).map((r) => r.d));
  let day = localDate();
  if (!done.has(day)) day = addDays(day, -1);
  let n = 0;
  for (let i = 0; i < 400; i++) {
    if (days.includes(String(weekdayOf(day)))) {
      if (!done.has(day)) break;
      n++;
    }
    day = addDays(day, -1);
  }
  return n;
}

// ---------- eventos que se repetem ----------
export const REPEATS = { '': 'Não repete', diario: 'Todo dia', dias_uteis: 'Dias úteis (seg-sex)', semanal: 'Toda semana', mensal: 'Todo mês' };

function occursOn(ev, day) {
  const startDay = ev.start.slice(0, 10);
  if (day < startDay) return false;
  const wd = weekdayOf(day);
  switch (ev.repeat) {
    case 'diario': return true;
    case 'dias_uteis': return wd >= 1 && wd <= 5;
    case 'semanal': return wd === weekdayOf(startDay);
    case 'mensal': return day.slice(8) === startDay.slice(8);
    default: return day === startDay;
  }
}

/** Compromissos entre `from` (inclusive) e `to` (exclusive), com as repetições já expandidas. */
export function expandEvents(userId, from, to) {
  const single = q.all(`SELECT * FROM events WHERE user_id = ? AND COALESCE(repeat, '') = '' AND start >= ? AND start < ?`, userId, from, to);
  const series = q.all(`SELECT * FROM events WHERE user_id = ? AND COALESCE(repeat, '') != '' AND start < ?`, userId, to);
  const out = [...single];
  for (const ev of series) {
    for (let day = from > ev.start.slice(0, 10) ? from : ev.start.slice(0, 10); day < to; day = addDays(day, 1)) {
      if (!occursOn(ev, day)) continue;
      out.push({ ...ev, start: `${day}T${ev.start.slice(11)}`, end: ev.end ? `${day}T${ev.end.slice(11)}` : null, series_start: ev.start });
    }
  }
  return out.sort((a, b) => (a.start < b.start ? -1 : a.start > b.start ? 1 : 0));
}

// ---------- metas sem tarefas pela frente ----------
export function goalsNeedingPlan(userId, today = localDate()) {
  return q.all(
    `SELECT g.id, g.title FROM goals g WHERE g.user_id = ? AND g.status = 'ativa'
       AND NOT EXISTS (SELECT 1 FROM tasks t WHERE t.goal_id = g.id AND t.done = 0 AND t.due_date >= ?)`,
    userId, today
  );
}

// ---------- rotas públicas (antes do login) ----------
export function registerPublicRoutes(app) {
  app.post('/api/auth/forgot', limitByIp('forgot', 5, 3600_000, 'Muitos pedidos. Tente de novo em 1 hora.'), wrap(async (req, res) => {
    const email = str(req.body.email, 160).toLowerCase();
    const user = q.get('SELECT id, name FROM users WHERE email = ?', email);
    const base = appUrl(req);
    if (!base) console.error('APP_URL não configurada: link de recuperação não enviado.');
    // no máximo 3 e-mails por conta por hora (evita usar o app para lotar a caixa de alguém)
    if (user && base && hit(`forgot-email|${email}`, 3, 3600_000)) {
      q.run('UPDATE password_resets SET used = 1 WHERE user_id = ?', user.id); // invalida links anteriores
      const token = crypto.randomBytes(32).toString('hex');
      const hash = crypto.createHash('sha256').update(token).digest('hex');
      q.run('INSERT INTO password_resets (token_hash, user_id, expires_at) VALUES (?, ?, ?)', hash, user.id, new Date(Date.now() + 3600_000).toISOString());
      const link = `${base}/#/redefinir/${token}`;
      await sendMail({
        to: email,
        subject: 'Rumo: redefinir sua senha',
        text: `Oi, ${user.name}!\n\nPara criar uma nova senha, abra este link (vale por 1 hora):\n${link}\n\nSe não foi você que pediu, ignore este e-mail.`,
        html: `<p>Oi, ${user.name.replace(/[<>&"']/g, '')}!</p><p>Para criar uma nova senha, clique no link abaixo (vale por 1 hora):</p><p><a href="${link}">Criar nova senha</a></p><p>Se não foi você que pediu, ignore este e-mail.</p>`,
      }).catch((e) => console.error('Falha ao enviar e-mail:', e.message));
    }
    // mesma resposta sempre, para não revelar quais e-mails têm conta
    res.json({ ok: true });
  }));

  app.post('/api/auth/reset', limitByIp('reset', 20, 3600_000), (req, res) => {
    const token = str(req.body.token, 200);
    const password = req.body.password;
    if (!validPassword(password)) return bad(res, `A senha precisa ter de ${PASSWORD_MIN} a ${PASSWORD_MAX} caracteres.`);
    const hash = crypto.createHash('sha256').update(token).digest('hex');
    const row = q.get('SELECT * FROM password_resets WHERE token_hash = ?', hash);
    if (!row || row.used || new Date(row.expires_at) < new Date()) return bad(res, 'Link inválido ou expirado. Peça um novo.');
    q.run('UPDATE password_resets SET used = 1 WHERE token_hash = ?', hash);
    q.run('UPDATE users SET pass_hash = ? WHERE id = ?', hashPassword(password), row.user_id);
    destroyOtherSessions(row.user_id); // desconecta todos os aparelhos
    const s = createSession(row.user_id);
    setSessionCookie(res, s.token, s.expires);
    res.json({ ok: true });
  });
}

// ---------- rotas que exigem login ----------
export function registerPrivateRoutes(app) {
  // senha
  app.put('/api/me/password', (req, res) => {
    if (!hit(`pw|${req.user.id}`, 10, 15 * 60_000)) return res.status(429).json({ error: 'Muitas tentativas. Tente mais tarde.' });
    const row = q.get('SELECT pass_hash FROM users WHERE id = ?', req.user.id);
    if (!verifyPassword(typeof req.body.current === 'string' ? req.body.current : '', row.pass_hash)) return bad(res, 'Senha atual incorreta.');
    const password = req.body.password;
    if (!validPassword(password)) return bad(res, `A nova senha precisa ter de ${PASSWORD_MIN} a ${PASSWORD_MAX} caracteres.`);
    q.run('UPDATE users SET pass_hash = ? WHERE id = ?', hashPassword(password), req.user.id);
    destroyOtherSessions(req.user.id, req.token); // desconecta os outros aparelhos
    res.json({ ok: true });
  });

  // lembretes
  app.put('/api/me/reminders', (req, res) => {
    const time = /^\d{2}:\d{2}$/.test(req.body.reminder_time) ? req.body.reminder_time : req.user.reminder_time;
    q.run('UPDATE users SET reminders = ?, reminder_time = ? WHERE id = ?', req.body.reminders ? 1 : 0, time, req.user.id);
    res.json({ ok: true });
  });
  app.get('/api/push/key', (req, res) => res.json({ key: vapidPublicKey() }));
  app.post('/api/push/subscribe', (req, res) => {
    const sub = req.body.subscription;
    if (!isAllowedPushEndpoint(sub?.endpoint)) return bad(res, 'Serviço de notificação não reconhecido.');
    const exists = q.get('SELECT id FROM push_subs WHERE endpoint = ?', sub.endpoint);
    if (!exists && !underQuota('push_subs', req.user.id)) return bad(res, 'Limite de aparelhos atingido. Desative um antes.');
    try { saveSubscription(req.user.id, sub); } catch (e) { return bad(res, e.message); }
    res.json({ ok: true });
  });
  app.post('/api/push/unsubscribe', (req, res) => {
    removeSubscription(req.user.id, str(req.body.endpoint, 1000));
    res.json({ ok: true });
  });
  app.post('/api/push/test', limitByIp('push-test', 10, 3600_000), wrap(async (req, res) => {
    const sent = await pushToUser(req.user.id, { title: 'Rumo', body: 'Notificações funcionando! Vou te lembrar das tarefas todo dia. 🔔', url: '/#/hoje' });
    res.json({ sent });
  }));

  // hábitos
  const days = (v) => (typeof v === 'string' && /^[0-6]{1,7}$/.test(v) ? [...new Set(v)].sort().join('') : '0123456');
  const ownGoal = (uid, gid) => (gid ? q.get('SELECT id FROM goals WHERE id = ? AND user_id = ?', Number(gid), uid)?.id ?? null : null);
  app.get('/api/habits', (req, res) => {
    res.json(q.all('SELECT * FROM habits WHERE user_id = ? ORDER BY active DESC, id', req.user.id).map((h) => ({
      ...h,
      streak: habitStreak(h.id, h.days),
      last7: q.all('SELECT due_date d, done FROM tasks WHERE habit_id = ? AND due_date >= ? ORDER BY due_date', h.id, addDays(localDate(), -6)),
    })));
  });
  app.post('/api/habits', quotaGuard('habits'), (req, res) => {
    const title = str(req.body.title, 200);
    if (!title) return bad(res, 'Escreva o hábito.');
    const { lastInsertRowid } = q.run('INSERT INTO habits (user_id, goal_id, title, minutes, days) VALUES (?, ?, ?, ?, ?)',
      req.user.id, ownGoal(req.user.id, req.body.goal_id), title, Math.max(1, Math.min(240, Number(req.body.minutes) || 10)), days(req.body.days));
    ensureHabitTasks(req.user.id);
    res.status(201).json(q.get('SELECT * FROM habits WHERE id = ?', lastInsertRowid));
  });
  app.patch('/api/habits/:id', (req, res) => {
    const h = q.get('SELECT * FROM habits WHERE id = ? AND user_id = ?', Number(req.params.id), req.user.id);
    if (!h) return res.status(404).json({ error: 'Hábito não encontrado.' });
    q.run('UPDATE habits SET title = ?, minutes = ?, days = ?, active = ? WHERE id = ?',
      str(req.body.title, 200) || h.title, Number(req.body.minutes) || h.minutes,
      req.body.days === undefined ? h.days : days(req.body.days), req.body.active === undefined ? h.active : req.body.active ? 1 : 0, h.id);
    res.json(q.get('SELECT * FROM habits WHERE id = ?', h.id));
  });
  app.delete('/api/habits/:id', (req, res) => {
    const h = q.get('SELECT id FROM habits WHERE id = ? AND user_id = ?', Number(req.params.id), req.user.id);
    if (h) {
      q.run('DELETE FROM tasks WHERE habit_id = ? AND done = 0 AND due_date >= ?', h.id, localDate());
      q.run('DELETE FROM habits WHERE id = ?', h.id);
    }
    res.json({ ok: true });
  });

  // administração
  const admin = (req, res, next) => (req.user.is_admin ? next() : res.status(403).json({ error: 'Acesso restrito.' }));
  // Vira admin quem informa ADMIN_SECRET (variável do servidor, mínimo 20 caracteres).
  app.post('/api/admin/claim', limitByIp('admin-claim', 5, 3600_000, 'Muitas tentativas. Tente em 1 hora.'), (req, res) => {
    if (!hit(`admin-claim-user|${req.user.id}`, 5, 3600_000)) return res.status(429).json({ error: 'Muitas tentativas. Tente em 1 hora.' });
    if (!adminSecretMatches(req.body.secret)) return res.status(403).json({ error: 'Código incorreto.' });
    q.run('UPDATE users SET is_admin = 1 WHERE id = ?', req.user.id);
    res.json({ ok: true });
  });
  app.get('/api/admin/stats', admin, (req, res) => {
    const today = localDate();
    const d7 = addDays(today, -6);
    const d30 = addDays(today, -29);
    res.json({
      users: q.get('SELECT COUNT(*) c FROM users').c,
      new7: q.get('SELECT COUNT(*) c FROM users WHERE created_at >= ?', d7).c,
      active7: q.get('SELECT COUNT(*) c FROM users WHERE last_seen >= ?', d7).c,
      active1: q.get('SELECT COUNT(*) c FROM users WHERE last_seen >= ?', today).c,
      onboarded: q.get('SELECT COUNT(*) c FROM users WHERE onboarded = 1').c,
      pro: q.get(`SELECT COUNT(*) c FROM users WHERE plan = 'pro'`).c,
      push: q.get('SELECT COUNT(DISTINCT user_id) c FROM push_subs').c,
      tasks_done7: q.get('SELECT COUNT(*) c FROM tasks WHERE done = 1 AND due_date >= ?', d7).c,
      ai_today: q.get('SELECT COALESCE(SUM(count), 0) c FROM ai_usage WHERE day = ?', today).c,
      ai30: q.all('SELECT day, SUM(count) n FROM ai_usage WHERE day >= ? GROUP BY day ORDER BY day', d30),
      signups30: q.all('SELECT substr(created_at, 1, 10) day, COUNT(*) n FROM users WHERE created_at >= ? GROUP BY day ORDER BY day', d30),
      recent: q.all(`SELECT u.id, u.name, u.email, u.plan, u.created_at, u.last_seen, u.role, u.is_admin,
                       (SELECT COUNT(*) FROM tasks t WHERE t.user_id = u.id AND t.done = 1) done
                     FROM users u ORDER BY u.id DESC LIMIT 50`),
    });
  });
  app.patch('/api/admin/users/:id', admin, (req, res) => {
    if (!Object.hasOwn(PLANS, req.body.plan)) return bad(res, 'Plano inválido.');
    q.run('UPDATE users SET plan = ? WHERE id = ?', req.body.plan, Number(req.params.id));
    res.json({ ok: true });
  });
}

// ---------- lembrete diário ----------
export async function sendDueReminders(now = new Date()) {
  const today = localDate(now);
  const hhmm = localDateTime(now).slice(11);
  const users = q.all(
    `SELECT DISTINCT u.id, u.name, u.reminder_time FROM users u JOIN push_subs p ON p.user_id = u.id
      WHERE u.reminders = 1 AND COALESCE(u.last_reminder, '') != ? AND u.reminder_time <= ?`,
    today, hhmm
  );
  for (const u of users) {
    q.run('UPDATE users SET last_reminder = ? WHERE id = ?', today, u.id);
    ensureHabitTasks(u.id, today);
    const pending = q.all('SELECT title FROM tasks WHERE user_id = ? AND due_date = ? AND done = 0', u.id, today);
    const first = u.name.split(' ')[0];
    const body = pending.length
      ? `${first}, você tem ${pending.length} tarefa${pending.length > 1 ? 's' : ''} hoje. Comece por: ${pending[0].title}`
      : `${first}, vamos montar seu dia? Leva 1 minuto.`;
    await pushToUser(u.id, { title: 'Bom dia! ☀️ Seu dia no Rumo', body, url: '/#/hoje' }).catch(() => {});
  }
  return users.length;
}

export function startReminderLoop() {
  const tick = () => sendDueReminders().catch((e) => console.error('Lembretes:', e.message));
  setInterval(tick, 60_000).unref();
  tick();
}
