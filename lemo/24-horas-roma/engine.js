// Motor de xilogravura: pinta uma imagem de tons (0 = madeira intacta, 1 = luz), transforma em cortes
// de faca que seguem a forma, e imprime tinta sobre papel. Tudo determinístico (sementes fixas).
'use strict';

const RNG = (seed) => () => {
  seed |= 0; seed = seed + 0x6D2B79F5 | 0;
  let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
  t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
  return ((t ^ t >>> 14) >>> 0) / 4294967296;
};
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, u) => a + (b - a) * u;
const ease = (u) => { u = clamp(u); return u * u * (3 - 2 * u); };
const easeInOut = (u) => { u = clamp(u); return u < .5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2; };

const PW = 940, PH = 1300;          // área da prancha
const TS = 0.5;                     // escala do mapa de tons

// ---------- mapa de tons → cortes ----------
function buildTone(paint) {
  const tw = Math.round(PW * TS), th = Math.round(PH * TS);
  const c = document.createElement('canvas'); c.width = tw; c.height = th;
  const g = c.getContext('2d');
  g.fillStyle = '#000'; g.fillRect(0, 0, tw, th);
  g.save(); g.scale(TS, TS); paint(g); g.restore();
  const d = g.getImageData(0, 0, tw, th).data;
  const T = new Float32Array(tw * th);
  for (let i = 0; i < tw * th; i++) T[i] = d[i * 4] / 255;
  // borrão leve para o gradiente (direção das isofotas)
  const B = new Float32Array(tw * th), B2 = new Float32Array(tw * th), r = 3;
  for (let y = 0; y < th; y++) { let s = 0, n = 0; for (let x = -r; x < tw + r; x++) {
    if (x + r < tw) { s += T[y * tw + x + r]; n++; } if (x - r - 1 >= 0) { s -= T[y * tw + x - r - 1]; n--; }
    if (x >= 0 && x < tw) B2[y * tw + x] = s / n; } }
  for (let x = 0; x < tw; x++) { let s = 0, n = 0; for (let y = -r; y < th + r; y++) {
    if (y + r < th) { s += B2[(y + r) * tw + x]; n++; } if (y - r - 1 >= 0) { s -= B2[(y - r - 1) * tw + x]; n--; }
    if (y >= 0 && y < th) B[y * tw + x] = s / n; } }
  return { T, B, tw, th, canvas: c };
}
function sample(A, tone, x, y) {
  const fx = clamp(x * TS, 0, tone.tw - 1.001), fy = clamp(y * TS, 0, tone.th - 1.001);
  const ix = fx | 0, iy = fy | 0, ux = fx - ix, uy = fy - iy, w = tone.tw, i = iy * w + ix;
  return (A[i] * (1 - ux) + A[i + 1] * ux) * (1 - uy) + (A[i + w] * (1 - ux) + A[i + w + 1] * ux) * uy;
}

// Gera os cortes de uma prancha. opts: s (espaçamento), dir(x,y) → ângulo ou null, thr, key(stroke) → 0..1
function carveStrokes(tone, opts, seed) {
  const s = opts.s || 8, thr = opts.thr ?? 0.06, rnd = RNG(seed);
  const cell = s * 0.85, gw = Math.ceil(PW / cell), gh = Math.ceil(PH / cell);
  const owner = new Int32Array(gw * gh).fill(-1), px = new Float32Array(gw * gh), py = new Float32Array(gw * gh);
  const sep = s * 0.78, h = Math.max(2.2, s * 0.42);
  const seeds = [];
  for (let y = s / 2; y < PH; y += s) for (let x = s / 2; x < PW; x += s)
    seeds.push([x + (rnd() - .5) * s, y + (rnd() - .5) * s, rnd()]);
  seeds.sort((a, b) => a[2] - b[2]);
  const strokes = [];
  const dirAt = (x, y) => {
    if (opts.dir) { const a = opts.dir(x, y); if (a != null) return a; }
    const e = 2 / TS;
    const gx = sample(tone.B, tone, x + e, y) - sample(tone.B, tone, x - e, y);
    const gy = sample(tone.B, tone, x, y + e) - sample(tone.B, tone, x, y - e);
    if (gx * gx + gy * gy < 1e-6) return opts.angle ?? -0.35;
    return Math.atan2(gy, gx) + Math.PI / 2;
  };
  const blocked = (x, y, id) => {
    const cx = (x / cell) | 0, cy = (y / cell) | 0;
    for (let j = cy - 1; j <= cy + 1; j++) for (let i = cx - 1; i <= cx + 1; i++) {
      if (i < 0 || j < 0 || i >= gw || j >= gh) continue;
      const k = j * gw + i, o = owner[k];
      if (o >= 0 && o !== id) { const dx = px[k] - x, dy = py[k] - y; if (dx * dx + dy * dy < sep * sep) return true; }
    }
    return false;
  };
  for (const [sx, sy] of seeds) {
    if (sx < 0 || sy < 0 || sx >= PW || sy >= PH) continue;
    const T0 = sample(tone.T, tone, sx, sy);
    if (T0 < thr) continue;
    const id = strokes.length;
    if (blocked(sx, sy, id)) continue;
    const maxLen = (14 + rnd() * 26) * s * (opts.lenK || 1);
    const trace = (sign) => {
      const out = []; let x = sx, y = sy, prev = null, L = 0;
      while (L < maxLen / 2) {
        let a = dirAt(x, y);
        let dx = Math.cos(a), dy = Math.sin(a);
        if (prev && dx * prev[0] + dy * prev[1] < 0) { dx = -dx; dy = -dy; }
        if (!prev && sign < 0) { dx = -dx; dy = -dy; }
        x += dx * h; y += dy * h; L += h; prev = [dx, dy];
        if (x < 1 || y < 1 || x > PW - 1 || y > PH - 1) break;
        const T = sample(tone.T, tone, x, y);
        if (T < thr || blocked(x, y, id)) break;
        out.push([x, y, T]);
      }
      return out;
    };
    const fw = trace(1), bw = trace(-1);
    const pts = bw.reverse().concat([[sx, sy, T0]], fw);
    if (pts.length < 4) continue;
    const n = pts.length, arr = new Float32Array(n * 3);
    let Tm = 0;
    const wmax = s * 0.95, jit = rnd() * 10;
    for (let i = 0; i < n; i++) {
      const [x, y, T] = pts[i], u = i / (n - 1);
      let w = wmax * Math.pow(clamp((T - thr) / (1 - thr)), 0.8);
      w *= Math.pow(Math.min(1, u / 0.08), 0.5) * Math.pow(Math.min(1, (1 - u) / 0.35), 0.8);
      w *= 1 + 0.12 * Math.sin(i * 1.7 + jit);
      arr[i * 3] = x; arr[i * 3 + 1] = y; arr[i * 3 + 2] = Math.max(0.6, w);
      Tm += T;
      const cx = (x / cell) | 0, cy = (y / cell) | 0, k = cy * gw + cx;
      if (owner[k] < 0) { owner[k] = id; px[k] = x; py[k] = y; }
    }
    strokes.push({ p: arr, n, T: Tm / n, x: pts[n >> 1][0], y: pts[n >> 1][1], r: rnd() });
  }
  return strokes;
}

function strokePath(st, frac) {
  const p = st.p, n = Math.max(2, Math.round(st.n * frac));
  const L = [], R = [];
  for (let i = 0; i < n; i++) {
    const a = Math.max(0, i - 1), b = Math.min(st.n - 1, i + 1);
    let tx = p[b * 3] - p[a * 3], ty = p[b * 3 + 1] - p[a * 3 + 1];
    const m = Math.hypot(tx, ty) || 1; tx /= m; ty /= m;
    let w = p[i * 3 + 2] / 2;
    if (frac < 1 && i > n - 4) w *= (n - i) / 4;
    L.push(p[i * 3] - ty * w, p[i * 3 + 1] + tx * w);
    R.push(p[i * 3] + ty * w, p[i * 3 + 1] - tx * w);
  }
  const P = new Path2D();
  P.moveTo(L[0], L[1]);
  for (let i = 2; i < L.length; i += 2) P.lineTo(L[i], L[i + 1]);
  for (let i = R.length - 2; i >= 0; i -= 2) P.lineTo(R[i], R[i + 1]);
  P.closePath();
  return P;
}

// ---------- figuras (silhueta + halo de faca + cortes de luz rasante) ----------
function capsule(P, ax, ay, bx, by, r) {
  const a = Math.atan2(by - ay, bx - ax);
  P.moveTo(ax + Math.cos(a + Math.PI / 2) * r, ay + Math.sin(a + Math.PI / 2) * r);
  P.arc(bx, by, r, a + Math.PI / 2, a - Math.PI / 2, true);
  P.arc(ax, ay, r, a - Math.PI / 2, a + Math.PI / 2, true);
  P.closePath();
}
// pose: ângulos em graus (0 = para cima, positivo = horário). Origem no quadril.
function figureParts(f) {
  const d = Math.PI / 180, k = f.k || 1, parts = [];
  const pt = (x, y, a, l) => [x + Math.sin(a * d) * l, y - Math.cos(a * d) * l];
  const hip = [0, 0];
  const sh = pt(0, 0, f.torso || 0, 72 * k);
  const neck = pt(sh[0], sh[1], (f.torso || 0) + (f.headTilt || 0), 12 * k);
  const head = pt(neck[0], neck[1], (f.torso || 0) + (f.headTilt || 0), 15 * k);
  // tronco com túnica
  const tor = new Path2D(), ta = (f.torso || 0) * d;
  const nx = Math.cos(ta), ny = Math.sin(ta);
  const ux = Math.sin(ta), uy = -Math.cos(ta);
  tor.moveTo(sh[0] - nx * 18 * k - ux * 2 * k, sh[1] - ny * 18 * k - uy * 2 * k);
  tor.quadraticCurveTo(sh[0] - nx * 27 * k + ux * 6 * k, sh[1] - ny * 27 * k + uy * 6 * k, sh[0] - nx * 25 * k - ux * 12 * k, sh[1] - ny * 25 * k - uy * 12 * k);
  tor.quadraticCurveTo(hip[0] - nx * 21 * k + ux * 30 * k, hip[1] - ny * 21 * k + uy * 30 * k, hip[0] - nx * 27 * k, hip[1] - ny * 27 * k);
  tor.lineTo(hip[0] + nx * 27 * k, hip[1] + ny * 27 * k);
  tor.quadraticCurveTo(hip[0] + nx * 21 * k + ux * 30 * k, hip[1] + ny * 21 * k + uy * 30 * k, sh[0] + nx * 25 * k - ux * 12 * k, sh[1] + ny * 25 * k - uy * 12 * k);
  tor.quadraticCurveTo(sh[0] + nx * 27 * k + ux * 6 * k, sh[1] + ny * 27 * k + uy * 6 * k, sh[0] + nx * 18 * k - ux * 2 * k, sh[1] + ny * 18 * k - uy * 2 * k);
  tor.closePath();
  parts.push({ P: tor, kind: 'tor' });
  // saia da túnica
  if (f.skirt !== false) {
    const sk = new Path2D(), da = ((f.torso || 0) + 180) * d, sl = (f.skirtLen || 42) * k;
    const bx = Math.sin(da) * sl, by = -Math.cos(da) * sl;
    sk.moveTo(-nx * 27 * k, -ny * 27 * k); sk.lineTo(nx * 27 * k, ny * 27 * k);
    sk.lineTo(bx + nx * 31 * k, by + ny * 31 * k); sk.lineTo(bx - nx * 31 * k, by - ny * 31 * k);
    sk.closePath(); parts.push({ P: sk, kind: 'skirt' });
  }
  for (const side of [-1, 1]) {
    const s0 = side < 0 ? 'L' : 'R';
    const sx = sh[0] + side * nx * 20 * k, sy = sh[1] + side * ny * 20 * k;
    const ua = f['ua' + s0] ?? 180 - side * 12, la = f['la' + s0] ?? ua;
    const el = pt(sx, sy, ua, 34 * k), wr = pt(el[0], el[1], la, 32 * k);
    const A = new Path2D(); capsule(A, sx, sy, el[0], el[1], 7.5 * k); capsule(A, el[0], el[1], wr[0], wr[1], 6.2 * k);
    A.moveTo(wr[0] + 7 * k, wr[1]); A.arc(wr[0], wr[1], 7 * k, 0, Math.PI * 2);
    parts.push({ P: A, kind: 'arm', side, wrist: wr });
    const hx = side * nx * 14 * k, hy = side * ny * 14 * k;
    const th = f['th' + s0] ?? 180, sn = f['sn' + s0] ?? th;
    const kn = pt(hx, hy, th, 44 * k), an = pt(kn[0], kn[1], sn, 44 * k);
    const G = new Path2D(); capsule(G, hx, hy, kn[0], kn[1], 9 * k); capsule(G, kn[0], kn[1], an[0], an[1], 7 * k);
    const fa = (sn + 90 * (f.face || 1)) * d;
    capsule(G, an[0], an[1], an[0] + Math.sin(fa) * 14 * k, an[1] - Math.cos(fa) * 14 * k, 5 * k);
    parts.push({ P: G, kind: 'leg', side });
  }
  const H = new Path2D(); H.ellipse(head[0], head[1], 15 * k, 16.5 * k, 0, 0, Math.PI * 2);
  capsule(H, sh[0], sh[1], neck[0], neck[1], 6 * k);
  parts.push({ P: H, kind: 'head', c: head });
  return { parts, head, sh };
}

// desenha a figura na camada de cortes (cut) já transformada
const RIM = document.createElement('canvas'), rimx = RIM.getContext('2d');
function figureRim(cut, f, fp, light) {
  const R = Math.ceil(250 * f.scale), sz = 2 * R;
  if (RIM.width < sz || RIM.height < sz) { RIM.width = Math.max(RIM.width, sz); RIM.height = Math.max(RIM.height, sz); }
  let lx = light[0], ly = light[1]; if (f.flip) lx = -lx;
  const c = Math.cos(-(f.rot || 0) * Math.PI / 180), s = Math.sin(-(f.rot || 0) * Math.PI / 180);
  [lx, ly] = [lx * c - ly * s, lx * s + ly * c];
  const local = (dx, dy) => { rimx.setTransform(1, 0, 0, 1, R, R); if (f.flip) rimx.scale(-1, 1); rimx.rotate((f.rot || 0) * Math.PI / 180);
    rimx.scale(f.scale, f.scale); rimx.translate(dx, dy); };
  const fillAll = () => { rimx.beginPath(); for (const p of fp.parts) rimx.fill(p.P); };
  const lines = f.scale > 1.6 ? [[3.5, 2.4], [9, 1.9], [16, 1.4], [25, 1.0]] : [[2.5, 1.8], [6.5, 1.3]];
  for (const [d, w] of lines) {
    rimx.setTransform(1, 0, 0, 1, 0, 0); rimx.clearRect(0, 0, sz, sz);
    rimx.fillStyle = '#fff'; rimx.globalCompositeOperation = 'source-over';
    local(-lx * (d - w) / f.scale, -ly * (d - w) / f.scale); fillAll();
    rimx.globalCompositeOperation = 'source-in'; local(0, 0); fillAll();
    rimx.globalCompositeOperation = 'destination-out'; local(-lx * d / f.scale, -ly * d / f.scale); fillAll();
    rimx.globalCompositeOperation = 'source-over';
    cut.drawImage(RIM, 0, 0, sz, sz, f.x - R, f.y - R, sz, sz);
  }
}
function drawFigure(cut, f, light, prog = 1) {
  const fp = figureParts(f);
  cut.save();
  cut.translate(f.x, f.y);
  if (f.flip) cut.scale(-1, 1);
  cut.rotate((f.rot || 0) * Math.PI / 180);
  cut.scale(f.scale, f.scale);
  const sc = f.scale, halo = (f.halo || 5) / sc;
  cut.lineJoin = 'round';
  // halo de faca (contorno branco) entalhado progressivamente
  cut.strokeStyle = '#fff'; cut.lineWidth = halo * 2;
  if (prog < 1) cut.setLineDash([900 * prog / sc, 9999]);
  for (const p of fp.parts) cut.stroke(p.P);
  cut.setLineDash([]);
  cut.globalCompositeOperation = 'destination-out';
  for (const p of fp.parts) cut.fill(p.P);
  cut.globalCompositeOperation = 'source-over';
  cut.restore();
  // cortes de luz rasante: só no contorno da silhueta inteira (sem costuras entre as partes)
  if (prog > 0.3) figureRim(cut, f, fp, light);
  cut.save(); cut.translate(f.x, f.y); if (f.flip) cut.scale(-1, 1); cut.rotate((f.rot || 0) * Math.PI / 180); cut.scale(f.scale, f.scale);
  if (prog > 0.3) {
    if (f.faceWhite && f.scale >= 1.8) { // rosto entalhado em branco, traços em preto
      const [hx, hy] = fp.head, k = f.k || 1;
      cut.fillStyle = '#fff'; cut.beginPath(); cut.ellipse(hx + 2 * k, hy + 1 * k, 9 * k, 11 * k, 0, 0, Math.PI * 2); cut.fill();
      cut.globalCompositeOperation = 'destination-out';
      cut.beginPath(); cut.arc(hx + 4 * k, hy - 2 * k, 1.6 * k, 0, Math.PI * 2); cut.fill();
      cut.fillRect(hx + 1 * k, hy + 5 * k, 6 * k, 1.4 * k);
      if (f.beard) { cut.beginPath(); cut.ellipse(hx + 2 * k, hy + 9 * k, 8 * k, 5 * k, 0, 0, Math.PI * 2); cut.fill(); }
      cut.beginPath(); cut.ellipse(hx - 2 * k, hy - 8 * k, 12 * k, 6 * k, 0, 0, Math.PI * 2); cut.fill();
      cut.globalCompositeOperation = 'source-over';
    }
  }
  cut.restore();
  return fp;
}

// ---------- texturas de impressão ----------
function paperTexture(W, H) {
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const g = c.getContext('2d'), r = RNG(7);
  g.fillStyle = '#e9dec6'; g.fillRect(0, 0, W, H);
  const im = g.getImageData(0, 0, W, H), d = im.data;
  for (let y = 0; y < H; y++) {
    const laid = (y % 22 < 2) ? -5 : 0;
    for (let x = 0; x < W; x++) {
      const i = (y * W + x) * 4, n = (r() - .5) * 10 + laid + Math.sin(x * 0.013 + y * 0.002) * 3;
      d[i] += n; d[i + 1] += n; d[i + 2] += n * 0.9;
    }
  }
  g.putImageData(im, 0, 0);
  g.globalAlpha = 0.06; g.strokeStyle = '#7a6a50';
  for (let i = 0; i < 900; i++) { const x = r() * W, y = r() * H, a = r() * 6.3, l = 6 + r() * 26;
    g.lineWidth = 0.6; g.beginPath(); g.moveTo(x, y); g.lineTo(x + Math.cos(a) * l, y + Math.sin(a) * l); g.stroke(); }
  g.globalAlpha = 1;
  const v = g.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.75);
  v.addColorStop(0, 'rgba(60,40,20,0)'); v.addColorStop(1, 'rgba(60,40,20,0.18)');
  g.fillStyle = v; g.fillRect(0, 0, W, H);
  return c;
}
function inkTexture(W, H) {
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const g = c.getContext('2d'), r = RNG(11);
  g.fillStyle = '#16120e'; g.fillRect(0, 0, W, H);
  // veio da madeira
  g.globalAlpha = 0.07; g.strokeStyle = '#4a3c2c';
  for (let i = 0; i < 260; i++) {
    let y = r() * H; g.lineWidth = 0.8 + r() * 2.2; g.beginPath(); g.moveTo(0, y);
    const ph = r() * 6, am = 4 + r() * 14;
    for (let x = 0; x <= W; x += 20) g.lineTo(x, y + Math.sin(x * 0.006 + ph) * am + Math.sin(x * 0.021 + ph * 2) * am * 0.3);
    g.stroke();
  }
  // irregularidade da tinta ±6%
  g.globalAlpha = 1;
  for (let i = 0; i < 160; i++) { const x = r() * W, y = r() * H, rr = 40 + r() * 160;
    const gr = g.createRadialGradient(x, y, 0, x, y, rr);
    const lv = r() < .5 ? 'rgba(70,58,44,0.09)' : 'rgba(0,0,0,0.12)';
    gr.addColorStop(0, lv); gr.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = gr; g.fillRect(x - rr, y - rr, rr * 2, rr * 2); }
  return c;
}
function speckles(W, H) { // falhas onde a tinta não pegou
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const g = c.getContext('2d'), r = RNG(19);
  g.fillStyle = '#fff';
  for (let i = 0; i < 1400; i++) { const x = r() * W, y = r() * H, rr = 0.4 + r() * r() * 1.8;
    g.globalAlpha = 0.25 + r() * 0.6; g.beginPath(); g.ellipse(x, y, rr, rr * (0.5 + r()), r() * 3, 0, Math.PI * 2); g.fill(); }
  return c;
}
function raggedEdge(x0, y0, w, h, seed) {
  const r = RNG(seed), P = new Path2D(), pts = [];
  const step = 7, jit = () => (r() - .5) * 3.2 + (r() < .03 ? (r() - .5) * 7 : 0);
  for (let x = 0; x <= w; x += step) pts.push([x0 + x, y0 + jit()]);
  for (let y = 0; y <= h; y += step) pts.push([x0 + w + jit(), y0 + y]);
  for (let x = w; x >= 0; x -= step) pts.push([x0 + x, y0 + h + jit()]);
  for (let y = h; y >= 0; y -= step) pts.push([x0 + jit(), y0 + y]);
  P.moveTo(pts[0][0], pts[0][1]); for (const p of pts) P.lineTo(p[0], p[1]); P.closePath();
  return P;
}
