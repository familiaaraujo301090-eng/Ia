'use strict';
// Linha do tempo, composição da impressão, legendas na margem e eventos de som.
const W = 1080, H = 1920, SCL = 0.9, PX = Math.round((1080 - 940 * 0.9) / 2), PY = 112;
const TL = window.TIMELINE;           // gerado por timeline.py a partir da narração
const FPS = 24;
const PEEL = new Set([1, 5, 7]), PEEL_DUR = 0.95;
const starts = TL.plates.map((p) => p.t);
window.DUR = TL.dur;
PLATES[2].hit = TL.hit3;

const cv = document.getElementById('c'), ctx = cv.getContext('2d');
const mk = (w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; };
const cutC = mk(PW, PH), colC = mk(PW, PH), inkC = mk(PW, PH), plateC = mk(PW, PH), prevC = mk(PW, PH);
const cut = cutC.getContext('2d'), col = colC.getContext('2d'), ink = inkC.getContext('2d'), pc = plateC.getContext('2d');
let PAPER, INK, SPECK, EDGE, PAPERPLATE;

function prepare(i) {
  const P = PLATES[i];
  if (P._strokes) return;
  const tone = buildTone((g) => P.paint(g));
  const st = carveStrokes(tone, { s: P.s, dir: P.dir ? (x, y) => P.dir(x, y) : null }, 1000 + i * 77);
  const [c0, c1] = P.carve, span = c1 - c0;
  for (const s of st) {
    s.t0 = c0 + clamp(P.key.call(P, s)) * span * 0.86 + s.r * span * 0.14;
    s.dur = 0.08 + 0.27 * ((s.r * 7.13) % 1);
    s.path = strokePath(s, 1);
  }
  st.sort((a, b) => a.t0 - b.t0);
  P._strokes = st;
  P._tone = tone;
  // poeira, multidão, estrelas: posições fixas por prancha
  if (P.flecks) { const r = RNG(P.flecks.seed), F = []; const reg = P.flecks.region;
    while (F.length < P.flecks.n) { const x = r() * PW, y = r() * PH; if (inPoly(x, y, reg) && y > 450) F.push([x, y, lerp(P.flecks.r[0], P.flecks.r[1], r()), r() * 6.28, lerp(P.flecks.drift[0], P.flecks.drift[1], r())]); }
    P._flecks = F; }
  if (P.crowd) { const r = RNG(P.crowd.seed), F = [];
    while (F.length < P.crowd.n) { const x = 470 + (r() - .5) * 1240, y = 700 + (r() - .5) * 980;
      const e = ((x - 470) / 600) ** 2 + ((y - 720) / 480) ** 2, ea = ((x - 470) / 312) ** 2 + ((y - 840) / 142) ** 2;
      if (e < 1 && ea > 1 && y > 250) F.push([x, y, 1.3 + r() * 2.2 * (y / 900), r() * 6.28]); }
    P._crowd = F; }
  if (P.stars) { const r = RNG(P.stars.seed), [x0, y0, w, h] = P.stars.box, F = [];
    for (let k = 0; k < P.stars.n; k++) F.push([x0 + r() * w, y0 + r() * h, 0.8 + r() * 2, r() * 6.28]); P._stars = F; }
}

function camera(P, t) {
  const c = P.cam.call(P, t), s = Math.max(1, c.s);
  const hw = PW / (2 * s), hh = PH / (2 * s);
  const cx = clamp(c.cx, hw, PW - hw), cy = clamp(c.cy, hh, PH - hh);
  return [s, 0, 0, s, PW / 2 - s * cx, PH / 2 - s * cy];
}

function stab(g, x, y, r, a) { g.beginPath(); for (let k = 0; k < 5; k++) { const aa = a + k * 1.26, rr = r * (0.7 + 0.3 * Math.sin(a * 3 + k));
  k ? g.lineTo(x + Math.cos(aa) * rr, y + Math.sin(aa) * rr) : g.moveTo(x + Math.cos(aa) * rr, y + Math.sin(aa) * rr); } g.closePath(); g.fill(); }

function flame(g, x, y, h, w, t, seed) { // chama redesenhada a cada 2 quadros (fervura deliberada)
  const r = RNG(seed + Math.floor(t * 12)), sway = Math.sin(t * 5.3) * w * 0.25;
  const P = new Path2D(); P.moveTo(x - w, y);
  P.bezierCurveTo(x - w * 1.1, y - h * 0.45, x - w * 0.3 + sway, y - h * 0.7, x + sway * 1.6 + (r() - .5) * 4, y - h * (1 + r() * 0.12));
  P.bezierCurveTo(x + w * 0.4 + sway, y - h * 0.65, x + w * 1.1, y - h * 0.4, x + w, y);
  P.quadraticCurveTo(x, y + w * 0.6, x - w, y); P.closePath();
  return P;
}

function writingGlyphs(P) {
  if (P._glyphs) return P._glyphs;
  const w = P.writing, r = RNG(w.seed), out = [];
  for (let row = 0; row < w.rows; row++) {
    const yb = w.y0 + row * w.dy, len = row === w.rows - 1 ? 0.55 : 1;
    let x = w.x0 - row * 6;
    while (x < lerp(w.x0, w.x1, len)) {
      const f = (x - (w.x0 - row * 6)) / (w.x1 - w.x0), g = [];
      const n = 2 + (r() * 3 | 0), cw = 16 + r() * 14;
      for (let k = 0; k < n; k++) g.push([x + r() * cw, yb - 4 - r() * 24 + f * (w.x1 - w.x0) * -0.045, x + r() * cw, yb - r() * 26 + f * (w.x1 - w.x0) * -0.045, x + r() * cw, yb + 2 - r() * 10 + f * (w.x1 - w.x0) * -0.045]);
      out.push({ row, f, g }); x += cw + 6 + (r() < 0.18 ? 18 : 0);
    }
  }
  return (P._glyphs = out);
}

function renderPlate(i, t, target) {
  prepare(i);
  const P = PLATES[i], m = camera(P, t);
  cut.setTransform(1, 0, 0, 1, 0, 0); cut.clearRect(0, 0, PW, PH);
  col.setTransform(1, 0, 0, 1, 0, 0); col.clearRect(0, 0, PW, PH);
  cut.setTransform(...m); col.setTransform(...m);
  cut.fillStyle = '#fff';
  const colourFn = P.colour;
  for (const s of P._strokes) {
    if (t < s.t0) break;
    const f = clamp((t - s.t0) / s.dur);
    const path = f >= 1 ? s.path : strokePath(s, f);
    cut.fill(path);
    if (colourFn) { const c = colourFn.call(P, s, t); if (c > 0.02) { col.globalAlpha = Math.min(1, c); col.fillStyle = '#d4601f'; col.fill(path); } }
  }
  col.globalAlpha = 1;
  // poeira na luz
  if (P._flecks) for (const [x, y, r, a, d] of P._flecks) {
    const key = clamp(P.key.call(P, { x, y }) * 0.86); if (t < P.carve[0] + key * (P.carve[1] - P.carve[0]) + 0.2) continue;
    stab(cut, x + Math.sin(t * 0.7 + a) * 6, y + ((t * d) % 60) - 30, r, a);
  }
  if (P._crowd) for (const [x, y, r, a] of P._crowd) {
    const key = P.key.call(P, { x, y }); if (t < P.carve[0] + key * (P.carve[1] - P.carve[0]) * 0.9) continue;
    const bob = t > P.hit - 0.3 ? Math.abs(Math.sin(onTwos(t) * 9 + a * 3)) * 4 : Math.abs(Math.sin(onTwos(t) * 3 + a * 3)) * 1.5;
    stab(cut, x, y - bob, r, a);
  }
  if (P._stars) for (const [x, y, r, a] of P._stars) { if (t > 0.3 + a / 12) { cut.globalAlpha = 0.6 + 0.4 * Math.sin(t * 3 + a * 5); stab(cut, x, y, r, a); } }
  cut.globalAlpha = 1;
  // figuras
  if (P.figures) for (const f of P.figures.call(P, t)) {
    const fp = drawFigure(cut, f, P.light, f.prog ?? 1);
    if (P.pouch && f.beard) { // a bolsa de moedas na mão do senador
      const w = fp.parts.find((p) => p.kind === 'arm' && p.side === 1).wrist;
      const bx = f.x + w[0] * f.scale + 22, by = f.y + w[1] * f.scale + 8;
      cut.fillStyle = '#fff'; cut.beginPath(); cut.arc(bx, by, 30, 0, Math.PI * 2); cut.fill();
      cut.save(); cut.globalCompositeOperation = 'destination-out'; cut.beginPath(); cut.arc(bx, by, 25, 0, Math.PI * 2); cut.fill(); cut.restore();
      cut.fillStyle = '#fff'; cut.lineWidth = 2; cut.strokeStyle = '#fff';
      for (const a of [-1.9, -1.2, -0.5, 0.2]) { cut.beginPath(); cut.arc(bx + Math.cos(a) * 12, by + Math.sin(a) * 12, 9, a + 1.6, a + 3.6); cut.stroke(); }
      const open = clamp((t - 1.6) / 0.6);
      if (open > 0) for (let k = 0; k < 5; k++) { const ph = (t * 1.3 + k * 0.37) % 1.6;
        const cx = bx + 10 + k * 6, cy = by - 22 - ph * 10; cut.globalAlpha = open * (0.5 + 0.5 * Math.sin(t * 8 + k));
        cut.beginPath(); cut.ellipse(cx, cy, 9, 4, 0.2, 0, Math.PI * 2); cut.fill(); }
      cut.globalAlpha = 1;
    }
    if (P.flame && P.flame.hand) {
      const w = fp.parts.find((p) => p.kind === 'arm' && p.side === 1).wrist;
      const lx = f.x + w[0] * f.scale, ly = f.y + w[1] * f.scale;
      cut.save(); cut.globalCompositeOperation = 'destination-out'; cut.beginPath(); cut.ellipse(lx + 8, ly - 4, 26, 10, 0, 0, Math.PI * 2); cut.fill(); cut.restore();
      cut.strokeStyle = '#fff'; cut.lineWidth = 2.2; cut.beginPath(); cut.ellipse(lx + 8, ly - 4, 28, 12, 0, 0, Math.PI * 2); cut.stroke();
      const F = flame(cut, lx + 26, ly - 10, P.flame.h, P.flame.w, t, 77);
      cut.fill(F); col.fillStyle = '#e06a1c'; col.globalAlpha = 1; col.fill(F);
    }
  }
  if (P.flame && !P.flame.hand && t > P.flame.on) {
    const grow = P.flame.on < 0 ? 1 : ease((t - P.flame.on) / 0.35);
    const F = flame(cut, P.flame.x, P.flame.y, P.flame.h * grow, P.flame.w * (0.6 + 0.4 * grow), t, 51);
    cut.fillStyle = '#fff'; cut.fill(F);
    col.fillStyle = '#e06a1c'; col.globalAlpha = 1; col.fill(F);
    // núcleo escuro da chama (pavio), mantém a forma legível
    cut.save(); cut.globalCompositeOperation = 'destination-out'; cut.beginPath();
    cut.ellipse(P.flame.x, P.flame.y - 6, P.flame.w * 0.25, P.flame.h * 0.18 * grow, 0, 0, Math.PI * 2); cut.fill(); cut.restore();
  }
  if (P.writing) { // a pena escreve: tinta (madeira intacta) sobre o pergaminho entalhado
    const w = P.writing, gl = writingGlyphs(P), u = clamp((t - w.t0) / (w.t1 - w.t0)) * w.rows;
    cut.save(); cut.globalCompositeOperation = 'destination-out'; cut.lineWidth = 3.4; cut.lineCap = 'round';
    for (const g of gl) { if (g.row + g.f > u) continue;
      for (const q of g.g) { cut.beginPath(); cut.moveTo(q[0], q[1]); cut.quadraticCurveTo(q[2], q[3], q[4], q[5]); cut.stroke(); } }
    cut.restore();
    const [tx, ty] = P.tip(t), hand = new Path2D();
    hand.moveTo(tx, ty); hand.lineTo(tx + 120, ty - 150); hand.lineTo(tx + 132, ty - 140); hand.closePath();
    const hp = new Path2D(); hp.ellipse(tx + 150, ty - 150, 62, 40, -0.6, 0, Math.PI * 2);
    hp.moveTo(tx + 170, ty - 150); hp.lineTo(tx + 420, ty - 300); hp.lineTo(tx + 470, ty - 220); hp.lineTo(tx + 190, ty - 110);
    cut.strokeStyle = '#fff'; cut.lineWidth = 9; cut.stroke(hp); cut.lineWidth = 5; cut.stroke(hand);
    cut.save(); cut.globalCompositeOperation = 'destination-out'; cut.fill(hp); cut.fill(hand); cut.restore();
    cut.save(); cut.clip(hp); cut.lineWidth = 2; for (const d of [6, 14, 24]) { cut.save(); cut.translate(d * 0.55, d * 0.8); cut.stroke(hp); cut.restore(); } cut.restore();
  }
  // impressão: papel + tinta com os cortes removidos + placa de cor multiplicada
  ink.setTransform(1, 0, 0, 1, 0, 0); ink.globalCompositeOperation = 'source-over'; ink.clearRect(0, 0, PW, PH);
  ink.drawImage(INK, 0, 0);
  ink.globalCompositeOperation = 'destination-out'; ink.drawImage(cutC, 0, 0); ink.globalAlpha = 0.5; ink.drawImage(SPECK, 0, 0); ink.globalAlpha = 1;
  ink.globalCompositeOperation = 'source-over';
  target.setTransform(1, 0, 0, 1, 0, 0); target.globalCompositeOperation = 'source-over';
  target.drawImage(PAPERPLATE, 0, 0); target.drawImage(inkC, 0, 0);
  target.globalCompositeOperation = 'multiply'; target.drawImage(colC, 0, 0); target.globalCompositeOperation = 'source-over';
}

function plateIndex(t) { let i = 0; while (i + 1 < starts.length && t >= starts[i + 1]) i++; return i; }

function caption(t) {
  const s = TL.sents.find((q) => t >= q.a - 0.05 && t < q.b + 0.45);
  if (!s) return;
  const fade = clamp((t - s.a + 0.05) / 0.1) * (1 - clamp((t - s.b - 0.3) / 0.15));
  ctx.save(); ctx.globalAlpha = fade; ctx.fillStyle = '#1b1612'; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
  // quebra em linhas, com a frase-chave (*...*) em itálico
  const toks = []; s.text.split(/(\*[^*]+\*)/).forEach((part) => { if (!part) return;
    const it = part.startsWith('*'); part.replace(/\*/g, '').split(' ').forEach((w) => w && toks.push({ w, it })); });
  const size = 56, fontN = `${size}px Fell`, fontI = `italic ${size}px FellI`, maxW = 900, lines = [[]];
  let lw = 0;
  for (const tk of toks) { ctx.font = tk.it ? fontI : fontN; const ww = ctx.measureText(tk.w + ' ').width;
    if (lw + ww > maxW && lines[lines.length - 1].length) { lines.push([]); lw = 0; }
    lines[lines.length - 1].push({ ...tk, ww }); lw += ww; }
  const y0 = 1388;
  lines.forEach((ln, k) => { const tot = ln.reduce((a, b) => a + b.ww, 0); let x = W / 2 - tot / 2;
    for (const tk of ln) { ctx.font = tk.it ? fontI : fontN; ctx.textAlign = 'left'; ctx.fillText(tk.w, x, y0 + k * 68); x += tk.ww; } });
  ctx.restore();
}

function margins(i, t) {
  const P = PLATES[i];
  ctx.save(); ctx.fillStyle = '#1b1612'; ctx.textAlign = 'center';
  ctx.font = '44px FellSC'; ctx.globalAlpha = 0.92;
  const lab = P.label.split('').join(String.fromCharCode(8202));
  ctx.fillText(lab, W / 2, 80);
  ctx.font = '30px FellSC'; ctx.globalAlpha = 0.6;
  ctx.textAlign = 'right'; ctx.fillText(['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII'][i], W - PX, 1316);
  ctx.restore();
}

window.render = (t) => {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.drawImage(PAPER, 0, 0);
  const i = plateIndex(t), tl = t - starts[i];
  renderPlate(i, tl, pc);
  let mx = 0, my = 0;
  const fr = Math.round(tl * FPS);
  if (!PEEL.has(i) && i > 0 && fr < 2) { mx = fr ? 2 : 4; my = fr ? -1 : -3; }   // nova impressão: desalinhamento
  ctx.save(); ctx.translate(PX, PY); ctx.scale(SCL, SCL); ctx.clip(EDGE);
  if (PEEL.has(i) && tl < PEEL_DUR) {
    const pi = i - 1; renderPlate(pi, starts[i] - starts[pi] - 0.01, prevC.getContext('2d'));
    ctx.drawImage(plateC, 0, 0);
    const u = tl / PEEL_DUR, e = u < 0.35 ? 0.25 * (u / 0.35) ** 2 : 0.25 + 0.75 * ease((u - 0.35) / 0.65);
    const yl = PH * (1 - e) + 60 * (1 - e), R = 70;
    // a folha ainda presa (parte de cima da prancha anterior)
    ctx.save(); ctx.beginPath(); ctx.rect(0, 0, PW, Math.max(0, yl - R)); ctx.clip(); ctx.drawImage(prevC, 0, 0); ctx.restore();
    // o cilindro: verso da folha com a imagem espelhada transparecendo
    if (yl - R < PH) {
      ctx.save(); ctx.beginPath(); ctx.rect(0, yl - R, PW, R * 1.6); ctx.clip();
      ctx.fillStyle = '#efe6d0'; ctx.fillRect(0, yl - R, PW, R * 1.6);
      ctx.globalAlpha = 0.16; ctx.translate(0, 2 * yl); ctx.scale(1, -1); ctx.drawImage(prevC, 0, 0); ctx.restore();
      const g = ctx.createLinearGradient(0, yl - R, 0, yl + R * 0.6);
      g.addColorStop(0, 'rgba(0,0,0,0.35)'); g.addColorStop(0.35, 'rgba(255,250,235,0.25)'); g.addColorStop(0.7, 'rgba(0,0,0,0.12)'); g.addColorStop(1, 'rgba(0,0,0,0.0)');
      ctx.fillStyle = g; ctx.fillRect(0, yl - R, PW, R * 1.6);
      const sh = ctx.createLinearGradient(0, yl + R * 0.6, 0, yl + R * 1.6); sh.addColorStop(0, 'rgba(0,0,0,0.35)'); sh.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = sh; ctx.fillRect(0, yl + R * 0.6, PW, R);
    }
  } else ctx.drawImage(plateC, mx, my);
  ctx.restore();
  // borda da prancha (rebarba da tinta)
  ctx.save(); ctx.translate(PX, PY); ctx.scale(SCL, SCL); ctx.strokeStyle = 'rgba(22,18,14,0.55)'; ctx.lineWidth = 1.5; ctx.stroke(EDGE); ctx.restore();
  margins(i, t);
  caption(t);
};

// eventos para o som: cortes, entalhes, folha, chama, moedas, multidão
const EV = [];
TL.plates.forEach((p, i) => {
  const P = PLATES[i];
  EV.push({ t: p.t, type: PEEL.has(i) ? 'peel' : (i ? 'impression' : 'first'), i });
  EV.push({ t: p.t + P.carve[0], type: 'carve', i, d: P.carve[1] - P.carve[0] });
});
EV.push({ t: starts[5] + 0.25, type: 'ignite' });
EV.push({ t: starts[3] + 1.6, type: 'coins', d: 2.6 });
EV.push({ t: starts[2] + TL.hit3, type: 'roar' });
EV.push({ t: starts[6] + 0.4, type: 'write', d: 5.2 });
window.EV = EV;

Promise.all([
  new FontFace('Fell', 'url(fonts/IMFeENrm28P.ttf)').load(), new FontFace('FellI', 'url(fonts/IMFeENit28P.ttf)').load(),
  new FontFace('FellSC', 'url(fonts/IMFeENsc28P.ttf)').load(),
]).then((fs) => {
  fs.forEach((f) => document.fonts.add(f));
  PAPER = paperTexture(W, H); INK = inkTexture(PW, PH); SPECK = speckles(PW, PH); EDGE = raggedEdge(0, 0, PW, PH, 23);
  PAPERPLATE = mk(PW, PH); { const g = PAPERPLATE.getContext('2d'); g.scale(1 / SCL, 1 / SCL); g.drawImage(PAPER, -PX, -PY); }
  for (let i = 0; i < PLATES.length; i++) prepare(i);
  window.READY = true;
});
