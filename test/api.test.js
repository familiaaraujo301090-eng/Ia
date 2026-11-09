import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import os from 'node:os';
import path from 'node:path';
import fs from 'node:fs';

const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'rumo-test-'));
process.env.DB_PATH = path.join(dir, 'test.db');
delete process.env.ANTHROPIC_API_KEY;
delete process.env.ANTHROPIC_AUTH_TOKEN;
process.env.ADMIN_SECRET = 'segredo-de-admin-bem-longo-123';
process.env.REGISTER_PER_HOUR = '1000';
process.env.FREE_AI_PER_DAY = '40';

const { app } = await import('../server/app.js');
let server, base;
before(async () => { server = app.listen(0); await new Promise((r) => server.once('listening', r)); base = `http://127.0.0.1:${server.address().port}`; });
after(() => { server.close(); fs.rmSync(dir, { recursive: true, force: true }); });

async function client(email) {
  let cookie = '';
  const call = async (p, method = 'GET', body) => {
    const res = await fetch(base + p, { method, headers: { 'content-type': 'application/json', cookie }, body: body && JSON.stringify(body) });
    const sc = res.headers.get('set-cookie');
    if (sc) cookie = sc.split(';')[0];
    const ct = res.headers.get('content-type') || '';
    return { status: res.status, body: ct.includes('json') ? await res.json() : await res.text() };
  };
  const r = await call('/api/auth/register', 'POST', { name: 'U', email, password: 'segredo1' });
  call.cookie = () => cookie;
  assert.equal(r.status, 201);
  return call;
}

test('requires login', async () => {
  const res = await fetch(`${base}/api/today`);
  assert.equal(res.status, 401);
});

test('register validation and duplicate email', async () => {
  await client('dup@x.com');
  const res = await fetch(`${base}/api/auth/register`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ name: 'A', email: 'dup@x.com', password: 'segredo1' }) });
  assert.equal(res.status, 409);
  const weak = await fetch(`${base}/api/auth/register`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ name: 'A', email: 'w@x.com', password: '1234567' }) });
  assert.equal(weak.status, 400);
});

test('login with wrong password fails', async () => {
  await client('login@x.com');
  const res = await fetch(`${base}/api/auth/login`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ email: 'login@x.com', password: 'errada' }) });
  assert.equal(res.status, 401);
  const ok = await fetch(`${base}/api/auth/login`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ email: 'LOGIN@x.com', password: 'segredo1' }) });
  assert.equal(ok.status, 200);
});

test('goal plan creates daily tasks and progress', async () => {
  const c = await client('plan@x.com');
  const g = await c('/api/goals', 'POST', { title: 'Correr 5km', deadline: '2030-01-01' });
  assert.equal(g.status, 201);
  const p = await c(`/api/goals/${g.body.id}/plan`, 'POST', { days: 5 });
  assert.equal(p.status, 200);
  const detail = await c(`/api/goals/${g.body.id}`);
  assert.equal(detail.body.tasks.length, 5);
  const today = await c('/api/today');
  assert.ok(today.body.tasks.some((t) => t.goal_id === g.body.id));
  const t = today.body.tasks[0];
  await c(`/api/tasks/${t.id}`, 'PATCH', { done: true });
  const after = await c('/api/today');
  assert.equal(after.body.streak, 1);
});

test('launch plan import creates 30 tasks', async () => {
  const c = await client('launch@x.com');
  const r = await c('/api/goals/import-launch-plan', 'POST', {});
  const g = await c(`/api/goals/${r.body.id}`);
  assert.equal(g.body.tasks.length, 30);
  assert.notEqual(g.body.tasks[0].due_date, g.body.tasks[29].due_date);
});

test('users cannot see or modify each other data', async () => {
  const a = await client('a@x.com');
  const b = await client('b@x.com');
  const g = await a('/api/goals', 'POST', { title: 'Segredo da A' });
  const t = await a('/api/tasks', 'POST', { title: 'tarefa da A' });
  const n = await a('/api/notes', 'POST', { title: 'nota A', content: 'privado' });
  const e = await a('/api/events', 'POST', { title: 'evento A', start: '2030-01-01T10:00' });
  assert.equal((await b(`/api/goals/${g.body.id}`)).status, 404);
  assert.equal((await b(`/api/notes/${n.body.id}`)).status, 404);
  assert.equal((await b(`/api/tasks/${t.body.id}`, 'PATCH', { done: true })).status, 404);
  assert.equal((await b(`/api/events/${e.body.id}`, 'PATCH', { title: 'x' })).status, 404);
  await b(`/api/goals/${g.body.id}`, 'DELETE');
  await b(`/api/notes/${n.body.id}`, 'DELETE');
  assert.equal((await a(`/api/goals/${g.body.id}`)).status, 200);
  assert.equal((await a(`/api/notes/${n.body.id}`)).status, 200);
  // B can't attach its task to A's goal
  const bt = await b('/api/tasks', 'POST', { title: 'x', goal_id: g.body.id });
  assert.equal(bt.body.goal_id, null);
  assert.equal((await b('/api/goals')).body.length, 0);
  assert.equal((await b('/api/notes')).body.length, 0);
});

test('AI tools respond in demo mode', async () => {
  const c = await client('ai@x.com');
  assert.ok((await c('/api/ai/amplify', 'POST', { idea: 'loja' })).body.angles.length > 0);
  assert.equal((await c('/api/ai/caption', 'POST', { topic: 'post' })).body.options.length, 3);
  assert.ok((await c('/api/ai/edit', 'POST', { action: 'tarefas', text: 'a. b' })).body.text.includes('- [ ]'));
  const ev = await c('/api/events/quick', 'POST', { text: 'reunião amanhã às 14h' });
  assert.match(ev.body.start, /T14:00$/);
  const chat = await c('/api/ai/chat', 'POST', { message: 'oi' });
  assert.match(chat.body, /"done":true/);
  assert.equal((await c('/api/chat')).body.length, 2);
});

test('onboarding saves profile, creates goal with plan and launch plan', async () => {
  const c = await client('onb@x.com');
  assert.equal((await c('/api/me')).body.user.onboarded, 0);
  const r = await c('/api/onboarding', 'POST', { name: 'Ana', role: 'Empreendedor(a)', about: 'vendo bolos', goal: 'Faturar 5 mil', why: 'liberdade', deadline: '2030-01-01', daily_minutes: 45, tone: 'gentil e acolhedor', launch_plan: true });
  assert.equal(r.status, 200);
  const me = (await c('/api/me')).body.user;
  assert.equal(me.onboarded, 1);
  assert.equal(me.daily_minutes, 45);
  assert.equal(me.name, 'Ana');
  const goals = (await c('/api/goals')).body;
  assert.equal(goals.length, 2);
  const msgs = (await c('/api/chat?today=1')).body;
  assert.equal(msgs.length, 1);
  assert.match(msgs[0].content, /Faturar 5 mil/);
});

test('chat acts on tasks: done, postpone, help', async () => {
  const c = await client('act@x.com');
  const t1 = (await c('/api/tasks', 'POST', { title: 'Gravar vídeo de apresentação' })).body;
  const t2 = (await c('/api/tasks', 'POST', { title: 'Responder comentários' })).body;
  const t3 = (await c('/api/tasks', 'POST', { title: 'Criar página de vendas' })).body;
  const help = await c('/api/ai/chat', 'POST', { help_task_id: t1.id });
  assert.match(help.body, /capcut|canva/i);
  const late = await c('/api/ai/chat', 'POST', { message: 'Estou sem tempo hoje' });
  assert.match(late.body, /movida para amanhã/);
  const today = (await c('/api/today')).body.tasks;
  assert.equal(today.length, 1);
  const all = await c('/api/ai/chat', 'POST', { message: 'Terminei tudo!' });
  assert.match(all.body, /Feito/);
  assert.equal((await c('/api/today')).body.tasks.filter((t) => t.done).length, 1);
  // someone else can't ask help about my task
  const other = await client('act2@x.com');
  const r = await other('/api/ai/chat', 'POST', { help_task_id: t2.id });
  assert.equal(r.status, 400);
  assert.ok(t3.id);
});

test('habits create daily tasks and track streak', async () => {
  const c = await client('hab@x.com');
  const h = await c('/api/habits', 'POST', { title: 'Beber 2L de água', minutes: 5, days: '0123456' });
  assert.equal(h.status, 201);
  const today = (await c('/api/today')).body;
  const t = today.tasks.find((x) => x.habit_id === h.body.id);
  assert.ok(t);
  await c('/api/today'); // não duplica
  assert.equal((await c('/api/today')).body.tasks.filter((x) => x.habit_id === h.body.id).length, 1);
  await c(`/api/tasks/${t.id}`, 'PATCH', { done: true });
  const list = (await c('/api/habits')).body;
  assert.equal(list[0].streak, 1);
  await c(`/api/habits/${h.body.id}`, 'DELETE');
  assert.equal((await c('/api/habits')).body.length, 0);
});

test('repeating events expand over the range', async () => {
  const c = await client('rep@x.com');
  const today = (await c('/api/me')).body.today;
  await c('/api/events', 'POST', { title: 'Academia', start: `${today}T07:00`, repeat: 'diario' });
  await c('/api/events', 'POST', { title: 'Reunião única', start: `${today}T10:00` });
  const evs = (await c(`/api/events?from=${today}&to=${today.slice(0, 8)}${String(Number(today.slice(8)) + 0).padStart(2, '0')}`)).body;
  assert.ok(evs.length >= 2);
  const week = (await fetchJSON(c, `/api/events?from=${today}`)).filter((e) => e.title === 'Academia');
  assert.ok(week.length >= 28);
});
async function fetchJSON(c, p) { return (await c(p)).body; }

test('password change and reset', async () => {
  const c = await client('pw@x.com');
  assert.equal((await c('/api/me/password', 'PUT', { current: 'errada', password: 'nova1234' })).status, 400);
  assert.equal((await c('/api/me/password', 'PUT', { current: 'segredo1', password: 'nova1234' })).status, 200);
  const login = await fetch(`${base}/api/auth/login`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ email: 'pw@x.com', password: 'nova1234' }) });
  assert.equal(login.status, 200);
  const forgot = await fetch(`${base}/api/auth/forgot`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ email: 'nao-existe@x.com' }) });
  assert.equal(forgot.status, 200);
  const badReset = await fetch(`${base}/api/auth/reset`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ token: 'x', password: 'abcdefgh' }) });
  assert.equal(badReset.status, 400);
});

test('reset token from forgot works once', async () => {
  await client('rs@x.com');
  const logs = [];
  const orig = console.log;
  console.log = (...a) => logs.push(a.join(' '));
  await fetch(`${base}/api/auth/forgot`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ email: 'rs@x.com' }) });
  console.log = orig;
  const token = logs.join('\n').match(/redefinir\/([a-f0-9]{64})/)[1];
  const r1 = await fetch(`${base}/api/auth/reset`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ token, password: 'outra123' }) });
  assert.equal(r1.status, 200);
  const r2 = await fetch(`${base}/api/auth/reset`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ token, password: 'outra123' }) });
  assert.equal(r2.status, 400);
});

test('daily AI limit by plan and admin can upgrade', async () => {
  const c = await client('lim@x.com');
  process.env.FREE_AI_PER_DAY = '2';
  assert.equal((await c('/api/ai/amplify', 'POST', { idea: 'a' })).status, 200);
  assert.equal((await c('/api/ai/amplify', 'POST', { idea: 'a' })).status, 200);
  const third = await c('/api/ai/amplify', 'POST', { idea: 'a' });
  assert.equal(third.status, 429);
  assert.match(third.body.error, /Grátis/);
  const me = (await c('/api/me')).body;
  assert.equal(me.usage.used, 2);
  const adm = await client('admin@x.com');
  assert.equal((await c('/api/admin/stats')).status, 403);
  assert.equal((await adm('/api/admin/stats')).status, 403); // e-mail não dá acesso
  assert.equal((await adm('/api/admin/claim', 'POST', { secret: 'errado' })).status, 403);
  assert.equal((await adm('/api/admin/claim', 'POST', { secret: 'segredo-de-admin-bem-longo-123' })).status, 200);
  const stats = await adm('/api/admin/stats');
  assert.equal(stats.status, 200);
  assert.ok(stats.body.users >= 1);
  assert.equal((await adm(`/api/admin/users/${me.user.id}`, 'PATCH', { plan: 'pro' })).status, 200);
  assert.equal((await c('/api/ai/amplify', 'POST', { idea: 'a' })).status, 200);
  process.env.FREE_AI_PER_DAY = '40';
});

test('needs_plan lists active goals without upcoming tasks', async () => {
  const c = await client('np@x.com');
  const g = (await c('/api/goals', 'POST', { title: 'Meta sem plano' })).body;
  assert.ok((await c('/api/today')).body.needs_plan.some((x) => x.id === g.id));
  await c(`/api/goals/${g.id}/plan`, 'POST', { days: 3 });
  assert.ok(!(await c('/api/today')).body.needs_plan.some((x) => x.id === g.id));
});

test('reminder loop with no devices sends nothing', async () => {
  const { sendDueReminders } = await import('../server/extras.js');
  assert.equal(await sendDueReminders(), 0);
});

// ---------------- segurança ----------------
const post = (p, body, headers = {}) => fetch(`${base}${p}`, { method: 'POST', headers: { 'content-type': 'application/json', ...headers }, body: JSON.stringify(body) });

test('security headers are present', async () => {
  const res = await fetch(`${base}/`);
  assert.match(res.headers.get('content-security-policy'), /frame-ancestors 'none'/);
  assert.match(res.headers.get('content-security-policy'), /script-src 'self'/);
  assert.equal(res.headers.get('x-frame-options'), 'DENY');
  assert.equal(res.headers.get('x-content-type-options'), 'nosniff');
  assert.equal(res.headers.get('x-powered-by'), null);
  const api = await fetch(`${base}/api/health`);
  assert.equal(api.headers.get('cache-control'), 'no-store');
});

test('cross-site requests are blocked (CSRF)', async () => {
  const c = await client('csrf@x.com');
  const evil = await fetch(`${base}/api/goals`, { method: 'POST', headers: { 'content-type': 'application/json', origin: 'https://evil.example', cookie: c.cookie() }, body: JSON.stringify({ title: 'x' }) });
  assert.equal(evil.status, 403);
  const form = await fetch(`${base}/api/goals`, { method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded', cookie: c.cookie() }, body: 'title=x' });
  assert.equal(form.status, 415);
  const site = await fetch(`${base}/api/goals`, { method: 'POST', headers: { 'content-type': 'application/json', 'sec-fetch-site': 'cross-site', cookie: c.cookie() }, body: JSON.stringify({ title: 'x' }) });
  assert.equal(site.status, 403);
  assert.equal((await c('/api/goals')).body.length, 0);
});

test('sessions are stored hashed and passwords use strong scrypt', async () => {
  const c = await client('hash@x.com');
  const { db } = await import('../server/db.js');
  const token = decodeURIComponent(c.cookie().split('=')[1]);
  assert.equal(db.prepare('SELECT COUNT(*) c FROM sessions WHERE token = ?').get(token).c, 0);
  const u = db.prepare('SELECT pass_hash FROM users WHERE email = ?').get('hash@x.com');
  assert.match(u.pass_hash, /^scrypt\$32768\$8\$1\$/);
});

test('legacy password hashes still log in and get upgraded', async () => {
  const crypto = await import('node:crypto');
  const { db } = await import('../server/db.js');
  const salt = 'abcd';
  const legacy = `${salt}:${crypto.scryptSync('antiga12', salt, 64).toString('hex')}`;
  db.prepare('INSERT INTO users (name, email, pass_hash) VALUES (?, ?, ?)').run('Old', 'old@x.com', legacy);
  assert.equal((await post('/api/auth/login', { email: 'old@x.com', password: 'antiga12' })).status, 200);
  assert.match(db.prepare('SELECT pass_hash FROM users WHERE email = ?').get('old@x.com').pass_hash, /^scrypt\$/);
});

test('password rules and brute force limits', async () => {
  assert.equal((await post('/api/auth/register', { name: 'A', email: 'long@x.com', password: 'x'.repeat(201) })).status, 400);
  await client('brute@x.com');
  let last;
  for (let i = 0; i < 11; i++) last = await post('/api/auth/login', { email: 'brute@x.com', password: `errada${i}` });
  assert.equal(last.status, 429);
  const nobody = await post('/api/auth/login', { email: 'ninguem@x.com', password: 'qualquer1' });
  assert.equal(nobody.status, 401);
  assert.match((await nobody.json()).error, /E-mail ou senha incorretos/);
});

test('push only accepts real push services (no SSRF)', async () => {
  const c = await client('push@x.com');
  const keys = { p256dh: 'BOr8x', auth: 'abc' };
  for (const endpoint of ['http://169.254.169.254/latest/meta-data', 'https://localhost/x', 'https://evil.example/push', 'https://fcm.googleapis.com:8443/x', 'file:///etc/passwd']) {
    assert.equal((await c('/api/push/subscribe', 'POST', { subscription: { endpoint, keys } })).status, 400, endpoint);
  }
  assert.equal((await c('/api/push/subscribe', 'POST', { subscription: { endpoint: 'https://fcm.googleapis.com/fcm/send/abc', keys } })).status, 200);
});

test('password reset link needs a trusted APP_URL in production', async () => {
  const { appUrl } = await import('../server/security.js');
  const fakeReq = { protocol: 'https', get: () => 'evil.example' };
  process.env.APP_URL = 'https://rumo.app/';
  assert.equal(appUrl(fakeReq), 'https://rumo.app');
  delete process.env.APP_URL;
});

test('account deletion requires the password', async () => {
  const c = await client('del@x.com');
  assert.equal((await c('/api/me', 'DELETE', { password: 'errada' })).status, 403);
  assert.equal((await c('/api/me', 'DELETE', { password: 'segredo1' })).status, 200);
  assert.equal((await c('/api/me')).status, 401);
});

test('internal errors are not leaked', async () => {
  const res = await fetch(`${base}/api/auth/login`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: '{"broken json' });
  assert.equal(res.status, 400);
  const body = await res.json();
  assert.doesNotMatch(body.error, /JSON|position|Unexpected/i);
});

test('repeat and plan values reject prototype keys', async () => {
  const c = await client('proto@x.com');
  const today = (await c('/api/me')).body.today;
  const ev = await c('/api/events', 'POST', { title: 'x', start: `${today}T10:00`, repeat: 'constructor' });
  assert.equal(ev.body.repeat, '');
});
