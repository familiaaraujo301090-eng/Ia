// Cenário procedural: rua de cidade do interior (Buri - SP) com casas coloridas,
// árvores, postes, faixas da equipe, morros, nuvens, céu em degradê e o pórtico
// de chegada. Tudo determinístico (semente fixa) para renderizar igual sempre.
import * as THREE from 'three';
import { bannerCanvas, roadCanvas, textCanvas } from './textures.js';

function rng(seed) {
  let s = seed % 2147483647;
  return () => ((s = (s * 16807) % 2147483647) - 1) / 2147483646;
}

const std = (color, extra = {}) => new THREE.MeshStandardMaterial({ color, roughness: 0.85, ...extra });

function add(parent, geo, material, pos, rot = [0, 0, 0], shadow = true) {
  const m = new THREE.Mesh(geo, material);
  m.position.set(...pos);
  m.rotation.set(...rot);
  m.castShadow = shadow;
  m.receiveShadow = true;
  parent.add(m);
  return m;
}

function canvasTex(c) {
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 4;
  return t;
}

export function buildSky(cfg) {
  const geo = new THREE.SphereGeometry(900, 32, 16);
  const m = new THREE.ShaderMaterial({
    side: THREE.BackSide,
    depthWrite: false,
    fog: false,
    uniforms: {
      top: { value: new THREE.Color(cfg.ceu.topo) },
      bottom: { value: new THREE.Color(cfg.ceu.horizonte) },
    },
    vertexShader: `varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
    fragmentShader: `uniform vec3 top; uniform vec3 bottom; varying vec3 vP;
      void main(){ float h = clamp(vP.y*1.6+0.05,0.0,1.0); gl_FragColor = vec4(mix(bottom, top, pow(h,0.7)),1.0); }`,
  });
  return new THREE.Mesh(geo, m);
}

export function buildEnvironment(cfg, logoImg, finishX) {
  const R = rng(20261031);
  const env = new THREE.Group();
  env.name = 'cenario';
  const X0 = -80, X1 = finishX + 120, L = X1 - X0, XC = (X0 + X1) / 2;

  // chão
  add(env, new THREE.PlaneGeometry(L + 600, 700), std('#6fae4a'), [XC, -0.06, 0], [-Math.PI / 2, 0, 0], false);
  const roadTex = canvasTex(roadCanvas());
  roadTex.wrapS = roadTex.wrapT = THREE.RepeatWrapping;
  roadTex.repeat.set(L / 8, 1);
  add(env, new THREE.PlaneGeometry(L, 8), std('#ffffff', { map: roadTex, roughness: 0.95 }), [XC, 0.015, 0], [-Math.PI / 2, 0, 0], false);
  const white = std('#f4f4f4');
  const yellow = std('#f2c230');
  for (let x = X0; x < X1; x += 4) add(env, new THREE.BoxGeometry(2, 0.01, 0.14), yellow, [x, 0.03, 0], [0, 0, 0], false);
  for (const z of [-3.8, 3.8]) add(env, new THREE.BoxGeometry(L, 0.01, 0.12), white, [XC, 0.03, z], [0, 0, 0], false);
  // calçadas e meio-fio
  for (const s of [-1, 1]) {
    add(env, new THREE.BoxGeometry(L, 0.16, 2.4), std('#c9c2b6'), [XC, 0.08, s * 5.2], [0, 0, 0], false);
    add(env, new THREE.BoxGeometry(L, 0.18, 0.15), std('#e8e4dc'), [XC, 0.09, s * 4.05], [0, 0, 0], false);
  }

  // casas coloridas
  const houseColors = ['#f4d35e', '#ee964b', '#f95738', '#7bc8a4', '#a8dadc', '#f7b2bd', '#ffffff', '#c3a6e0', '#90be6d'];
  const roof = std('#b5532f');
  const doorM = std('#6b3e26');
  const winM = std('#bfe3ff', { roughness: 0.2, metalness: 0.1 });
  for (const s of [-1, 1]) {
    let x = X0 + R() * 6;
    while (x < X1) {
      const w = 5 + R() * 4, h = 3 + R() * 2.2, d = 5 + R() * 2;
      const z = s * (10 + R() * 1.5 + d / 2);
      const g = new THREE.Group();
      g.position.set(x + w / 2, 0, z);
      env.add(g);
      add(g, new THREE.BoxGeometry(w, h, d), std(houseColors[Math.floor(R() * houseColors.length)]), [0, h / 2, 0]);
      const r = add(g, new THREE.ConeGeometry(Math.hypot(w, d) / 2 * 1.05, 1.8, 4), roof, [0, h + 0.9, 0], [0, Math.PI / 4, 0]);
      r.scale.set(1, 1, d / w);
      const front = -s * (d / 2 + 0.02);
      add(g, new THREE.BoxGeometry(1, 2, 0.06), doorM, [-w * 0.15, 1, front], [0, 0, 0], false);
      add(g, new THREE.BoxGeometry(1.1, 0.9, 0.06), winM, [w * 0.22, h * 0.55, front], [0, 0, 0], false);
      x += w + 1.5 + R() * 4;
    }
  }

  // árvores
  const trunk = std('#7a5230');
  const leafs = [std('#3f8f3a'), std('#2f7a34'), std('#5aa547')];
  const tree = (x, z, sc) => {
    const g = new THREE.Group();
    g.position.set(x, 0, z);
    g.scale.setScalar(sc);
    env.add(g);
    add(g, new THREE.CylinderGeometry(0.18, 0.25, 2.2, 8), trunk, [0, 1.1, 0]);
    const lm = leafs[Math.floor(R() * leafs.length)];
    add(g, new THREE.IcosahedronGeometry(1.4, 1), lm, [0, 2.9, 0]);
    add(g, new THREE.IcosahedronGeometry(1.0, 1), lm, [0.7, 2.5, 0.3]);
    add(g, new THREE.IcosahedronGeometry(0.9, 1), lm, [-0.6, 2.6, -0.3]);
  };
  for (let x = X0; x < X1; x += 7 + R() * 5) tree(x, (R() < 0.5 ? -1 : 1) * (7.3 + R() * 0.6), 0.8 + R() * 0.5);
  for (let i = 0; i < 70; i++) tree(X0 + R() * L, (R() < 0.5 ? -1 : 1) * (22 + R() * 40), 1 + R() * 1.2);

  // postes
  const pole = std('#5c6670', { roughness: 0.5, metalness: 0.4 });
  const lamp = std('#fff6d0', { emissive: '#fff2b0', emissiveIntensity: 0.4 });
  for (let x = X0; x < X1; x += 16) {
    for (const s of [-1, 1]) {
      add(env, new THREE.CylinderGeometry(0.07, 0.09, 5, 8), pole, [x + (s > 0 ? 8 : 0), 2.5, s * 6]);
      add(env, new THREE.BoxGeometry(0.12, 0.1, 1.4), pole, [x + (s > 0 ? 8 : 0), 4.95, s * 5.4]);
      add(env, new THREE.BoxGeometry(0.3, 0.12, 0.5), lamp, [x + (s > 0 ? 8 : 0), 4.88, s * 4.8], [0, 0, 0], false);
    }
  }

  // faixas da equipe nas calçadas
  const banners = cfg.faixas.map((t) => std('#ffffff', { map: canvasTex(bannerCanvas(t, logoImg)), roughness: 0.7 }));
  let bi = 0;
  for (let x = X0 + 12; x < finishX - 10; x += 26) {
    const s = bi % 2 ? 1 : -1;
    const g = new THREE.Group();
    g.position.set(x, 0, s * 5.6);
    g.rotation.y = s > 0 ? Math.PI : 0;
    env.add(g);
    add(g, new THREE.CylinderGeometry(0.05, 0.05, 2.6, 8), pole, [-1.5, 1.3, 0]);
    add(g, new THREE.CylinderGeometry(0.05, 0.05, 2.6, 8), pole, [1.5, 1.3, 0]);
    add(g, new THREE.BoxGeometry(3, 0.75, 0.04), banners[bi % banners.length], [0, 2.1, 0]);
    bi++;
  }

  // cones de prova no meio da rua
  const coneM = std('#ff7a1a');
  for (let x = X0 + 20; x < finishX; x += 12) {
    add(env, new THREE.ConeGeometry(0.22, 0.6, 12), coneM, [x, 0.3, 2.6]);
    add(env, new THREE.CylinderGeometry(0.15, 0.17, 0.08, 12), white, [x, 0.38, 2.6], [0, 0, 0], false);
  }

  // morros ao fundo
  const hillM = [std('#4d8a3c'), std('#5f9c48'), std('#3f7a35')];
  for (let i = 0; i < 26; i++) {
    const s = R() < 0.5 ? -1 : 1;
    const h = add(env, new THREE.SphereGeometry(40 + R() * 40, 20, 12), hillM[i % 3], [X0 + R() * (L + 200) - 100, -18, s * (140 + R() * 120)], [0, 0, 0], false);
    h.scale.set(1.6, 0.6 + R() * 0.3, 1);
  }

  // nuvens
  const cloudM = new THREE.MeshLambertMaterial({ color: '#ffffff' });
  const clouds = new THREE.Group();
  env.add(clouds);
  for (let i = 0; i < 30; i++) {
    const g = new THREE.Group();
    g.position.set(X0 - 100 + R() * (L + 300), 45 + R() * 40, -220 + R() * 300);
    g.scale.setScalar(4 + R() * 5);
    for (let k = 0; k < 5; k++) add(g, new THREE.SphereGeometry(1 + R() * 0.8, 12, 8), cloudM, [k * 1.1 - 2.2, R() * 0.6, R() * 0.8], [0, 0, 0], false);
    clouds.add(g);
  }

  // pórtico de chegada + torcida
  const arch = new THREE.Group();
  arch.position.set(finishX, 0, 0);
  env.add(arch);
  const archM = std('#2246a8', { roughness: 0.5 });
  for (const s of [-1, 1]) add(arch, new THREE.BoxGeometry(0.6, 5, 0.6), archM, [0, 2.5, s * 4.6]);
  const topTex = canvasTex(bannerCanvas('CHEGADA', logoImg, { w: 1024, h: 160 }));
  add(arch, new THREE.BoxGeometry(0.5, 1.3, 9.8), [std('#fff', { map: topTex }), std('#fff', { map: topTex }), archM, archM, archM, archM], [0, 5, 0]);
  const clockTex = canvasTex(textCanvas(['BURI - SP'], { w: 512, h: 128, color: '#4dd75d', bg: '#111', size: 70 }));
  add(arch, new THREE.BoxGeometry(2.4, 0.6, 0.15), std('#fff', { map: clockTex, emissive: '#ffffff', emissiveMap: clockTex, emissiveIntensity: 0.4 }), [-0.4, 3.95, 0], [0, -Math.PI / 2, 0]);
  // fita: duas metades que se abrem quando o corredor passa
  const tapeM = std('#e8262b', { roughness: 0.6 });
  const tapes = [];
  for (const s of [-1, 1]) {
    const pivot = new THREE.Group();
    pivot.position.set(0, 1.2, s * 4.3);
    arch.add(pivot);
    add(pivot, new THREE.BoxGeometry(0.03, 0.09, 4.3), tapeM, [0, 0, -s * 2.15], [0, 0, 0], false);
    tapes.push({ pivot, s });
  }
  const crowd = [];
  const shirts = ['#2246a8', '#4dd75d', '#ffffff', '#f2c230', '#2246a8', '#e8262b'];
  for (let i = 0; i < 22; i++) {
    const s = i % 2 ? 1 : -1;
    const g = new THREE.Group();
    g.position.set(finishX - 14 + R() * 22, 0.16, s * (5 + R() * 1.4));
    g.rotation.y = s > 0 ? Math.PI : 0;
    env.add(g);
    add(g, new THREE.CapsuleGeometry(0.22, 0.6, 4, 10), std(shirts[i % shirts.length]), [0, 0.75, 0]);
    add(g, new THREE.SphereGeometry(0.19, 12, 10), std(['#e0a47a', '#8d5a3b', '#f1c6a0', '#5b3a29'][i % 4]), [0, 1.45, 0]);
    crowd.push({ g, ph: R() * 6.28, sp: 6 + R() * 4 });
  }

  function update(t, charX) {
    clouds.position.x = t * 1.2;
    const k = THREE.MathUtils.clamp((charX - finishX + 0.3) / 0.6, 0, 1);
    for (const { pivot, s } of tapes) {
      pivot.rotation.y = s * k * 1.3;
      pivot.rotation.x = k * 0.5;
    }
    const near = Math.abs(charX - finishX) < 40;
    for (const c of crowd) c.g.position.y = 0.16 + (near ? Math.max(0, Math.sin(t * c.sp + c.ph)) * 0.25 : 0);
  }

  return { group: env, update, arch };
}
