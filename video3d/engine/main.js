// Motor de render: monta cena, personagem, cenário e linha do tempo a partir do
// roteiro e expõe window.setup / window.frame / window.sheet para o render.js.
import * as THREE from 'three';
import { buildCharacter } from './character.js';
import { buildModelCharacter } from './modelCharacter.js';
import { buildEnvironment, buildSky } from './environment.js';
import { buildTimeline, poseFor, applyPose } from './animation.js';
import { cameraFor } from './camera.js';
import { makeOverlay } from './overlay.js';
import { buildSheets } from './sheets.js';

function loadImage(src) {
  return new Promise((res, rej) => {
    const i = new Image();
    i.onload = () => res(i);
    i.onerror = rej;
    i.src = src;
  });
}

const E = {};
window.E = E;

window.setup = async (roteiro) => {
  await document.fonts.ready;
  const { largura: W, altura: H } = roteiro.formato;
  const logo = await loadImage('/' + roteiro.personagem.logo);

  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(1);
  renderer.setSize(W, H);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;

  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog(roteiro.cenario.ceu.horizonte, 60, 420);
  const sky = buildSky(roteiro.cenario);
  scene.add(sky);

  const hemi = new THREE.HemisphereLight('#cfe6ff', '#5a7a3a', 1.1);
  scene.add(hemi);
  const sun = new THREE.DirectionalLight('#fff1d6', 2.6);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  const sc = sun.shadow.camera;
  sc.left = sc.bottom = -14;
  sc.right = sc.top = 14;
  sc.near = 1;
  sc.far = 80;
  sun.shadow.bias = -0.0005;
  sun.shadow.normalBias = 0.02;
  scene.add(sun, sun.target);

  const timeline = buildTimeline(roteiro);
  // trechos onde a câmera gira em volta do corredor: sem carros/árvores na frente da lente
  const livres = timeline.cenas
    .filter((c) => ['orbita', 'baixa', 'drone', 'grua', 'aproximar'].includes(c.camera.tipo))
    .map((c) => [timeline.at(c.inicio).x - 9, timeline.at(c.fim - 0.001).x + 9]);
  const env = buildEnvironment(roteiro.cenario, logo, timeline.finishX, livres);
  scene.add(env.group);
  const char = roteiro.personagem.modelo ? await buildModelCharacter(roteiro.personagem, logo) : buildCharacter(roteiro.personagem, logo);
  scene.add(char.root);
  // amigos que entram no grupo ao longo da história (clones do modelo, cena.amigos = quantos)
  const amigos = [];
  const maxAmigos = Math.max(0, ...timeline.cenas.map((c) => c.amigos || 0));
  if (char.clonar && maxAmigos) {
    const paleta = roteiro.personagem.coresAmigos || [roteiro.personagem.modelo.cores || {}];
    for (let i = 0; i < maxAmigos; i++) {
      const a = char.clonar(paleta[i % paleta.length]);
      a.root.visible = false;
      scene.add(a.root);
      amigos.push(a);
    }
  }

  const camera = new THREE.PerspectiveCamera(50, W / H, 0.1, 2000);
  const out = document.createElement('canvas');
  out.width = W;
  out.height = H;
  const overlay = makeOverlay(logo);

  Object.assign(E, { THREE, renderer, scene, sky, sun, hemi, timeline, env, char, amigos, camera, out, overlay, logo, roteiro, W, H });
  E.sheets = buildSheets(E);
  return { total: timeline.total, finishX: timeline.finishX, cenas: timeline.cenas.map((c) => [c.id, c.inicio, c.fim]) };
};

// formação do grupo atrás/ao lado do corredor principal (x = atrás, z = lado)
const FORMACAO = [[-1.4, 1.5], [-1.4, -1.5], [-2.9, 0], [-2.9, 2.6], [-2.9, -2.6], [-4.4, 1.3], [-4.4, -1.3], [-5.9, 2.4], [-5.9, -2.4], [-5.9, 0], [-7.4, 1.3], [-7.4, -1.3]];

function posarAmigos(st, p, t) {
  const n = st.cena.amigos || 0;
  const antes = st.index > 0 ? E.timeline.cenas[st.index - 1].amigos || 0 : 0;
  E.amigos.forEach((a, i) => {
    a.root.visible = i < n;
    if (i >= n) return;
    const [fx, fz] = FORMACAO[i % FORMACAO.length];
    // quem acabou de entrar chega correndo de trás no primeiro segundo da cena
    const chegando = i >= antes ? 1 - THREE.MathUtils.smoothstep(st.local, 0, 1.2) : 0;
    const q = { ...p, phase: p.phase + i * 0.7, local: p.local + i * 0.3 };
    applyPose(a, q, st.x + fx - chegando * 10, t);
    a.root.position.z = fz;
  });
}

// Posiciona tudo no instante t (sem desenhar).
export function pose(t) {
  const st = E.timeline.at(t);
  const p = poseFor(st);
  applyPose(E.char, p, st.x, t);
  posarAmigos(st, p, t);
  E.env.update(t, st.x);
  E.sun.position.set(st.x - 12, 22, 14);
  E.sun.target.position.set(st.x, 0, 0);
  E.sky.position.set(st.x, 0, 0);
  const cam = cameraFor(st.cena, st.u, st.x, t);
  // "punch-in": cada cena começa um pouco mais aberta e fecha rápido
  E.camera.fov = cam.fov * (1 + 0.18 * Math.exp(-st.local / 0.12));
  E.camera.position.copy(cam.pos);
  E.camera.lookAt(cam.look);
  return st;
}
E.pose = pose;

export function renderComposite(t, W = E.W, H = E.H) {
  const st = pose(t);
  E.renderer.setSize(W, H);
  E.camera.aspect = W / H;
  E.camera.updateProjectionMatrix();
  E.renderer.render(E.scene, E.camera);
  const out = W === E.out.width && H === E.out.height ? E.out : Object.assign(document.createElement('canvas'), { width: W, height: H });
  const g = out.getContext('2d');
  g.drawImage(E.renderer.domElement, 0, 0);
  E.overlay(g, W, H, st, E.timeline.total, t);
  return out;
}
E.renderComposite = renderComposite;

window.frame = (t, quality = 0.92) => renderComposite(t).toDataURL('image/jpeg', quality);
window.sheet = (name) => E.sheets[name]().toDataURL('image/png');
window.ready = true;
