// As oito pranchas. Coordenadas da prancha: 940 × 1300. Tons: 0 = madeira, 1 = luz.
'use strict';

const grey = (v) => { const c = Math.round(clamp(v) * 255); return `rgb(${c},${c},${c})`; };
const G = {
  rect(g, v, x, y, w, h) { g.fillStyle = grey(v); g.fillRect(x, y, w, h); },
  poly(g, v, pts) { g.fillStyle = grey(v); g.beginPath(); g.moveTo(pts[0][0], pts[0][1]); for (const p of pts) g.lineTo(p[0], p[1]); g.closePath(); g.fill(); },
  ell(g, v, x, y, rx, ry, rot = 0) { g.fillStyle = grey(v); g.beginPath(); g.ellipse(x, y, rx, ry, rot, 0, Math.PI * 2); g.fill(); },
  glow(g, x, y, r, v, mode = 'lighter') { const gr = g.createRadialGradient(x, y, 0, x, y, r);
    gr.addColorStop(0, grey(v)); gr.addColorStop(1, 'rgb(0,0,0)');
    g.save(); g.globalCompositeOperation = mode; g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2); g.restore(); },
  vgrad(g, x, y, w, h, v0, v1) { const gr = g.createLinearGradient(0, y, 0, y + h); gr.addColorStop(0, grey(v0)); gr.addColorStop(1, grey(v1)); g.fillStyle = gr; g.fillRect(x, y, w, h); },
  hgrad(g, x, y, w, h, v0, v1) { const gr = g.createLinearGradient(x, 0, x + w, 0); gr.addColorStop(0, grey(v0)); gr.addColorStop(1, grey(v1)); g.fillStyle = gr; g.fillRect(x, y, w, h); },
  arch(g, v, x, y, w, h) { g.fillStyle = grey(v); g.beginPath(); g.moveTo(x, y + h); g.lineTo(x, y + w / 2);
    g.arc(x + w / 2, y + w / 2, w / 2, Math.PI, 0); g.lineTo(x + w, y + h); g.closePath(); g.fill(); },
  line(g, v, x0, y0, x1, y1, w) { g.strokeStyle = grey(v); g.lineWidth = w; g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke(); },
};
const inPoly = (x, y, P) => { let c = false; for (let i = 0, j = P.length - 1; i < P.length; j = i++) {
  const [xi, yi] = P[i], [xj, yj] = P[j];
  if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) c = !c; } return c; };
const radialKey = (cx, cy, R) => (st) => clamp(Math.hypot(st.x - cx, st.y - cy) / R);
const lightKey = (st) => clamp(1 - st.T) * 0.8 + (st.y / PH) * 0.2;
const tangentAround = (cx, cy, ex = 1) => (x, y) => Math.atan2((y - cy) / ex, (x - cx)) + Math.PI / 2;
const radialFrom = (cx, cy) => (x, y) => Math.atan2(y - cy, x - cx);
const N = (a, b) => { const m = Math.hypot(a, b); return [a / m, b / m]; };

// pequenas animações de figura
const walk = (ph, amp = 26) => { const s = Math.sin(ph); return { thL: 180 + s * amp, snL: 180 + s * amp - Math.max(0, -s) * 30,
  thR: 180 - s * amp, snR: 180 - s * amp - Math.max(0, s) * 30, uaL: 180 - s * amp * 0.8, uaR: 180 + s * amp * 0.8 }; };
const onTwos = (t) => Math.floor(t * 12) / 12;

// ---------- 1 · hora prima: o despertar ----------
const BEAM1 = [[612, 250], [768, 430], [600, 1250], [150, 1235]];
const P1 = {
  label: 'HORA PRIMA · 6 h', s: 7.5, carve: [0.15, 3.0],
  paint(g) {
    G.glow(g, 690, 330, 620, 0.22);
    G.rect(g, 0.07, 0, 1085, PW, 215);
    g.save(); g.globalCompositeOperation = 'lighter';
    const gr = g.createLinearGradient(690, 330, 370, 1240); gr.addColorStop(0, grey(0.62)); gr.addColorStop(1, grey(0.34));
    g.fillStyle = gr; g.beginPath(); BEAM1.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.closePath(); g.fill();
    g.restore();
    G.glow(g, 380, 1215, 300, 0.42);
    G.arch(g, 1.0, 610, 120, 160, 310);
    G.rect(g, 0.03, 685, 120, 10, 312); G.rect(g, 0.03, 610, 300, 160, 9);
    G.rect(g, 0.0, 595, 430, 190, 14);
    G.rect(g, 0.0, 150, 1168, 430, 34); G.rect(g, 0.85, 150, 1166, 430, 3);
  },
  dir: (x, y) => inPoly(x, y, BEAM1) && y > 440 ? Math.atan2(1240 - 330, 370 - 690) : null,
  key: radialKey(690, 300, 1250),
  light: N(0.45, -0.9),
  cam(t) { const u = easeInOut((t - 0.2) / 3.4); return { s: lerp(1.22, 1.0, u), cx: lerp(690, 470, u), cy: lerp(420, 650, u) }; },
  figures(t) {
    const u = ease((onTwos(t) - 2.5) / 1.1);
    return [{ x: 330, y: 1166, scale: 2.05, k: 1, torso: lerp(-92, 6, u), headTilt: lerp(0, 22, u),
      thL: 92, snL: 96, thR: 96, snR: 100, uaL: lerp(-80, 210, u), laL: lerp(-80, 190, u), uaR: lerp(-95, 150, u), laR: lerp(-95, 140, u),
      skirtLen: 26, face: 1, faceWhite: true, prog: clamp((t - 1.4) / 1.4) }];
  },
  flecks: { n: 70, seed: 5, region: BEAM1, r: [1.2, 3.2], drift: [6, 14] },
};

// ---------- 2 · hora tertia: o fórum ----------
const P2 = {
  label: 'HORA TERTIA · 9 h', s: 7, carve: [0.05, 1.7],
  paint(g) {
    G.vgrad(g, 0, 0, PW, 560, 0.55, 0.88);
    G.glow(g, 140, 120, 420, 0.45);
    G.vgrad(g, 0, 640, PW, 660, 0.48, 0.74);
    // pórticos laterais
    for (const side of [0, 1]) { const x0 = side ? 760 : 0;
      G.rect(g, 0.0, x0, 330, 180, 330);
      for (let i = 0; i < 3; i++) G.arch(g, side ? 0.3 : 0.62, x0 + 18 + i * 56, 410, 40, 210); }
    // templo
    G.poly(g, 0.0, [[250, 262], [690, 262], [470, 160]]);
    G.poly(g, 0.55, [[300, 252], [640, 252], [470, 186]]);
    G.rect(g, 0.0, 250, 260, 440, 38);
    G.rect(g, 0.0, 268, 298, 404, 330);
    for (let i = 0; i < 7; i++) { const x = 284 + i * 56; G.hgrad(g, x, 300, 30, 322, 0.7, 0.12); }
    for (let k = 0; k < 4; k++) { G.rect(g, 0.0, 236 - k * 14, 628 + k * 12, 468 + k * 28, 12); G.rect(g, 0.62, 236 - k * 14, 628 + k * 12, 468 + k * 28, 2.5); }
  },
  dir(x, y) {
    if (y > 690) return Math.atan2(y - 600, x - 470);
    if (y < 250) return -0.04;
    if (x > 268 && x < 672 && y > 298 && y < 628) return Math.PI / 2;
    return null;
  },
  key: lightKey, light: N(-0.85, -0.5),
  cam(t) { const u = easeInOut(t / 6.4); return { s: 1.12, cx: lerp(400, 545, u), cy: 690 }; },
  figures(t) {
    const out = [], r = RNG(42), tt = onTwos(t);
    for (let i = 0; i < 15; i++) {
      const y = 760 + r() * 470, sc = 0.55 + (y - 700) / 600 * 1.25, dirn = r() < .5 ? -1 : 1, sp = (25 + r() * 35) * sc;
      let x = ((r() * 1400 + dirn * sp * tt) % 1400 + 1400) % 1400 - 230;
      out.push(Object.assign({ x, y, scale: sc, flip: dirn < 0, torso: 6 * dirn, prog: clamp((t - 0.6 - r() * .6) / .6), halo: 4 }, walk(tt * 7 + i)));
    }
    out.sort((a, b) => a.y - b.y);
    // você, correndo no meio
    out.push(Object.assign({ x: 520 + 40 * tt, y: 1235, scale: 2.0, torso: 16, faceWhite: true, prog: clamp((t - .5) / .8) }, walk(tt * 11, 40)));
    return out;
  },
};

// ---------- 3 · hora sexta: o Coliseu ----------
const P3 = {
  label: 'HORA SEXTA · 12 h', s: 6.5, carve: [0.05, 1.6],
  paint(g) {
    G.vgrad(g, 0, 0, PW, 320, 0.95, 0.72);
    G.glow(g, 470, 30, 380, 0.5);
    G.ell(g, 0.0, 470, 720, 650, 540);
    // anel superior com arcos abertos para o céu
    for (let i = 0; i < 34; i++) { const a = Math.PI * 1.02 + i / 33 * Math.PI * 0.96, x = 470 + Math.cos(a) * 600, y = 720 + Math.sin(a) * 495;
      G.arch(g, 0.95, x - 12, y - 10, 24, 34); }
    // fileiras da arquibancada
    g.lineWidth = 5;
    for (let k = 0; k < 10; k++) { const u = k / 9, rx = lerp(560, 330, u), ry = lerp(440, 165, u), cy = lerp(730, 830, u);
      g.strokeStyle = grey(0.42 - u * 0.12); g.beginPath(); g.ellipse(470, cy, rx, ry, 0, Math.PI * 0.98, Math.PI * 2.02); g.stroke(); }
    G.ell(g, 0.0, 470, 842, 322, 148);
    G.ell(g, 0.88, 470, 845, 305, 134);
    G.ell(g, 0.45, 420, 820, 215, 92);
    G.ell(g, 0.88, 500, 852, 240, 104);
    G.rect(g, 0.0, 0, 1180, PW, 120);
  },
  dir(x, y) { if (y < 250) return radialFrom(470, 30)(x, y); return tangentAround(470, 800, 0.62)(x, y); },
  key: radialKey(470, 40, 1350), light: N(-0.3, -0.95),
  hit: 0, // preenchido pela linha do tempo: segundo em que o zoom brusco acontece
  cam(t) { const z = clamp((t - this.hit) / 0.2); const u = ease(z);
    return { s: lerp(1.0, 1.55, u) + 0.02 * Math.sin(t * 40) * (1 - clamp((t - this.hit - 0.2) / 0.4)) * z, cx: 470, cy: lerp(650, 760, u) }; },
  figures(t) {
    const tt = onTwos(t), out = [];
    const f1 = Math.sin(tt * 18), f2 = Math.sin(tt * 18 + 2);
    out.push(Object.assign({ x: 440 + 8 * f1, y: 845, scale: 0.42, torso: 10 * f1, uaR: 70 + 30 * f1, laR: 60, prog: 1, halo: 3 }, walk(tt * 6, 14)));
    out.push(Object.assign({ x: 505 - 8 * f2, y: 848, scale: 0.42, flip: true, torso: 10 * f2, uaR: 70 + 30 * f2, laR: 60, prog: 1, halo: 3 }, walk(tt * 6 + 1, 14)));
    const pump = t > this.hit - 0.15 ? Math.abs(Math.sin((tt - this.hit) * 7)) : 0.15;
    out.push({ x: 470, y: 1400, scale: 3.3, torso: -4 + 4 * pump, headTilt: -6, uaR: lerp(170, 12, pump), laR: lerp(170, 0, pump),
      uaL: 205, laL: 190, skirt: false, prog: clamp((t - .3) / .7), halo: 6 });
    return out;
  },
  crowd: { n: 1700, seed: 9 },
};

// ---------- 4 · hora nona: o senador ----------
const P4 = {
  label: 'HORA NONA · 15 h', s: 8, carve: [0.05, 1.7],
  paint(g) {
    for (let y = 0; y < PH; y += 64) for (let x = (y / 64 % 2) * 60; x < PW; x += 120) { G.rect(g, 0.13, x + 3, y + 3, 114, 58); G.glow(g, x + 30, y + 15, 40, 0.06); }
    G.arch(g, 0.0, 170, 180, 600, 1120);
    G.arch(g, 0.62, 190, 200, 560, 1100);
    G.hgrad(g, 190, 470, 560, 830, 0.22, 0.72);
    G.vgrad(g, 190, 1060, 560, 240, 0.4, 0.66);
    G.arch(g, 0.95, 640, 520, 80, 220); G.rect(g, 0.05, 676, 520, 8, 220);
    G.glow(g, 680, 620, 320, 0.25);
    for (const x of [120, 750]) { G.rect(g, 0.0, x, 180, 70, 1120); G.hgrad(g, x + 4, 180, 20, 1120, 0.5, 0.05); }
  },
  dir(x, y) { if (x < 190 || x > 750 || y < 200) return 0; if (y > 1060) return 0.02; return null; },
  key: lightKey, light: N(0.9, -0.42),
  cam(t) { const u = easeInOut(t / 5.4); return { s: lerp(1.0, 1.32, u), cx: lerp(470, 500, u), cy: lerp(700, 900, u) }; },
  figures(t) {
    const tt = onTwos(t), off = ease((tt - 0.9) / 0.8), hes = ease((tt - 3.2) / 1.2);
    const folds = [[-14, -60, 4, -30, -18, 10], [6, -64, 16, -20, 2, 20], [-20, 10, -4, 30, -24, 40]];
    return [
      { x: 360, y: 1200, scale: 3.4, k: 1, torso: 4, headTilt: 6, uaR: lerp(175, 100, off), laR: lerp(175, 92, off), uaL: 190, laL: 200,
        beard: true, faceWhite: true, folds, prog: clamp((t - .5) / 1.0) },
      { x: 625, y: 1205, scale: 3.1, k: 1, flip: true, torso: lerp(0, -9, hes), headTilt: lerp(0, 18, hes), uaR: 188, laR: 178, uaL: 172, laL: 160,
        faceWhite: true, prog: clamp((t - .7) / 1.0) }];
  },
  pouch: true,
};

// ---------- 5 · hora duodécima: o sol cai ----------
const P5 = {
  label: 'HORA DUODECIMA · 18 h', s: 7.5, carve: [0.05, 2.0],
  paint(g) {
    G.glow(g, 470, 700, 1000, 0.58);
    G.glow(g, 470, 700, 330, 0.3);
    G.ell(g, 1.0, 470, 700, 118, 118);
    G.vgrad(g, 0, 760, PW, 300, 0.28, 0.16);
    g.save(); g.globalCompositeOperation = 'lighter'; G.hgrad(g, 400, 770, 70, 290, 0.0, 0.55); G.hgrad(g, 470, 770, 70, 290, 0.55, 0.0); g.restore();
    // horizonte de Roma
    G.rect(g, 0.0, 0, 742, PW, 26);
    G.poly(g, 0.0, [[150, 742], [150, 690], [210, 690], [210, 742]]);
    g.fillStyle = grey(0); g.beginPath(); g.arc(300, 700, 82, Math.PI, 0); g.fill(); G.rect(g, 0.0, 214, 696, 172, 50);
    G.rect(g, 0.0, 296, 612, 8, 12);
    for (let i = 0; i < 9; i++) { G.rect(g, 0.0, 560 + i * 44, 668, 44, 76); G.arch(g, 0.72, 568 + i * 44, 694, 28, 48); }
    G.rect(g, 0.0, 556, 660, 390, 12);
    for (const [x, h] of [[60, 140], [95, 110], [420, 90], [880, 130], [905, 100]]) G.ell(g, 0.0, x, 742 - h / 2, 14, h / 2);
    for (let i = 0; i < 6; i++) G.rect(g, 0.0, 30 + i * 18, 700, 8, 44);
    // colina em primeiro plano
    g.fillStyle = grey(0); g.beginPath(); g.moveTo(0, 1300); g.lineTo(0, 1110); g.quadraticCurveTo(420, 1010, 940, 1080); g.lineTo(940, 1300); g.fill();
    g.strokeStyle = grey(0.8); g.lineWidth = 3; g.beginPath(); g.moveTo(0, 1110); g.quadraticCurveTo(420, 1010, 940, 1080); g.stroke();
  },
  dir(x, y) { if (y < 742) return tangentAround(470, 700)(x, y); if (y < 1060) return 0; return null; },
  key: radialKey(470, 700, 900), light: N(-0.6, -0.8),
  cam(t) { const u = easeInOut(t / 4.6); return { s: lerp(1.22, 1.08, u), cx: lerp(470, 560, u), cy: lerp(560, 860, u) }; },
  figures(t) { return [{ x: 650, y: 1046, scale: 1.15, flip: true, torso: -8, headTilt: -6, thL: 120, snL: 175, thR: 115, snR: 170,
    uaL: 150, laL: 120, uaR: 160, laR: 120, skirtLen: 24, prog: clamp((t - 1.0) / 1.0), halo: 4 }]; },
};

// ---------- 6 · secunda vigilia: o imperador escreve ----------
const FL6 = [690, 846];
const PROFILE = [[296, 428], [352, 438], [384, 470], [393, 520], [399, 540], [426, 586], [403, 600], [407, 612], [400, 626], [405, 637],
  [396, 652], [414, 702], [372, 764], [300, 766], [262, 700], [248, 610], [252, 512], [272, 455]];
const P6 = {
  label: 'SECUNDA VIGILIA · 21 h', s: 7.5, carve: [0.35, 2.7],
  paint(g) {
    const a = document.createElement('canvas'); a.width = g.canvas.width; a.height = g.canvas.height;
    const A = a.getContext('2d'); A.scale(TS, TS);
    G.rect(A, 0.34, 0, 0, PW, PH);
    G.rect(A, 0.62, 0, 905, PW, 395); G.rect(A, 0.95, 0, 903, PW, 4);
    // manto e ombros
    G.poly(A, 0.5, [[300, 760], [384, 760], [470, 840], [520, 905], [150, 905], [190, 830]]);
    // braço até o pergaminho
    A.strokeStyle = grey(0.5); A.lineWidth = 58; A.lineCap = 'round'; A.beginPath(); A.moveTo(420, 835); A.lineTo(560, 940); A.stroke();
    G.ell(A, 0.9, 575, 950, 30, 20, 0.4);
    G.line(A, 0.15, 585, 952, 640, 900, 5);
    // pergaminho e lamparina
    G.poly(A, 1.0, [[300, 925], [770, 915], [790, 1005], [280, 1015]]);
    G.ell(A, 0.18, 620, 885, 72, 26); G.ell(A, 0.18, 690, 872, 26, 12); G.ell(A, 0.7, 610, 868, 34, 7);
    // cabeça de perfil
    G.poly(A, 0.27, PROFILE);
    G.poly(A, 1.0, [[352, 446], [384, 472], [393, 520], [399, 540], [426, 586], [403, 600], [407, 612], [398, 628], [362, 640], [330, 600], [326, 500]]);
    G.poly(A, 0.22, [[398, 640], [414, 702], [372, 764], [318, 748], [330, 640], [362, 640]]);
    G.ell(A, 0.05, 376, 540, 10, 5, -0.2); G.line(A, 0.05, 360, 522, 392, 516, 4); G.ell(A, 0.3, 318, 585, 13, 20);
    const L = document.createElement('canvas'); L.width = a.width; L.height = a.height;
    const C = L.getContext('2d'); C.scale(TS, TS); C.fillStyle = '#000'; C.fillRect(0, 0, PW, PH);
    const gr = C.createRadialGradient(FL6[0], FL6[1], 0, FL6[0], FL6[1], 820);
    [[0, 1], [0.2, 0.96], [0.42, 0.82], [0.65, 0.45], [1, 0.08]].forEach(([o, v]) => gr.addColorStop(o, grey(v)));
    C.fillStyle = gr; C.fillRect(0, 0, PW, PH);
    g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.drawImage(a, 0, 0); g.globalCompositeOperation = 'multiply'; g.drawImage(L, 0, 0); g.restore();
    G.ell(g, 1.0, FL6[0], FL6[1] - 10, 12, 28);
  },
  dir(x, y) { if (y > 1020) return 0.0; return null; },
  key: radialKey(FL6[0], FL6[1], 900), light: N(1, -0.2),
  flame: { x: FL6[0], y: FL6[1], h: 64, w: 22, on: 0.25 },
  colour(st, t) { const d = Math.hypot(st.x - FL6[0], st.y - FL6[1]); return Math.pow(clamp(1 - d / 190), 1.4) * clamp((t - 0.3) / 0.6); },
  cam(t) { const u = easeInOut(t / 8.8); return { s: lerp(1.0, 1.3, u), cx: lerp(470, 500, u), cy: lerp(700, 690, u) }; },
};

// ---------- 7 · a frase ----------
const FL7 = [770, 250];
const P7 = {
  label: 'SECUNDA VIGILIA · 21 h', s: 8.5, carve: [0.0, 1.4],
  paint(g) {
    const a = document.createElement('canvas'); a.width = g.canvas.width; a.height = g.canvas.height;
    const A = a.getContext('2d'); A.scale(TS, TS);
    G.rect(A, 0.3, 0, 0, PW, PH);
    G.poly(A, 1.0, [[90, 560], [870, 520], [900, 1240], [60, 1270]]);
    G.poly(A, 0.55, [[90, 560], [870, 520], [872, 556], [92, 598]]);
    G.ell(A, 0.2, 760, 345, 150, 50); G.ell(A, 0.2, 890, 330, 70, 26); G.ell(A, 0.75, 735, 312, 70, 12);
    const L = document.createElement('canvas'); L.width = a.width; L.height = a.height;
    const C = L.getContext('2d'); C.scale(TS, TS); C.fillStyle = '#000'; C.fillRect(0, 0, PW, PH);
    const gr = C.createRadialGradient(FL7[0], FL7[1], 0, FL7[0], FL7[1], 1300);
    [[0, 1], [0.2, 0.9], [0.5, 0.62], [1, 0.25]].forEach(([o, v]) => gr.addColorStop(o, grey(v)));
    C.fillStyle = gr; C.fillRect(0, 0, PW, PH);
    g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.drawImage(a, 0, 0); g.globalCompositeOperation = 'multiply'; g.drawImage(L, 0, 0); g.restore();
    G.ell(g, 1.0, FL7[0], FL7[1] - 22, 26, 60);
  },
  dir(x, y) { if (y > 600 && y < 1240 && x > 80 && x < 890) return -0.045; return null; },
  key: radialKey(FL7[0], FL7[1], 1300), light: N(0.7, -0.7),
  flame: { x: FL7[0], y: FL7[1], h: 130, w: 46, on: -1 },
  colour(st, t) { const R = lerp(200, 760, ease(t / 4.5)) * (1 - 0.35 * ease((t - 5.2) / 1.2));
    const d = Math.hypot(st.x - FL7[0], st.y - FL7[1]); return Math.pow(clamp(1 - d / R), 1.1) * 0.85; },
  writing: { x0: 150, y0: 660, rows: 7, dy: 82, x1: 800, t0: 0.4, t1: 5.6, seed: 3 },
  cam(t) { const p = this.tip(t); return { s: 1.32, cx: lerp(470, p[0], 0.55), cy: lerp(700, p[1], 0.6) }; },
  tip(t) { const w = this.writing, u = clamp((t - w.t0) / (w.t1 - w.t0)) * w.rows, row = Math.min(w.rows - 1, Math.floor(u)), f = u - row;
    return [lerp(w.x0, w.x1, f) - row * 6, w.y0 + row * w.dy + (w.x1 - w.x0) * f * -0.045]; },
};

// ---------- 8 · media nox: o eco ----------
const P8 = {
  label: 'MEDIA NOX · 24 h', s: 7.5, carve: [0.1, 2.0],
  lamp: [0, 0],
  paint(g) {
    const f = this.figures(9)[0], fp = figureParts(f);
    const w = fp.parts.find((p) => p.kind === 'arm' && p.side === 1).wrist;
    const lx = f.x + w[0] * f.scale, ly = f.y + w[1] * f.scale - 26; this.lamp = [lx, ly];
    G.glow(g, lx, ly, 760, 0.55);
    G.glow(g, lx, ly, 260, 0.3);
    G.rect(g, 0.0, 0, 1085, PW, 6);
    G.arch(g, 0.0, 600, 110, 180, 330);
    G.arch(g, 0.2, 610, 120, 160, 310);
    G.ell(g, 1.0, 712, 210, 26, 26); G.ell(g, 0.2, 724, 202, 22, 22);
    G.rect(g, 0.0, 685, 120, 10, 312); G.rect(g, 0.0, 610, 300, 160, 9);
    G.rect(g, 0.0, 150, 1168, 430, 34); G.rect(g, 0.6, 150, 1166, 430, 3);
  },
  key(st) { return radialKey(this.lamp[0], this.lamp[1], 1100)(st); },
  light: N(0.6, -0.8),
  colour(st, t) { const d = Math.hypot(st.x - this.lamp[0], st.y - this.lamp[1]); return Math.pow(clamp(1 - d / 70), 1.5) * 0.8; },
  cam(t) { const u = easeInOut((t - 0.3) / 4.5); return { s: lerp(1.3, 1.0, u), cx: lerp(470, 470, u), cy: lerp(820, 650, u) }; },
  figures(t) {
    const tt = onTwos(t), u = ease((tt - 0.2) / 1.6);
    return [{ x: 400, y: 1078, scale: 2.35, torso: 2, headTilt: lerp(10, -4, u), uaR: lerp(150, 62, u), laR: lerp(140, 42, u),
      uaL: 192, laL: 182, faceWhite: true, prog: clamp((t - 0.4) / 1.0) }];
  },
  flame: { hand: true, h: 40, w: 14, on: -1 },
  stars: { n: 28, seed: 31, box: [615, 130, 150, 290] },
};

const PLATES = [P1, P2, P3, P4, P5, P6, P7, P8];
