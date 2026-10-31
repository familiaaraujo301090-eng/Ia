// Camada 2D desenhada por cima do 3D: selo, legenda, marca d'água, barra de
// progresso, logo final e transições (fade entre cenas).
import { FONT, logoCircleCanvas } from './textures.js';

const { min, max } = Math;
export const NARRACAO_DELAY = 0.25;

// agrupa as palavras em blocos curtos (até 3 palavras / 18 letras)
function chunk(palavras) {
  const out = [];
  let cur = [];
  for (const p of palavras) {
    const len = cur.reduce((a, q) => a + q.w.length + 1, 0) + p.w.length;
    if (cur.length && (cur.length >= 3 || len > 18)) {
      out.push(cur);
      cur = [];
    }
    cur.push(p);
    if (/[.,!?:]$/.test(p.w)) {
      out.push(cur);
      cur = [];
    }
  }
  if (cur.length) out.push(cur);
  return out;
}
const clamp01 = (v) => min(1, max(0, v));
const easeOutBack = (x) => {
  const c1 = 1.70158, c3 = c1 + 1;
  return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2);
};

function roundRect(g, x, y, w, h, r) {
  g.beginPath();
  g.moveTo(x + r, y);
  g.arcTo(x + w, y, x + w, y + h, r);
  g.arcTo(x + w, y + h, x, y + h, r);
  g.arcTo(x, y + h, x, y, r);
  g.arcTo(x, y, x + w, y, r);
  g.closePath();
}

export function makeOverlay(logoImg) {
  const logo = logoCircleCanvas(logoImg, 512);

  return function draw(g, W, H, state, total, t) {
    const { cena, local } = state;
    const S = W / 720;

    // marca d'água
    g.save();
    g.globalAlpha = 0.9;
    g.drawImage(logo, 24 * S, 24 * S, 92 * S, 92 * S);
    g.restore();

    // selo (pílula verde)
    if (cena.selo) {
      const k = easeOutBack(clamp01(local / 0.45));
      g.save();
      g.font = `bold ${44 * S}px ${FONT}`;
      const tw = g.measureText(cena.selo).width;
      const w = tw + 70 * S, h = 82 * S;
      g.translate(W / 2, 175 * S);
      g.scale(k, k);
      g.shadowColor = 'rgba(0,0,0,0.35)';
      g.shadowBlur = 18 * S;
      g.fillStyle = '#4dd75d';
      roundRect(g, -w / 2, -h / 2, w, h, h / 2);
      g.fill();
      g.shadowBlur = 0;
      g.fillStyle = '#13296b';
      g.textAlign = 'center';
      g.textBaseline = 'middle';
      g.fillText(cena.selo, 0, 3 * S);
      g.restore();
    }

    // logo grande no encerramento
    if (cena.logoFinal) {
      const k = easeOutBack(clamp01((local - 0.6) / 0.6));
      if (k > 0) {
        const r = 100 * S * k;
        g.save();
        g.shadowColor = 'rgba(0,0,0,0.45)';
        g.shadowBlur = 30 * S;
        g.beginPath();
        g.arc(W / 2, 345 * S, r + 8 * S, 0, Math.PI * 2);
        g.fillStyle = '#ffffff';
        g.fill();
        g.shadowBlur = 0;
        g.drawImage(logo, W / 2 - r, 345 * S - r, r * 2, r * 2);
        g.restore();
      }
    }

    // legendas estilo "viral": blocos de até 3 palavras, palavra falada em verde
    if (cena.palavras && cena.palavras.length) {
      const tt = local - NARRACAO_DELAY;
      const chunks = chunk(cena.palavras);
      let ci = -1;
      for (let i = 0; i < chunks.length; i++) if (tt >= chunks[i][0].t0 - 0.05) ci = i;
      const last = chunks[chunks.length - 1];
      if (ci >= 0 && tt < last[last.length - 1].t1 + 0.6) {
        const ch = chunks[ci];
        const k = easeOutBack(clamp01((tt - ch[0].t0 + 0.05) / 0.14));
        g.save();
        g.translate(W / 2, H * 0.7);
        g.scale(k, k);
        g.font = `900 ${60 * S}px ${FONT}`;
        g.textAlign = 'left';
        g.textBaseline = 'middle';
        g.lineJoin = 'round';
        const words = ch.map((p) => p.w.toUpperCase());
        const sp = 24 * S;
        const widths = words.map((w) => g.measureText(w).width * 1.12);
        const full = widths.reduce((a, b) => a + b, 0) + sp * (words.length - 1);
        const fit = Math.min(1, (W - 60 * S) / full);
        g.scale(fit, fit);
        let x = -full / 2;
        words.forEach((w, i) => {
          const on = tt >= ch[i].t0 - 0.03 && (i === ch.length - 1 || tt < ch[i + 1].t0);
          g.save();
          g.translate(x + widths[i] / 2, 0);
          if (on) g.scale(1.12, 1.12);
          g.lineWidth = 12 * S;
          g.strokeStyle = '#0b1640';
          g.strokeText(w, -widths[i] / 2 / 1.12, 0);
          g.fillStyle = on ? '#4dd75d' : '#ffffff';
          g.fillText(w, -widths[i] / 2 / 1.12, 0);
          g.restore();
          x += widths[i] + sp;
        });
        g.restore();
      }
    }

    // barra de progresso
    g.fillStyle = 'rgba(255,255,255,0.35)';
    g.fillRect(0, H - 10 * S, W, 10 * S);
    g.fillStyle = '#4dd75d';
    g.fillRect(0, H - 10 * S, (W * t) / total, 10 * S);

    // flash branco nos cortes; fade preto só no início e no fim do vídeo
    const isFirst = cena.inicio === 0, isLast = Math.abs(cena.fim - total) < 1e-6;
    if (!isFirst && local < 0.12) {
      g.fillStyle = `rgba(255,255,255,${0.85 * (1 - local / 0.12)})`;
      g.fillRect(0, 0, W, H);
    }
    let fade = 0;
    if (isFirst && local < 0.4) fade = 1 - local / 0.4;
    if (isLast && cena.duracao - local < 0.6) fade = 1 - (cena.duracao - local) / 0.6;
    if (fade > 0) {
      g.fillStyle = `rgba(0,0,0,${clamp01(fade)})`;
      g.fillRect(0, 0, W, H);
    }
  };
}
