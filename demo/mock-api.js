// Backend simulado que roda no navegador, usado só na versão de teste (link).
// Intercepta fetch('/api/...') e responde como o servidor real em modo demonstração.
// Os dados ficam no navegador de quem está testando.
import { localDate, localDateTime, addDays } from '../server/time.js';
import * as demo from '../server/demo.js';
import { LAUNCH_PLAN } from '../server/launchPlan.js';

const KEY = 'rumo-demo-db-v2';
const empty = () => ({ seq: 1, session: null, users: [], goals: [], tasks: [], events: [], notes: [], messages: [], checkins: [] });
let db;
try { db = JSON.parse(localStorage.getItem(KEY)) || empty(); } catch { db = empty(); }
const persist = () => { try { localStorage.setItem(KEY, JSON.stringify(db)); } catch { /* sem storage: só memória */ } };
const id = () => db.seq++;
const now = () => localDateTime().replace('T', ' ');
const isDate = (v) => typeof v === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v);
const isDT = (v) => typeof v === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(v);
const s = (v, max = 5000) => (typeof v === 'string' ? v.trim().slice(0, max) : '');

class HttpError extends Error { constructor(status, msg) { super(msg); this.status = status; } }
const fail = (status, msg) => { throw new HttpError(status, msg); };
const json = (data, status = 200) => new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

function me() {
  const u = db.users.find((x) => x.id === db.session);
  if (!u) fail(401, 'Faça login para continuar.');
  return u;
}
const mine = (list, uid) => list.filter((x) => x.user_id === uid);
const own = (list, uid, rid) => list.find((x) => x.user_id === uid && x.id === Number(rid)) || null;
const goalId = (uid, gid) => (gid == null || gid === '' ? null : own(db.goals, uid, gid)?.id ?? null);

function addTask(uid, t, source = 'manual') {
  const task = {
    id: id(), user_id: uid, goal_id: goalId(uid, t.goal_id), title: s(t.title, 300), detail: s(t.detail, 2000),
    due_date: isDate(t.due_date) ? t.due_date : localDate(), minutes: Math.max(1, Math.min(600, Number(t.minutes) || 15)),
    done: 0, done_at: null, source, created_at: now(),
  };
  db.tasks.push(task);
  return task;
}
function addEvent(uid, b) {
  if (!s(b.title) || !isDT(b.start)) return null;
  const ev = { id: id(), user_id: uid, title: s(b.title, 300), start: b.start, end: isDT(b.end) ? b.end : null, notes: s(b.notes, 2000), created_at: now() };
  db.events.push(ev);
  return ev;
}
function progress(uid) {
  return mine(db.goals, uid).map((g) => {
    const ts = db.tasks.filter((t) => t.goal_id === g.id);
    return { ...g, total: ts.length, done: ts.filter((t) => t.done).length };
  }).sort((a, b) => (b.status === 'ativa') - (a.status === 'ativa') || b.id - a.id);
}
function streak(uid) {
  const days = new Set(mine(db.tasks, uid).filter((t) => t.done).map((t) => t.due_date));
  let day = localDate();
  if (!days.has(day)) day = addDays(day, -1);
  let n = 0;
  while (days.has(day)) { n++; day = addDays(day, -1); }
  return n;
}
const byDateId = (a, b) => (a.due_date < b.due_date ? -1 : a.due_date > b.due_date ? 1 : a.done - b.done || a.id - b.id);

const routes = [];
const on = (method, pattern, fn) => routes.push({ method, re: new RegExp(`^${pattern.replace(/:\w+/g, '([^/]+)')}$`), fn });

on('POST', '/api/auth/register', (b) => {
  const email = s(b.email, 160).toLowerCase();
  if (!s(b.name) || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) fail(400, 'Informe nome e e-mail válidos.');
  if (String(b.password || '').length < 6) fail(400, 'A senha precisa ter pelo menos 6 caracteres.');
  if (db.users.some((u) => u.email === email)) fail(409, 'E-mail já cadastrado.');
  const u = { id: id(), name: s(b.name, 80), email, password: b.password, about: '', niche: '', tone: 'motivador e direto', role: '', daily_minutes: 30, onboarded: 0 };
  db.users.push(u);
  db.session = u.id;
  return { ok: true };
});
on('POST', '/api/auth/login', (b) => {
  const u = db.users.find((x) => x.email === s(b.email).toLowerCase() && x.password === b.password);
  if (!u) fail(401, 'E-mail ou senha incorretos.');
  db.session = u.id;
  return { ok: true };
});
on('POST', '/api/auth/logout', () => { db.session = null; return { ok: true }; });

on('GET', '/api/me', () => { const { password, ...user } = me(); return { user, ai: false, today: localDate() }; });
on('PUT', '/api/me', (b) => { const u = me(); Object.assign(u, { name: s(b.name, 80) || u.name, about: s(b.about, 1000), niche: s(b.niche, 200), tone: s(b.tone, 100) || u.tone, daily_minutes: Number(b.daily_minutes) || u.daily_minutes }); return { ok: true }; });
on('DELETE', '/api/me', () => {
  const u = me();
  for (const k of ['goals', 'tasks', 'events', 'notes', 'messages', 'checkins']) db[k] = db[k].filter((x) => x.user_id !== u.id);
  db.users = db.users.filter((x) => x.id !== u.id);
  db.session = null;
  return { ok: true };
});

on('GET', '/api/today', () => {
  const u = me();
  const today = localDate();
  const ts = mine(db.tasks, u.id);
  const week = {};
  for (const t of ts.filter((t) => t.due_date >= addDays(today, -6) && t.due_date <= today)) {
    (week[t.due_date] ||= { d: t.due_date, total: 0, done: 0 }).total++;
    if (t.done) week[t.due_date].done++;
  }
  return {
    date: today,
    tasks: ts.filter((t) => t.due_date === today).sort(byDateId),
    overdue: ts.filter((t) => t.due_date < today && !t.done).sort((a, b) => (a.due_date < b.due_date ? 1 : -1)).slice(0, 20),
    events: mine(db.events, u.id).filter((e) => e.start >= today && e.start < addDays(today, 2)).sort((a, b) => (a.start < b.start ? -1 : 1)),
    goals: progress(u.id).filter((g) => g.status === 'ativa'),
    streak: streak(u.id),
    checkin: mine(db.checkins, u.id).find((c) => c.day === today) || null,
    week: Object.values(week),
  };
});
on('POST', '/api/checkin', (b) => {
  const u = me();
  const day = localDate();
  db.checkins = db.checkins.filter((c) => !(c.user_id === u.id && c.day === day));
  db.checkins.push({ id: id(), user_id: u.id, day, mood: Math.max(1, Math.min(5, Number(b.mood) || 3)), note: s(b.note) });
  return { ok: true };
});

on('GET', '/api/tasks', (b, q) => {
  const u = me();
  const ts = mine(db.tasks, u.id);
  if (isDate(q.get('from')) && isDate(q.get('to'))) return ts.filter((t) => t.due_date >= q.get('from') && t.due_date <= q.get('to')).sort(byDateId);
  const date = isDate(q.get('date')) ? q.get('date') : localDate();
  return ts.filter((t) => t.due_date === date).sort(byDateId);
});
on('POST', '/api/tasks', (b) => { if (!s(b.title)) fail(400, 'Escreva a tarefa.'); return addTask(me().id, b); });
on('PATCH', '/api/tasks/:id', (b, q, rid) => {
  const t = own(db.tasks, me().id, rid) || fail(404, 'Tarefa não encontrada.');
  if (b.title) t.title = s(b.title, 300);
  if (b.detail !== undefined) t.detail = s(b.detail);
  if (isDate(b.due_date)) t.due_date = b.due_date;
  if (b.minutes) t.minutes = Number(b.minutes);
  if (b.done !== undefined) { t.done = b.done ? 1 : 0; t.done_at = t.done ? new Date().toISOString() : null; }
  return t;
});
on('DELETE', '/api/tasks/:id', (b, q, rid) => { const uid = me().id; db.tasks = db.tasks.filter((t) => !(t.user_id === uid && t.id === Number(rid))); return { ok: true }; });

on('GET', '/api/goals', () => progress(me().id));
function importLaunch(u) {
  const start = localDate();
  const g = { id: id(), user_id: u.id, title: LAUNCH_PLAN.title, why: LAUNCH_PLAN.why, area: LAUNCH_PLAN.area, deadline: addDays(start, 29), status: 'ativa', created_at: now(),
    plan: 'Plano de 30 dias em 4 semanas: **Fundação** → **Ritmo** → **Prova e parcerias** → **Conversão e escala**. Uma tarefa por dia.' };
  db.goals.push(g);
  LAUNCH_PLAN.tasks.forEach(([title, detail, minutes], i) => addTask(u.id, { title, detail, minutes, goal_id: g.id, due_date: addDays(start, i) }, 'plano'));
  return { id: g.id };
}
on('POST', '/api/goals/import-launch-plan', () => importLaunch(me()));

on('POST', '/api/onboarding', async (b) => {
  const u = me();
  Object.assign(u, { name: s(b.name, 80) || u.name, role: s(b.role, 80), about: s(b.about, 1000), niche: s(b.niche, 200), tone: s(b.tone, 100) || u.tone, daily_minutes: Number(b.daily_minutes) || 30 });
  let goal = null;
  if (s(b.goal)) {
    await wait(900);
    goal = { id: id(), user_id: u.id, title: s(b.goal, 300), why: s(b.why, 2000), area: s(b.area, 60) || 'geral', deadline: isDate(b.deadline) ? b.deadline : null, status: 'ativa', created_at: now(), plan: '' };
    db.goals.push(goal);
    const plan = demo.goalPlan(goal, 7);
    plan.tasks.forEach((t) => addTask(u.id, { ...t, goal_id: goal.id, due_date: addDays(localDate(), t.day_offset) }, 'ai'));
    goal.plan = `${plan.summary}\n\n**Primeiro passo agora:** ${plan.first_step}`;
    db.messages.push({ id: id(), user_id: u.id, role: 'assistant', created_at: now(),
      content: `Prontinho, ${u.name.split(' ')[0]}! 🎉 Criei sua meta **${goal.title}** com um plano de 7 dias.\n\n**Seu primeiro passo agora:** ${plan.first_step}\n\nAs tarefas de hoje estão logo acima. Toque em **✓ Feito** quando terminar, ou em **🆘 Me ajuda** que eu te entrego a solução.` });
  }
  if (b.launch_plan) importLaunch(u);
  u.onboarded = 1;
  return { ok: true, goal_id: goal?.id ?? null };
});
on('POST', '/api/onboarding/skip', () => { me().onboarded = 1; return { ok: true }; });
on('GET', '/api/goals/:id', (b, q, rid) => {
  const g = own(db.goals, me().id, rid) || fail(404, 'Meta não encontrada.');
  return { ...g, tasks: db.tasks.filter((t) => t.goal_id === g.id).sort(byDateId) };
});
on('POST', '/api/goals', (b) => {
  if (!s(b.title)) fail(400, 'Descreva a meta.');
  const g = { id: id(), user_id: me().id, title: s(b.title, 300), why: s(b.why, 2000), area: s(b.area, 60) || 'geral', deadline: isDate(b.deadline) ? b.deadline : null, status: 'ativa', plan: '', created_at: now() };
  db.goals.push(g);
  return g;
});
on('PATCH', '/api/goals/:id', (b, q, rid) => {
  const g = own(db.goals, me().id, rid) || fail(404, 'Meta não encontrada.');
  if (['ativa', 'pausada', 'concluida'].includes(b.status)) g.status = b.status;
  if (b.title) g.title = s(b.title, 300);
  return g;
});
on('DELETE', '/api/goals/:id', (b, q, rid) => {
  const g = own(db.goals, me().id, rid);
  if (g) { db.goals = db.goals.filter((x) => x !== g); db.tasks = db.tasks.filter((t) => t.goal_id !== g.id); }
  return { ok: true };
});
on('POST', '/api/goals/:id/plan', async (b, q, rid) => {
  const u = me();
  const g = own(db.goals, u.id, rid) || fail(404, 'Meta não encontrada.');
  await wait(700);
  const plan = demo.goalPlan(g, Math.max(3, Math.min(14, Number(b.days) || 7)));
  const start = isDate(b.start) ? b.start : localDate();
  plan.tasks.forEach((t) => addTask(u.id, { ...t, goal_id: g.id, due_date: addDays(start, t.day_offset) }, 'ai'));
  g.plan = `${plan.summary}\n\n**Marcos**\n${plan.milestones.map((m) => `- ${m.title} — ${m.by}`).join('\n')}\n\n**Primeiro passo agora:** ${plan.first_step}`;
  return { plan, planText: g.plan };
});

on('POST', '/api/ai/daily', async () => {
  const u = me();
  await wait(600);
  const out = demo.dailyTasks(u);
  out.tasks.forEach((t) => addTask(u.id, t, 'ai'));
  return { message: out.message, count: out.tasks.length };
});

on('GET', '/api/events', (b, q) => {
  const from = isDate(q.get('from')) ? q.get('from') : addDays(localDate(), -1);
  const to = isDate(q.get('to')) ? q.get('to') : addDays(from, 31);
  return mine(db.events, me().id).filter((e) => e.start >= from && e.start < addDays(to, 1)).sort((a, b) => (a.start < b.start ? -1 : 1));
});
on('POST', '/api/events', (b) => addEvent(me().id, b) || fail(400, 'Informe título e data/hora.'));
on('POST', '/api/events/quick', async (b) => {
  if (!s(b.text)) fail(400, 'Escreva o compromisso.');
  await wait(400);
  return addEvent(me().id, demo.parseEvent(s(b.text, 500))) || fail(400, 'Não entendi a data. Tente: "dentista amanhã às 15h".');
});
on('DELETE', '/api/events/:id', (b, q, rid) => { const uid = me().id; db.events = db.events.filter((e) => !(e.user_id === uid && e.id === Number(rid))); return { ok: true }; });

on('GET', '/api/notes', () => mine(db.notes, me().id).sort((a, b) => (a.updated_at < b.updated_at ? 1 : -1)).map((n) => ({ ...n, preview: n.content.slice(0, 160) })));
on('GET', '/api/notes/:id', (b, q, rid) => own(db.notes, me().id, rid) || fail(404, 'Nota não encontrada.'));
on('POST', '/api/notes', (b) => {
  const n = { id: id(), user_id: me().id, title: s(b.title, 200) || 'Sem título', content: s(b.content, 200000), kind: s(b.kind, 20) || 'nota', updated_at: now() };
  db.notes.push(n);
  return n;
});
on('PUT', '/api/notes/:id', (b, q, rid) => {
  const n = own(db.notes, me().id, rid) || fail(404, 'Nota não encontrada.');
  Object.assign(n, { title: s(b.title, 200) || 'Sem título', content: s(b.content, 200000), updated_at: now() });
  return { ok: true };
});
on('DELETE', '/api/notes/:id', (b, q, rid) => { const uid = me().id; db.notes = db.notes.filter((n) => !(n.user_id === uid && n.id === Number(rid))); return { ok: true }; });

on('POST', '/api/ai/edit', async (b) => { me(); if (!s(b.text)) fail(400, 'Escreva algum texto primeiro.'); await wait(500); return { text: demo.edit(s(b.action), s(b.text, 50000)) }; });
on('POST', '/api/ai/amplify', async (b) => { me(); if (!s(b.idea)) fail(400, 'Descreva sua ideia.'); await wait(800); return demo.amplify(s(b.idea, 4000)); });
on('POST', '/api/ai/caption', async (b) => { me(); if (!s(b.topic)) fail(400, 'Sobre o que é o post?'); await wait(700); return demo.captions(s(b.topic), s(b.platform)); });
on('POST', '/api/ai/review', async () => {
  const u = me();
  await wait(600);
  const today = localDate();
  const rows = mine(db.tasks, u.id).filter((t) => t.due_date >= addDays(today, -6) && t.due_date <= today);
  return { text: demo.review(`Tarefas: ${rows.filter((r) => r.done).length}/${rows.length} concluídas.`) };
});

on('GET', '/api/chat', (b, q) => { const all = mine(db.messages, me().id); return q.get('today') ? all.filter((m) => m.created_at >= localDate()).slice(-60) : all.slice(-100); });
on('DELETE', '/api/chat', () => { const uid = me().id; db.messages = db.messages.filter((m) => m.user_id !== uid); return { ok: true }; });

function chatStream(b) {
  const u = me();
  const helpTask = b.help_task_id ? own(db.tasks, u.id, b.help_task_id) : null;
  const message = helpTask ? `🆘 Me ajuda com: ${helpTask.title}` : s(b.message, 8000);
  if (!message) fail(400, 'Mensagem vazia.');
  db.messages.push({ id: id(), user_id: u.id, role: 'user', content: message, created_at: now() });
  const done = [];
  const acts = {
    concluir_tarefa: ({ task_id }) => { const t = own(db.tasks, u.id, task_id); t.done = 1; return `✅ Feito: "${t.title}"`; },
    reagendar_tarefa: ({ task_id, due_date }) => { const t = own(db.tasks, u.id, task_id); t.due_date = due_date; return `⏭️ "${t.title}" movida para amanhã`; },
    criar_compromisso: (e) => { const ev = addEvent(u.id, e); return ev ? `📅 Agendado: "${ev.title}" em ${ev.start.slice(8, 10)}/${ev.start.slice(5, 7)} às ${ev.start.slice(11)}` : 'Não entendi a data.'; },
    criar_tarefa: (t) => { addTask(u.id, t, 'ai'); return `➕ Tarefa criada: "${t.title}"`; },
  };
  const today = localDate();
  const reply = demo.chatTurn(u, message, {
    helpTask,
    todayTasks: mine(db.tasks, u.id).filter((t) => t.due_date === today),
    act: (name, input) => { const d = acts[name](input); done.push(d); return d; },
  }).replace('configure `ANTHROPIC_API_KEY` para respostas reais da IA', 'na versão publicada a IA real personaliza tudo para você');
  db.messages.push({ id: id(), user_id: u.id, role: 'assistant', content: reply, created_at: now() });
  persist();
  const enc = new TextEncoder();
  const body = new ReadableStream({
    async start(ctrl) {
      const send = (o) => ctrl.enqueue(enc.encode(`data: ${JSON.stringify(o)}\n\n`));
      await wait(400);
      for (const chunk of reply.match(/[\s\S]{1,18}/g)) { send({ t: chunk }); await wait(15); }
      for (const a of done) send({ action: a });
      send({ done: true });
      ctrl.close();
    },
  });
  return new Response(body, { headers: { 'content-type': 'text/event-stream' } });
}

const realFetch = window.fetch.bind(window);
window.fetch = async (input, init = {}) => {
  const url = new URL(typeof input === 'string' ? input : input.url, location.href);
  if (!url.pathname.startsWith('/api/')) return realFetch(input, init);
  const method = (init.method || 'GET').toUpperCase();
  let body = {};
  try { body = init.body ? JSON.parse(init.body) : {}; } catch { /* corpo vazio */ }
  try {
    if (method === 'POST' && url.pathname === '/api/ai/chat') return chatStream(body);
    for (const r of routes) {
      const m = r.method === method && url.pathname.match(r.re);
      if (m) {
        const data = await r.fn(body, url.searchParams, m[1]);
        persist();
        return json(data, method === 'POST' && /register|goals$|tasks$|notes$|events/.test(url.pathname) ? 201 : 200);
      }
    }
    return json({ error: 'Rota não encontrada.' }, 404);
  } catch (e) {
    return json({ error: e.message }, e.status || 500);
  }
};

// Conta de teste pronta (ainda não configurada, para passar pelo passo a passo).
if (!db.users.length) {
  db.users.push({ id: id(), name: 'Visitante', email: 'teste@rumo.app', password: 'rumo123', about: '', niche: '', tone: 'motivador e direto', role: '', daily_minutes: 30, onboarded: 0 });
  persist();
}
