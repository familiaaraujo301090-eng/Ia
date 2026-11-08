import express from 'express';
import path from 'node:path';
import { q, db } from './db.js';
import {
  hashPassword, verifyPassword, createSession, destroySession,
  setSessionCookie, clearSessionCookie, requireUser,
} from './auth.js';
import * as ai from './ai.js';
import { localDate, localDateTime, addDays } from './time.js';
import { LAUNCH_PLAN } from './launchPlan.js';

export const app = express();
app.disable('x-powered-by');
app.use(express.json({ limit: '1mb' }));
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('Referrer-Policy', 'same-origin');
  next();
});

const wrap = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
const str = (v, max = 5000) => (typeof v === 'string' ? v.trim().slice(0, max) : '');
const isDate = (v) => typeof v === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v);
const isDateTime = (v) => typeof v === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(v);
const bad = (res, msg) => res.status(400).json({ error: msg });

// ---------- simple per-user AI rate limit ----------
const hits = new Map();
function aiLimit(req, res, next) {
  const now = Date.now();
  const list = (hits.get(req.user.id) || []).filter((t) => now - t < 60_000);
  if (list.length >= Number(process.env.AI_PER_MINUTE || 20)) {
    return res.status(429).json({ error: 'Muitas solicitações à IA. Espere um minutinho.' });
  }
  list.push(now);
  hits.set(req.user.id, list);
  next();
}

// ---------- auth ----------
const loginTries = new Map();
app.post('/api/auth/register', (req, res) => {
  const name = str(req.body.name, 80);
  const email = str(req.body.email, 160).toLowerCase();
  const password = typeof req.body.password === 'string' ? req.body.password : '';
  if (!name || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return bad(res, 'Informe nome e e-mail válidos.');
  if (password.length < 6) return bad(res, 'A senha precisa ter pelo menos 6 caracteres.');
  if (q.get('SELECT id FROM users WHERE email = ?', email)) return res.status(409).json({ error: 'E-mail já cadastrado.' });
  const { lastInsertRowid } = q.run('INSERT INTO users (name, email, pass_hash) VALUES (?, ?, ?)', name, email, hashPassword(password));
  const s = createSession(Number(lastInsertRowid));
  setSessionCookie(res, s.token, s.expires);
  res.status(201).json({ ok: true });
});

app.post('/api/auth/login', (req, res) => {
  const email = str(req.body.email, 160).toLowerCase();
  const key = `${req.ip}|${email}`;
  const tries = (loginTries.get(key) || []).filter((t) => Date.now() - t < 15 * 60_000);
  if (tries.length >= 10) return res.status(429).json({ error: 'Muitas tentativas. Tente em 15 minutos.' });
  const user = q.get('SELECT id, pass_hash FROM users WHERE email = ?', email);
  if (!user || !verifyPassword(String(req.body.password || ''), user.pass_hash)) {
    tries.push(Date.now());
    loginTries.set(key, tries);
    return res.status(401).json({ error: 'E-mail ou senha incorretos.' });
  }
  loginTries.delete(key);
  const s = createSession(user.id);
  setSessionCookie(res, s.token, s.expires);
  res.json({ ok: true });
});

app.post('/api/auth/logout', (req, res) => {
  const m = (req.headers.cookie || '').match(/rumo_session=([^;]+)/);
  destroySession(m && m[1]);
  clearSessionCookie(res);
  res.json({ ok: true });
});

app.get('/api/health', (req, res) => res.json({ ok: true, ai: ai.aiEnabled }));

// everything below requires login
app.use('/api', requireUser);

app.get('/api/me', (req, res) => res.json({ user: req.user, ai: ai.aiEnabled, today: localDate() }));
app.put('/api/me', (req, res) => {
  const name = str(req.body.name, 80) || req.user.name;
  q.run('UPDATE users SET name = ?, about = ?, niche = ?, tone = ?, daily_minutes = ? WHERE id = ?',
    name, str(req.body.about, 1000), str(req.body.niche, 200), str(req.body.tone, 100) || 'motivador e direto',
    Math.max(5, Math.min(600, Number(req.body.daily_minutes) || req.user.daily_minutes || 30)), req.user.id);
  res.json({ ok: true });
});
app.delete('/api/me', (req, res) => {
  q.run('DELETE FROM users WHERE id = ?', req.user.id);
  clearSessionCookie(res);
  res.json({ ok: true });
});

// ---------- dashboard ----------
function streak(userId) {
  const days = new Set(q.all('SELECT DISTINCT due_date d FROM tasks WHERE user_id = ? AND done = 1', userId).map((r) => r.d));
  let day = localDate();
  if (!days.has(day)) day = addDays(day, -1);
  let n = 0;
  while (days.has(day)) { n++; day = addDays(day, -1); }
  return n;
}

function goalsWithProgress(userId) {
  return q.all(
    `SELECT g.*, COUNT(t.id) total, COALESCE(SUM(t.done), 0) done
       FROM goals g LEFT JOIN tasks t ON t.goal_id = g.id
      WHERE g.user_id = ? GROUP BY g.id ORDER BY g.status = 'ativa' DESC, g.id DESC`,
    userId
  );
}

app.get('/api/today', (req, res) => {
  const today = localDate();
  res.json({
    date: today,
    tasks: q.all('SELECT * FROM tasks WHERE user_id = ? AND due_date = ? ORDER BY done, id', req.user.id, today),
    overdue: q.all('SELECT * FROM tasks WHERE user_id = ? AND due_date < ? AND done = 0 ORDER BY due_date DESC LIMIT 20', req.user.id, today),
    events: q.all('SELECT * FROM events WHERE user_id = ? AND start >= ? AND start < ? ORDER BY start', req.user.id, today, addDays(today, 2)),
    goals: goalsWithProgress(req.user.id).filter((g) => g.status === 'ativa'),
    streak: streak(req.user.id),
    checkin: q.get('SELECT mood, note FROM checkins WHERE user_id = ? AND day = ?', req.user.id, today) || null,
    week: q.all(
      `SELECT due_date d, COUNT(*) total, SUM(done) done FROM tasks WHERE user_id = ? AND due_date BETWEEN ? AND ? GROUP BY due_date`,
      req.user.id, addDays(today, -6), today
    ),
  });
});

app.post('/api/checkin', (req, res) => {
  const mood = Math.max(1, Math.min(5, Number(req.body.mood) || 3));
  q.run(`INSERT INTO checkins (user_id, day, mood, note) VALUES (?, ?, ?, ?)
         ON CONFLICT(user_id, day) DO UPDATE SET mood = excluded.mood, note = excluded.note`,
    req.user.id, localDate(), mood, str(req.body.note, 1000));
  res.json({ ok: true });
});

// ---------- tasks ----------
app.get('/api/tasks', (req, res) => {
  const { from, to } = req.query;
  if (isDate(from) && isDate(to)) {
    return res.json(q.all('SELECT * FROM tasks WHERE user_id = ? AND due_date BETWEEN ? AND ? ORDER BY due_date, done, id', req.user.id, from, to));
  }
  const date = isDate(req.query.date) ? req.query.date : localDate();
  res.json(q.all('SELECT * FROM tasks WHERE user_id = ? AND due_date = ? ORDER BY done, id', req.user.id, date));
});

function ownGoal(userId, goalId) {
  if (goalId == null || goalId === '') return null;
  const g = q.get('SELECT id FROM goals WHERE id = ? AND user_id = ?', Number(goalId), userId);
  return g ? g.id : null;
}

app.post('/api/tasks', (req, res) => {
  const title = str(req.body.title, 300);
  if (!title) return bad(res, 'Escreva a tarefa.');
  const due = isDate(req.body.due_date) ? req.body.due_date : localDate();
  const { lastInsertRowid } = q.run(
    'INSERT INTO tasks (user_id, goal_id, title, detail, due_date, minutes, source) VALUES (?, ?, ?, ?, ?, ?, ?)',
    req.user.id, ownGoal(req.user.id, req.body.goal_id), title, str(req.body.detail), due,
    Math.max(1, Math.min(600, Number(req.body.minutes) || 15)), 'manual'
  );
  res.status(201).json(q.get('SELECT * FROM tasks WHERE id = ?', lastInsertRowid));
});

app.patch('/api/tasks/:id', (req, res) => {
  const t = q.get('SELECT * FROM tasks WHERE id = ? AND user_id = ?', Number(req.params.id), req.user.id);
  if (!t) return res.status(404).json({ error: 'Tarefa não encontrada.' });
  const done = req.body.done === undefined ? t.done : req.body.done ? 1 : 0;
  q.run('UPDATE tasks SET title = ?, detail = ?, due_date = ?, minutes = ?, done = ?, done_at = ? WHERE id = ?',
    str(req.body.title, 300) || t.title,
    req.body.detail === undefined ? t.detail : str(req.body.detail),
    isDate(req.body.due_date) ? req.body.due_date : t.due_date,
    req.body.minutes ? Math.max(1, Math.min(600, Number(req.body.minutes))) : t.minutes,
    done, done ? (t.done_at || new Date().toISOString()) : null, t.id);
  res.json(q.get('SELECT * FROM tasks WHERE id = ?', t.id));
});

app.delete('/api/tasks/:id', (req, res) => {
  q.run('DELETE FROM tasks WHERE id = ? AND user_id = ?', Number(req.params.id), req.user.id);
  res.json({ ok: true });
});

// ---------- goals ----------
app.get('/api/goals', (req, res) => res.json(goalsWithProgress(req.user.id)));

app.get('/api/goals/:id', (req, res) => {
  const g = q.get('SELECT * FROM goals WHERE id = ? AND user_id = ?', Number(req.params.id), req.user.id);
  if (!g) return res.status(404).json({ error: 'Meta não encontrada.' });
  g.tasks = q.all('SELECT * FROM tasks WHERE goal_id = ? ORDER BY due_date, id', g.id);
  res.json(g);
});

app.post('/api/goals', (req, res) => {
  const title = str(req.body.title, 300);
  if (!title) return bad(res, 'Descreva a meta.');
  const { lastInsertRowid } = q.run('INSERT INTO goals (user_id, title, why, area, deadline) VALUES (?, ?, ?, ?, ?)',
    req.user.id, title, str(req.body.why, 2000), str(req.body.area, 60) || 'geral', isDate(req.body.deadline) ? req.body.deadline : null);
  res.status(201).json(q.get('SELECT * FROM goals WHERE id = ?', lastInsertRowid));
});

app.patch('/api/goals/:id', (req, res) => {
  const g = q.get('SELECT * FROM goals WHERE id = ? AND user_id = ?', Number(req.params.id), req.user.id);
  if (!g) return res.status(404).json({ error: 'Meta não encontrada.' });
  const status = ['ativa', 'pausada', 'concluida'].includes(req.body.status) ? req.body.status : g.status;
  q.run('UPDATE goals SET title = ?, why = ?, area = ?, deadline = ?, status = ? WHERE id = ?',
    str(req.body.title, 300) || g.title,
    req.body.why === undefined ? g.why : str(req.body.why, 2000),
    str(req.body.area, 60) || g.area,
    req.body.deadline === undefined ? g.deadline : isDate(req.body.deadline) ? req.body.deadline : null,
    status, g.id);
  res.json(q.get('SELECT * FROM goals WHERE id = ?', g.id));
});

app.delete('/api/goals/:id', (req, res) => {
  q.run('DELETE FROM goals WHERE id = ? AND user_id = ?', Number(req.params.id), req.user.id);
  res.json({ ok: true });
});

function insertTasks(userId, goalId, tasks, startDate, source) {
  const stmt = db.prepare('INSERT INTO tasks (user_id, goal_id, title, detail, due_date, minutes, source) VALUES (?, ?, ?, ?, ?, ?, ?)');
  db.exec('BEGIN');
  try {
    for (const t of tasks) {
      stmt.run(userId, goalId, String(t.title).slice(0, 300), String(t.detail || '').slice(0, 2000),
        addDays(startDate, Math.max(0, Number(t.day_offset) || 0)), Math.max(1, Math.min(600, Number(t.minutes) || 15)), source);
    }
    db.exec('COMMIT');
  } catch (e) {
    db.exec('ROLLBACK');
    throw e;
  }
}

app.post('/api/goals/:id/plan', aiLimit, wrap(async (req, res) => {
  const g = q.get('SELECT * FROM goals WHERE id = ? AND user_id = ?', Number(req.params.id), req.user.id);
  if (!g) return res.status(404).json({ error: 'Meta não encontrada.' });
  const days = Math.max(3, Math.min(14, Number(req.body.days) || 7));
  const start = isDate(req.body.start) ? req.body.start : localDate();
  const plan = await ai.goalPlan(req.user, g, days);
  if (req.body.replace) q.run(`DELETE FROM tasks WHERE goal_id = ? AND done = 0 AND due_date >= ? AND source = 'ai'`, g.id, start);
  insertTasks(req.user.id, g.id, plan.tasks, start, 'ai');
  const planText = `${plan.summary}\n\n**Marcos**\n${plan.milestones.map((m) => `- ${m.title} — ${m.by}`).join('\n')}\n\n**Primeiro passo agora:** ${plan.first_step}`;
  q.run('UPDATE goals SET plan = ? WHERE id = ?', planText, g.id);
  res.json({ plan, planText });
}));

function importLaunchPlan(uid, start = localDate()) {
  const { lastInsertRowid } = q.run('INSERT INTO goals (user_id, title, why, area, deadline, plan) VALUES (?, ?, ?, ?, ?, ?)',
    uid, LAUNCH_PLAN.title, LAUNCH_PLAN.why, LAUNCH_PLAN.area, addDays(start, 29),
    'Plano de 30 dias em 4 semanas: **Fundação** → **Ritmo** → **Prova e parcerias** → **Conversão e escala**. Uma tarefa por dia. Veja o guia completo em docs/PLANO_DE_DIVULGACAO.md.');
  insertTasks(uid, Number(lastInsertRowid),
    LAUNCH_PLAN.tasks.map(([title, detail, minutes], i) => ({ title, detail, minutes, day_offset: i })), start, 'plano');
  return Number(lastInsertRowid);
}

app.post('/api/goals/import-launch-plan', (req, res) => {
  res.status(201).json({ id: importLaunchPlan(req.user.id, isDate(req.body.start) ? req.body.start : localDate()) });
});

// ---------- AI daily tasks ----------
app.post('/api/ai/daily', aiLimit, wrap(async (req, res) => {
  const today = localDate();
  const recent = q.all(
    'SELECT due_date, title, done FROM tasks WHERE user_id = ? AND due_date BETWEEN ? AND ? ORDER BY due_date',
    req.user.id, addDays(today, -5), today
  ).map((t) => `${t.due_date} [${t.done ? 'x' : ' '}] ${t.title}`).join('\n');
  const out = await ai.dailyTasks(req.user, recent);
  const tasks = out.tasks.slice(0, 6).map((t) => ({ ...t, day_offset: 0 }));
  const stmt = db.prepare('INSERT INTO tasks (user_id, goal_id, title, detail, due_date, minutes, source) VALUES (?, ?, ?, ?, ?, ?, ?)');
  for (const t of tasks) stmt.run(req.user.id, ownGoal(req.user.id, t.goal_id), String(t.title).slice(0, 300), String(t.detail || ''), today, Math.max(1, Math.min(600, Number(t.minutes) || 15)), 'ai');
  res.json({ message: out.message, count: tasks.length });
}));

// ---------- events / agenda ----------
app.get('/api/events', (req, res) => {
  const from = isDate(req.query.from) ? req.query.from : addDays(localDate(), -1);
  const to = isDate(req.query.to) ? req.query.to : addDays(from, 31);
  res.json(q.all('SELECT * FROM events WHERE user_id = ? AND start >= ? AND start < ? ORDER BY start', req.user.id, from, addDays(to, 1)));
});

function createEvent(userId, b) {
  const title = str(b.title, 300);
  if (!title || !isDateTime(b.start)) return null;
  const { lastInsertRowid } = q.run('INSERT INTO events (user_id, title, start, end, notes) VALUES (?, ?, ?, ?, ?)',
    userId, title, b.start, isDateTime(b.end) ? b.end : null, str(b.notes, 2000));
  return q.get('SELECT * FROM events WHERE id = ?', lastInsertRowid);
}

app.post('/api/events', (req, res) => {
  const ev = createEvent(req.user.id, req.body);
  if (!ev) return bad(res, 'Informe título e data/hora (AAAA-MM-DDTHH:MM).');
  res.status(201).json(ev);
});

app.post('/api/events/quick', aiLimit, wrap(async (req, res) => {
  const sentence = str(req.body.text, 500);
  if (!sentence) return bad(res, 'Escreva o compromisso.');
  const parsed = await ai.parseEvent(req.user, sentence);
  const ev = createEvent(req.user.id, parsed);
  if (!ev) return bad(res, 'Não entendi a data. Tente: "dentista amanhã às 15h".');
  res.status(201).json(ev);
}));

app.patch('/api/events/:id', (req, res) => {
  const e = q.get('SELECT * FROM events WHERE id = ? AND user_id = ?', Number(req.params.id), req.user.id);
  if (!e) return res.status(404).json({ error: 'Compromisso não encontrado.' });
  q.run('UPDATE events SET title = ?, start = ?, end = ?, notes = ? WHERE id = ?',
    str(req.body.title, 300) || e.title, isDateTime(req.body.start) ? req.body.start : e.start,
    req.body.end === undefined ? e.end : isDateTime(req.body.end) ? req.body.end : null,
    req.body.notes === undefined ? e.notes : str(req.body.notes, 2000), e.id);
  res.json(q.get('SELECT * FROM events WHERE id = ?', e.id));
});

app.delete('/api/events/:id', (req, res) => {
  q.run('DELETE FROM events WHERE id = ? AND user_id = ?', Number(req.params.id), req.user.id);
  res.json({ ok: true });
});

// ---------- notes / editor ----------
app.get('/api/notes', (req, res) => {
  res.json(q.all('SELECT id, title, kind, substr(content, 1, 160) preview, updated_at FROM notes WHERE user_id = ? ORDER BY updated_at DESC', req.user.id));
});
app.get('/api/notes/:id', (req, res) => {
  const n = q.get('SELECT * FROM notes WHERE id = ? AND user_id = ?', Number(req.params.id), req.user.id);
  if (!n) return res.status(404).json({ error: 'Nota não encontrada.' });
  res.json(n);
});
app.post('/api/notes', (req, res) => {
  const { lastInsertRowid } = q.run('INSERT INTO notes (user_id, title, content, kind) VALUES (?, ?, ?, ?)',
    req.user.id, str(req.body.title, 200) || 'Sem título', str(req.body.content, 200_000), str(req.body.kind, 20) || 'nota');
  res.status(201).json(q.get('SELECT * FROM notes WHERE id = ?', lastInsertRowid));
});
app.put('/api/notes/:id', (req, res) => {
  const r = q.run(`UPDATE notes SET title = ?, content = ?, updated_at = datetime('now') WHERE id = ? AND user_id = ?`,
    str(req.body.title, 200) || 'Sem título', str(req.body.content, 200_000), Number(req.params.id), req.user.id);
  if (!r.changes) return res.status(404).json({ error: 'Nota não encontrada.' });
  res.json({ ok: true });
});
app.delete('/api/notes/:id', (req, res) => {
  q.run('DELETE FROM notes WHERE id = ? AND user_id = ?', Number(req.params.id), req.user.id);
  res.json({ ok: true });
});

// ---------- AI tools ----------
app.post('/api/ai/edit', aiLimit, wrap(async (req, res) => {
  const input = str(req.body.text, 50_000);
  if (!input) return bad(res, 'Escreva algum texto primeiro.');
  res.json({ text: await ai.edit(req.user, str(req.body.action, 30), input, str(req.body.instruction, 1000)) });
}));

app.post('/api/ai/amplify', aiLimit, wrap(async (req, res) => {
  const idea = str(req.body.idea, 4000);
  if (!idea) return bad(res, 'Descreva sua ideia.');
  res.json(await ai.amplify(req.user, idea));
}));

app.post('/api/ai/caption', aiLimit, wrap(async (req, res) => {
  const topic = str(req.body.topic, 2000);
  if (!topic) return bad(res, 'Sobre o que é o post?');
  res.json(await ai.captions(req.user, {
    topic, platform: str(req.body.platform, 40), style: str(req.body.style, 200), goal: str(req.body.goal, 200),
  }));
}));

app.post('/api/ai/review', aiLimit, wrap(async (req, res) => {
  const today = localDate();
  const rows = q.all('SELECT due_date, title, done FROM tasks WHERE user_id = ? AND due_date BETWEEN ? AND ? ORDER BY due_date', req.user.id, addDays(today, -6), today);
  const moods = q.all('SELECT day, mood, note FROM checkins WHERE user_id = ? AND day >= ?', req.user.id, addDays(today, -6));
  const summary = `Tarefas (${rows.filter((r) => r.done).length}/${rows.length} concluídas):\n${rows.map((r) => `${r.due_date} [${r.done ? 'x' : ' '}] ${r.title}`).join('\n') || '(nenhuma)'}\n\nHumor:\n${moods.map((m) => `${m.day}: ${m.mood}/5 ${m.note}`).join('\n') || '(sem check-ins)'}`;
  res.json({ text: await ai.weeklyReview(req.user, summary) });
}));

// ---------- chat ----------
// created_at das mensagens é gravado no horário local, para filtrar "a conversa de hoje".
app.get('/api/chat', (req, res) => {
  if (req.query.today) {
    return res.json(q.all('SELECT id, role, content, created_at FROM messages WHERE user_id = ? AND created_at >= ? ORDER BY id DESC LIMIT 60', req.user.id, localDate()).reverse());
  }
  res.json(q.all('SELECT id, role, content, created_at FROM messages WHERE user_id = ? ORDER BY id DESC LIMIT 100', req.user.id).reverse());
});
app.delete('/api/chat', (req, res) => {
  q.run('DELETE FROM messages WHERE user_id = ?', req.user.id);
  res.json({ ok: true });
});

function addMessage(uid, role, content) {
  q.run('INSERT INTO messages (user_id, role, content, created_at) VALUES (?, ?, ?, ?)', uid, role, content, localDateTime().replace('T', ' '));
}

/** Ações que a IA pode executar, sempre restritas ao usuário logado. */
function chatActions(uid) {
  const task = (id) => q.get('SELECT * FROM tasks WHERE id = ? AND user_id = ?', id, uid) || (() => { throw new Error(`Tarefa ${id} não encontrada.`); })();
  return {
    criar_tarefa: (t) => {
      const due = isDate(t.due_date) ? t.due_date : localDate();
      q.run('INSERT INTO tasks (user_id, goal_id, title, detail, due_date, minutes, source) VALUES (?, ?, ?, ?, ?, ?, ?)',
        uid, ownGoal(uid, t.goal_id), t.title, t.detail || '', due, t.minutes || 15, 'ai');
      return `➕ Tarefa criada: "${t.title}"${due === localDate() ? '' : ` (${due})`}`;
    },
    concluir_tarefa: ({ task_id, done = true }) => {
      const t = task(task_id);
      q.run('UPDATE tasks SET done = ?, done_at = ? WHERE id = ?', done ? 1 : 0, done ? new Date().toISOString() : null, t.id);
      return done ? `✅ Feito: "${t.title}"` : `↩️ Reaberta: "${t.title}"`;
    },
    reagendar_tarefa: ({ task_id, due_date }) => {
      const t = task(task_id);
      q.run('UPDATE tasks SET due_date = ? WHERE id = ?', due_date, t.id);
      return `⏭️ "${t.title}" movida para ${due_date === addDays(localDate(), 1) ? 'amanhã' : due_date}`;
    },
    editar_tarefa: ({ task_id, title, detail, minutes }) => {
      const t = task(task_id);
      q.run('UPDATE tasks SET title = ?, detail = ?, minutes = ? WHERE id = ?', title || t.title, detail ?? t.detail, minutes || t.minutes, t.id);
      return `✏️ Tarefa ajustada: "${title || t.title}"`;
    },
    excluir_tarefa: ({ task_id }) => {
      const t = task(task_id);
      q.run('DELETE FROM tasks WHERE id = ?', t.id);
      return `🗑️ Tarefa removida: "${t.title}"`;
    },
    criar_compromisso: (e) => {
      const ev = createEvent(uid, e);
      if (!ev) throw new Error('Data/hora inválida.');
      return `📅 Agendado: "${ev.title}" em ${ev.start.slice(8, 10)}/${ev.start.slice(5, 7)} às ${ev.start.slice(11)}`;
    },
    criar_meta: (g) => {
      const { lastInsertRowid } = q.run('INSERT INTO goals (user_id, title, why, area, deadline) VALUES (?, ?, ?, ?, ?)',
        uid, g.title, g.why || '', g.area || 'geral', isDate(g.deadline) ? g.deadline : null);
      return `🎯 Meta criada: "${g.title}" (id ${lastInsertRowid}). Abra em Metas para gerar o plano.`;
    },
    atualizar_meta: ({ goal_id, status, deadline, why }) => {
      const g = q.get('SELECT * FROM goals WHERE id = ? AND user_id = ?', goal_id, uid);
      if (!g) throw new Error(`Meta ${goal_id} não encontrada.`);
      q.run('UPDATE goals SET status = ?, deadline = ?, why = ? WHERE id = ?', status || g.status, deadline === undefined ? g.deadline : deadline, why ?? g.why, g.id);
      return `🎯 Meta atualizada: "${g.title}"${status ? ` (${status})` : ''}`;
    },
    atualizar_perfil: (p) => {
      const u = q.get('SELECT about, niche, tone, daily_minutes FROM users WHERE id = ?', uid);
      q.run('UPDATE users SET about = ?, niche = ?, tone = ?, daily_minutes = ? WHERE id = ?',
        p.about ?? u.about, p.niche ?? u.niche, p.tone ?? u.tone, p.daily_minutes ?? u.daily_minutes, uid);
      return '👤 Perfil atualizado';
    },
    salvar_nota: (n) => {
      q.run('INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)', uid, n.title, n.content);
      return `📝 Nota salva: "${n.title}"`;
    },
  };
}

app.post('/api/ai/chat', aiLimit, async (req, res) => {
  const uid = req.user.id;
  const helpTask = req.body.help_task_id
    ? q.get('SELECT * FROM tasks WHERE id = ? AND user_id = ?', Number(req.body.help_task_id), uid)
    : null;
  const message = helpTask ? `🆘 Me ajuda com: ${helpTask.title}` : str(req.body.message, 8000);
  if (!message) return bad(res, 'Mensagem vazia.');
  addMessage(uid, 'user', message);
  const history = q.all('SELECT role, content FROM messages WHERE user_id = ? ORDER BY id DESC LIMIT 30', uid).reverse();
  while (history.length && history[0].role !== 'user') history.shift();

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache, no-transform');
  res.setHeader('X-Accel-Buffering', 'no');
  res.flushHeaders();
  const send = (obj) => res.write(`data: ${JSON.stringify(obj)}\n\n`);
  try {
    const full = await ai.chatStream(req.user, history, {
      onText: (t) => send({ t }),
      onAction: (a) => send({ action: a }),
      actions: chatActions(uid),
      today: () => q.all('SELECT * FROM tasks WHERE user_id = ? AND due_date = ? ORDER BY id', uid, localDate()),
      helpTask,
    });
    if (full) addMessage(uid, 'assistant', full);
    send({ done: true });
  } catch (err) {
    send({ error: err.message || 'Erro na IA.' });
  }
  res.end();
});

// ---------- onboarding (passo a passo do novo usuário) ----------
app.post('/api/onboarding', aiLimit, wrap(async (req, res) => {
  const uid = req.user.id;
  const b = req.body;
  const minutes = Math.max(5, Math.min(600, Number(b.daily_minutes) || 30));
  q.run('UPDATE users SET name = ?, role = ?, about = ?, niche = ?, tone = ?, daily_minutes = ? WHERE id = ?',
    str(b.name, 80) || req.user.name, str(b.role, 80), str(b.about, 1000), str(b.niche, 200), str(b.tone, 100) || 'motivador e direto', minutes, uid);
  const user = { ...req.user, name: str(b.name, 80) || req.user.name, role: str(b.role, 80), about: str(b.about, 1000), niche: str(b.niche, 200), tone: str(b.tone, 100), daily_minutes: minutes };
  let goalId = null;
  const title = str(b.goal, 300);
  if (title) {
    const { lastInsertRowid } = q.run('INSERT INTO goals (user_id, title, why, area, deadline) VALUES (?, ?, ?, ?, ?)',
      uid, title, str(b.why, 2000), str(b.area, 60) || 'geral', isDate(b.deadline) ? b.deadline : null);
    goalId = Number(lastInsertRowid);
    const g = q.get('SELECT * FROM goals WHERE id = ?', goalId);
    const plan = await ai.goalPlan(user, g, 7);
    insertTasks(uid, goalId, plan.tasks, localDate(), 'ai');
    q.run('UPDATE goals SET plan = ? WHERE id = ?',
      `${plan.summary}\n\n**Marcos**\n${plan.milestones.map((m) => `- ${m.title} — ${m.by}`).join('\n')}\n\n**Primeiro passo agora:** ${plan.first_step}`, goalId);
    addMessage(uid, 'assistant', `Prontinho, ${user.name.split(' ')[0]}! 🎉 Criei sua meta **${title}** com um plano de 7 dias.\n\n**Seu primeiro passo agora:** ${plan.first_step}\n\nAs tarefas de hoje estão logo acima. Toque em **✓ Feito** quando terminar, ou em **🆘 Me ajuda** que eu te entrego a solução.`);
  }
  if (b.launch_plan) importLaunchPlan(uid);
  q.run('UPDATE users SET onboarded = 1 WHERE id = ?', uid);
  res.json({ ok: true, goal_id: goalId });
}));

app.post('/api/onboarding/skip', (req, res) => {
  q.run('UPDATE users SET onboarded = 1 WHERE id = ?', req.user.id);
  res.json({ ok: true });
});

// ---------- export ----------
app.get('/api/export', (req, res) => {
  const id = req.user.id;
  res.setHeader('Content-Disposition', 'attachment; filename="rumo-backup.json"');
  res.json({
    exported_at: new Date().toISOString(),
    user: req.user,
    goals: q.all('SELECT * FROM goals WHERE user_id = ?', id),
    tasks: q.all('SELECT * FROM tasks WHERE user_id = ?', id),
    events: q.all('SELECT * FROM events WHERE user_id = ?', id),
    notes: q.all('SELECT * FROM notes WHERE user_id = ?', id),
    checkins: q.all('SELECT * FROM checkins WHERE user_id = ?', id),
    messages: q.all('SELECT role, content, created_at FROM messages WHERE user_id = ?', id),
  });
});

app.use('/api', (req, res) => res.status(404).json({ error: 'Rota não encontrada.' }));

// ---------- static frontend ----------
const pub = path.resolve('public');
app.use(express.static(pub, { maxAge: '1h', setHeaders: (res, p) => { if (p.endsWith('sw.js') || p.endsWith('.html')) res.setHeader('Cache-Control', 'no-cache'); } }));
app.get(/^\/(?!api).*/, (req, res) => res.sendFile(path.join(pub, 'index.html')));

// eslint-disable-next-line no-unused-vars
app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).json({ error: err.message || 'Erro interno.' });
});
