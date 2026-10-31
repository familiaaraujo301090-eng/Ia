// Motor de render: monta cena, personagem, cenário e linha do tempo a partir do
// roteiro e expõe window.setup / window.frame / window.sheet para o render.js.
import * as THREE from 'three';
import { buildCharacter } from './character.js';
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
  const env = buildEnvironment(roteiro.cenario, logo, timeline.finishX);
  scene.add(env.group);
  const char = buildCharacter(roteiro.personagem, logo);
  scene.add(char.root);

  const camera = new THREE.PerspectiveCamera(50, W / H, 0.1, 2000);
  const out = document.createElement('canvas');
  out.width = W;
  out.height = H;
  const overlay = makeOverlay(logo);

  Object.assign(E, { THREE, renderer, scene, sky, sun, hemi, timeline, env, char, camera, out, overlay, logo, roteiro, W, H });
  E.sheets = buildSheets(E);
  return { total: timeline.total, finishX: timeline.finishX, cenas: timeline.cenas.map((c) => [c.id, c.inicio, c.fim]) };
};

// Posiciona tudo no instante t (sem desenhar).
export function pose(t) {
  const st = E.timeline.at(t);
  applyPose(E.char, poseFor(st), st.x, t);
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
