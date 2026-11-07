import { $, $$, esc, api, toast, md, fmtDate, addDays, busy, copy, icon, ask } from './util.js';

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
  if (name === 'entrar') return renderAuth();
  if (!state.me) {
    try {
      const me = await api('/api/me');
      Object.assign(state, { me: me.user, ai: me.ai, today: me.today });
    } catch { return renderAuth(); }
  }
  const view = views[name] || views.hoje;
  renderShell(name in views ? name : 'hoje');
  const main = $('#main');
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
          <nav>${NAV.map(([k, l, i]) => `<a class="nav-link" data-k="${k}" href="#/${k}">${icon(i)} ${l}</a>`).join('')}</nav>
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
function renderAuth() {
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
          <div class="field"><label for="a-pass">Senha</label><input id="a-pass" type="password" required minlength="6" autocomplete="current-password"></div>
          <button class="btn primary" style="width:100%;justify-content:center" type="submit">Entrar</button>
        </form>
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
  });
  $('#auth-form').onsubmit = async (e) => {
    e.preventDefault();
    const body = { name: $('#a-name').value, email: $('#a-email').value, password: $('#a-pass').value };
    try {
      await api(mode === 'register' ? '/api/auth/register' : '/api/auth/login', { method: 'POST', body });
      go(mode === 'register' ? '#/perfil/novo' : '#/hoje');
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

// ---------------- HOJE ----------------
views.hoje = async (main) => {
  const d = await api('/api/today');
  state.today = d.date;
  const hour = new Date().getHours();
  const hello = hour < 12 ? 'Bom dia' : hour < 18 ? 'Boa tarde' : 'Boa noite';
  const doneCount = d.tasks.filter((t) => t.done).length;
  const pct = d.tasks.length ? Math.round((doneCount / d.tasks.length) * 100) : 0;
  const weekMap = Object.fromEntries(d.week.map((w) => [w.d, w]));
  const moods = ['😞', '😕', '😐', '🙂', '🤩'];

  main.innerHTML = `
    ${!state.ai ? '<div class="banner">IA em <b>modo demonstração</b>. Para respostas reais, configure <code>ANTHROPIC_API_KEY</code> no servidor (veja o README).</div>' : ''}
    <div class="card hero" style="margin-bottom:16px">
      <div class="row between">
        <div>
          <h1>${hello}, ${esc(state.me.name.split(' ')[0])}!</h1>
          <p class="muted" style="margin:0">${fmtDate(d.date)} · ${d.streak ? `🔥 ${d.streak} dia${d.streak > 1 ? 's' : ''} seguido${d.streak > 1 ? 's' : ''}` : 'Comece sua sequência hoje'}</p>
        </div>
        <button class="btn" id="gen-daily" data-busy="Montando seu dia…">${icon('spark')} Tarefas do dia com IA</button>
      </div>
      <p id="daily-msg" class="hidden" style="margin:12px 0 0;font-weight:500"></p>
    </div>

    <div class="grid grid-2">
      <section class="card">
        <div class="row between"><h2>Tarefas de hoje</h2><span class="muted small">${doneCount}/${d.tasks.length}</span></div>
        <div class="progress" style="margin:6px 0 10px"><span style="width:${pct}%"></span></div>
        <div id="today-tasks">${d.tasks.length ? d.tasks.map((t) => taskRow(t)).join('') : `<div class="empty">Nada para hoje ainda.<br>Toque em <b>Tarefas do dia com IA</b> ou adicione abaixo.</div>`}</div>
        <form id="add-task" class="row" style="margin-top:10px;flex-wrap:nowrap">
          <input type="text" id="new-task" placeholder="Adicionar tarefa rápida…" aria-label="Nova tarefa">
          <button class="btn primary" type="submit" aria-label="Adicionar">${icon('plus')}</button>
        </form>
        ${d.overdue.length ? `<details style="margin-top:14px"><summary class="muted small">Pendentes de dias anteriores (${d.overdue.length})</summary><div id="overdue">${d.overdue.map((t) => taskRow(t, { showDate: true })).join('')}</div></details>` : ''}
      </section>

      <div class="stack">
        <section class="card">
          <h2>Sua semana</h2>
          <div class="week">${Array.from({ length: 7 }, (_, i) => {
            const day = addDays(d.date, i - 6);
            const w = weekMap[day];
            const ratio = w && w.total ? w.done / w.total : 0;
            const lvl = !w || !w.done ? '' : ratio >= 1 ? 'l3' : ratio >= 0.5 ? 'l2' : 'l1';
            return `<div><div class="dot ${lvl}">${w ? w.done : ''}</div>${fmtDate(day, { weekday: 'short' }).replace('.', '')}</div>`;
          }).join('')}</div>
          <button class="btn sm" id="review" style="margin-top:12px" data-busy="Analisando…">${icon('spark')} Revisão da semana com IA</button>
          <div id="review-out" class="md small" style="margin-top:10px"></div>
        </section>

        <section class="card">
          <h2>Como você está hoje?</h2>
          <div class="moods">${moods.map((m, i) => `<button data-mood="${i + 1}" class="${d.checkin?.mood === i + 1 ? 'sel' : ''}" aria-label="Humor ${i + 1}">${m}</button>`).join('')}</div>
        </section>

        <section class="card">
          <div class="row between"><h2>Próximos compromissos</h2><a href="#/agenda" class="small">Agenda →</a></div>
          ${d.events.length ? d.events.map((e) => `<div class="row" style="padding:6px 0"><b style="min-width:92px">${e.start.slice(0, 10) === d.date ? 'Hoje' : 'Amanhã'} ${e.start.slice(11)}</b><span>${esc(e.title)}</span></div>`).join('') : '<p class="muted small">Nada marcado para hoje e amanhã.</p>'}
        </section>

        <section class="card">
          <div class="row between"><h2>Metas</h2><a href="#/metas" class="small">Ver todas →</a></div>
          ${d.goals.length ? d.goals.slice(0, 4).map((g) => `<a href="#/metas/${g.id}" style="display:block;color:inherit;text-decoration:none;padding:6px 0"><div class="row between small"><b>${esc(g.title)}</b><span class="muted">${g.total ? Math.round((g.done / g.total) * 100) : 0}%</span></div><div class="progress"><span style="width:${g.total ? (g.done / g.total) * 100 : 0}%"></span></div></a>`).join('') : '<p class="muted small">Você ainda não tem metas. <a href="#/metas">Criar a primeira</a></p>'}
        </section>
      </div>
    </div>`;

  const refresh = () => views.hoje(main);
  bindTasks(main, refresh);
  $('#add-task').onsubmit = async (e) => {
    e.preventDefault();
    const title = $('#new-task').value.trim();
    if (!title) return;
    await api('/api/tasks', { method: 'POST', body: { title, due_date: d.date } });
    refresh();
  };
  $('#gen-daily').onclick = (e) => busy(e.currentTarget, async () => {
    const r = await api('/api/ai/daily', { method: 'POST', body: {} });
    await refresh();
    const msg = $('#daily-msg');
    msg.textContent = r.message;
    msg.classList.remove('hidden');
  });
  $('#review').onclick = (e) => busy(e.currentTarget, async () => {
    const r = await api('/api/ai/review', { method: 'POST', body: {} });
    $('#review-out').innerHTML = md(r.text);
  });
  $$('[data-mood]').forEach((b) => b.onclick = async () => {
    await api('/api/checkin', { method: 'POST', body: { mood: Number(b.dataset.mood) } });
    $$('[data-mood]').forEach((x) => x.classList.toggle('sel', x === b));
    toast(Number(b.dataset.mood) <= 2 ? 'Dias difíceis passam. Que tal conversar com a IA?' : 'Anotado!');
  });
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
        ${byDay[day].events.map((e) => `<div class="event" data-ev="${e.id}"><div class="event-time">${e.start.slice(11)}</div><div style="flex:1"><b>${esc(e.title)}</b>${e.end ? `<div class="small muted">até ${e.end.slice(11)}</div>` : ''}${e.notes ? `<div class="small muted">${esc(e.notes.length > 140 ? `${e.notes.slice(0, 140)}…` : e.notes)}</div>` : ''}</div><button class="btn sm ghost danger" data-del-ev="${e.id}" aria-label="Excluir">${icon('trash')}</button></div>`).join('')}
        ${byDay[day].tasks.length ? `<div class="small muted">📋 ${byDay[day].tasks.filter((t) => t.done).length}/${byDay[day].tasks.length} tarefas: ${byDay[day].tasks.slice(0, 3).map((t) => esc(t.title)).join(' · ')}${byDay[day].tasks.length > 3 ? '…' : ''}</div>` : ''}
      </div>`).join('') : '<div class="card empty">Agenda livre pelos próximos 30 dias.</div>'}</div>

    <dialog id="ev-dialog"><form method="dialog" id="ev-form">
      <h2>Novo compromisso</h2>
      <div class="field"><label>Título</label><input type="text" id="ev-title" required></div>
      <div class="grid grid-2" style="gap:10px">
        <div class="field"><label>Início</label><input type="datetime-local" id="ev-start" required></div>
        <div class="field"><label>Fim (opcional)</label><input type="datetime-local" id="ev-end"></div>
      </div>
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
    await api('/api/events', { method: 'POST', body: { title: $('#ev-title').value, start: $('#ev-start').value, end: $('#ev-end').value || null, notes: $('#ev-notes').value } });
    dlg.close();
    refresh();
  };
  main.addEventListener('click', async (e) => {
    const b = e.target.closest('[data-del-ev]');
    if (b && await ask('Excluir este compromisso?', { okLabel: 'Excluir', danger: true })) { await api(`/api/events/${b.dataset.delEv}`, { method: 'DELETE' }); refresh(); }
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

  const dlg = $('#goal-dialog');
  $('#new-goal').onclick = () => dlg.showModal();
  $('#goal-form').onsubmit = (e) => {
    if (e.submitter?.value !== 'ok') return;
    e.preventDefault();
    busy(e.submitter, async () => {
      const g = await api('/api/goals', { method: 'POST', body: { title: $('#g-title').value, why: $('#g-why').value, area: $('#g-area').value, deadline: $('#g-deadline').value || null } });
      if ($('#g-plan').checked) await api(`/api/goals/${g.id}/plan`, { method: 'POST', body: { days: 7 } });
      dlg.close();
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
  const bubble = (m) => `<div class="bubble ${m.role} ${m.role === 'assistant' ? 'md' : ''}">${m.role === 'assistant' ? md(m.content) : esc(m.content)}</div>`;
  main.innerHTML = `
    <div class="page-head" style="margin-bottom:10px"><div><h1>Conversar com a IA</h1><p class="muted small" style="margin:0">Ela conhece suas metas, tarefas e agenda.</p></div>
      <button class="btn sm ghost" id="clear-chat">Limpar conversa</button></div>
    <div class="chat">
      <div class="chat-log" id="log">${history.length ? history.map(bubble).join('') : `<div class="empty">Desabafe, peça ideias, planeje o dia. Estou aqui.</div>`}</div>
      <div class="suggestions">${['Me ajuda a planejar meu dia', 'Estou travado, o que faço agora?', 'Me dá 5 ideias de post para hoje', 'Agenda uma reunião amanhã às 10h', 'Como eu divulgo meu trabalho?'].map((s) => `<button data-s="${esc(s)}">${esc(s)}</button>`).join('')}</div>
      <form class="chat-input" id="chat-form">
        <textarea id="msg" placeholder="Escreva sua mensagem…" rows="1" aria-label="Mensagem"></textarea>
        <button class="btn primary" type="submit" aria-label="Enviar">Enviar</button>
      </form>
    </div>`;
  const log = $('#log');
  log.scrollTop = log.scrollHeight;
  const input = $('#msg');
  let sending = false;

  async function send(text) {
    if (!text || sending) return;
    sending = true;
    $('.empty', log)?.remove();
    log.insertAdjacentHTML('beforeend', bubble({ role: 'user', content: text }));
    log.insertAdjacentHTML('beforeend', '<div class="bubble assistant md"><span class="loading"></span></div>');
    const out = log.lastElementChild;
    log.scrollTop = log.scrollHeight;
    let acc = '';
    try {
      const res = await fetch('/api/ai/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: text }) });
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
          if (ev.t) { acc += ev.t; out.innerHTML = md(acc); log.scrollTop = log.scrollHeight; }
          if (ev.action) { out.insertAdjacentHTML('afterend', `<div class="chip accent" style="align-self:flex-start">${esc(ev.action)}</div>`); }
          if (ev.error) throw new Error(ev.error);
        }
      }
    } catch (e) {
      out.innerHTML = `<span style="color:var(--danger)">${esc(e.message)}</span>`;
    } finally { sending = false; }
  }
  $('#chat-form').onsubmit = (e) => { e.preventDefault(); const t = input.value.trim(); input.value = ''; send(t); };
  input.onkeydown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); $('#chat-form').requestSubmit(); } };
  $$('[data-s]').forEach((b) => b.onclick = () => send(b.dataset.s));
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
  const save = () => { $('#save-state').textContent = 'Salvando…'; clearTimeout(timer); timer = setTimeout(async () => { await api(`/api/notes/${note.id}`, { method: 'PUT', body: { title: title.value, content: body.value } }); $('#save-state').textContent = 'Salvo'; }, 600); };
  title.oninput = save;
  body.oninput = save;
  const autosize = () => { body.style.height = 'auto'; body.style.height = `${Math.max(body.scrollHeight, 300)}px`; };
  body.addEventListener('input', autosize);
  autosize();

  let result = '';
  const run = (btn, action, instruction) => busy(btn, async () => {
    const sel = body.value.slice(body.selectionStart, body.selectionEnd);
    const text = sel || body.value;
    if (!text.trim()) throw new Error('Escreva algo primeiro.');
    const r = await api('/api/ai/edit', { method: 'POST', body: { action, text, instruction } });
    result = r.text;
    $('#ai-text').innerHTML = md(result);
    $('#ai-result').classList.remove('hidden');
  });
  $$('[data-ai]').forEach((b) => b.onclick = () => run(b, b.dataset.ai));
  $('#custom-ai').onclick = async (e) => { const btn = e.currentTarget; const ins = await ask('O que a IA deve fazer com o texto?', { input: true, placeholder: 'Ex: deixe mais curto e engraçado', okLabel: 'Pedir' }); if (ins) run(btn, 'custom', ins); };
  $('#ai-replace').onclick = () => { body.value = result; save(); autosize(); $('#ai-result').classList.add('hidden'); };
  $('#ai-append').onclick = () => { body.value = `${body.value}\n\n${result}`; save(); autosize(); $('#ai-result').classList.add('hidden'); };
  $('#ai-copy').onclick = () => copy(result);
  $('#ai-close').onclick = () => $('#ai-result').classList.add('hidden');
  $('#del-note').onclick = async () => { if (await ask('Excluir esta nota?', { okLabel: 'Excluir', danger: true })) { await api(`/api/notes/${note.id}`, { method: 'DELETE' }); go('#/editor'); } };
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
        await api(`/api/goals/${g.id}/plan`, { method: 'POST', body: { days: 7 } });
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
      <div class="field"><label>Sobre o que é o post?</label><textarea id="c-topic" placeholder="Ex: foto minha no escritório comemorando o primeiro cliente do mês"></textarea></div>
      <div class="grid grid-3" style="gap:10px">
        <div class="field"><label>Plataforma</label><select id="c-platform"><option>Instagram</option><option>TikTok</option><option>LinkedIn</option><option>Facebook</option><option>X (Twitter)</option><option>YouTube Shorts</option><option>WhatsApp Status</option></select></div>
        <div class="field"><label>Estilo</label><select id="c-style"><option>autêntico e humano</option><option>motivacional</option><option>engraçado</option><option>profissional</option><option>vendedor (persuasivo)</option><option>vulnerável e reflexivo</option><option>curto e impactante</option></select></div>
        <div class="field"><label>Objetivo</label><select id="c-goal"><option>engajamento</option><option>ganhar seguidores</option><option>vender</option><option>gerar conversa nos comentários</option><option>levar para o link da bio</option></select></div>
      </div>
      <div class="row" style="justify-content:flex-end"><button class="btn primary" type="submit" data-busy="Escrevendo…">${icon('spark')} Gerar legendas</button></div>
    </form>
    <div id="cap-out" style="margin-top:16px"></div>`;
  $('#cap-form').onsubmit = (e) => {
    e.preventDefault();
    const topic = $('#c-topic').value.trim();
    if (!topic) return toast('Sobre o que é o post?');
    busy(e.submitter, async () => {
      const r = await api('/api/ai/caption', { method: 'POST', body: { topic, platform: $('#c-platform').value, style: $('#c-style').value, goal: $('#c-goal').value } });
      const full = (o) => `${o.caption}\n\n${o.cta}\n\n${o.hashtags.map((h) => (h.startsWith('#') ? h : `#${h}`)).join(' ')}`;
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
          await api('/api/events', { method: 'POST', body: { title: `Postar no ${$('#c-platform').value}: ${o.hook}`.slice(0, 300), start, notes: full(o) } });
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
views.perfil = async (main, arg) => {
  const { user } = await api('/api/me');
  state.me = user;
  main.innerHTML = `
    <h1>${arg === 'novo' ? 'Bem-vindo(a)! Conte um pouco sobre você' : 'Perfil'}</h1>
    <p class="muted">Quanto mais a IA souber, mais personalizadas ficam as tarefas e conversas.</p>
    <form class="card" id="profile">
      <div class="field"><label>Nome</label><input type="text" id="p-name" value="${esc(user.name)}"></div>
      <div class="field"><label>Sobre você</label><textarea id="p-about" placeholder="Ex: tenho 28 anos, trabalho como designer e quero viver do meu próprio estúdio. Tenho 1h por dia livre à noite.">${esc(user.about)}</textarea></div>
      <div class="field"><label>Seu nicho / área de atuação</label><input type="text" id="p-niche" value="${esc(user.niche)}" placeholder="Ex: confeitaria artesanal, coaching fitness, desenvolvimento web"></div>
      <div class="field"><label>Como a IA deve falar com você?</label><select id="p-tone">
        ${['motivador e direto', 'gentil e acolhedor', 'exigente, sem passar a mão na cabeça', 'divertido e leve', 'técnico e objetivo'].map((t) => `<option ${t === user.tone ? 'selected' : ''}>${t}</option>`).join('')}
      </select></div>
      <div class="row" style="justify-content:flex-end"><button class="btn primary" type="submit">Salvar</button></div>
    </form>
    <div class="card" style="margin-top:16px">
      <h2>Aparência e dados</h2>
      <div class="row" style="margin-top:10px">
        <select id="theme" style="width:auto"><option value="">Tema do sistema</option><option value="light">Claro</option><option value="dark">Escuro</option></select>
        <a class="btn" href="/api/export">Baixar meus dados</a>
        <button class="btn" id="logout">Sair</button>
        <button class="btn danger" id="del-acc">Excluir conta</button>
      </div>
      <p class="small muted" style="margin-top:12px">Dica: no celular, use “Adicionar à tela inicial” para instalar o Rumo como app.</p>
    </div>`;
  try { $('#theme').value = localStorage.getItem('theme') || ''; } catch { /* storage blocked */ }
  $('#theme').onchange = (e) => { setTheme(e.target.value); };
  $('#profile').onsubmit = async (e) => {
    e.preventDefault();
    await api('/api/me', { method: 'PUT', body: { name: $('#p-name').value, about: $('#p-about').value, niche: $('#p-niche').value, tone: $('#p-tone').value } });
    state.me.name = $('#p-name').value;
    toast('Perfil salvo!');
    if (arg === 'novo') location.hash = '#/metas';
  };
  $('#logout').onclick = async () => { await api('/api/auth/logout', { method: 'POST' }); state.me = null; go('#/entrar'); };
  $('#del-acc').onclick = async () => {
    if (await ask('Isso apaga TODOS os seus dados. Digite EXCLUIR para confirmar.', { input: true, okLabel: 'Excluir conta', danger: true }) !== 'EXCLUIR') return;
    await api('/api/me', { method: 'DELETE' });
    state.me = null;
    location.hash = '#/entrar';
  };
};

function setTheme(v) {
  if (v) document.documentElement.dataset.theme = v; else delete document.documentElement.dataset.theme;
  try { if (v) localStorage.setItem('theme', v); else localStorage.removeItem('theme'); } catch { /* ignore */ }
}
try { const t = localStorage.getItem('theme'); if (t) document.documentElement.dataset.theme = t; } catch { /* ignore */ }

if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
route();
