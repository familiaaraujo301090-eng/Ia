// Texturas geradas em canvas 2D: logo recortado em círculo, textos, faixas e
// placas. Assim nenhum asset além do logo precisa existir em disco.
export const FONT = '"Liberation Sans", "DejaVu Sans", Arial, sans-serif';

export function canvas(w, h) {
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  return c;
}

// O logo original é um círculo azul num fundo escuro: recortamos só o círculo.
export function logoCircleCanvas(img, size = 512) {
  const c = canvas(size, size);
  const g = c.getContext('2d');
  g.save();
  g.beginPath();
  g.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2);
  g.clip();
  g.fillStyle = '#213e86';
  g.fillRect(0, 0, size, size);
  const inset = size * 0.035;
  g.drawImage(img, -inset, -inset, size + inset * 2, size + inset * 2);
  g.restore();
  return c;
}

export function textCanvas(lines, { w = 512, h = 256, color = '#fff', bg = null, size = 80, weight = 'bold' } = {}) {
  const c = canvas(w, h);
  const g = c.getContext('2d');
  if (bg) {
    g.fillStyle = bg;
    g.fillRect(0, 0, w, h);
  }
  g.fillStyle = color;
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.font = `${weight} ${size}px ${FONT}`;
  const lh = size * 1.1;
  lines.forEach((l, i) => g.fillText(l, w / 2, h / 2 + (i - (lines.length - 1) / 2) * lh));
  return c;
}

export function bannerCanvas(text, logoImg, { w = 1024, h = 256 } = {}) {
  const c = canvas(w, h);
  const g = c.getContext('2d');
  const grad = g.createLinearGradient(0, 0, 0, h);
  grad.addColorStop(0, '#2a52bf');
  grad.addColorStop(1, '#16307a');
  g.fillStyle = grad;
  g.fillRect(0, 0, w, h);
  g.fillStyle = '#4dd75d';
  g.fillRect(0, 0, w, 14);
  g.fillRect(0, h - 14, w, 14);
  if (logoImg) g.drawImage(logoCircleCanvas(logoImg, h - 50), 25, 25);
  g.fillStyle = '#ffffff';
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  let size = 110;
  g.font = `bold ${size}px ${FONT}`;
  const maxW = w - (logoImg ? h + 40 : 60);
  while (g.measureText(text).width > maxW && size > 30) {
    size -= 4;
    g.font = `bold ${size}px ${FONT}`;
  }
  g.fillText(text, logoImg ? (h + w) / 2 - 10 : w / 2, h / 2 + 4);
  return c;
}

export function roadCanvas() {
  const c = canvas(512, 512);
  const g = c.getContext('2d');
  g.fillStyle = '#4a4d52';
  g.fillRect(0, 0, 512, 512);
  // granulado do asfalto (determinístico)
  let s = 7;
  const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647);
  for (let i = 0; i < 9000; i++) {
    const v = 60 + rnd() * 40;
    g.fillStyle = `rgba(${v},${v},${v + 4},0.5)`;
    g.fillRect(rnd() * 512, rnd() * 512, 2, 2);
  }
  return c;
}

function seeded(seed) {
  let s = seed;
  return () => ((s = (s * 16807) % 2147483647) / 2147483647);
}

// Calçada portuguesa em ondas pretas e brancas, típica de cidades brasileiras.
export function sidewalkCanvas() {
  const W = 512, H = 512;
  const c = canvas(W, H);
  const g = c.getContext('2d');
  const rnd = seeded(11);
  for (let y = 0; y < H; y += 8) {
    for (let x = 0; x < W; x += 8) {
      const wave = Math.sin((x / W) * Math.PI * 4) * 70 + H / 2;
      const band = Math.abs(y - wave) < 46 || Math.abs(y - wave + H) < 46 || Math.abs(y - wave - H) < 46;
      const v = band ? 40 + rnd() * 25 : 215 + rnd() * 30;
      g.fillStyle = `rgb(${v},${v - 4},${v - 10})`;
      g.fillRect(x + 1, y + 1, 6 + rnd() * 2, 6 + rnd() * 2);
    }
  }
  g.globalCompositeOperation = 'destination-over';
  g.fillStyle = '#8a857c';
  g.fillRect(0, 0, W, H);
  return c;
}

export function grassCanvas() {
  const W = 512;
  const c = canvas(W, W);
  const g = c.getContext('2d');
  g.fillStyle = '#6aa845';
  g.fillRect(0, 0, W, W);
  const rnd = seeded(5);
  for (let i = 0; i < 2600; i++) {
    const r = 4 + rnd() * 26;
    g.fillStyle = `rgba(${60 + rnd() * 70},${120 + rnd() * 70},${30 + rnd() * 40},0.18)`;
    g.beginPath();
    g.arc(rnd() * W, rnd() * W, r, 0, Math.PI * 2);
    g.fill();
  }
  for (let i = 0; i < 6000; i++) {
    g.fillStyle = `rgba(${40 + rnd() * 40},${90 + rnd() * 60},${20 + rnd() * 30},0.5)`;
    g.fillRect(rnd() * W, rnd() * W, 1, 3);
  }
  return c;
}

export function roofCanvas() {
  const W = 256;
  const c = canvas(W, W);
  const g = c.getContext('2d');
  g.fillStyle = '#b5532f';
  g.fillRect(0, 0, W, W);
  for (let y = 0; y < W; y += 16) {
    for (let x = (y / 16) % 2 ? 8 : 0; x < W; x += 16) {
      const grd = g.createLinearGradient(x, 0, x + 16, 0);
      grd.addColorStop(0, 'rgba(255,190,150,0.35)');
      grd.addColorStop(0.5, 'rgba(0,0,0,0)');
      grd.addColorStop(1, 'rgba(60,15,5,0.45)');
      g.fillStyle = grd;
      g.fillRect(x, y, 16, 16);
    }
    g.fillStyle = 'rgba(60,15,5,0.5)';
    g.fillRect(0, y + 14, W, 2);
  }
  return c;
}

export function awningCanvas(cor) {
  const c = canvas(256, 64);
  const g = c.getContext('2d');
  for (let i = 0; i < 8; i++) {
    g.fillStyle = i % 2 ? '#ffffff' : cor;
    g.fillRect(i * 32, 0, 32, 64);
  }
  return c;
}

// ---------- texturas com relevo (realismo) ----------

// Converte um mapa de altura (tons de cinza) em mapa de normais.
export function normalFromHeight(src, forca = 2) {
  const W = src.width, H = src.height;
  const d = src.getContext('2d').getImageData(0, 0, W, H).data;
  const h = (x, y) => d[(((y + H) % H) * W + ((x + W) % W)) * 4] / 255;
  const c = canvas(W, H);
  const g = c.getContext('2d');
  const out = g.createImageData(W, H);
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const dx = (h(x + 1, y) - h(x - 1, y)) * forca;
      const dy = (h(x, y + 1) - h(x, y - 1)) * forca;
      const l = Math.hypot(dx, dy, 1);
      const i = (y * W + x) * 4;
      out.data[i] = ((-dx / l) * 0.5 + 0.5) * 255;
      out.data[i + 1] = ((dy / l) * 0.5 + 0.5) * 255;
      out.data[i + 2] = ((1 / l) * 0.5 + 0.5) * 255;
      out.data[i + 3] = 255;
    }
  }
  g.putImageData(out, 0, 0);
  return c;
}

// Calçada portuguesa com pedras irregulares: cor + altura (pedras altas, rejunte baixo).
export function calcadaMaps(tam = 1024) {
  const cor = canvas(tam, tam), alt = canvas(tam, tam);
  const gc = cor.getContext('2d'), ga = alt.getContext('2d');
  gc.fillStyle = '#6f6a62';
  gc.fillRect(0, 0, tam, tam);
  ga.fillStyle = '#000';
  ga.fillRect(0, 0, tam, tam);
  const rnd = seeded(23);
  const p = tam / 96; // ~24 pedras por metro quando a textura cobre 4 m
  for (let y = 0; y < tam; y += p) {
    for (let x = 0; x < tam; x += p) {
      const wave = Math.sin((x / tam) * Math.PI * 4) * tam * 0.14 + tam / 2;
      const band = [0, tam, -tam].some((o) => Math.abs(y - wave + o) < tam * 0.085);
      const v = band ? 35 + rnd() * 30 : 205 + rnd() * 40;
      const jx = (rnd() - 0.5) * p * 0.25, jy = (rnd() - 0.5) * p * 0.25;
      const w = p * (0.72 + rnd() * 0.2), hh = p * (0.72 + rnd() * 0.2);
      gc.fillStyle = `rgb(${v},${v - 5},${v - 12})`;
      ga.fillStyle = `rgb(${150 + rnd() * 100},0,0)`;
      gc.beginPath();
      ga.beginPath();
      gc.ellipse(x + p / 2 + jx, y + p / 2 + jy, w / 2, hh / 2, rnd(), 0, Math.PI * 2);
      ga.ellipse(x + p / 2 + jx, y + p / 2 + jy, w / 2, hh / 2, rnd(), 0, Math.PI * 2);
      gc.fill();
      ga.fill();
    }
  }
  // o canal vermelho serve de altura
  const ad = ga.getImageData(0, 0, tam, tam);
  for (let i = 0; i < ad.data.length; i += 4) ad.data[i + 1] = ad.data[i + 2] = ad.data[i];
  ga.putImageData(ad, 0, 0);
  return { cor, normal: normalFromHeight(alt, 3) };
}

// Reboco: ruído suave de manchas (cor) e grão fino (relevo).
export function rebocoMaps(base = '#f0d9bf', tam = 512) {
  const cor = canvas(tam, tam), alt = canvas(tam, tam);
  const gc = cor.getContext('2d'), ga = alt.getContext('2d');
  gc.fillStyle = base;
  gc.fillRect(0, 0, tam, tam);
  ga.fillStyle = '#808080';
  ga.fillRect(0, 0, tam, tam);
  const rnd = seeded(41);
  for (let i = 0; i < 400; i++) {
    gc.fillStyle = `rgba(${rnd() < 0.5 ? '90,70,50' : '255,255,255'},${0.03 + rnd() * 0.04})`;
    gc.beginPath();
    gc.arc(rnd() * tam, rnd() * tam, 10 + rnd() * 60, 0, Math.PI * 2);
    gc.fill();
  }
  for (let i = 0; i < 30000; i++) {
    const v = 90 + rnd() * 80;
    ga.fillStyle = `rgb(${v},${v},${v})`;
    ga.fillRect(rnd() * tam, rnd() * tam, 2, 2);
  }
  // escorrido de chuva na parte de baixo
  const gr = gc.createLinearGradient(0, tam * 0.75, 0, tam);
  gr.addColorStop(0, 'rgba(80,60,40,0)');
  gr.addColorStop(1, 'rgba(80,60,40,0.12)');
  gc.fillStyle = gr;
  gc.fillRect(0, 0, tam, tam);
  return { cor, normal: normalFromHeight(alt, 0.6) };
}

export function cascaMaps(tam = 256) {
  const cor = canvas(tam, tam), alt = canvas(tam, tam);
  const gc = cor.getContext('2d'), ga = alt.getContext('2d');
  gc.fillStyle = '#6b5a49';
  gc.fillRect(0, 0, tam, tam);
  ga.fillStyle = '#808080';
  ga.fillRect(0, 0, tam, tam);
  const rnd = seeded(7);
  for (let i = 0; i < 260; i++) {
    const x = rnd() * tam, w = 2 + rnd() * 6, v = rnd();
    gc.fillStyle = `rgba(${v < 0.5 ? '40,30,20' : '150,135,115'},0.35)`;
    gc.fillRect(x, 0, w, tam);
    ga.fillStyle = `rgba(${v < 0.5 ? '0,0,0' : '255,255,255'},0.35)`;
    ga.fillRect(x, 0, w, tam);
  }
  return { cor, normal: normalFromHeight(alt, 2.5) };
}

// Cartão de folhagem: muitas folhinhas com transparência (para copas instanciadas).
export function folhagemCanvas(tons = ['#2f6b2a', '#3a7d31', '#4a8f38', '#285c25', '#5c9e3f'], tam = 256, seed = 3) {
  const c = canvas(tam, tam);
  const g = c.getContext('2d');
  const rnd = seeded(seed);
  for (let i = 0; i < 70; i++) {
    const x = tam * (0.12 + rnd() * 0.76), y = tam * (0.12 + rnd() * 0.76);
    if (Math.hypot(x - tam / 2, y - tam / 2) > tam * 0.42) continue;
    const a = rnd() * Math.PI * 2, L = tam * (0.07 + rnd() * 0.05);
    g.save();
    g.translate(x, y);
    g.rotate(a);
    g.fillStyle = tons[Math.floor(rnd() * tons.length)];
    g.beginPath();
    g.ellipse(0, 0, L, L * 0.45, 0, 0, Math.PI * 2);
    g.fill();
    g.strokeStyle = 'rgba(20,40,15,0.5)';
    g.lineWidth = 1;
    g.beginPath();
    g.moveTo(-L, 0);
    g.lineTo(L, 0);
    g.stroke();
    g.restore();
  }
  return c;
}

// Folha de palmeira (fronde) com folíolos, vista de cima; transparente fora das folhas.
export function frondeCanvas(tam = 512) {
  const c = canvas(tam / 4, tam);
  const g = c.getContext('2d');
  const W = c.width;
  g.strokeStyle = '#6f8f3a';
  g.lineWidth = 4;
  g.beginPath();
  g.moveTo(W / 2, tam);
  g.lineTo(W / 2, 0);
  g.stroke();
  for (let y = 10; y < tam - 10; y += 7) {
    const k = 1 - Math.abs(y / tam - 0.45) * 1.4;
    const L = (W / 2) * Math.max(0.2, k);
    g.strokeStyle = y % 14 ? '#3f8a2f' : '#4f9a36';
    g.lineWidth = 3;
    for (const s of [-1, 1]) {
      g.beginPath();
      g.moveTo(W / 2, y);
      g.lineTo(W / 2 + s * L, y + 18);
      g.stroke();
    }
  }
  return c;
}
