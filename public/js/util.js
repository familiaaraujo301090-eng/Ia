export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

export function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

export async function api(path, { method = 'GET', body } = {}) {
  let res;
  try {
    res = await fetch(path, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : {},
      body: body ? JSON.stringify(body) : undefined,
      credentials: 'same-origin',
    });
  } catch {
    throw new Error(navigator.onLine === false ? 'Você está sem internet. Tente de novo quando a conexão voltar.' : 'Não consegui falar com o servidor. Tente de novo.');
  }
  let data = null;
  try { data = await res.json(); } catch { /* empty */ }
  if (res.status === 401 && !path.startsWith('/api/auth') && path !== '/api/me') {
    location.hash = '#/entrar';
  }
  if (!res.ok) throw new Error(data?.error || `Erro ${res.status}`);
  return data;
}

let toastTimer;
/** Mensagem rápida no rodapé. Com `action`, mostra um botão (ex: Desfazer) por alguns segundos. */
export function toast(msg, action) {
  const el = $('#toast');
  el.textContent = msg;
  if (action) {
    const b = document.createElement('button');
    b.className = 'toast-btn';
    b.textContent = action.label;
    b.onclick = () => { el.classList.remove('show'); action.run(); };
    el.append(b);
  }
  el.classList.toggle('has-action', !!action);
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), action ? 5000 : 2600);
}

/** Chuva de confete curta (respeita "reduzir movimento"). */
export function confetti() {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const c = document.createElement('canvas');
  c.className = 'confetti';
  document.body.append(c);
  const ctx = c.getContext('2d');
  const W = (c.width = innerWidth);
  const H = (c.height = innerHeight);
  const colors = ['#ff6a3d', '#ffb703', '#1f9d63', '#3a86ff', '#e85d75'];
  const bits = Array.from({ length: 140 }, () => ({
    x: W / 2 + (Math.random() - 0.5) * W * 0.3, y: H * 0.35, vx: (Math.random() - 0.5) * 12, vy: -Math.random() * 14 - 4,
    s: 4 + Math.random() * 6, r: Math.random() * 6, c: colors[Math.floor(Math.random() * colors.length)],
  }));
  let frame = 0;
  (function draw() {
    ctx.clearRect(0, 0, W, H);
    for (const b of bits) {
      b.vy += 0.35; b.x += b.vx; b.y += b.vy; b.r += 0.1;
      ctx.save(); ctx.translate(b.x, b.y); ctx.rotate(b.r); ctx.fillStyle = b.c; ctx.fillRect(-b.s / 2, -b.s / 2, b.s, b.s * 0.6); ctx.restore();
    }
    if (++frame < 110) requestAnimationFrame(draw); else c.remove();
  })();
}

/** Ditado por voz (pt-BR) num campo de texto. Retorna false se o navegador não suporta. */
export function attachMic(field, button) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { button.remove(); return false; }
  let rec = null;
  button.onclick = () => {
    if (rec) { rec.stop(); return; }
    rec = new SR();
    rec.lang = 'pt-BR';
    rec.interimResults = true;
    const base = field.value ? `${field.value.trimEnd()} ` : '';
    rec.onresult = (e) => { field.value = base + [...e.results].map((r) => r[0].transcript).join(''); field.dispatchEvent(new Event('input')); };
    rec.onend = () => { rec = null; button.classList.remove('rec'); field.focus(); };
    rec.onerror = (e) => { if (e.error === 'not-allowed') toast('Permita o microfone para ditar.'); };
    button.classList.add('rec');
    rec.start();
  };
  return true;
}

/** Reduz uma foto para enviar à IA (máx. 1280px, JPEG). */
export function shrinkImage(file, max = 1280) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      const k = Math.min(1, max / Math.max(img.width, img.height));
      const cv = document.createElement('canvas');
      cv.width = Math.round(img.width * k);
      cv.height = Math.round(img.height * k);
      cv.getContext('2d').drawImage(img, 0, 0, cv.width, cv.height);
      URL.revokeObjectURL(img.src);
      const url = cv.toDataURL('image/jpeg', 0.85);
      resolve({ media_type: 'image/jpeg', data: url.split(',')[1], preview: url });
    };
    img.onerror = () => reject(new Error('Não consegui abrir essa imagem.'));
    img.src = URL.createObjectURL(file);
  });
}

/** Minimal, safe markdown (escapes HTML first). */
export function md(src) {
  const lines = esc(src).split('\n');
  const out = [];
  let list = null;
  let inCode = false;
  let code = [];
  const inline = (s) => {
    const codes = [];
    s = s.replace(/`([^`]+)`/g, (_, c) => `\u0000${codes.push(c) - 1}\u0000`);
    return s
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>')
    .replace(/(^|\s)_([^_\n]+)_/g, '$1<em>$2</em>')
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer nofollow">$1</a>')
    .replace(/\u0000(\d+)\u0000/g, (_, i) => `<code>${codes[i]}</code>`);
  };
  const closeList = () => { if (list) { out.push(`</${list}>`); list = null; } };
  for (const raw of lines) {
    if (raw.trim().startsWith('```')) {
      if (inCode) { out.push(`<pre><code>${code.join('\n')}</code></pre>`); code = []; inCode = false; } else { closeList(); inCode = true; }
      continue;
    }
    if (inCode) { code.push(raw); continue; }
    const line = raw.trimEnd();
    let m;
    if ((m = line.match(/^(#{1,3})\s+(.*)$/))) { closeList(); const n = m[1].length + 1; out.push(`<h${n}>${inline(m[2])}</h${n}>`); continue; }
    if ((m = line.match(/^\s*[-*]\s+\[( |x)\]\s+(.*)$/i))) {
      if (list !== 'ul') { closeList(); out.push('<ul style="list-style:none;padding-left:0">'); list = 'ul'; }
      out.push(`<li>${m[1].toLowerCase() === 'x' ? '☑' : '☐'} ${inline(m[2])}</li>`); continue;
    }
    if ((m = line.match(/^\s*[-*•]\s+(.*)$/))) { if (list !== 'ul') { closeList(); out.push('<ul>'); list = 'ul'; } out.push(`<li>${inline(m[1])}</li>`); continue; }
    if ((m = line.match(/^\s*\d+[.)]\s+(.*)$/))) { if (list !== 'ol') { closeList(); out.push('<ol>'); list = 'ol'; } out.push(`<li>${inline(m[1])}</li>`); continue; }
    if ((m = line.match(/^&gt;\s?(.*)$/))) { closeList(); out.push(`<blockquote>${inline(m[1])}</blockquote>`); continue; }
    if (!line.trim()) { closeList(); continue; }
    closeList();
    out.push(`<p>${inline(line)}</p>`);
  }
  if (inCode) out.push(`<pre><code>${code.join('\n')}</code></pre>`);
  closeList();
  return out.join('');
}

export function fmtDate(ymd, opts = { weekday: 'long', day: 'numeric', month: 'long' }) {
  const [y, m, d] = ymd.split('-').map(Number);
  return new Intl.DateTimeFormat('pt-BR', { ...opts, timeZone: 'UTC' }).format(new Date(Date.UTC(y, m - 1, d)));
}

export function addDays(ymd, n) {
  const [y, m, d] = ymd.split('-').map(Number);
  return new Date(Date.UTC(y, m - 1, d + n)).toISOString().slice(0, 10);
}

export async function busy(btn, fn) {
  const label = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<span class="loading"></span> ${btn.dataset.busy || 'Pensando…'}`;
  try { return await fn(); } catch (e) { toast(e.message); return undefined; } finally { btn.disabled = false; btn.innerHTML = label; }
}

export async function copy(text) {
  try { await navigator.clipboard.writeText(text); toast('Copiado!'); } catch { toast('Não foi possível copiar.'); }
}

const P = {
  home: '<path d="M3 11l9-8 9 8v9a2 2 0 0 1-2 2h-4v-7H9v7H5a2 2 0 0 1-2-2z"/>',
  cal: '<rect x="3" y="4" width="18" height="18" rx="3"/><path d="M16 2v4M8 2v4M3 10h18"/>',
  target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>',
  chat: '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 21l1.9-5.4A8 8 0 1 1 21 12z"/>',
  pen: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
  bulb: '<path d="M9 18h6M10 22h4"/><path d="M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.3h6c0-1 .4-1.8 1-2.3A7 7 0 0 0 12 2z"/>',
  quote: '<path d="M4 6h16M4 12h10M4 18h7"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  spark: '<path d="M12 3l1.8 5.4L19 10l-5.2 1.6L12 17l-1.8-5.4L5 10l5.2-1.6z"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
  trash: '<path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"/>',
  check: '<path d="M5 12l5 5L20 7"/>',
  rocket: '<path d="M5 15c-1.5 1.5-2 5-2 5s3.5-.5 5-2"/><path d="M9 15l-3-3a12 12 0 0 1 12-9 12 12 0 0 1-9 12z"/>',
};
export const icon = (name) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${P[name] || ''}</svg>`;

/** In-page confirm/prompt. `input`: false | true (text) | an input type. Resolves true/false, or the typed value/null. */
export function ask(message, { input = false, value = '', placeholder = '', okLabel = 'Confirmar', danger = false } = {}) {
  return new Promise((resolve) => {
    const d = document.createElement('dialog');
    const type = input === true ? 'text' : input;
    d.innerHTML = `<form method="dialog" class="stack">
      <p style="margin:0;white-space:pre-line;font-weight:600">${esc(message)}</p>
      ${input ? `<input type="${esc(type)}" id="ask-input" value="${esc(value)}" placeholder="${esc(placeholder)}" aria-label="Resposta">` : ''}
      <div class="row" style="justify-content:flex-end">
        <button class="btn ${danger ? 'danger' : 'primary'}" value="ok">${esc(okLabel)}</button>
        <button class="btn" type="button" data-cancel style="order:-1">Cancelar</button>
      </div></form>`;
    document.body.append(d);
    d.querySelector('[data-cancel]').onclick = () => d.close('cancel');
    d.addEventListener('close', () => {
      const ok = d.returnValue === 'ok';
      const v = input ? d.querySelector('input').value.trim() : true;
      d.remove();
      resolve(ok ? v : input ? null : false);
    });
    d.showModal();
    d.querySelector(input ? 'input' : 'button[value=ok]').focus();
  });
}

// Qualquer erro não tratado vira um aviso amigável, em vez de falhar em silêncio.
window.addEventListener('unhandledrejection', (e) => {
  const msg = e.reason?.message;
  toast(msg && !/^[A-Z][a-z]+Error\b/.test(msg) ? msg : 'Algo deu errado. Tente de novo.');
});
window.addEventListener('offline', () => toast('Você está sem internet. Suas ações vão falhar até a conexão voltar.'));
window.addEventListener('online', () => toast('Conexão de volta! ✅'));
