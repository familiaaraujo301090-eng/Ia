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
