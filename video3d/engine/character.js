// Personagem 3D procedural: corredor com uniforme azul (boné, camisa com o logo,
// short e tênis). O modelo é montado com primitivas e superfícies de revolução
// numa hierarquia de juntas que as animações (animation.js) rotacionam a cada quadro.
import * as THREE from 'three';
import { logoCircleCanvas, FONT } from './textures.js';

const fabric = (color) =>
  new THREE.MeshPhysicalMaterial({ color, roughness: 0.72, sheen: 0.8, sheenRoughness: 0.5, sheenColor: new THREE.Color('#9fb8ff') });
const mat = (color, extra = {}) => new THREE.MeshStandardMaterial({ color, roughness: 0.55, ...extra });

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

// Superfície de revolução com perfil r(y) amostrado uniformemente em y, para que a
// coordenada v da textura seja linear na altura (facilita posicionar o logo).
function lathe(y0, y1, rOf, steps = 40, segs = 48) {
  const pts = [];
  for (let i = 0; i <= steps; i++) {
    const y = y0 + ((y1 - y0) * i) / steps;
    pts.push(new THREE.Vector2(Math.max(0.0005, rOf(y)), y));
  }
  // phiStart = PI: a emenda fica nas costas e u = 0.5 é a frente (+z)
  return new THREE.LatheGeometry(pts, segs, Math.PI, Math.PI * 2);
}

// Textura da camisa: azul com vivos verdes nas laterais, logo no peito e nome nas costas.
function shirtCanvas(logoImg, c, { y0, y1, logoY, logoD, perim }) {
  const W = 2048, H = 1024;
  const cv = document.createElement('canvas');
  cv.width = W;
  cv.height = H;
  const g = cv.getContext('2d');
  g.fillStyle = c.uniforme;
  g.fillRect(0, 0, W, H);
  // leve degradê de tecido
  const gr = g.createLinearGradient(0, 0, 0, H);
  gr.addColorStop(0, 'rgba(255,255,255,0.06)');
  gr.addColorStop(1, 'rgba(0,0,0,0.12)');
  g.fillStyle = gr;
  g.fillRect(0, 0, W, H);
  // vivos laterais
  g.fillStyle = '#4dd75d';
  for (const u of [0.25, 0.75]) g.fillRect(u * W - 14, 0, 28, H);
  // barra
  g.fillStyle = c.uniformeEscuro;
  g.fillRect(0, H - 40, W, 40);
  const vy = (y) => H - ((y - y0) / (y1 - y0)) * H; // v=0 embaixo
  const pw = (logoD / perim) * W, ph = (logoD / (y1 - y0)) * H;
  g.drawImage(logoCircleCanvas(logoImg, 512), W / 2 - pw / 2, vy(logoY) - ph / 2, pw, ph);
  // nome nas costas (u = 0 e u = 1 são o mesmo ponto)
  g.fillStyle = '#4dd75d';
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  for (const x of [0, W]) {
    g.save();
    g.translate(x, vy(0.1));
    g.scale(1, 1.7);
    g.font = `bold 64px ${FONT}`;
    g.fillText('AMIGOS DO', 0, -40);
    g.fillText('SERGINHO', 0, 40);
    g.restore();
  }
  return cv;
}

// Contorno "toon": casca de cada malha, empurrada pelas normais e vista por dentro.
function addOutline(root, espessura = 0.0065) {
  const m = new THREE.MeshBasicMaterial({ color: '#0e1430', side: THREE.BackSide });
  m.onBeforeCompile = (sh) => {
    sh.vertexShader = sh.vertexShader.replace('#include <begin_vertex>', `vec3 transformed = position + normal * ${espessura.toFixed(4)};`);
  };
  const alvos = [];
  root.traverse((o) => {
    let p = o, livre = false;
    while (p) {
      if (p.userData.semContorno) livre = true;
      p = p.parent;
    }
    if (o.isMesh && !livre && !o.material.transparent && o.geometry.attributes.normal) alvos.push(o);
  });
  for (const o of alvos) {
    o.geometry.computeBoundingSphere();
    if (o.geometry.boundingSphere.radius < 0.035) continue;
    const casca = new THREE.Mesh(o.geometry, m);
    casca.castShadow = false;
    casca.userData.contorno = true;
    o.add(casca);
  }
}

export function buildCharacter(cfg, logoImg) {
  const c = cfg.cores;
  const M = {
    uni: fabric(c.uniforme),
    uniDark: fabric(c.uniformeEscuro),
    skin: new THREE.MeshPhysicalMaterial({ color: c.pele, roughness: 0.6, sheen: 0.3, sheenColor: new THREE.Color('#ffd0b0'), emissive: new THREE.Color(c.pele), emissiveIntensity: 0.14 }),
    hair: mat(c.cabelo, { roughness: 0.85 }),
    sole: mat(c.solado, { roughness: 0.6 }),
    sock: fabric(c.meia),
    white: mat('#ffffff', { roughness: 0.15 }),
    iris: mat('#5a3418', { roughness: 0.2 }),
    pupil: mat('#0b0b0b', { roughness: 0.1 }),
    green: fabric('#4dd75d'),
    mouth: mat('#5e1d1a', { roughness: 0.6 }),
    tongue: mat('#d0605a'),
    blush: new THREE.MeshStandardMaterial({ color: '#ff8a7a', transparent: true, opacity: 0.35, roughness: 0.8 }),
    brow: mat('#2b1a10', { roughness: 0.9 }),
  };
  const logoTex = new THREE.CanvasTexture(logoCircleCanvas(logoImg, 512));
  logoTex.colorSpace = THREE.SRGBColorSpace;
  const logoMat = new THREE.MeshStandardMaterial({ map: logoTex, roughness: 0.6, transparent: true });

  const J = {};
  const root = new THREE.Group();
  root.name = 'personagem';

  // ---- quadril / short
  const pelvis = joint(root, 'pelvis', [0, 1.05, 0], J);
  const shorts = lathe(-0.14, 0.14, (y) => 0.205 + 0.02 * Math.cos((y / 0.14) * 1.4) - (y > 0.1 ? (y - 0.1) * 0.6 : 0), 16, 40);
  pelvis.add(mesh(shorts, M.uni, [0, 0, 0], [0, 0, 0], [1.12, 1, 0.8]));
  pelvis.add(mesh(new THREE.TorusGeometry(0.2, 0.02, 8, 40), M.uniDark, [0, 0.13, 0], [Math.PI / 2, 0, 0], [1.12, 0.8, 1]));
  // cordão do short
  pelvis.add(mesh(new THREE.CapsuleGeometry(0.008, 0.06, 4, 6), M.white, [0.025, 0.08, 0.165], [0, 0, 0.2]));
  pelvis.add(mesh(new THREE.CapsuleGeometry(0.008, 0.06, 4, 6), M.white, [-0.025, 0.08, 0.165], [0, 0, -0.2]));

  // ---- tronco / camisa (textura com logo)
  const spine = joint(pelvis, 'spine', [0, 0.08, 0], J);
  const chest = joint(spine, 'chest', [0, 0.25, 0], J);
  const ty0 = -0.37, ty1 = 0.37;
  const torsoR = (y) => {
    const k = (y - ty0) / (ty1 - ty0);
    let r = 0.2 + 0.012 * Math.sin(k * Math.PI) + 0.05 * THREE.MathUtils.smoothstep(k, 0.45, 0.82);
    if (k > 0.82) r *= Math.sqrt(Math.max(0, 1 - ((k - 0.82) / 0.18) ** 2)) * 0.55 + 0.45 * (1 - (k - 0.82) / 0.18);
    return r;
  };
  const sz = 0.72;
  const shirtTex = new THREE.CanvasTexture(
    shirtCanvas(logoImg, c, { y0: ty0, y1: ty1, logoY: 0.08, logoD: 0.25, perim: 2 * Math.PI * Math.sqrt((0.24 ** 2 + (0.24 * sz) ** 2) / 2) })
  );
  shirtTex.colorSpace = THREE.SRGBColorSpace;
  shirtTex.anisotropy = 8;
  const shirtMat = fabric('#ffffff');
  shirtMat.map = shirtTex;
  chest.add(mesh(lathe(ty0, ty1, torsoR), shirtMat, [0, 0, 0], [0, 0, 0], [1.1, 1, sz]));
  chest.add(mesh(new THREE.TorusGeometry(0.085, 0.022, 8, 24), M.uniDark, [0, 0.355, 0.0], [Math.PI / 2 - 0.15, 0, 0], [1, 0.9, 1]));

  // ---- pescoço e cabeça
  const neck = joint(chest, 'neck', [0, 0.29, 0], J);
  neck.add(mesh(new THREE.CylinderGeometry(0.065, 0.075, 0.16, 16), M.skin, [0, 0.04, 0]));
  const head = joint(neck, 'head', [0, 0.22, 0], J);
  head.scale.set(1.12, 1.26, 1.12);
  // rosto num grupo próprio, sem contorno, para um acabamento limpo
  const face = new THREE.Group();
  face.userData.semContorno = true;
  head.add(face);
  face.add(mesh(new THREE.SphereGeometry(0.22, 48, 36), M.skin, [0, 0.01, 0], [0, 0, 0], [1, 1.02, 0.97]));
  // cabelo: nuca e costeletas aparecendo por baixo do boné
  face.add(mesh(new THREE.SphereGeometry(0.226, 32, 20, 0, Math.PI * 2, 0, Math.PI * 0.62), M.hair, [0, 0.03, -0.035], [-0.5, 0, 0]));

  // olhos grandes, olhando para frente, com dois brilhos e linha de cílios
  J.eyes = [];
  J.brows = [];
  for (const s of [-1, 1]) {
    const eye = new THREE.Group();
    eye.position.set(0.074 * s, 0.026, 0);
    face.add(eye);
    eye.add(mesh(new THREE.SphereGeometry(0.05, 28, 20), M.white, [0, 0, 0.186], [0, 0, 0], [0.9, 1.15, 0.5]));
    eye.add(mesh(new THREE.SphereGeometry(0.034, 24, 16), M.iris, [0, -0.004, 0.2012], [0, 0, 0], [1, 1.08, 0.35]));
    eye.add(mesh(new THREE.SphereGeometry(0.018, 16, 12), M.pupil, [0, -0.004, 0.2075], [0, 0, 0], [1, 1.08, 0.35]));
    eye.add(mesh(new THREE.SphereGeometry(0.0075, 10, 8), M.white, [0.011, 0.01, 0.2135]));
    eye.add(mesh(new THREE.SphereGeometry(0.004, 8, 6), M.white, [-0.009, -0.016, 0.2128]));
    // linha superior de cílios (arco grosso sobre o olho)
    eye.add(mesh(new THREE.TorusGeometry(0.046, 0.0055, 6, 24, Math.PI * 0.92), M.pupil, [0, 0.002, 0.2], [-0.12, 0, Math.PI * 0.04], [0.98, 1.2, 1]));
    J.eyes.push(eye);
    // sobrancelha grossa e arqueada (sobe na comemoração)
    const brow = mesh(new THREE.TorusGeometry(0.05, 0.011, 8, 18, Math.PI * 0.55), M.brow, [0.076 * s, 0.1, 0.188], [-0.15, 0, Math.PI * 0.225], [1, 0.7, 1]);
    brow.userData.y0 = 0.1;
    face.add(brow);
    J.brows.push(brow);
    // bochechas rosadas e orelhas
    face.add(mesh(new THREE.CircleGeometry(0.03, 20), M.blush, [0.125 * s, -0.045, 0.176], [0.15, 0.6 * s, 0]));
    face.add(mesh(new THREE.SphereGeometry(0.05, 14, 12), M.skin, [0.214 * s, -0.005, 0.0], [0, 0, 0], [0.45, 0.95, 0.75]));
    face.add(mesh(new THREE.TorusGeometry(0.024, 0.008, 6, 12), M.skin, [0.232 * s, -0.005, 0.005], [0, Math.PI / 2, 0]));
  }
  // nariz pequeno
  face.add(mesh(new THREE.SphereGeometry(0.024, 16, 12), M.skin, [0, -0.028, 0.212], [0, 0, 0], [1.15, 0.85, 0.9]));
  // boca sorridente: formato "D" com dentes e língua; abre mais na comemoração
  const bocaShape = new THREE.Shape();
  bocaShape.moveTo(-0.046, 0);
  bocaShape.quadraticCurveTo(0, 0.01, 0.046, 0);
  bocaShape.bezierCurveTo(0.044, -0.05, -0.044, -0.05, -0.046, 0);
  const dentes = new THREE.Shape();
  dentes.moveTo(-0.04, -0.001);
  dentes.quadraticCurveTo(0, 0.0085, 0.04, -0.001);
  dentes.quadraticCurveTo(0.036, -0.013, 0.03, -0.014);
  dentes.quadraticCurveTo(0, -0.008, -0.03, -0.014);
  dentes.quadraticCurveTo(-0.036, -0.013, -0.04, -0.001);
  const open = new THREE.Group();
  open.position.set(0, -0.084, 0.1995);
  open.rotation.x = 0.42;
  face.add(open);
  open.add(mesh(new THREE.ShapeGeometry(bocaShape, 16), M.mouth));
  open.add(mesh(new THREE.ShapeGeometry(dentes, 12), M.white, [0, 0, 0.0008]));
  open.add(mesh(new THREE.CircleGeometry(0.02, 16), M.tongue, [0, -0.028, 0.0006], [0, 0, 0], [1.2, 0.55, 1]));
  // cantinhos da boca (covinhas)
  for (const s of [-1, 1]) face.add(mesh(new THREE.TorusGeometry(0.008, 0.0028, 6, 10, Math.PI), M.mouth, [0.05 * s, -0.082, 0.195], [0.4, 0.25 * s, s > 0 ? -1.2 : Math.PI + 1.2]));
  const smile = new THREE.Group();
  J.smile = smile;
  J.mouthOpen = open;

  // boné
  const cap = new THREE.Group();
  cap.position.set(0, 0.118, -0.02);
  cap.rotation.x = -0.42;
  cap.scale.setScalar(0.97);
  head.add(cap);
  cap.add(mesh(new THREE.SphereGeometry(0.236, 40, 20, 0, Math.PI * 2, 0, Math.PI / 2), M.uni, [0, 0, 0], [0, 0, 0], [1, 1.05, 1.03]));
  for (let i = 0; i < 6; i++) {
    const a = (i / 6) * Math.PI * 2;
    cap.add(mesh(new THREE.TorusGeometry(0.236, 0.004, 4, 24, Math.PI / 2), M.uniDark, [0, 0, 0], [0, a, Math.PI / 2], [1.03, 1.05, 1]));
  }
  cap.add(mesh(new THREE.CylinderGeometry(0.238, 0.238, 0.045, 40, 1, true), M.uniDark, [0, 0.01, 0], [0, 0, 0], [1, 1, 1.03]));
  const brim = new THREE.Group();
  brim.position.set(0, 0.005, 0.12);
  brim.rotation.x = 0.16;
  cap.add(brim);
  brim.add(mesh(new THREE.CylinderGeometry(0.235, 0.235, 0.016, 40, 1, false, -Math.PI / 2, Math.PI), M.uni, [0, 0.002, 0], [0, 0, 0], [1, 1, 1.0]));
  brim.add(mesh(new THREE.CylinderGeometry(0.232, 0.232, 0.006, 40, 1, false, -Math.PI / 2, Math.PI), M.green, [0, -0.008, 0], [0, 0, 0], [1, 1, 0.98]));
  cap.add(mesh(new THREE.SphereGeometry(0.026, 12, 8), M.green, [0, 0.247, 0]));
  cap.add(mesh(new THREE.CircleGeometry(0.08, 40), logoMat, [0, 0.125, 0.205], [-0.58, 0, 0]));

  // ---- braços
  for (const [side, s] of [['L', 1], ['R', -1]]) {
    const sh = joint(chest, 'shoulder' + side, [0.255 * s, 0.2, 0], J);
    sh.add(mesh(new THREE.SphereGeometry(0.09, 20, 14), M.uni, [0, -0.01, 0], [0, 0, 0], [1, 1, 0.95]));
    sh.add(mesh(lathe(-0.17, 0.0, (y) => 0.088 - y * -0.06, 6, 24), M.uni));
    sh.add(mesh(new THREE.TorusGeometry(0.096, 0.012, 6, 20), M.green, [0, -0.168, 0], [Math.PI / 2, 0, 0]));
    sh.add(mesh(new THREE.CylinderGeometry(0.064, 0.056, 0.2, 14), M.skin, [0, -0.17, 0]));
    const el = joint(sh, 'elbow' + side, [0, -0.28, 0], J);
    el.add(mesh(new THREE.SphereGeometry(0.057, 14, 10), M.skin));
    el.add(mesh(new THREE.CylinderGeometry(0.055, 0.045, 0.2, 14), M.skin, [0, -0.1, 0]));
    if (s > 0) {
      // relógio esportivo no pulso esquerdo
      el.add(mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.04, 14), mat('#111111', { roughness: 0.4 }), [0, -0.19, 0]));
      el.add(mesh(new THREE.BoxGeometry(0.05, 0.045, 0.02), mat('#1e2a3a', { roughness: 0.1, metalness: 0.6 }), [0, -0.19, 0.05]));
      el.add(mesh(new THREE.BoxGeometry(0.036, 0.03, 0.005), mat('#4dd75d', { emissive: '#4dd75d', emissiveIntensity: 0.6 }), [0, -0.19, 0.061]));
    } else el.add(mesh(new THREE.CylinderGeometry(0.052, 0.052, 0.05, 14), M.green, [0, -0.19, 0]));
    // mão fechada com polegar
    const hand = new THREE.Group();
    hand.position.set(0, -0.26, 0);
    el.add(hand);
    hand.add(mesh(new THREE.SphereGeometry(0.06, 16, 12), M.skin, [0, 0, 0.005], [0, 0, 0], [0.85, 1.05, 0.9]));
    hand.add(mesh(new THREE.CapsuleGeometry(0.018, 0.04, 4, 8), M.skin, [-0.03 * s, 0.01, 0.04], [0.4, 0, 0.5 * s]));
    for (let f = 0; f < 4; f++) hand.add(mesh(new THREE.SphereGeometry(0.02, 8, 6), M.skin, [(f - 1.5) * 0.024 * s * 0.5, -0.045, 0.035 - f * 0.002]));
  }

  // ---- pernas
  for (const [side, s] of [['L', 1], ['R', -1]]) {
    const hip = joint(pelvis, 'hip' + side, [0.11 * s, -0.05, 0], J);
    hip.add(mesh(new THREE.CylinderGeometry(0.11, 0.115, 0.22, 20, 1, true), M.uni, [0, -0.09, 0]));
    hip.add(mesh(new THREE.TorusGeometry(0.113, 0.012, 6, 20), M.green, [0, -0.2, 0], [Math.PI / 2, 0, 0]));
    hip.add(mesh(new THREE.CylinderGeometry(0.088, 0.068, 0.36, 16), M.skin, [0, -0.25, 0]));
    const knee = joint(hip, 'knee' + side, [0, -0.44, 0], J);
    knee.add(mesh(new THREE.SphereGeometry(0.069, 14, 10), M.skin));
    // panturrilha com volume
    knee.add(mesh(lathe(-0.42, 0, (y) => 0.05 + 0.022 * Math.sin(((y + 0.42) / 0.42) * Math.PI) ** 1.5 + (y > -0.05 ? 0.015 : 0), 14, 18), M.skin));
    const ankle = joint(knee, 'ankle' + side, [0, -0.44, 0], J);
    ankle.add(mesh(new THREE.CylinderGeometry(0.058, 0.055, 0.12, 14), M.sock, [0, 0.05, 0]));
    ankle.add(mesh(new THREE.TorusGeometry(0.058, 0.008, 6, 14), M.green, [0, 0.085, 0], [Math.PI / 2, 0, 0]));
    // tênis: cabedal azul, biqueira, calcanhar, solado branco, cadarços e faixa verde
    ankle.add(mesh(new THREE.CapsuleGeometry(0.072, 0.16, 8, 16), M.uni, [0, -0.04, 0.055], [Math.PI / 2, 0, 0], [1, 1, 0.8]));
    ankle.add(mesh(new THREE.SphereGeometry(0.07, 16, 10), M.uniDark, [0, -0.06, 0.16], [0, 0, 0], [1, 0.6, 0.9]));
    ankle.add(mesh(new THREE.SphereGeometry(0.068, 14, 10), M.uniDark, [0, -0.03, -0.06], [0, 0, 0], [1, 1, 0.7]));
    ankle.add(mesh(new THREE.CapsuleGeometry(0.075, 0.2, 6, 16), M.sole, [0, -0.105, 0.055], [Math.PI / 2, 0, 0], [1.05, 1, 0.3]));
    for (let k = 0; k < 3; k++) ankle.add(mesh(new THREE.BoxGeometry(0.075, 0.01, 0.014), M.white, [0, 0.012 - k * 0.022, 0.09 + k * 0.03], [-0.6, 0, 0]));
    for (const q of [-1, 1]) ankle.add(mesh(new THREE.BoxGeometry(0.004, 0.022, 0.14), M.green, [0.071 * q, -0.06, 0.06], [-0.25, 0, 0]));
  }

  addOutline(root);
  return { root, joints: J };
}
