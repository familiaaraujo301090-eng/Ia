// Personagem 3D procedural: corredor com uniforme azul (boné, camisa com o logo,
// short e tênis). Todo o modelo é montado com primitivas e uma hierarquia de
// juntas que as animações (animation.js) rotacionam a cada quadro.
import * as THREE from 'three';
import { logoCircleCanvas, textCanvas } from './textures.js';

const mat = (color, extra = {}) =>
  new THREE.MeshStandardMaterial({ color, roughness: 0.55, metalness: 0.0, ...extra });

function mesh(geo, material, pos = [0, 0, 0], rot = [0, 0, 0], scale = [1, 1, 1]) {
  const m = new THREE.Mesh(geo, material);
  m.position.set(...pos);
  m.rotation.set(...rot);
  m.scale.set(...scale);
  m.castShadow = true;
  m.receiveShadow = true;
  return m;
}

function joint(parent, name, pos, joints) {
  const g = new THREE.Group();
  g.name = name;
  g.position.set(...pos);
  parent.add(g);
  joints[name] = g;
  return g;
}

export function buildCharacter(cfg, logoImg) {
  const c = cfg.cores;
  const M = {
    uni: mat(c.uniforme),
    uniDark: mat(c.uniformeEscuro),
    skin: mat(c.pele, { roughness: 0.7 }),
    hair: mat(c.cabelo, { roughness: 0.9 }),
    sole: mat(c.solado),
    sock: mat(c.meia),
    black: mat('#111111', { roughness: 0.3 }),
    white: mat('#ffffff', { roughness: 0.2 }),
    green: mat('#4dd75d'),
    mouth: mat('#7a2a22'),
  };
  const logoTex = new THREE.CanvasTexture(logoCircleCanvas(logoImg, 512));
  logoTex.colorSpace = THREE.SRGBColorSpace;
  logoTex.anisotropy = 4;
  const logoMat = new THREE.MeshStandardMaterial({ map: logoTex, roughness: 0.6, transparent: true });
  const backTex = new THREE.CanvasTexture(
    textCanvas(['AMIGOS DO', 'SERGINHO'], { w: 512, h: 256, color: '#4dd75d', size: 92 })
  );
  backTex.colorSpace = THREE.SRGBColorSpace;
  const backMat = new THREE.MeshStandardMaterial({ map: backTex, transparent: true, roughness: 0.6 });

  const J = {};
  const root = new THREE.Group();
  root.name = 'personagem';

  // ---- quadril / short
  const pelvis = joint(root, 'pelvis', [0, 0.95, 0], J);
  pelvis.add(mesh(new THREE.CylinderGeometry(0.2, 0.21, 0.26, 24), M.uni, [0, 0.0, 0], [0, 0, 0], [1.1, 1, 0.8]));
  pelvis.add(mesh(new THREE.BoxGeometry(0.02, 0.2, 0.06), M.green, [0.232, -0.02, 0]));
  pelvis.add(mesh(new THREE.BoxGeometry(0.02, 0.2, 0.06), M.green, [-0.232, -0.02, 0]));
  pelvis.add(mesh(new THREE.TorusGeometry(0.205, 0.018, 8, 32), M.uniDark, [0, 0.12, 0], [Math.PI / 2, 0, 0], [1.1, 0.8, 1]));

  // ---- tronco / camisa
  const spine = joint(pelvis, 'spine', [0, 0.08, 0], J);
  const chest = joint(spine, 'chest', [0, 0.25, 0], J);
  chest.add(mesh(new THREE.CapsuleGeometry(0.2, 0.3, 8, 24), M.uni, [0, 0, 0], [0, 0, 0], [1.15, 1, 0.75]));
  // gola
  chest.add(mesh(new THREE.TorusGeometry(0.09, 0.02, 8, 24), M.uniDark, [0, 0.33, 0], [Math.PI / 2, 0, 0]));
  // logo no peito e texto nas costas
  chest.add(mesh(new THREE.CircleGeometry(0.125, 48), logoMat, [0, 0.07, 0.153]));
  const back = mesh(new THREE.PlaneGeometry(0.36, 0.18), backMat, [0, 0.1, -0.153], [0, Math.PI, 0]);
  back.castShadow = false;
  chest.add(back);

  // ---- pescoço e cabeça
  const neck = joint(chest, 'neck', [0, 0.27, 0], J);
  neck.add(mesh(new THREE.CylinderGeometry(0.07, 0.075, 0.14, 16), M.skin, [0, 0.04, 0]));
  const head = joint(neck, 'head', [0, 0.2, 0], J);
  head.add(mesh(new THREE.SphereGeometry(0.22, 32, 24), M.skin, [0, 0, 0], [0, 0, 0], [1, 1.02, 0.98]));
  head.add(mesh(new THREE.SphereGeometry(0.222, 24, 16), M.hair, [0, 0.02, -0.03], [0, 0, 0], [1.02, 1, 0.98]));
  for (const s of [-1, 1]) {
    head.add(mesh(new THREE.SphereGeometry(0.034, 16, 12), M.black, [0.075 * s, 0.015, 0.192], [0, 0, 0], [1, 1.25, 0.6]));
    head.add(mesh(new THREE.SphereGeometry(0.01, 8, 8), M.white, [0.075 * s + 0.01, 0.03, 0.212]));
    head.add(mesh(new THREE.BoxGeometry(0.07, 0.016, 0.02), M.hair, [0.078 * s, 0.075, 0.19], [0, 0, -0.12 * s]));
    head.add(mesh(new THREE.SphereGeometry(0.05, 12, 12), M.skin, [0.215 * s, -0.01, 0], [0, 0, 0], [0.6, 1, 1]));
  }
  head.add(mesh(new THREE.SphereGeometry(0.03, 12, 12), M.skin, [0, -0.035, 0.218]));
  const smile = mesh(new THREE.TorusGeometry(0.06, 0.013, 8, 20, Math.PI), M.mouth, [0, -0.07, 0.196], [0, 0, Math.PI]);
  head.add(smile);
  J.smile = smile;

  // boné
  const cap = new THREE.Group();
  cap.position.set(0, 0.03, 0);
  cap.rotation.x = -0.12;
  head.add(cap);
  cap.add(mesh(new THREE.SphereGeometry(0.235, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2), M.uni));
  cap.add(mesh(new THREE.CylinderGeometry(0.235, 0.235, 0.05, 32, 1, true), M.uniDark, [0, 0.0, 0]));
  cap.add(mesh(new THREE.CylinderGeometry(0.24, 0.24, 0.018, 32, 1, false, -Math.PI / 2, Math.PI), M.uni, [0, 0.0, 0.07], [0.12, 0, 0], [1, 1, 1.25]));
  cap.add(mesh(new THREE.SphereGeometry(0.025, 12, 8), M.uniDark, [0, 0.235, 0]));
  cap.add(mesh(new THREE.CircleGeometry(0.075, 32), logoMat, [0, 0.12, 0.2], [-0.62, 0, 0]));

  // ---- braços
  for (const [side, s] of [['L', 1], ['R', -1]]) {
    const sh = joint(chest, 'shoulder' + side, [0.25 * s, 0.2, 0], J);
    sh.add(mesh(new THREE.SphereGeometry(0.082, 16, 12), M.uni));
    sh.add(mesh(new THREE.CylinderGeometry(0.09, 0.08, 0.17, 16), M.uni, [0, -0.07, 0]));
    sh.add(mesh(new THREE.TorusGeometry(0.08, 0.012, 6, 16), M.uniDark, [0, -0.155, 0], [Math.PI / 2, 0, 0]));
    sh.add(mesh(new THREE.CapsuleGeometry(0.058, 0.16, 6, 12), M.skin, [0, -0.15, 0]));
    const el = joint(sh, 'elbow' + side, [0, -0.28, 0], J);
    el.add(mesh(new THREE.CapsuleGeometry(0.052, 0.16, 6, 12), M.skin, [0, -0.11, 0]));
    el.add(mesh(new THREE.CylinderGeometry(0.058, 0.058, 0.05, 12), M.green, [0, -0.2, 0]));
    el.add(mesh(new THREE.SphereGeometry(0.068, 14, 12), M.skin, [0, -0.27, 0], [0, 0, 0], [0.9, 1.1, 0.8]));
  }

  // ---- pernas
  for (const [side, s] of [['L', 1], ['R', -1]]) {
    const hip = joint(pelvis, 'hip' + side, [0.11 * s, -0.05, 0], J);
    hip.add(mesh(new THREE.CylinderGeometry(0.11, 0.1, 0.22, 16), M.uni, [0, -0.09, 0]));
    hip.add(mesh(new THREE.CapsuleGeometry(0.075, 0.28, 6, 12), M.skin, [0, -0.24, 0]));
    const knee = joint(hip, 'knee' + side, [0, -0.44, 0], J);
    knee.add(mesh(new THREE.CapsuleGeometry(0.064, 0.3, 6, 12), M.skin, [0, -0.2, 0]));
    const ankle = joint(knee, 'ankle' + side, [0, -0.44, 0], J);
    ankle.add(mesh(new THREE.CylinderGeometry(0.066, 0.066, 0.09, 12), M.sock, [0, 0.05, 0]));
    // tênis azul com solado branco e cadarço verde
    ankle.add(mesh(new THREE.CapsuleGeometry(0.075, 0.17, 6, 14), M.uni, [0, -0.035, 0.06], [Math.PI / 2, 0, 0], [1, 1, 0.85]));
    ankle.add(mesh(new THREE.BoxGeometry(0.16, 0.04, 0.33), M.sole, [0, -0.1, 0.06]));
    ankle.add(mesh(new THREE.BoxGeometry(0.07, 0.012, 0.1), M.green, [0, 0.03, 0.1], [-0.35, 0, 0]));
  }

  return { root, joints: J };
}
