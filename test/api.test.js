import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import os from 'node:os';
import path from 'node:path';
import fs from 'node:fs';

const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'rumo-test-'));
process.env.DB_PATH = path.join(dir, 'test.db');
delete process.env.ANTHROPIC_API_KEY;
delete process.env.ANTHROPIC_AUTH_TOKEN;

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
  const weak = await fetch(`${base}/api/auth/register`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ name: 'A', email: 'w@x.com', password: '1' }) });
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
