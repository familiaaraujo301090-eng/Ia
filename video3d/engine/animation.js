// Animações do personagem (procedurais, guiadas pelo tempo) e a linha do tempo
// que transforma o roteiro em posição/fase de corrida para qualquer instante t.
import * as THREE from 'three';

export const BASE_Y = 1.05;
const { clamp, smoothstep, lerp } = THREE.MathUtils;
const ss = (a, b, x) => smoothstep(x, a, b);

// ---------- linha do tempo ----------
export function speedFor(cena, u) {
  if (cena.acao === 'correr') return cena.velocidade;
  if (cena.acao === 'chegada') return cena.velocidade * (1 - ss(0.3, 0.5, u));
  return 0;
}

export function buildTimeline(roteiro) {
  const cenas = [];
  let t0 = 0;
  for (const c of roteiro.cenas) {
    cenas.push({ ...c, inicio: t0, fim: t0 + c.duracao });
    t0 += c.duracao;
  }
  const total = t0;
  const dt = 1 / 240;
  const n = Math.ceil(total / dt) + 2;
  const xs = new Float32Array(n), ph = new Float32Array(n);
  let x = 0, p = 0, finishX = null;
  for (let i = 0; i < n; i++) {
    const t = i * dt;
    const { cena, u } = sceneAt(cenas, t);
    const v = speedFor(cena, u);
    xs[i] = x;
    ph[i] = p;
    if (cena.acao === 'chegada' && finishX === null && u >= 0.28) finishX = x;
    x += v * dt;
    // cadência: passos mais rápidos conforme a velocidade; trote leve parado
    const jog = cena.acao === 'alongar' ? ss(0.55, 0.62, u) : 0;
    p += dt * Math.PI * 2 * (v > 0.2 ? 1.25 + v * 0.05 : 1.3 * jog);
  }
  const sample = (arr, t) => {
    const f = clamp(t / dt, 0, n - 1.001), i = Math.floor(f);
    return lerp(arr[i], arr[i + 1], f - i);
  };
  return {
    cenas,
    total,
    finishX: finishX ?? x,
    at(t) {
      const s = sceneAt(cenas, t);
      return { ...s, x: sample(xs, t), phase: sample(ph, t), speed: speedFor(s.cena, s.u) };
    },
  };
}

export function sceneAt(cenas, t) {
  let i = cenas.findIndex((c) => t < c.fim);
  if (i < 0) i = cenas.length - 1;
  const cena = cenas[i];
  return { cena, index: i, local: t - cena.inicio, u: clamp((t - cena.inicio) / cena.duracao, 0, 1) };
}

// ---------- poses ----------
const JOINTS = ['pelvis', 'spine', 'chest', 'neck', 'head', 'shoulderL', 'shoulderR', 'elbowL', 'elbowR', 'hipL', 'hipR', 'kneeL', 'kneeR', 'ankleL', 'ankleR'];

function zeroPose() {
  const p = { y: BASE_Y, heading: Math.PI / 2, smile: 1, mouth: 0 };
  for (const j of JOINTS) p[j] = [0, 0, 0];
  p.shoulderL = [0, 0, 0.12];
  p.shoulderR = [0, 0, -0.12];
  return p;
}

function runPose(phase, amp = 1) {
  const p = zeroPose();
  const s = Math.sin(phase), c = Math.cos(phase);
  p.y = BASE_Y - 0.04 * amp + Math.abs(c) * 0.07 * amp;
  p.spine = [0.16 * amp, 0.12 * s * amp, 0];
  p.pelvis = [0, -0.12 * s * amp, 0];
  p.head = [-0.1 * amp, 0, 0];
  p.hipL = [-0.8 * s * amp, 0, 0];
  p.hipR = [0.8 * s * amp, 0, 0];
  p.kneeL = [(0.25 + Math.max(0, Math.sin(phase + 1.3)) * 1.35) * amp, 0, 0];
  p.kneeR = [(0.25 + Math.max(0, Math.sin(phase + Math.PI + 1.3)) * 1.35) * amp, 0, 0];
  p.ankleL = [-0.2 * c * amp, 0, 0];
  p.ankleR = [0.2 * c * amp, 0, 0];
  p.shoulderL = [0.75 * s * amp, 0, 0.15];
  p.shoulderR = [-0.75 * s * amp, 0, -0.15];
  p.elbowL = [-1.45 * amp, 0, 0];
  p.elbowR = [-1.45 * amp, 0, 0];
  return p;
}

function stretchPose(t) {
  // braços acima da cabeça balançando para os lados
  const p = zeroPose();
  const sway = Math.sin(t * 2.4) * 0.35;
  p.spine = [0, 0, sway * 0.6];
  p.chest = [0, 0, sway * 0.4];
  p.shoulderL = [0, 0, 2.75];
  p.shoulderR = [0, 0, -2.75];
  p.elbowL = [0, 0, 0.35];
  p.elbowR = [0, 0, -0.35];
  p.hipL = [0, 0, 0.12];
  p.hipR = [0, 0, -0.12];
  p.y = BASE_Y - 0.03;
  p.head = [0.1, 0, sway * 0.3];
  return p;
}

function celebratePose(t) {
  const p = zeroPose();
  const hop = Math.abs(Math.sin(t * 5.5));
  p.y = BASE_Y + hop * 0.45;
  p.shoulderL = [-0.2, 0, 2.5 + Math.sin(t * 11) * 0.2];
  p.shoulderR = [-0.2, 0, -2.5 - Math.sin(t * 11) * 0.2];
  p.elbowL = [0, 0, 0.3];
  p.elbowR = [0, 0, -0.3];
  const tuck = 1 - hop;
  p.hipL = [-0.5 * tuck, 0, 0.1];
  p.hipR = [-0.5 * tuck, 0, -0.1];
  p.kneeL = [0.9 * tuck, 0, 0];
  p.kneeR = [0.9 * tuck, 0, 0];
  p.head = [-0.25, 0, 0];
  p.spine = [-0.1, 0, 0];
  p.mouth = 1;
  return p;
}

function wavePose(t) {
  const p = zeroPose();
  p.heading = 0;
  p.y = BASE_Y + Math.sin(t * 2) * 0.008;
  p.shoulderR = [0, 0, -2.55];
  p.elbowR = [0, 0, -0.35 + Math.sin(t * 9) * 0.45];
  p.shoulderL = [0.15, 0, 0.55];
  p.elbowL = [-0.4, 0, -1.6];
  p.head = [0.05, 0, Math.sin(t * 1.5) * 0.08];
  p.spine = [0, 0, Math.sin(t * 1.2) * 0.03];
  p.mouth = 0.6;
  return p;
}

function mixPose(a, b, k) {
  const out = { y: lerp(a.y, b.y, k), heading: lerp(a.heading, b.heading, k), smile: lerp(a.smile, b.smile, k), mouth: lerp(a.mouth, b.mouth, k) };
  for (const j of JOINTS) out[j] = a[j].map((v, i) => lerp(v, b[j][i], k));
  return out;
}

export function poseFor(state) {
  const { cena, u, local, phase } = state;
  switch (cena.acao) {
    case 'alongar': {
      const k = ss(0.5, 0.62, u);
      return mixPose(stretchPose(local), runPose(phase, 0.45), k);
    }
    case 'correr':
      return runPose(phase, 1);
    case 'chegada': {
      const k = ss(0.42, 0.56, u);
      const p = mixPose(runPose(phase, 1 - k * 0.7), celebratePose(local), k);
      p.heading = lerp(Math.PI / 2, Math.PI / 4, ss(0.55, 0.75, u));
      return p;
    }
    case 'acenar': {
      const p = mixPose(zeroPose(), wavePose(local), ss(0, 0.12, u));
      p.heading = lerp(Math.PI / 2, 0, ss(0, 0.15, u));
      return p;
    }
    default:
      return zeroPose();
  }
}

export function applyPose(char, pose, x, t = null) {
  const J = char.joints;
  char.root.position.set(x, 0, 0);
  char.root.rotation.y = pose.heading;
  for (const j of JOINTS) J[j].rotation.set(...pose[j]);
  J.pelvis.position.y = pose.y;
  // piscada a cada ~3,2 s e boca aberta conforme a pose
  const bt = t === null ? 1 : (t % 3.2) / 0.14;
  const blink = bt < 1 ? Math.max(0.08, Math.abs(1 - 2 * bt)) : 1;
  for (const e of J.eyes) e.scale.y = blink;
  J.mouthOpen.visible = pose.mouth > 0.05;
  J.mouthOpen.scale.set(1, pose.mouth, 1);
  J.smile.visible = pose.mouth <= 0.05;
}
