import { $, $$, esc, api, toast, md, fmtDate, addDays, busy, copy, icon, ask, confetti, attachMic, shrinkImage } from './util.js';

const state = { me: null, ai: false, today: null };
const app = $('#app');

const NAV = [
  ['hoje', 'Hoje', 'home'],
  ['agenda', 'Agenda', 'cal'],
  ['metas', 'Metas', 'target'],
  ['chat', 'Conversar', 'chat'],
  ['editor', 'Editor', 'pen'],
  ['ideias', 'Amplificar ideias', 'bulb'],
  ['legendas', 'Legendas', 'quote'],
  ['perfil', 'Perfil', 'user'],
];
const MOBILE_NAV = [['hoje', 'Hoje', 'home'], ['agenda', 'Agenda', 'cal'], ['metas', 'Metas', 'target'], ['chat', 'IA', 'chat'], ['criar', 'Criar', 'grid']];

// ---------------- router ----------------
const views = {};
async function route() {
  const [, name = 'hoje', arg] = location.hash.match(/^#\/([^/]*)\/?(.*)$/) || [];
  if (name === 'entrar') return renderAuth(arg);
  if (name === 'redefinir') return renderReset(arg);
  if (!state.me) {
    try {
      const me = await api('/api/me');
      Object.assign(state, { me: me.user, ai: me.ai, today: me.today, repeats: me.repeats || {} });
    } catch { return renderLanding(); }
  }
  if (name === 'boas-vindas') return renderOnboarding();
  if (!state.me.onboarded) { location.hash = '#/boas-vindas'; return; }
  const view = views[name] || views.hoje;
  renderShell(name in views ? name : 'hoje');
  const old = $('#main');
  const main = old.cloneNode(false);
  old.replaceWith(main);
  main.innerHTML = '<div class="empty"><span class="loading"></span></div>';
  try { await view(main, decodeURIComponent(arg || '')); } catch (e) { main.innerHTML = `<div class="card empty">${esc(e.message)}</div>`; }
  window.scrollTo(0, 0);
}
window.addEventListener('hashchange', route);
function go(hash) { if (location.hash === hash) route(); else location.hash = hash; }

function renderShell(active) {
  if (!$('.shell')) {
    app.innerHTML = `
      <div class="shell">
        <aside class="sidebar">
          <div class="brand"><span class="brand-mark">➜</span> Rumo</div>
          <nav>${[...NAV, ...(state.me?.is_admin ? [['admin', 'Painel admin', 'grid']] : [])].map(([k, l, i]) => `<a class="nav-link" data-k="${k}" href="#/${k}">${icon(i)} ${l}</a>`).join('')}</nav>
          <div class="spacer"></div>
          <div class="small muted" style="padding:0 12px">${state.ai ? '● IA conectada' : '○ IA em modo demonstração'}</div>
        </aside>
        <main class="main" id="main"></main>
        <nav class="bottom-nav">${MOBILE_NAV.map(([k, l, i]) => `<a data-k="${k}" href="#/${k}">${icon(i)}<span>${l}</span></a>`).join('')}</nav>
      </div>`;
  }
  const group = ['editor', 'ideias', 'legendas', 'perfil', 'criar'].includes(active) ? 'criar' : active;
  $$('[data-k]').forEach((a) => a.classList.toggle('active', a.dataset.k === active || (a.closest('.bottom-nav') && a.dataset.k === group)));
}

// ---------------- auth ----------------
function renderAuth(arg) {
  state.me = null;
  let mode = 'login';
  app.innerHTML = `
    <div class="auth">
      <div class="card auth-card">
        <div class="brand" style="padding:0"><span class="brand-mark">➜</span> Rumo</div>
        <p class="muted" style="margin-top:8px">Seu parceiro com IA para tirar metas do papel: pequenas tarefas todos os dias, agenda, ideias e conteúdo.</p>
        <div class="auth-tabs"><button data-m="login" class="on">Entrar</button><button data-m="register">Criar conta</button></div>
        <form id="auth-form">
          <div class="field hidden" id="name-field"><label for="a-name">Seu nome</label><input id="a-name" type="text" autocomplete="name"></div>
          <div class="field"><label for="a-email">E-mail</label><input id="a-email" type="email" required autocomplete="email"></div>
          <div class="field"><label for="a-pass">Senha</label><input id="a-pass" type="password" required maxlength="200" autocomplete="current-password"></div>
          <button class="btn primary" style="width:100%;justify-content:center" type="submit">Entrar</button>
          <button class="btn ghost sm" type="button" id="forgot" style="margin-top:8px;width:100%;justify-content:center">Esqueci minha senha</button>
        </form>
        <p class="small muted" style="margin:14px 0 0;text-align:center"><a href="#/" data-home>← Conhecer o Rumo</a></p>
        <ul class="feature-list">
          <li>🎯 Metas quebradas em tarefas diárias pela IA</li>
          <li>📅 Agenda com linguagem natural (“dentista amanhã 15h”)</li>
          <li>💡 Amplificador de ideias e editor com IA</li>
          <li>✍️ Legendas prontas para Instagram, TikTok e mais</li>
        </ul>
      </div>
    </div>`;
  $$('.auth-tabs button').forEach((b) => b.onclick = () => {
    mode = b.dataset.m;
    $$('.auth-tabs button').forEach((x) => x.classList.toggle('on', x === b));
    $('#name-field').classList.toggle('hidden', mode !== 'register');
    $('#auth-form button[type=submit]').textContent = mode === 'register' ? 'Criar minha conta' : 'Entrar';
    $('#a-pass').autocomplete = mode === 'register' ? 'new-password' : 'current-password';
    $('#a-pass').minLength = mode === 'register' ? 8 : 1;
    $('#a-pass').placeholder = mode === 'register' ? 'Mínimo de 8 caracteres' : '';
  });
  if (arg === 'criar') $('[data-m=register]').click();
  $('#forgot').onclick = async () => {
    const email = await ask('Qual o e-mail da sua conta? Vamos enviar um link para criar uma nova senha.', { input: 'email', value: $('#a-email').value, okLabel: 'Enviar link' });
    if (!email) return;
    try {
      await api('/api/auth/forgot', { method: 'POST', body: { email } });
      toast('Se esse e-mail tiver conta, o link chega em alguns minutos. Veja também o spam.');
    } catch (err) { toast(err.message); }
  };
  $('#auth-form').onsubmit = async (e) => {
    e.preventDefault();
    const body = { name: $('#a-name').value, email: $('#a-email').value, password: $('#a-pass').value };
    try {
      await api(mode === 'register' ? '/api/auth/register' : '/api/auth/login', { method: 'POST', body });
      go(mode === 'register' ? '#/boas-vindas' : '#/hoje');
    } catch (err) { toast(err.message); }
  };
}

// ---------------- shared: task row ----------------
function taskRow(t, { showDate = false } = {}) {
  return `<div class="task ${t.done ? 'done' : ''}" data-id="${t.id}">
    <button class="check" data-act="toggle" aria-label="Concluir">${t.done ? icon('check') : ''}</button>
    <div class="task-body">
      <div class="task-title">${esc(t.title)}</div>
      ${t.detail ? `<div class="task-detail">${esc(t.detail)}</div>` : ''}
      <div class="row small muted" style="gap:6px;margin-top:4px">
        <span class="chip">${t.minutes} min</span>
        ${t.source === 'ai' ? '<span class="chip accent">IA</span>' : ''}${t.source === 'plano' ? '<span class="chip accent">plano</span>' : ''}
        ${showDate ? `<span class="chip">${fmtDate(t.due_date, { day: 'numeric', month: 'short' })}</span>` : ''}
      </div>
    </div>
    <div class="task-actions row" style="gap:2px">
      ${showDate && !t.done ? '<button class="btn sm ghost" data-act="today" title="Fazer hoje">Hoje</button>' : ''}
      <button class="btn sm ghost danger" data-act="del" title="Excluir">${icon('trash')}</button>
    </div>
  </div>`;
}

function bindTasks(root, refresh) {
  root.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-act]');
    const row = e.target.closest('.task');
    if (!btn || !row) return;
    const id = row.dataset.id;
    if (btn.dataset.act === 'toggle') {
      const done = !row.classList.contains('done');
      row.classList.toggle('done', done);
      await api(`/api/tasks/${id}`, { method: 'PATCH', body: { done } });
      if (done) toast(['Boa! 🔥', 'Mais um passo! 💪', 'Isso aí! ✅', 'Constância vence talento. 🚀'][Math.floor(Math.random() * 4)]);
    } else if (btn.dataset.act === 'del') {
      await api(`/api/tasks/${id}`, { method: 'DELETE' });
    } else if (btn.dataset.act === 'today') {
      await api(`/api/tasks/${id}`, { method: 'PATCH', body: { due_date: state.today } });
    }
    refresh();
  });
}

// ---------------- shared: conversa com a IA ----------------
const bubble = (m) => `<div class="bubble ${m.role} ${m.role === 'assistant' ? 'md' : ''}">${m.role === 'assistant' ? md(m.content) : esc(m.content)}</div>`;

/**
 * Envia uma mensagem (ou pedido de ajuda) e mostra a resposta da IA chegando aos poucos dentro de `log`.
 * Resolve com o número de ações que a IA executou no app.
 */
async function talk(log, payload, display, { scroll = () => {} } = {}) {
  $('.empty', log)?.remove();
  log.insertAdjacentHTML('beforeend', bubble({ role: 'user', content: display }));
  log.insertAdjacentHTML('beforeend', '<div class="bubble assistant md"><span class="loading"></span> <span class="muted small">pensando…</span></div>');
  const out = log.lastElementChild;
  scroll();
  let acc = '';
  let actions = 0;
  let anchor = out;
  try {
    const res = await fetch('/api/ai/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).error || 'Erro ao enviar.');
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = '';
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const parts = buf.split('\n\n');
      buf = parts.pop();
      for (const p of parts) {
        if (!p.startsWith('data: ')) continue;
        const ev = JSON.parse(p.slice(6));
        if (ev.t) { acc += ev.t; out.innerHTML = md(acc); scroll(); }
        if (ev.action) {
          actions++;
          anchor.insertAdjacentHTML('afterend', `<div class="action-chip">${esc(ev.action)}</div>`);
          anchor = anchor.nextElementSibling;
        }
        if (ev.error) throw new Error(ev.error);
      }
    }
    if (!acc) out.remove();
  } catch (e) {
    out.innerHTML = `<span style="color:var(--danger)">${esc(e.message)}</span>`;
  }
  scroll();
  return actions;
}

// ---------------- HOJE (as tarefas do dia em forma de conversa) ----------------
function taskCard(t, goalName) {
  if (t.done) {
    return `<div class="task-card done" data-id="${t.id}">
      <button class="check" data-act="toggle" aria-label="Desfazer">${icon('check')}</button>
      <div class="task-body"><div class="task-title">${esc(t.title)}</div></div>
    </div>`;
  }
  return `<div class="task-card" data-id="${t.id}">
    <div class="row" style="align-items:flex-start;flex-wrap:nowrap;gap:12px">
      <button class="check" data-act="toggle" aria-label="Marcar como feita"></button>
      <div class="task-body">
        <div class="task-title">${esc(t.title)}</div>
        ${t.detail ? `<div class="task-detail">${esc(t.detail)}</div>` : ''}
        <div class="row small" style="gap:6px;margin-top:6px">
          <span class="chip">⏱ ${t.minutes} min</span>
          ${t.source === 'habito' ? '<span class="chip accent">🔁 hábito</span>' : ''}
          ${goalName ? `<span class="chip">🎯 ${esc(goalName.length > 34 ? `${goalName.slice(0, 34)}…` : goalName)}</span>` : ''}
        </div>
      </div>
    </div>
    <div class="task-buttons">
      <button class="btn sm primary" data-act="toggle">✓ Feito</button>
      <button class="btn sm" data-act="help">🆘 Me ajuda</button>
      <button class="btn sm" data-act="focus">▶ Foco</button>
      <button class="btn sm" data-act="talk">💬 Falar</button>
      <button class="btn sm ghost" data-act="later">⏭ Amanhã</button>
      <button class="btn sm ghost danger" data-act="del" aria-label="Excluir tarefa">${icon('trash')}</button>
    </div>
  </div>`;
}

views.hoje = async (main) => {
  const [d, msgs] = await Promise.all([api('/api/today'), api('/api/chat?today=1')]);
  state.today = d.date;
  const first = esc(state.me.name.split(' ')[0]);
  const moods = ['😞', '😕', '😐', '🙂', '🤩'];

  main.innerHTML = `
    ${!state.ai ? '<div class="banner">IA em <b>modo demonstração</b>. Para respostas reais, configure <code>ANTHROPIC_API_KEY</code> no servidor (veja o README).</div>' : ''}
    <div class="today-layout">
      <section class="today-feed">
        <div id="today-head"></div>
        <div class="feed" id="today-block"></div>
        <div class="feed" id="today-msgs">${msgs.map(bubble).join('')}</div>
        <form class="composer" id="composer">
          <div class="suggestions" id="quick">
            ${[['plan', '✨ Montar meu dia'], ['msg', 'Terminei tudo! 🎉'], ['msg', 'Estou sem tempo hoje'], ['msg', 'Me dá uma tarefa extra'], ['msg', 'Estou travado, me ajuda a começar']]
              .map(([k, l]) => `<button type="button" data-q="${k}" data-text="${esc(l)}">${esc(l)}</button>`).join('')}
          </div>
          <div class="row" style="flex-wrap:nowrap;gap:8px">
            <textarea id="say" rows="1" placeholder="Fale com a IA: “fiz a primeira”, “hoje não dá”, “marca dentista sexta 15h”…" aria-label="Mensagem para a IA"></textarea>
            <button class="btn mic" type="button" id="say-mic" aria-label="Falar por voz">🎤</button>
            <button class="btn primary" type="submit" aria-label="Enviar">Enviar</button>
          </div>
        </form>
      </section>

      <aside class="stack today-side">
        <section class="card">
          <h2>Sua semana</h2>
          <div class="week" id="week"></div>
          <button class="btn sm" id="review" style="margin-top:12px" data-busy="Analisando…">${icon('spark')} Revisão da semana</button>
          <div id="review-out" class="md small" style="margin-top:10px"></div>
        </section>
        <section class="card">
          <h2>Como você está hoje?</h2>
          <div class="moods">${moods.map((m, i) => `<button type="button" data-mood="${i + 1}" class="${d.checkin?.mood === i + 1 ? 'sel' : ''}" aria-label="Humor ${i + 1} de 5">${m}</button>`).join('')}</div>
        </section>
        <section class="card">
          <div class="row between"><h2>Metas</h2><a href="#/metas" class="small">Ver todas →</a></div>
          <div id="goals-mini"></div>
        </section>
      </aside>
    </div>`;

  let data = d;
  const goalNames = () => Object.fromEntries(data.goals.map((g) => [g.id, g.title]));
  const scrollEnd = () => window.scrollTo({ top: document.body.scrollHeight });

  function renderBlock() {
    const done = data.tasks.filter((t) => t.done).length;
    const total = data.tasks.length;
    const pct = total ? Math.round((done / total) * 100) : 0;
    const left = data.tasks.filter((t) => !t.done);
    const mins = left.reduce((s, t) => s + t.minutes, 0);
    const hour = new Date().getHours();
    const hello = hour < 12 ? 'Bom dia' : hour < 18 ? 'Boa tarde' : 'Boa noite';
    $('#today-head').innerHTML = `
      <div class="today-hero">
        <div class="row between" style="align-items:flex-end">
          <div><h1 style="margin:0">${hello}, ${first}!</h1>
            <div class="muted small">${fmtDate(data.date)} · ${data.streak ? `🔥 ${data.streak} dia${data.streak > 1 ? 's' : ''} seguido${data.streak > 1 ? 's' : ''}` : 'comece sua sequência hoje'}</div></div>
          <div class="small" style="text-align:right"><b>${done}/${total}</b> feitas</div>
        </div>
        <div class="progress" style="margin-top:10px"><span style="width:${pct}%"></span></div>
      </div>`;

    let intro;
    if (!total) {
      intro = `Ainda não montei seu dia, ${first}. Quer que eu prepare as tarefas de hoje a partir das suas metas?
        <div style="margin-top:10px"><button class="btn primary sm" data-q="plan">✨ Montar meu dia</button></div>`;
    } else if (!left.length) {
      intro = md(`**Você concluiu tudo hoje! 🎉** Isso é constância de verdade.\n\nQuer uma tarefa extra, ou prefere fazer a revisão da semana?`);
    } else {
      const focus = data.goals[0]?.title;
      intro = md(`Aqui está seu dia: **${left.length} tarefa${left.length > 1 ? 's' : ''}**, uns **${mins} min** no total.${focus ? ` Foco principal: _${focus}_.` : ''}\n\nComece pela primeira 👇 Se travar, toque em **🆘 Me ajuda** que eu te entrego a solução.`);
    }
    const ev = data.events.filter((e) => e.start.startsWith(data.date));
    $('#today-block').innerHTML = `
      <div class="bubble assistant">${intro}</div>
      ${data.tasks.filter((t) => !t.done).map((t) => taskCard(t, goalNames()[t.goal_id])).join('')}
      ${done ? `<details class="done-list"><summary class="muted small">✅ Feitas hoje (${done})</summary>${data.tasks.filter((t) => t.done).map((t) => taskCard(t)).join('')}</details>` : ''}
      ${data.overdue.length ? `<div class="bubble assistant">Ficaram <b>${data.overdue.length}</b> tarefa${data.overdue.length > 1 ? 's' : ''} de dias anteriores. <div class="row" style="margin-top:8px"><button class="btn sm" data-q="bring">Trazer para hoje</button><button class="btn sm ghost" data-q="clear-overdue">Descartar</button></div></div>` : ''}
      ${(data.needs_plan || []).slice(0, 2).map((g) => `<div class="bubble assistant">Sua meta <b>${esc(g.title)}</b> está sem tarefas pela frente. Quer que eu planeje os próximos 7 dias?<div style="margin-top:8px"><button class="btn sm primary" data-q="plan-goal" data-goal="${g.id}" data-busy="Planejando…">✨ Planejar 7 dias</button></div></div>`).join('')}
      ${ev.length ? `<div class="bubble assistant">📅 Hoje na agenda: ${ev.map((e) => `<b>${e.start.slice(11)}</b> ${esc(e.title)}`).join(' · ')}</div>` : ''}`;

    const weekMap = Object.fromEntries(data.week.map((w) => [w.d, w]));
    $('#week').innerHTML = Array.from({ length: 7 }, (_, i) => {
      const day = addDays(data.date, i - 6);
      const w = weekMap[day];
      const ratio = w && w.total ? w.done / w.total : 0;
      const lvl = !w || !w.done ? '' : ratio >= 1 ? 'l3' : ratio >= 0.5 ? 'l2' : 'l1';
      return `<div><div class="dot ${lvl}">${w ? w.done : ''}</div>${fmtDate(day, { weekday: 'short' }).replace('.', '')}</div>`;
    }).join('');
    $('#goals-mini').innerHTML = data.goals.length
      ? data.goals.slice(0, 4).map((g) => `<a href="#/metas/${g.id}" class="goal-mini"><div class="row between small" style="flex-wrap:nowrap"><b>${esc(g.title)}</b><span class="muted">${g.total ? Math.round((g.done / g.total) * 100) : 0}%</span></div><div class="progress"><span style="width:${g.total ? (g.done / g.total) * 100 : 0}%"></span></div></a>`).join('')
      : '<p class="muted small">Nenhuma meta ainda. <a href="#/metas">Criar</a></p>';
  }

  async function reload() {
    data = await api('/api/today');
    if (document.body.contains(main)) renderBlock(); // a pessoa pode ter mudado de tela
  }
  async function markDone(t, done) {
    await api(`/api/tasks/${t.id}`, { method: 'PATCH', body: { done } });
    await reload();
    if (!done) return;
    const left = data.tasks.filter((x) => !x.done).length;
    if (!left) confetti();
    toast(left ? ['Boa! 🔥', 'Mais um passo! 💪', 'Isso aí! ✅', 'Constância vence talento. 🚀'][Math.floor(Math.random() * 4)] : 'Dia completo! 🎉', {
      label: 'Desfazer',
      run: async () => { await api(`/api/tasks/${t.id}`, { method: 'PATCH', body: { done: false } }); await reload(); },
    });
  }
  renderBlock();

  const log = $('#today-msgs');
  const say = $('#say');
  let busyTalk = false;
  async function converse(payload, display) {
    if (busyTalk) return;
    busyTalk = true;
    try {
      const acted = await talk(log, payload, display, { scroll: scrollEnd });
      if (acted) await reload();
    } finally { busyTalk = false; }
  }
  function note(text) {
    log.insertAdjacentHTML('beforeend', `<div class="action-chip">${esc(text)}</div>`);
  }

  async function planDay(btn) {
    const run = async () => {
      const r = await api('/api/ai/daily', { method: 'POST', body: {} });
      await reload();
      log.insertAdjacentHTML('beforeend', bubble({ role: 'assistant', content: `${r.message}\n\nAdicionei **${r.count} tarefas** para hoje. Estão logo acima. 👆` }));
      scrollEnd();
    };
    if (btn) await busy(btn, run); else await run();
  }

  main.addEventListener('click', async (e) => {
    const q = e.target.closest('[data-q]');
    if (q) {
      if (q.dataset.q === 'plan') return planDay(q);
      if (q.dataset.q === 'plan-goal') {
        return busy(q, async () => {
          await api(`/api/goals/${q.dataset.goal}/plan`, { method: 'POST', body: { days: 7 } });
          await reload();
          toast('Plano criado! As tarefas de hoje já estão na lista.');
        });
      }
      if (q.dataset.q === 'msg') return converse({ message: q.dataset.text }, q.dataset.text);
      if (q.dataset.q === 'bring' || q.dataset.q === 'clear-overdue') {
        for (const t of data.overdue) {
          if (q.dataset.q === 'bring') await api(`/api/tasks/${t.id}`, { method: 'PATCH', body: { due_date: data.date } });
          else await api(`/api/tasks/${t.id}`, { method: 'DELETE' });
        }
        await reload();
        return toast(q.dataset.q === 'bring' ? 'Trouxe as pendentes para hoje.' : 'Pendentes descartadas.');
      }
    }
    const btn = e.target.closest('[data-act]');
    const card = e.target.closest('.task-card');
    if (!btn || !card) return;
    const t = data.tasks.find((x) => String(x.id) === card.dataset.id);
    if (!t) return;
    const act = btn.dataset.act;
    if (busyTasks.has(t.id) && act !== 'help' && act !== 'talk') return; // evita toque duplo
    busyTasks.add(t.id);
    try { await taskAction(act, t, btn); } finally { busyTasks.delete(t.id); }
  });
  const busyTasks = new Set();
  async function taskAction(act, t) {
    if (act === 'toggle') {
      await markDone(t, !t.done);
    } else if (act === 'focus') {
      startFocus(t, async () => {
        if (document.body.contains(main)) return markDone(t, true);
        await api(`/api/tasks/${t.id}`, { method: 'PATCH', body: { done: true } }); // saiu da tela Hoje
        toast(`✅ Feito: ${t.title}`);
      });
    } else if (act === 'help') {
      converse({ help_task_id: t.id }, `🆘 Me ajuda com: ${t.title}`);
    } else if (act === 'talk') {
      say.value = `Sobre "${t.title}": `;
      say.focus();
      say.scrollIntoView({ block: 'center' });
    } else if (act === 'later') {
      await api(`/api/tasks/${t.id}`, { method: 'PATCH', body: { due_date: addDays(data.date, 1) } });
      await reload();
      note(`⏭️ "${t.title}" ficou para amanhã`);
    } else if (act === 'del') {
      if (!await ask(`Excluir a tarefa "${t.title}"?`, { okLabel: 'Excluir', danger: true })) return;
      await api(`/api/tasks/${t.id}`, { method: 'DELETE' });
      await reload();
    }
  }

  $('#composer').onsubmit = (e) => {
    e.preventDefault();
    const text = say.value.trim();
    if (!text) return;
    say.value = '';
    converse({ message: text }, text);
  };
  say.onkeydown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); $('#composer').requestSubmit(); } };
  attachMic(say, $('#say-mic'));
  $('#review').onclick = (e) => busy(e.currentTarget, async () => {
    const r = await api('/api/ai/review', { method: 'POST', body: {} });
    if (!document.body.contains(main)) return; // a pessoa saiu da tela enquanto a IA respondia
    $('#review-out').innerHTML = md(r.text);
  });
  $$('[data-mood]').forEach((b) => b.onclick = async () => {
    await api('/api/checkin', { method: 'POST', body: { mood: Number(b.dataset.mood) } });
    $$('[data-mood]').forEach((x) => x.classList.toggle('sel', x === b));
    if (Number(b.dataset.mood) <= 2) converse({ message: 'Hoje não estou num dia bom.' }, 'Hoje não estou num dia bom. 😕');
    else toast('Anotado!');
  });
  if (msgs.length) scrollEnd();
};

// ---------------- BOAS-VINDAS (passo a passo do novo usuário) ----------------
const ROLES = ['Empreendedor(a)', 'Criador(a) de conteúdo', 'Freelancer / autônomo', 'Estudante', 'Trabalho CLT e quero mudar', 'Outro'];
const GOAL_EXAMPLES = {
  'Empreendedor(a)': ['Faturar R$ 5 mil por mês', 'Conseguir os primeiros 10 clientes', 'Lançar meu produto'],
  'Criador(a) de conteúdo': ['Chegar a 10 mil seguidores', 'Postar todos os dias por 30 dias', 'Fechar minha primeira publi'],
  'Freelancer / autônomo': ['Ter agenda cheia de clientes', 'Aumentar meu preço em 30%', 'Montar meu portfólio'],
  Estudante: ['Passar no concurso/vestibular', 'Estudar 2h por dia', 'Aprender inglês'],
  'Trabalho CLT e quero mudar': ['Ter uma renda extra de R$ 2 mil', 'Mudar de área em 6 meses', 'Abrir meu negócio'],
  Outro: ['Organizar minha vida financeira', 'Entrar em forma', 'Ler 12 livros no ano'],
};
const TONES = ['motivador e direto', 'gentil e acolhedor', 'exigente, sem passar a mão na cabeça', 'divertido e leve', 'técnico e objetivo'];

function onboardingSteps(a) {
  const name = a.name ? esc(a.name.split(' ')[0]) : '';
  const steps = [
    { key: 'name', q: 'Oi! Eu sou o <b>Rumo</b>, sua IA parceira. 👋<br>Vou te fazer umas perguntas rápidas (uns 2 minutos) para deixar o app do seu jeito.<br><br><b>Como você quer ser chamado(a)?</b>', input: 'text', required: true },
    { key: 'role', q: `Prazer, ${name}! <b>O que melhor descreve você hoje?</b>`, chips: ROLES, required: true },
    { key: 'about', q: '<b>Conte em uma ou duas frases o que você faz ou quer fazer.</b><br><span class="muted small">Quanto mais eu souber, melhores ficam suas tarefas.</span>', input: 'textarea', placeholder: 'Ex: Faço bolos caseiros e vendo pelo Instagram. Quero transformar isso na minha renda principal.', extra: { key: 'niche', label: 'Seu nicho ou área (opcional)', placeholder: 'Ex: confeitaria, fitness, design' } },
    { key: 'goal', q: '<b>Qual é a sua meta principal agora?</b> Onde você quer chegar?', input: 'text', chips: GOAL_EXAMPLES[a.role] || GOAL_EXAMPLES.Outro, chipsFill: true, required: true, placeholder: 'Escreva com suas palavras' },
    { key: 'why', q: '<b>Por que isso é importante para você?</b><br><span class="muted small">Nos dias difíceis eu vou te lembrar disso.</span>', input: 'textarea', placeholder: 'Ex: Quero ter liberdade e mais tempo com minha família.' },
    { key: 'deadline', q: '<b>Em quanto tempo você quer chegar lá?</b>', chips: ['1 mês', '3 meses', '6 meses', '1 ano'], input: 'date' },
    { key: 'daily_minutes', q: '<b>Quanto tempo por dia você consegue dedicar a isso?</b><br><span class="muted small">Seja realista. Pouco todo dia vence muito de vez em quando.</span>', chips: ['15 min', '30 min', '1 hora', '2 horas'], required: true },
    { key: 'tone', q: '<b>Como você prefere que eu fale com você?</b>', chips: TONES, required: true },
  ];
  if (['Empreendedor(a)', 'Criador(a) de conteúdo', 'Freelancer / autônomo'].includes(a.role)) {
    steps.push({ key: 'launch_plan', q: 'Última! Tenho um <b>plano de divulgação de 30 dias</b>, uma tarefa por dia, para você ser visto(a) e conquistar clientes. <b>Quer incluir?</b>', chips: ['Sim, quero!', 'Agora não'], required: true });
  }
  return steps;
}

const DEADLINES = { '1 mês': 30, '3 meses': 91, '6 meses': 182, '1 ano': 365 };
const MINUTES = { '15 min': 15, '30 min': 30, '1 hora': 60, '2 horas': 120 };

function renderOnboarding() {
  const a = { name: state.me.name };
  let i = 0;
  app.innerHTML = '<div class="ob"><div class="ob-card" id="ob"></div></div>';
  const box = $('#ob');

  function show() {
    const steps = onboardingSteps(a);
    const s = steps[i];
    const val = a[s.key] ?? '';
    box.innerHTML = `
      <div class="row between small muted"><span>${i + 1} de ${steps.length}</span><button class="btn sm ghost" id="ob-skip">Pular configuração</button></div>
      <div class="progress" style="margin:8px 0 18px"><span style="width:${((i + 1) / steps.length) * 100}%"></span></div>
      <div class="row" style="align-items:flex-start;flex-wrap:nowrap;gap:10px">
        <span class="brand-mark" style="flex:none">➜</span>
        <div class="bubble assistant ob-q">${s.q}</div>
      </div>
      <form id="ob-form" class="stack" style="margin-top:16px">
        ${s.chips ? `<div class="choice">${s.chips.map((c) => `<button type="button" class="${(s.key === 'deadline' ? a.deadline_label : s.key === 'daily_minutes' ? a.minutes_label : s.key === 'launch_plan' ? a.launch_label : val) === c ? 'sel' : ''}" data-c="${esc(c)}">${esc(c)}</button>`).join('')}</div>` : ''}
        ${s.input === 'text' ? `<input type="text" id="ob-in" value="${esc(val)}" placeholder="${esc(s.placeholder || '')}" aria-label="Resposta">` : ''}
        ${s.input === 'textarea' ? `<textarea id="ob-in" placeholder="${esc(s.placeholder || '')}" aria-label="Resposta">${esc(val)}</textarea>` : ''}
        ${s.input === 'date' ? `<label for="ob-in">Ou escolha uma data</label><input type="date" id="ob-in" value="${esc(a.deadline || '')}">` : ''}
        ${s.extra ? `<div><label for="ob-extra">${s.extra.label}</label><input type="text" id="ob-extra" value="${esc(a[s.extra.key] || '')}" placeholder="${esc(s.extra.placeholder)}"></div>` : ''}
        <div class="row between" style="margin-top:6px">
          ${i ? '<button type="button" class="btn ghost" id="ob-back">← Voltar</button>' : '<span></span>'}
          <button class="btn primary" type="submit">${i === steps.length - 1 ? 'Montar meu plano ✨' : 'Continuar →'}</button>
        </div>
      </form>`;
    const input = $('#ob-in');
    input?.focus();
    $$('.choice button', box).forEach((b) => b.onclick = () => {
      const c = b.dataset.c;
      if (s.key === 'deadline') { a.deadline_label = c; a.deadline = addDays(state.today || new Date().toISOString().slice(0, 10), DEADLINES[c]); if (input) input.value = a.deadline; }
      else if (s.key === 'daily_minutes') { a.minutes_label = c; a.daily_minutes = MINUTES[c]; }
      else if (s.key === 'launch_plan') { a.launch_label = c; a.launch_plan = c.startsWith('Sim'); }
      else if (s.chipsFill && input) { input.value = c; }
      else a[s.key] = c;
      $$('.choice button', box).forEach((x) => x.classList.toggle('sel', x === b));
      if (!s.input && !s.chipsFill) $('#ob-form').requestSubmit();
    });
    $('#ob-back')?.addEventListener('click', () => { i--; show(); });
    $('#ob-skip').onclick = async () => {
      await api('/api/onboarding/skip', { method: 'POST', body: {} });
      state.me.onboarded = 1;
      go('#/tutorial');
    };
    $('#ob-form').onsubmit = (e) => {
      e.preventDefault();
      if (input && s.key !== 'deadline') a[s.key] = input.value.trim();
      if (s.key === 'deadline' && input?.value) a.deadline = input.value;
      if (s.extra) a[s.extra.key] = $('#ob-extra').value.trim();
      const filled = s.key === 'daily_minutes' ? a.daily_minutes : s.key === 'launch_plan' ? a.launch_label : a[s.key];
      if (s.required && !filled) return toast('Responda para continuar 🙂');
      if (i < onboardingSteps(a).length - 1) { i++; show(); } else finish();
    };
  }

  async function finish() {
    box.innerHTML = `<div class="empty" style="padding:50px 10px"><span class="loading" style="width:28px;height:28px"></span>
      <h2 style="margin-top:16px">Montando seu plano, ${esc(a.name.split(' ')[0])}…</h2>
      <p class="muted">Estou quebrando sua meta em passos pequenos para os próximos 7 dias.</p></div>`;
    try {
      await api('/api/onboarding', { method: 'POST', body: {
        name: a.name, role: a.role, about: a.about, niche: a.niche, goal: a.goal, why: a.why, deadline: a.deadline,
        daily_minutes: a.daily_minutes, tone: a.tone, launch_plan: !!a.launch_plan,
        area: /client|fatur|vend|negóc|produto|renda/i.test(a.goal) ? 'negócio' : /seguidor|post|publi|conteúdo/i.test(a.goal) ? 'divulgação' : 'geral',
      } });
      state.me = (await api('/api/me')).user;
      go('#/tutorial');
    } catch (e) {
      toast(e.message);
      show();
    }
  }
  show();
}

// ---------------- TUTORIAL ----------------
views.tutorial = async (main) => {
  const tips = [
    ['home', 'Hoje é uma conversa', 'Suas tarefas do dia aparecem como cartões. Toque em <b>✓ Feito</b> quando terminar, <b>⏭ Amanhã</b> para adiar ou <b>🗑</b> para excluir.'],
    ['spark', '🆘 Me ajuda: eu faço junto', 'Em qualquer tarefa, toque em <b>Me ajuda</b>. Eu entrego a solução pronta (texto, roteiro, modelo), o passo a passo e links úteis.'],
    ['chat', 'Fale do seu jeito', 'Escreva <i>“fiz a primeira”</i>, <i>“hoje não dá tempo”</i> ou <i>“marca dentista sexta às 15h”</i>. Eu atualizo tarefas, agenda e metas sozinho.'],
    ['target', 'Metas que viram passos', 'Em <b>Metas</b>, cada meta tem um plano. Quando a semana acabar, toque em <b>Planejar próximos 7 dias</b>.'],
    ['grid', 'Criar: editor, ideias e legendas', 'Escreva textos com IA, transforme ideias soltas em planos e gere legendas prontas para seus posts.'],
    ['rocket', 'Instale no celular', 'No navegador do celular, toque em <b>Compartilhar</b> ou no <b>menu ⋮</b> e depois em <b>Adicionar à tela inicial</b>. O Rumo vira um app.'],
  ];
  main.innerHTML = `
    <h1>Como o Rumo funciona</h1>
    <p class="muted">São 30 segundos. Você pode rever isto quando quiser em <b>Perfil</b>.</p>
    <div class="grid grid-2" style="margin-top:16px">
      ${tips.map(([i, t, d]) => `<div class="card tip"><span class="tip-icon">${icon(i)}</span><div><h3>${t}</h3><p class="small muted" style="margin:0">${d}</p></div></div>`).join('')}
    </div>
    <div class="row" style="justify-content:center;margin-top:24px"><a class="btn primary" href="#/hoje" style="padding:12px 22px">Começar meu dia →</a></div>`;
};

// ---------------- AGENDA ----------------
views.agenda = async (main) => {
  const from = state.today || new Date().toISOString().slice(0, 10);
  const [events, tasks] = await Promise.all([
    api(`/api/events?from=${from}&to=${addDays(from, 30)}`),
    api(`/api/tasks?from=${from}&to=${addDays(from, 13)}`),
  ]);
  const byDay = {};
  for (const e of events) (byDay[e.start.slice(0, 10)] ||= { events: [], tasks: [] }).events.push(e);
  for (const t of tasks) (byDay[t.due_date] ||= { events: [], tasks: [] }).tasks.push(t);
  const days = Object.keys(byDay).sort();

  main.innerHTML = `
    <div class="page-head"><div><h1>Agenda</h1><p class="muted" style="margin:0">Escreva do seu jeito, a IA entende.</p></div>
      <button class="btn" id="new-ev">${icon('plus')} Novo compromisso</button></div>
    <form class="card row" id="quick" style="margin-bottom:20px;flex-wrap:nowrap">
      <input type="text" id="quick-text" placeholder="Ex: reunião com a Ana sexta às 14h30 por 1 hora" aria-label="Compromisso em linguagem natural">
      <button class="btn primary" type="submit" data-busy="Agendando…">${icon('spark')} Agendar</button>
    </form>
    <div id="days">${days.length ? days.map((day) => `
      <div class="day-group"><h3>${day === from ? 'Hoje · ' : day === addDays(from, 1) ? 'Amanhã · ' : ''}${fmtDate(day)}</h3>
        ${byDay[day].events.map((e) => `<div class="event" data-ev="${e.id}"><div class="event-time">${e.start.slice(11)}</div><div style="flex:1"><b>${esc(e.title)}</b>${e.repeat ? ` <span class="chip" title="Repete">🔁 ${esc((state.repeats || {})[e.repeat] || '')}</span>` : ''}${e.end ? `<div class="small muted">até ${e.end.slice(11)}</div>` : ''}${e.notes ? `<div class="small muted">${esc(e.notes.length > 140 ? `${e.notes.slice(0, 140)}…` : e.notes)}</div>` : ''}</div><button class="btn sm ghost danger" data-del-ev="${e.id}" data-series="${e.repeat ? 1 : ''}" aria-label="Excluir">${icon('trash')}</button></div>`).join('')}
        ${byDay[day].tasks.length ? `<div class="small muted">📋 ${byDay[day].tasks.filter((t) => t.done).length}/${byDay[day].tasks.length} tarefas: ${byDay[day].tasks.slice(0, 3).map((t) => esc(t.title)).join(' · ')}${byDay[day].tasks.length > 3 ? '…' : ''}</div>` : ''}
      </div>`).join('') : '<div class="card empty">Agenda livre pelos próximos 30 dias.</div>'}</div>

    <dialog id="ev-dialog"><form method="dialog" id="ev-form">
      <h2>Novo compromisso</h2>
      <div class="field"><label>Título</label><input type="text" id="ev-title" required></div>
      <div class="grid grid-2" style="gap:10px">
        <div class="field"><label>Início</label><input type="datetime-local" id="ev-start" required></div>
        <div class="field"><label>Fim (opcional)</label><input type="datetime-local" id="ev-end"></div>
      </div>
      <div class="field"><label for="ev-repeat">Repetir</label><select id="ev-repeat">${Object.entries(state.repeats || { '': 'Não repete' }).map(([k, v]) => `<option value="${k}">${v}</option>`).join('')}</select></div>
      <div class="field"><label>Notas</label><textarea id="ev-notes"></textarea></div>
      <div class="row" style="justify-content:flex-end"><button class="btn" value="cancel" formnovalidate>Cancelar</button><button class="btn primary" value="ok">Salvar</button></div>
    </form></dialog>`;

  const refresh = () => views.agenda(main);
  $('#quick').onsubmit = (e) => {
    e.preventDefault();
    const text = $('#quick-text').value.trim();
    if (!text) return;
    busy(e.submitter || $('#quick button'), async () => {
      const ev = await api('/api/events/quick', { method: 'POST', body: { text } });
      toast(`Agendado: ${ev.title} em ${fmtDate(ev.start.slice(0, 10), { day: 'numeric', month: 'short' })} às ${ev.start.slice(11)}`);
      refresh();
    });
  };
  const dlg = $('#ev-dialog');
  $('#new-ev').onclick = () => { $('#ev-start').value = `${from}T09:00`; dlg.showModal(); };
  $('#ev-form').onsubmit = async (e) => {
    if (e.submitter?.value !== 'ok') return;
    e.preventDefault();
    await api('/api/events', { method: 'POST', body: { title: $('#ev-title').value, start: $('#ev-start').value, end: $('#ev-end').value || null, notes: $('#ev-notes').value, repeat: $('#ev-repeat').value } });
    dlg.close();
    refresh();
  };
  main.addEventListener('click', async (e) => {
    const b = e.target.closest('[data-del-ev]');
    if (b && await ask(b.dataset.series ? 'Excluir este compromisso e todas as repetições?' : 'Excluir este compromisso?', { okLabel: 'Excluir', danger: true })) { await api(`/api/events/${b.dataset.delEv}`, { method: 'DELETE' }); refresh(); }
  });
};

// ---------------- METAS ----------------
views.metas = async (main, id) => {
  if (id) return goalDetail(main, Number(id));
  const goals = await api('/api/goals');
  const active = goals.filter((g) => g.status === 'ativa');
  const other = goals.filter((g) => g.status !== 'ativa');
  const card = (g) => {
    const pct = g.total ? Math.round((g.done / g.total) * 100) : 0;
    return `<a class="card" href="#/metas/${g.id}" style="text-decoration:none;color:inherit;display:block">
      <div class="row between"><span class="chip">${esc(g.area)}</span>${g.deadline ? `<span class="small muted">até ${fmtDate(g.deadline, { day: 'numeric', month: 'short', year: 'numeric' })}</span>` : ''}</div>
      <h2 style="margin-top:10px">${esc(g.title)}</h2>
      ${g.why ? `<p class="small muted">${esc(g.why.slice(0, 140))}</p>` : ''}
      <div class="row between small"><span class="muted">${g.done}/${g.total} tarefas</span><b>${pct}%</b></div>
      <div class="progress"><span style="width:${pct}%"></span></div>
    </a>`;
  };
  main.innerHTML = `
    <div class="page-head"><div><h1>Metas</h1><p class="muted" style="margin:0">Onde você quer chegar? A IA divide em passos pequenos.</p></div>
      <div class="row"><button class="btn" id="import-plan">${icon('rocket')} Plano de divulgação 30 dias</button><button class="btn primary" id="new-goal">${icon('plus')} Nova meta</button></div></div>
    ${active.length ? `<div class="grid grid-2">${active.map(card).join('')}</div>` : `<div class="card empty"><h2>Comece por uma meta</h2><p>Ex: “Ganhar R$ 5 mil/mês com meu negócio”, “Chegar a 10 mil seguidores”, “Correr 10 km”.</p></div>`}
    <section class="card" id="habits" style="margin-top:20px"></section>
    ${other.length ? `<h2 style="margin-top:28px">Pausadas e concluídas</h2><div class="grid grid-2">${other.map(card).join('')}</div>` : ''}

    <dialog id="goal-dialog"><form method="dialog" id="goal-form">
      <h2>Nova meta</h2>
      <div class="field"><label>Onde você quer chegar?</label><input type="text" id="g-title" required placeholder="Ex: Faturar R$ 10 mil em vendas online"></div>
      <div class="field"><label>Por que isso importa para você?</label><textarea id="g-why" placeholder="Seu motivo é o combustível nos dias difíceis."></textarea></div>
      <div class="grid grid-2" style="gap:10px">
        <div class="field"><label>Área</label><select id="g-area"><option>negócio</option><option>divulgação</option><option>finanças</option><option>saúde</option><option>estudos</option><option>carreira</option><option>pessoal</option><option>geral</option></select></div>
        <div class="field"><label>Prazo</label><input type="date" id="g-deadline"></div>
      </div>
      <label class="row small" style="gap:8px;color:var(--text)"><input type="checkbox" id="g-plan" checked style="width:auto"> Gerar plano e tarefas com IA</label>
      <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="btn" value="cancel" formnovalidate>Cancelar</button><button class="btn primary" value="ok" data-busy="Criando plano…">Criar meta</button></div>
    </form></dialog>`;

  renderHabits($('#habits'));
  const dlg = $('#goal-dialog');
  $('#new-goal').onclick = () => dlg.showModal();
  $('#goal-form').onsubmit = (e) => {
    if (e.submitter?.value !== 'ok') return;
    e.preventDefault();
    busy(e.submitter, async () => {
      const g = await api('/api/goals', { method: 'POST', body: { title: $('#g-title').value, why: $('#g-why').value, area: $('#g-area').value, deadline: $('#g-deadline').value || null } });
      dlg.close(); // a meta já existe: fecha antes do plano, para um erro da IA não gerar meta repetida
      if ($('#g-plan').checked) {
        await api(`/api/goals/${g.id}/plan`, { method: 'POST', body: { days: 7 } })
          .catch((err) => toast(`Meta criada, mas o plano falhou: ${err.message} Toque em “Gerar plano com IA” para tentar de novo.`));
      }
      location.hash = `#/metas/${g.id}`;
    });
  };
  $('#import-plan').onclick = async () => {
    if (!await ask('Importar o plano de divulgação de 30 dias? Ele cria uma meta com 1 tarefa por dia, começando hoje.', { okLabel: 'Importar' })) return;
    const r = await api('/api/goals/import-launch-plan', { method: 'POST', body: {} });
    toast('Plano importado! Sua primeira tarefa já está em Hoje.');
    location.hash = `#/metas/${r.id}`;
  };
};

async function goalDetail(main, id) {
  const g = await api(`/api/goals/${id}`);
  const pct = g.tasks.length ? Math.round((g.tasks.filter((t) => t.done).length / g.tasks.length) * 100) : 0;
  const upcoming = g.tasks.filter((t) => !t.done);
  const done = g.tasks.filter((t) => t.done);
  main.innerHTML = `
    <a href="#/metas" class="small">← Metas</a>
    <div class="page-head" style="margin-top:8px"><div><span class="chip">${esc(g.area)}</span> <span class="chip">${esc(g.status)}</span>
      <h1 style="margin-top:8px">${esc(g.title)}</h1>${g.deadline ? `<p class="muted" style="margin:0">Prazo: ${fmtDate(g.deadline)}</p>` : ''}</div>
      <div class="row">
        <button class="btn primary" id="plan7" data-busy="Planejando…">${icon('spark')} ${g.plan ? 'Planejar próximos 7 dias' : 'Gerar plano com IA'}</button>
        <select id="status" style="width:auto"><option value="ativa">Ativa</option><option value="pausada">Pausada</option><option value="concluida">Concluída 🎉</option></select>
        <button class="btn danger" id="del-goal">${icon('trash')}</button>
      </div></div>
    <div class="grid grid-2">
      <section class="card">
        <div class="row between"><h2>Progresso</h2><b>${pct}%</b></div>
        <div class="progress" style="margin-bottom:14px"><span style="width:${pct}%"></span></div>
        ${g.why ? `<p><b>Por quê:</b> ${esc(g.why)}</p>` : ''}
        ${g.plan ? `<div class="md">${md(g.plan)}</div>` : '<p class="muted">Sem plano ainda. Gere com a IA ou adicione tarefas manualmente.</p>'}
      </section>
      <section class="card">
        <h2>Próximas tarefas</h2>
        <div id="g-tasks">${upcoming.length ? upcoming.map((t) => taskRow(t, { showDate: true })).join('') : '<p class="muted">Nenhuma tarefa pendente.</p>'}</div>
        <form id="g-add" class="stack" style="margin-top:12px">
          <div class="row" style="flex-wrap:nowrap"><input type="text" id="gt-title" placeholder="Nova tarefa para esta meta" aria-label="Nova tarefa"><input type="date" id="gt-date" style="width:auto" value="${state.today}" aria-label="Data"></div>
          <button class="btn" type="submit">${icon('plus')} Adicionar</button>
        </form>
        ${done.length ? `<details style="margin-top:12px"><summary class="muted small">Concluídas (${done.length})</summary>${done.map((t) => taskRow(t, { showDate: true })).join('')}</details>` : ''}
      </section>
    </div>`;
  $('#status').value = g.status;
  const refresh = () => goalDetail(main, id);
  bindTasks(main, refresh);
  $('#status').onchange = async (e) => { await api(`/api/goals/${id}`, { method: 'PATCH', body: { status: e.target.value } }); if (e.target.value === 'concluida') toast('Meta concluída! Orgulho de você 🎉'); refresh(); };
  $('#del-goal').onclick = async () => { if (await ask('Excluir esta meta e todas as tarefas dela?', { okLabel: 'Excluir', danger: true })) { await api(`/api/goals/${id}`, { method: 'DELETE' }); location.hash = '#/metas'; } };
  $('#plan7').onclick = (e) => busy(e.currentTarget, async () => {
    const last = g.tasks.map((t) => t.due_date).sort().at(-1);
    const start = last && last >= state.today ? addDays(last, 1) : state.today;
    await api(`/api/goals/${id}/plan`, { method: 'POST', body: { days: 7, start } });
    toast('Plano criado! As tarefas aparecem em Hoje no dia certo.');
    refresh();
  });
  $('#g-add').onsubmit = async (e) => {
    e.preventDefault();
    const title = $('#gt-title').value.trim();
    if (!title) return;
    await api('/api/tasks', { method: 'POST', body: { title, goal_id: id, due_date: $('#gt-date').value } });
    refresh();
  };
}

// ---------------- CHAT ----------------
views.chat = async (main) => {
  const history = await api('/api/chat');
  main.innerHTML = `
    <div class="page-head" style="margin-bottom:10px"><div><h1>Conversar com a IA</h1><p class="muted small" style="margin:0">Ela conhece suas metas, tarefas e agenda, e pode atualizar tudo.</p></div>
      <button class="btn sm ghost" id="clear-chat">Limpar conversa</button></div>
    <div class="chat">
      <div class="chat-log" id="log">${history.length ? history.map(bubble).join('') : '<div class="empty">Desabafe, peça ideias, planeje o dia. Estou aqui.</div>'}</div>
      <div class="suggestions">${['Me ajuda a planejar meu dia', 'Estou travado, o que faço agora?', 'Me dá 5 ideias de post para hoje', 'Agenda uma reunião amanhã às 10h', 'Como eu divulgo meu trabalho?'].map((t) => `<button data-s="${esc(t)}">${esc(t)}</button>`).join('')}</div>
      <form class="chat-input" id="chat-form">
        <textarea id="msg" placeholder="Escreva sua mensagem…" rows="1" aria-label="Mensagem"></textarea>
        <button class="btn mic" type="button" id="msg-mic" aria-label="Falar por voz">🎤</button>
        <button class="btn primary" type="submit" aria-label="Enviar">Enviar</button>
      </form>
    </div>`;
  const log = $('#log');
  log.scrollTop = log.scrollHeight;
  const input = $('#msg');
  let sending = false;
  const send = async (text) => {
    if (!text || sending) return;
    sending = true;
    try { await talk(log, { message: text }, text, { scroll: () => { log.scrollTop = log.scrollHeight; } }); } finally { sending = false; }
  };
  $('#chat-form').onsubmit = (e) => { e.preventDefault(); const t = input.value.trim(); input.value = ''; send(t); };
  input.onkeydown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); $('#chat-form').requestSubmit(); } };
  $$('[data-s]').forEach((b) => b.onclick = () => send(b.dataset.s));
  attachMic(input, $('#msg-mic'));
  $('#clear-chat').onclick = async () => { if (await ask('Apagar todo o histórico da conversa?', { okLabel: 'Apagar', danger: true })) { await api('/api/chat', { method: 'DELETE' }); views.chat(main); } };
};

// ---------------- EDITOR ----------------
views.editor = async (main, id) => {
  const notes = await api('/api/notes');
  if (!id && notes.length) id = String(notes[0].id);
  const note = id ? await api(`/api/notes/${id}`).catch(() => null) : null;
  main.innerHTML = `
    <div class="page-head"><h1>Editor</h1><button class="btn primary" id="new-note">${icon('plus')} Nova nota</button></div>
    <div class="editor-layout">
      <aside class="card note-list">${notes.length ? notes.map((n) => `<div class="note-item ${String(n.id) === id ? 'active' : ''}" data-note="${n.id}"><b>${esc(n.title)}</b>${n.kind !== 'nota' ? ` <span class="chip">${esc(n.kind)}</span>` : ''}<div class="small muted">${esc((n.preview || '').slice(0, 70))}</div></div>`).join('') : '<p class="muted small">Nenhuma nota ainda.</p>'}</aside>
      <section class="card">${note ? `
        <input class="note-title-input" type="text" id="n-title" value="${esc(note.title)}" aria-label="Título">
        <div class="toolbar">
          ${[['melhorar', '✨ Melhorar'], ['corrigir', '✓ Corrigir'], ['resumir', '📝 Resumir'], ['expandir', '➕ Expandir'], ['continuar', '✍️ Continuar'], ['post', '📱 Virar post'], ['roteiro', '🎬 Roteiro de vídeo'], ['tarefas', '☑ Extrair tarefas']].map(([a, l]) => `<button class="btn sm" data-ai="${a}" data-busy="IA escrevendo…">${l}</button>`).join('')}
          <button class="btn sm" id="custom-ai">💬 Pedir algo…</button>
        </div>
        <textarea class="note-body" id="n-body" placeholder="Escreva aqui. Use a IA para melhorar, resumir ou transformar.">${esc(note.content)}</textarea>
        <div id="ai-result" class="hidden" style="margin-top:12px">
          <div class="row between"><h3>Sugestão da IA</h3><div class="row"><button class="btn sm primary" id="ai-replace">Substituir</button><button class="btn sm" id="ai-append">Adicionar ao fim</button><button class="btn sm" id="ai-copy">Copiar</button><button class="btn sm ghost" id="ai-close">✕</button></div></div>
          <div class="card md" id="ai-text" style="background:var(--surface-2)"></div>
        </div>
        <div class="row between small muted" style="margin-top:10px"><span id="save-state">Salvo</span><button class="btn sm ghost danger" id="del-note">${icon('trash')} Excluir</button></div>
      ` : '<div class="empty">Crie uma nota para começar a escrever.</div>'}</section>
    </div>`;

  $('#new-note').onclick = async () => { const n = await api('/api/notes', { method: 'POST', body: { title: 'Nova nota', content: '' } }); location.hash = `#/editor/${n.id}`; };
  $$('[data-note]').forEach((el) => el.onclick = () => { location.hash = `#/editor/${el.dataset.note}`; });
  if (!note) return;

  const title = $('#n-title');
  const body = $('#n-body');
  let timer;
  const saveState = $('#save-state'); // referência guardada: continua válida mesmo se a pessoa sair da tela
  const save = () => {
    saveState.textContent = 'Salvando…';
    clearTimeout(timer);
    timer = setTimeout(async () => {
      try {
        await api(`/api/notes/${note.id}`, { method: 'PUT', body: { title: title.value, content: body.value } });
        saveState.textContent = 'Salvo';
      } catch (err) {
        saveState.textContent = 'Não salvo';
        toast(`A nota não foi salva: ${err.message}`);
      }
    }, 600);
  };
  title.oninput = save;
  body.oninput = save;
  const autosize = () => { body.style.height = 'auto'; body.style.height = `${Math.max(body.scrollHeight, 300)}px`; };
  body.addEventListener('input', autosize);
  autosize();

  let result = '';
  let range = null; // trecho selecionado quando a IA foi chamada (null = texto inteiro)
  const run = (btn, action, instruction) => busy(btn, async () => {
    const { selectionStart: a, selectionEnd: b } = body;
    const sel = body.value.slice(a, b);
    range = sel.trim() ? [a, b] : null;
    const text = sel.trim() ? sel : body.value;
    if (!text.trim()) throw new Error('Escreva algo primeiro.');
    const r = await api('/api/ai/edit', { method: 'POST', body: { action, text, instruction } });
    if (!document.body.contains(main)) return; // a pessoa saiu da tela enquanto a IA respondia
    result = r.text;
    $('#ai-text').innerHTML = md(result);
    $('#ai-result').classList.remove('hidden');
  });
  $$('[data-ai]').forEach((b) => b.onclick = () => run(b, b.dataset.ai));
  $('#custom-ai').onclick = async (e) => { const btn = e.currentTarget; const ins = await ask('O que a IA deve fazer com o texto?', { input: true, placeholder: 'Ex: deixe mais curto e engraçado', okLabel: 'Pedir' }); if (ins) run(btn, 'custom', ins); };
  $('#ai-replace').onclick = () => {
    body.value = range ? body.value.slice(0, range[0]) + result + body.value.slice(range[1]) : result;
    save(); autosize(); $('#ai-result').classList.add('hidden');
  };
  $('#ai-append').onclick = () => { body.value = `${body.value}\n\n${result}`; save(); autosize(); $('#ai-result').classList.add('hidden'); };
  $('#ai-copy').onclick = () => copy(result);
  $('#ai-close').onclick = () => $('#ai-result').classList.add('hidden');
  $('#del-note').onclick = async () => { if (await ask('Excluir esta nota?', { okLabel: 'Excluir', danger: true })) { clearTimeout(timer); await api(`/api/notes/${note.id}`, { method: 'DELETE' }); go('#/editor'); } };
};

// ---------------- IDEIAS ----------------
views.ideias = async (main) => {
  main.innerHTML = `
    <div class="page-head"><div><h1>Amplificador de ideias</h1><p class="muted" style="margin:0">Jogue uma ideia crua. A IA expande em ângulos, público, dinheiro e próximos passos.</p></div></div>
    <form class="card" id="idea-form">
      <textarea id="idea" placeholder="Ex: vender marmitas fit para quem trabalha em home office no meu bairro" style="min-height:110px"></textarea>
      <div class="row" style="justify-content:flex-end;margin-top:10px"><button class="btn primary" type="submit" data-busy="Amplificando…">${icon('bulb')} Amplificar</button></div>
    </form>
    <div id="idea-out" style="margin-top:16px"></div>`;
  $('#idea-form').onsubmit = (e) => {
    e.preventDefault();
    const idea = $('#idea').value.trim();
    if (!idea) return toast('Descreva sua ideia.');
    busy(e.submitter, async () => {
      const r = await api('/api/ai/amplify', { method: 'POST', body: { idea } });
      const list = (arr) => `<ul>${arr.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>`;
      const asText = `# ${r.headline}\n\nIdeia original: ${idea}\n\n## Ângulos\n${r.angles.map((a) => `- **${a.title}**: ${a.description}`).join('\n')}\n\n## Público\n${r.audience}\n\n## Como ganhar dinheiro\n${r.monetization.map((x) => `- ${x}`).join('\n')}\n\n## Riscos\n${r.risks.map((x) => `- ${x}`).join('\n')}\n\n## Ideias de conteúdo\n${r.content_ideas.map((x) => `- ${x}`).join('\n')}\n\n## Próximos passos\n${r.next_steps.map((x) => `- [ ] ${x}`).join('\n')}`;
      if (!document.body.contains(main)) return; // a pessoa saiu da tela enquanto a IA respondia
      $('#idea-out').innerHTML = `
        <div class="card hero" style="margin-bottom:16px"><h2>${esc(r.headline)}</h2>
          <div class="row" style="margin-top:10px"><button class="btn" id="save-idea">Salvar no editor</button><button class="btn" id="goal-idea">Transformar em meta</button></div></div>
        <div class="grid grid-2">${r.angles.map((a) => `<div class="card"><h3>${esc(a.title)}</h3><p class="small muted" style="margin:0">${esc(a.description)}</p></div>`).join('')}</div>
        <div class="grid grid-2" style="margin-top:16px">
          <div class="card"><h3>👥 Público</h3><p>${esc(r.audience)}</p><h3>💰 Como ganhar dinheiro</h3>${list(r.monetization)}</div>
          <div class="card"><h3>⚠️ Riscos</h3>${list(r.risks)}<h3>📱 Conteúdo para divulgar</h3>${list(r.content_ideas)}</div>
        </div>
        <div class="card" style="margin-top:16px"><h3>🚀 Próximos passos</h3>${list(r.next_steps)}</div>`;
      $('#save-idea').onclick = async () => { const n = await api('/api/notes', { method: 'POST', body: { title: r.headline.slice(0, 120), content: asText, kind: 'ideia' } }); location.hash = `#/editor/${n.id}`; };
      $('#goal-idea').onclick = async (ev) => busy(ev.currentTarget, async () => {
        const g = await api('/api/goals', { method: 'POST', body: { title: r.headline.slice(0, 200), why: idea, area: 'negócio' } });
        await api(`/api/goals/${g.id}/plan`, { method: 'POST', body: { days: 7 } })
          .catch((err) => toast(`Meta criada, mas o plano falhou: ${err.message}`));
        location.hash = `#/metas/${g.id}`;
      });
    });
  };
};

// ---------------- LEGENDAS ----------------
views.legendas = async (main) => {
  main.innerHTML = `
    <div class="page-head"><div><h1>Legendas</h1><p class="muted" style="margin:0">Legendas prontas para colar, com gancho, CTA e hashtags.</p></div></div>
    <form class="card" id="cap-form">
      <div class="field"><label for="c-topic">Sobre o que é o post?</label><textarea id="c-topic" placeholder="Ex: foto minha no escritório comemorando o primeiro cliente do mês"></textarea></div>
      <div class="field"><label for="c-photo">Foto do post (opcional): a IA olha a imagem para escrever</label>
        <div class="row"><input type="file" id="c-photo" accept="image/*" style="width:auto"><img id="c-prev" class="photo-prev hidden" alt="Prévia da foto"><button type="button" class="btn sm ghost hidden" id="c-clear">Remover foto</button></div></div>
      <div class="grid grid-3" style="gap:10px">
        <div class="field"><label>Plataforma</label><select id="c-platform"><option>Instagram</option><option>TikTok</option><option>LinkedIn</option><option>Facebook</option><option>X (Twitter)</option><option>YouTube Shorts</option><option>WhatsApp Status</option></select></div>
        <div class="field"><label>Estilo</label><select id="c-style"><option>autêntico e humano</option><option>motivacional</option><option>engraçado</option><option>profissional</option><option>vendedor (persuasivo)</option><option>vulnerável e reflexivo</option><option>curto e impactante</option></select></div>
        <div class="field"><label>Objetivo</label><select id="c-goal"><option>engajamento</option><option>ganhar seguidores</option><option>vender</option><option>gerar conversa nos comentários</option><option>levar para o link da bio</option></select></div>
      </div>
      <div class="row" style="justify-content:flex-end"><button class="btn primary" type="submit" data-busy="Escrevendo…">${icon('spark')} Gerar legendas</button></div>
    </form>
    <div id="cap-out" style="margin-top:16px"></div>`;
  let photo = null;
  $('#c-photo').onchange = async (e) => {
    const f = e.target.files[0];
    if (!f) return;
    try {
      photo = await shrinkImage(f);
      $('#c-prev').src = photo.preview;
      $('#c-prev').classList.remove('hidden');
      $('#c-clear').classList.remove('hidden');
    } catch (err) { toast(err.message); }
  };
  $('#c-clear').onclick = () => { photo = null; $('#c-photo').value = ''; $('#c-prev').classList.add('hidden'); $('#c-clear').classList.add('hidden'); };
  $('#cap-form').onsubmit = (e) => {
    e.preventDefault();
    const topic = $('#c-topic').value.trim();
    if (!topic && !photo) return toast('Escreva sobre o que é o post ou anexe uma foto.');
    busy(e.submitter, async () => {
      const platform = $('#c-platform').value;
      const r = await api('/api/ai/caption', { method: 'POST', body: { topic, platform, style: $('#c-style').value, goal: $('#c-goal').value, image: photo && { media_type: photo.media_type, data: photo.data } } });
      const full = (o) => `${o.caption}\n\n${o.cta}\n\n${o.hashtags.map((h) => (h.startsWith('#') ? h : `#${h}`)).join(' ')}`;
      if (!document.body.contains(main)) return; // a pessoa saiu da tela enquanto a IA respondia
      $('#cap-out').innerHTML = `
        <div class="grid grid-2">${r.options.map((o, i) => `
          <div class="card stack"><div class="row between"><b>Opção ${i + 1}</b><div class="row" style="gap:6px"><button class="btn sm" data-sched="${i}">📅 Agendar post</button><button class="btn sm" data-copy="${i}">Copiar</button></div></div>
            <div class="copy-box">${esc(full(o))}</div></div>`).join('')}</div>
        <div class="card" style="margin-top:16px"><p><b>⏰ Melhor horário:</b> ${esc(r.best_time)}</p><p style="margin:0"><b>💡 Dica:</b> ${esc(r.tip)}</p></div>`;
      $$('[data-copy]').forEach((b) => b.onclick = () => copy(full(r.options[Number(b.dataset.copy)])));
      $$('[data-sched]').forEach((b) => b.onclick = async () => {
        const when = await ask('Quando postar?', { input: 'datetime-local', value: `${addDays(state.today, 1)}T19:00`, okLabel: 'Agendar' });
        if (!when) return;
        const start = when.trim().replace(' ', 'T');
        const o = r.options[Number(b.dataset.sched)];
        try {
          await api('/api/events', { method: 'POST', body: { title: `Postar no ${platform}: ${o.hook}`.slice(0, 300), start, notes: full(o) } });
          toast('Post agendado na Agenda! A legenda fica nas notas do compromisso.');
        } catch (e) { toast(e.message); }
      });
    });
  };
};

// ---------------- CRIAR (mobile hub) ----------------
views.criar = async (main) => {
  main.innerHTML = `<h1>Criar</h1><div class="grid grid-2" style="margin-top:16px">
    ${[['editor', 'Editor', 'pen', 'Escreva e melhore textos com IA'], ['ideias', 'Amplificar ideias', 'bulb', 'Transforme ideias em planos'], ['legendas', 'Legendas', 'quote', 'Textos prontos para seus posts'], ['perfil', 'Perfil', 'user', 'Seus dados e preferências']]
      .map(([k, l, i, d]) => `<a class="card row" href="#/${k}" style="text-decoration:none;color:inherit;flex-wrap:nowrap"><span style="color:var(--accent);width:28px">${icon(i)}</span><div><b>${l}</b><div class="small muted">${d}</div></div></a>`).join('')}
  </div>`;
};

// ---------------- PERFIL ----------------
function b64ToU8(b64) {
  const pad = '='.repeat((4 - (b64.length % 4)) % 4);
  const raw = atob((b64 + pad).replace(/-/g, '+').replace(/_/g, '/'));
  return Uint8Array.from(raw, (c) => c.charCodeAt(0));
}
const pushSupported = () => 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;

async function enablePush() {
  if (!pushSupported()) throw new Error('Este navegador não suporta notificações. No iPhone, primeiro adicione o Rumo à tela inicial (iOS 16.4 ou mais novo).');
  const perm = await Notification.requestPermission();
  if (perm !== 'granted') throw new Error('Permissão negada. Libere as notificações do site nas configurações do navegador.');
  const reg = await navigator.serviceWorker.ready;
  const { key } = await api('/api/push/key');
  const sub = (await reg.pushManager.getSubscription()) || await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: b64ToU8(key) });
  await api('/api/push/subscribe', { method: 'POST', body: { subscription: sub.toJSON() } });
}

views.perfil = async (main, arg) => {
  const me = await api('/api/me');
  const user = me.user;
  const u = me.usage || { used: 0, limit: 0, plan: 'gratis', plan_name: 'Grátis' };
  state.me = user;
  const pushState = !pushSupported() ? 'indisponível' : Notification.permission === 'granted' ? 'ativadas' : Notification.permission === 'denied' ? 'bloqueadas' : 'desativadas';
  main.innerHTML = `
    <h1>${arg === 'novo' ? 'Bem-vindo(a)! Conte um pouco sobre você' : 'Perfil'}</h1>
    <p class="muted">Quanto mais a IA souber, mais personalizadas ficam as tarefas e conversas.</p>
    <div class="grid grid-2">
      <form class="card" id="profile">
        <h2>Sobre você</h2>
        <div class="field"><label for="p-name">Nome</label><input type="text" id="p-name" value="${esc(user.name)}"></div>
        <div class="field"><label for="p-about">Sobre você</label><textarea id="p-about" placeholder="Ex: tenho 28 anos, trabalho como designer e quero viver do meu próprio estúdio. Tenho 1h por dia livre à noite.">${esc(user.about)}</textarea></div>
        <div class="field"><label for="p-niche">Seu nicho / área de atuação</label><input type="text" id="p-niche" value="${esc(user.niche)}" placeholder="Ex: confeitaria artesanal, coaching fitness, desenvolvimento web"></div>
        <div class="field"><label for="p-min">Minutos por dia para suas metas</label><input type="number" id="p-min" min="5" max="600" value="${user.daily_minutes || 30}"></div>
        <div class="field"><label for="p-tone">Como a IA deve falar com você?</label><select id="p-tone">
          ${['motivador e direto', 'gentil e acolhedor', 'exigente, sem passar a mão na cabeça', 'divertido e leve', 'técnico e objetivo'].map((t) => `<option ${t === user.tone ? 'selected' : ''}>${t}</option>`).join('')}
        </select></div>
        <div class="row" style="justify-content:flex-end"><button class="btn primary" type="submit">Salvar</button></div>
      </form>

      <div class="stack">
        <section class="card">
          <div class="row between"><h2>Seu plano</h2><span class="chip ${u.plan === 'pro' ? 'accent' : ''}">${u.plan === 'pro' ? '⭐ ' : ''}${esc(u.plan_name)}</span></div>
          <div class="row between small" style="margin-top:6px"><span class="muted">Ações de IA hoje</span><b>${u.used}/${u.limit}</b></div>
          <div class="progress" style="margin:6px 0 12px"><span style="width:${u.limit ? Math.min(100, (u.used / u.limit) * 100) : 0}%"></span></div>
          ${u.plan === 'pro' ? '<p class="small muted" style="margin:0">Obrigado por apoiar o Rumo! 💛</p>' : `
            <p class="small" style="margin-bottom:10px"><b>Pro:</b> 10x mais IA por dia, revisão semanal, legendas com foto sem limite e prioridade nas novidades.</p>
            ${u.checkout_url ? `<a class="btn primary" href="${esc(u.checkout_url)}" target="_blank" rel="noopener noreferrer">Assinar o Pro</a>` : '<span class="small muted">Assinatura Pro chegando em breve.</span>'}`}
        </section>

        <section class="card">
          <h2>Lembrete diário</h2>
          <p class="small muted">Uma notificação por dia com as suas tarefas. Notificações neste aparelho: <b id="push-state">${pushState}</b>.</p>
          <div class="row">
            <label class="row small" style="gap:8px;margin:0;color:var(--text)"><input type="checkbox" id="rem-on" ${user.reminders ? 'checked' : ''} style="width:auto"> Lembrar às</label>
            <input type="time" id="rem-time" value="${esc(user.reminder_time || '08:00')}" style="width:auto" aria-label="Horário do lembrete">
          </div>
          <div class="row" style="margin-top:10px">
            <button class="btn primary sm" id="push-on" data-busy="Ativando…">🔔 Ativar neste aparelho</button>
            <button class="btn sm" id="push-test" data-busy="Enviando…">Enviar teste</button>
          </div>
        </section>

        <form class="card" id="pw-form">
          <h2>Trocar senha</h2>
          <div class="field"><label for="pw-cur">Senha atual</label><input type="password" id="pw-cur" autocomplete="current-password" required></div>
          <div class="field"><label for="pw-new">Nova senha</label><input type="password" id="pw-new" autocomplete="new-password" minlength="8" maxlength="200" required placeholder="Mínimo de 8 caracteres"></div>
          <button class="btn sm" type="submit">Trocar senha</button>
        </form>
      </div>
    </div>

    <div class="card" style="margin-top:16px">
      <h2>Aparência e dados</h2>
      <div class="row" style="margin-top:10px">
        <select id="theme" style="width:auto" aria-label="Tema"><option value="">Tema do sistema</option><option value="light">Claro</option><option value="dark">Escuro</option></select>
        <a class="btn" href="/api/export">Baixar meus dados</a>
        <a class="btn" href="#/tutorial">Ver tutorial</a>
        <a class="btn" href="#/boas-vindas">Refazer configuração</a>
        ${user.is_admin ? '<a class="btn" href="#/admin">Painel admin</a>' : ''}
        <button class="btn" id="logout">Sair</button>
        <button class="btn danger" id="del-acc">Excluir conta</button>
      </div>
      <p class="small muted" style="margin-top:12px">Instale no celular: no navegador, toque em Compartilhar (iPhone) ou no menu ⋮ (Android) e depois em “Adicionar à tela inicial”.</p>
    </div>`;
  try { $('#theme').value = localStorage.getItem('theme') || ''; } catch { /* storage blocked */ }
  $('#theme').onchange = (e) => { setTheme(e.target.value); };
  $('#profile').onsubmit = async (e) => {
    e.preventDefault();
    await api('/api/me', { method: 'PUT', body: { name: $('#p-name').value, about: $('#p-about').value, niche: $('#p-niche').value, tone: $('#p-tone').value, daily_minutes: Number($('#p-min').value) } });
    state.me.name = $('#p-name').value;
    toast('Perfil salvo!');
    if (arg === 'novo') location.hash = '#/metas';
  };
  const saveRem = () => api('/api/me/reminders', { method: 'PUT', body: { reminders: $('#rem-on').checked, reminder_time: $('#rem-time').value } }).then(() => toast('Lembrete salvo.'));
  $('#rem-on').onchange = saveRem;
  $('#rem-time').onchange = saveRem;
  $('#push-on').onclick = (e) => busy(e.currentTarget, async () => {
    await enablePush();
    if ($('#push-state')) $('#push-state').textContent = 'ativadas';
    toast('Notificações ativadas! 🔔');
  });
  $('#push-test').onclick = (e) => busy(e.currentTarget, async () => {
    const r = await api('/api/push/test', { method: 'POST', body: {} });
    toast(r.sent ? 'Enviado! Confira a notificação.' : 'Nenhum aparelho ativado ainda. Toque em “Ativar neste aparelho”.');
  });
  $('#pw-form').onsubmit = async (e) => {
    e.preventDefault();
    try {
      await api('/api/me/password', { method: 'PUT', body: { current: $('#pw-cur').value, password: $('#pw-new').value } });
      e.target.reset();
      toast('Senha trocada. Outros aparelhos foram desconectados.');
    } catch (err) { toast(err.message); }
  };
  $('#logout').onclick = async () => { await api('/api/auth/logout', { method: 'POST' }); state.me = null; go('#/entrar'); };
  $('#del-acc').onclick = async () => {
    if (await ask('Isso apaga TODOS os seus dados. Digite EXCLUIR para confirmar.', { input: true, okLabel: 'Continuar', danger: true }) !== 'EXCLUIR') return;
    const password = await ask('Por segurança, confirme sua senha.', { input: 'password', okLabel: 'Excluir minha conta', danger: true });
    if (!password) return;
    try {
      await api('/api/me', { method: 'DELETE', body: { password } });
      state.me = null;
      toast('Conta excluída. Sentiremos sua falta.');
      go('#/');
    } catch (err) { toast(err.message); }
  };
};

// ---------------- ADMIN ----------------
views.admin = async (main) => {
  if (!state.me.is_admin) {
    main.innerHTML = `
      <form class="card auth-card" id="claim" style="margin:20px auto">
        <h2>Área do administrador</h2>
        <p class="small muted">Digite o código de administrador definido no servidor (variável ADMIN_SECRET).</p>
        <div class="field"><label for="claim-secret">Código</label><input type="password" id="claim-secret" autocomplete="off" required maxlength="200"></div>
        <button class="btn primary" type="submit">Entrar como admin</button>
      </form>`;
    $('#claim').onsubmit = async (e) => {
      e.preventDefault();
      try {
        await api('/api/admin/claim', { method: 'POST', body: { secret: $('#claim-secret').value } });
        state.me.is_admin = true;
        $('.shell')?.remove();
        go('#/admin');
      } catch (err) { toast(err.message); }
    };
    return;
  }
  const s = await api('/api/admin/stats');
  const bars = (raw, label) => {
    const byDay = Object.fromEntries(raw.map((r) => [r.day, r.n]));
    const rows = Array.from({ length: 30 }, (_, i) => { const day = addDays(state.today, i - 29); return { day, n: byDay[day] || 0 }; });
    const max = Math.max(1, ...rows.map((r) => r.n));
    return rows.length
      ? `<div class="bars" role="img" aria-label="${esc(label)}">${rows.map((r) => `<div title="${r.day}: ${r.n}"><span style="height:${(r.n / max) * 100}%"></span></div>`).join('')}</div>
         <div class="row between small muted"><span>${fmtDate(rows[0].day, { day: 'numeric', month: 'short' })}</span><span>${fmtDate(rows.at(-1).day, { day: 'numeric', month: 'short' })}</span></div>`
      : '<p class="muted small">Sem dados ainda.</p>';
  };
  const tiles = [['Usuários', s.users], ['Novos (7 dias)', s.new7], ['Ativos hoje', s.active1], ['Ativos (7 dias)', s.active7], ['Fizeram o passo a passo', s.onboarded], ['Assinantes Pro', s.pro], ['Com notificações', s.push], ['Tarefas feitas (7 dias)', s.tasks_done7], ['Ações de IA hoje', s.ai_today]];
  main.innerHTML = `
    <h1>Painel do Rumo</h1>
    <p class="muted">Visão geral dos usuários e do uso da IA.</p>
    <div class="grid grid-3">${tiles.map(([l, v]) => `<div class="card"><div class="small muted">${l}</div><div class="stat">${v}</div></div>`).join('')}</div>
    <div class="grid grid-2" style="margin-top:16px">
      <div class="card"><h2>Cadastros (30 dias)</h2>${bars(s.signups30, 'Cadastros por dia')}</div>
      <div class="card"><h2>Uso da IA (30 dias)</h2>${bars(s.ai30, 'Ações de IA por dia')}</div>
    </div>
    <div class="card" style="margin-top:16px">
      <h2>Últimos usuários</h2>
      <div class="table-wrap"><table class="table">
        <thead><tr><th>Nome</th><th>E-mail</th><th>Perfil</th><th>Desde</th><th>Último acesso</th><th>Feitas</th><th>Plano</th></tr></thead>
        <tbody>${s.recent.map((r) => `<tr><td>${esc(r.name)}</td><td>${esc(r.email)}</td><td>${esc(r.role || '—')}</td><td>${esc(r.created_at.slice(0, 10))}</td><td>${esc(r.last_seen || '—')}</td><td class="num">${r.done}</td>
          <td><select data-plan="${r.id}" aria-label="Plano de ${esc(r.name)}"><option value="gratis" ${r.plan !== 'pro' ? 'selected' : ''}>Grátis</option><option value="pro" ${r.plan === 'pro' ? 'selected' : ''}>Pro</option></select></td></tr>`).join('')}</tbody>
      </table></div>
    </div>`;
  $$('[data-plan]').forEach((sel) => sel.onchange = async () => {
    await api(`/api/admin/users/${sel.dataset.plan}`, { method: 'PATCH', body: { plan: sel.value } });
    toast('Plano atualizado.');
  });
};

// ---------------- HÁBITOS (dentro de Metas) ----------------
const DAY_NAMES = ['D', 'S', 'T', 'Q', 'Q', 'S', 'S'];
const daysLabel = (d) => (d === '0123456' ? 'todo dia' : d === '12345' ? 'seg a sex' : d.split('').map((x) => ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb'][x]).join(', '));

async function renderHabits(box) {
  const habits = await api('/api/habits');
  box.innerHTML = `
    <div class="row between"><h2>Hábitos</h2><span class="small muted">Viram tarefa sozinhos nos dias escolhidos</span></div>
    ${habits.length ? habits.map((h) => `
      <div class="habit ${h.active ? '' : 'paused'}" data-h="${h.id}">
        <div style="flex:1;min-width:0"><b>${esc(h.title)}</b>
          <div class="small muted">${daysLabel(h.days)} · ${h.minutes} min${h.streak ? ` · 🔥 ${h.streak}` : ''}${h.active ? '' : ' · pausado'}</div></div>
        <div class="habit-dots" aria-label="Últimos 7 dias">${Array.from({ length: 7 }, (_, i) => {
          const day = addDays(state.today, i - 6);
          const t = h.last7.find((x) => x.d === day);
          return `<span class="${t ? (t.done ? 'on' : day === state.today ? '' : 'miss') : ''}" title="${day}"></span>`;
        }).join('')}</div>
        <button class="btn sm ghost" data-h-toggle="${h.id}">${h.active ? 'Pausar' : 'Retomar'}</button>
        <button class="btn sm ghost danger" data-h-del="${h.id}" aria-label="Excluir hábito">${icon('trash')}</button>
      </div>`).join('') : '<p class="small muted">Ex: “Postar 1 story”, “Ler 10 páginas”, “Beber 2L de água”.</p>'}
    <form id="habit-form" class="stack" style="margin-top:12px">
      <div class="row" style="flex-wrap:nowrap"><input type="text" id="h-title" placeholder="Novo hábito" aria-label="Novo hábito"><input type="number" id="h-min" value="10" min="1" max="240" style="width:84px" aria-label="Minutos"></div>
      <div class="row between"><div class="day-pick">${DAY_NAMES.map((n, i) => `<button type="button" class="sel" data-day="${i}" aria-pressed="true" aria-label="${['domingo', 'segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado'][i]}">${n}</button>`).join('')}</div>
      <button class="btn sm primary" type="submit">${icon('plus')} Criar hábito</button></div>
    </form>`;
  $$('.day-pick button', box).forEach((b) => b.onclick = () => { b.classList.toggle('sel'); b.setAttribute('aria-pressed', b.classList.contains('sel')); });
  $('#habit-form', box).onsubmit = async (e) => {
    e.preventDefault();
    const title = $('#h-title', box).value.trim();
    const days = $$('.day-pick button.sel', box).map((b) => b.dataset.day).join('');
    if (!title) return toast('Escreva o hábito.');
    if (!days) return toast('Escolha pelo menos um dia.');
    await api('/api/habits', { method: 'POST', body: { title, minutes: Number($('#h-min', box).value), days } });
    toast('Hábito criado! Ele aparece em Hoje nos dias escolhidos.');
    renderHabits(box);
  };
  box.onclick = async (e) => {
    const t = e.target.closest('[data-h-toggle]');
    const d = e.target.closest('[data-h-del]');
    if (t) {
      const h = habits.find((x) => String(x.id) === t.dataset.hToggle);
      await api(`/api/habits/${h.id}`, { method: 'PATCH', body: { active: !h.active } });
      renderHabits(box);
    } else if (d && await ask('Excluir este hábito?', { okLabel: 'Excluir', danger: true })) {
      await api(`/api/habits/${d.dataset.hDel}`, { method: 'DELETE' });
      renderHabits(box);
    }
  };
}

// ---------------- CRONÔMETRO DE FOCO ----------------
const focus = { task: null, end: 0, left: 0, paused: false, timer: null, onDone: null };
function beep() {
  try {
    const ac = new (window.AudioContext || window.webkitAudioContext)();
    [0, 0.25, 0.5].forEach((t) => { const o = ac.createOscillator(); const g = ac.createGain(); o.frequency.value = 880; o.connect(g); g.connect(ac.destination); g.gain.setValueAtTime(0.15, ac.currentTime + t); o.start(ac.currentTime + t); o.stop(ac.currentTime + t + 0.15); });
  } catch { /* sem áudio */ }
}
function renderFocus() {
  let el = $('#focus');
  if (!focus.task) { el?.remove(); document.title = 'Rumo'; return; }
  if (!el) { el = document.createElement('div'); el.id = 'focus'; el.className = 'focus-pill'; document.body.append(el); }
  const ms = focus.paused ? focus.left : Math.max(0, focus.end - Date.now());
  const mm = String(Math.floor(ms / 60000)).padStart(2, '0');
  const ss = String(Math.floor((ms % 60000) / 1000)).padStart(2, '0');
  const over = ms <= 0;
  document.title = over ? '⏰ Tempo! · Rumo' : `${mm}:${ss} · ${focus.task.title}`;
  el.innerHTML = `<span class="focus-time">${over ? '⏰' : `${mm}:${ss}`}</span>
    <span class="focus-title">${over ? 'Tempo! Terminou?' : esc(focus.task.title)}</span>
    ${over ? '' : `<button class="btn sm ghost" data-f="pause" aria-label="${focus.paused ? 'Continuar' : 'Pausar'}">${focus.paused ? '▶' : 'II'}</button>`}
    <button class="btn sm primary" data-f="done">✓ Feito</button>
    <button class="btn sm ghost" data-f="stop" aria-label="Fechar cronômetro">✕</button>`;
  el.onclick = (e) => {
    const f = e.target.closest('[data-f]')?.dataset.f;
    if (f === 'pause') {
      if (focus.paused) { focus.end = Date.now() + focus.left; focus.paused = false; } else { focus.left = focus.end - Date.now(); focus.paused = true; }
      renderFocus();
    } else if (f === 'done') { const cb = focus.onDone; stopFocus(); cb?.(); } else if (f === 'stop') stopFocus();
  };
}
function startFocus(task, onDone) {
  stopFocus();
  Object.assign(focus, { task, end: Date.now() + task.minutes * 60000, paused: false, onDone });
  let rang = false;
  focus.timer = setInterval(() => {
    if (!focus.paused && Date.now() >= focus.end && !rang) {
      rang = true;
      beep();
      navigator.vibrate?.([200, 100, 200]);
    }
    renderFocus();
  }, 1000);
  renderFocus();
  toast(`Foco de ${task.minutes} min começou. Você consegue! 💪`);
}
function stopFocus() { clearInterval(focus.timer); focus.task = null; renderFocus(); }

// ---------------- PÁGINA DE APRESENTAÇÃO (visitantes) ----------------
function renderLanding() {
  state.me = null;
  app.innerHTML = `
    <div class="landing">
      <header class="lp-top"><div class="brand" style="padding:0"><span class="brand-mark">➜</span> Rumo</div>
        <div class="row"><a class="btn ghost" href="#/entrar">Entrar</a><a class="btn primary" href="#/entrar/criar">Criar conta grátis</a></div></header>

      <section class="lp-hero">
        <div class="lp-copy">
          <span class="chip accent">IA em português, feita para quem quer sair do lugar</span>
          <h1>Sua meta, um passo pequeno por dia.</h1>
          <p class="lp-sub">O Rumo conversa com você, transforma seus objetivos em tarefas de 10 a 30 minutos e ajuda a fazer cada uma: entrega o texto pronto, o passo a passo e os links.</p>
          <div class="row"><a class="btn primary lp-cta" href="#/entrar/criar">Começar grátis</a><button type="button" class="btn ghost" data-scroll="como">Como funciona ↓</button></div>
          <p class="small muted">Sem cartão. Leva 2 minutos para configurar.</p>
        </div>
        <div class="lp-demo" aria-hidden="true">
          <div class="bubble assistant">Bom dia, Ana! Hoje são <b>3 tarefas</b>, uns <b>40 min</b>. Foco: <i>Conseguir os primeiros 10 clientes</i>. 👇</div>
          <div class="task-card"><div class="row" style="flex-wrap:nowrap;gap:12px;align-items:flex-start"><span class="check"></span><div><div class="task-title">Mande mensagem para 5 ex-clientes</div><div class="task-detail">Ofereça uma condição especial de retorno.</div></div></div>
            <div class="task-buttons"><span class="btn sm primary">✓ Feito</span><span class="btn sm">🆘 Me ajuda</span><span class="btn sm">▶ Foco</span></div></div>
          <div class="bubble user">🆘 Me ajuda com: Mande mensagem para 5 ex-clientes</div>
          <div class="bubble assistant">Aqui está uma mensagem pronta para copiar: <i>“Oi, Carla! Tudo bem? Lembrei de você…”</i> E o passo a passo em 3 etapas 👇</div>
        </div>
      </section>

      <section class="lp-section" id="como">
        <h2>Como funciona</h2>
        <div class="grid grid-3">
          ${[['1', 'Conte onde quer chegar', 'Responda 8 perguntas rápidas: sua meta, o prazo e quanto tempo você tem por dia.'],
             ['2', 'Receba seu dia pronto', 'A IA monta tarefas pequenas todo dia, no tamanho do seu tempo, e avisa no celular.'],
             ['3', 'Faça junto com a IA', 'Travou? Toque em “Me ajuda” e receba a solução. Fez? Toque em “Feito” e mantenha a sequência 🔥.']]
            .map(([n, t, d]) => `<div class="card"><span class="lp-step">${n}</span><h3>${t}</h3><p class="small muted" style="margin:0">${d}</p></div>`).join('')}
        </div>
      </section>

      <section class="lp-section">
        <h2>Tudo num lugar só</h2>
        <div class="grid grid-3">
          ${[['home', 'Dia em forma de conversa', 'Fale “fiz a primeira” ou “hoje não dá” e a IA atualiza tudo.'],
             ['target', 'Metas e hábitos', 'Planos semanais, hábitos diários e sequência de dias.'],
             ['cal', 'Agenda inteligente', '“Dentista sexta às 15h” vira compromisso. Também aceita repetições.'],
             ['pen', 'Editor com IA', 'Melhore, resuma, transforme em post ou em roteiro de vídeo.'],
             ['bulb', 'Amplificador de ideias', 'Uma ideia solta vira público, formas de ganhar dinheiro e próximos passos.'],
             ['quote', 'Legendas com foto', 'Envie a foto do post e receba 3 legendas prontas, com hashtags.']]
            .map(([i, t, d]) => `<div class="card tip"><span class="tip-icon">${icon(i)}</span><div><h3>${t}</h3><p class="small muted" style="margin:0">${d}</p></div></div>`).join('')}
        </div>
      </section>

      <section class="lp-section">
        <h2>Planos</h2>
        <div class="grid grid-2 lp-plans">
          <div class="card"><h3>Grátis</h3><div class="stat">R$ 0</div><ul class="small"><li>Metas, hábitos e agenda</li><li>30 ações de IA por dia</li><li>Lembrete diário no celular</li></ul><a class="btn" href="#/entrar/criar">Começar grátis</a></div>
          <div class="card lp-pro"><h3>Pro ⭐</h3><div class="stat">R$ 19,90<span class="small muted">/mês</span></div><ul class="small"><li>Tudo do Grátis</li><li>10x mais IA por dia</li><li>Legendas com foto e revisão semanal sem limite</li><li>Novidades primeiro</li></ul><a class="btn primary" href="#/entrar/criar">Experimentar</a></div>
        </div>
      </section>

      <section class="lp-section">
        <h2>Perguntas frequentes</h2>
        ${[['Preciso instalar alguma coisa?', 'Não. Funciona no navegador. No celular, você pode adicionar à tela inicial e usar como app.'],
           ['Meus dados ficam seguros?', 'Cada conta tem os próprios dados, protegidos por senha. Você pode baixar ou apagar tudo quando quiser.'],
           ['A IA faz as tarefas por mim?', 'Ela faz o máximo possível: escreve textos, mensagens, roteiros e planos, e indica links. A ação final é sua.'],
           ['Serve para qualquer meta?', 'Sim: negócio, conteúdo, estudos, saúde, finanças. Você conta a meta e o Rumo adapta o plano.']]
          .map(([q, a]) => `<details class="faq"><summary>${q}</summary><p class="muted">${a}</p></details>`).join('')}
      </section>

      <section class="lp-final card hero"><h2>Comece hoje. Amanhã você agradece.</h2><a class="btn" href="#/entrar/criar">Criar minha conta grátis →</a></section>
      <footer class="small muted lp-foot">Rumo · feito no Brasil 🇧🇷</footer>
    </div>`;
  $('[data-scroll]')?.addEventListener('click', () => $('#como').scrollIntoView({ behavior: 'smooth' }));
}

// ---------------- REDEFINIR SENHA ----------------
function renderReset(token) {
  app.innerHTML = `
    <div class="auth"><form class="card auth-card" id="reset-form">
      <div class="brand" style="padding:0"><span class="brand-mark">➜</span> Rumo</div>
      <h2 style="margin-top:16px">Criar nova senha</h2>
      <div class="field"><label for="r1">Nova senha</label><input type="password" id="r1" minlength="8" maxlength="200" required autocomplete="new-password" placeholder="Mínimo de 8 caracteres"></div>
      <div class="field"><label for="r2">Repita a senha</label><input type="password" id="r2" minlength="8" maxlength="200" required autocomplete="new-password"></div>
      <button class="btn primary" style="width:100%;justify-content:center" type="submit">Salvar e entrar</button>
    </form></div>`;
  $('#reset-form').onsubmit = async (e) => {
    e.preventDefault();
    if ($('#r1').value !== $('#r2').value) return toast('As senhas não são iguais.');
    try {
      await api('/api/auth/reset', { method: 'POST', body: { token, password: $('#r1').value } });
      toast('Senha nova salva!');
      go('#/hoje');
    } catch (err) { toast(err.message); }
  };
}

function setTheme(v) {
  if (v) document.documentElement.dataset.theme = v; else delete document.documentElement.dataset.theme;
  try { if (v) localStorage.setItem('theme', v); else localStorage.removeItem('theme'); } catch { /* ignore */ }
}
try { const t = localStorage.getItem('theme'); if (t) document.documentElement.dataset.theme = t; } catch { /* ignore */ }

if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
route();
