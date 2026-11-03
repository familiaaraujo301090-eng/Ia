// Cenário procedural: rua de cidade do interior (Buri - SP) com casas coloridas,
// árvores, postes, faixas da equipe, morros, nuvens, céu em degradê e o pórtico
// de chegada. Tudo determinístico (semente fixa) para renderizar igual sempre.
import * as THREE from 'three';
import { awningCanvas, bannerCanvas, grassCanvas, roadCanvas, roofCanvas, sidewalkCanvas, textCanvas } from './textures.js';

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

function mesh2(geo, material) {
  const m = new THREE.Mesh(geo, material);
  m.receiveShadow = true;
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

export function buildEnvironment(cfg, logoImg, finishX, livres = []) {
  const livre = (x) => livres.some(([a, b]) => x > a && x < b);
  const R = rng(20261031);
  const env = new THREE.Group();
  env.name = 'cenario';
  const X0 = -80, X1 = finishX + 120, L = X1 - X0, XC = (X0 + X1) / 2;

  // chão com textura de grama
  const grassTex = canvasTex(grassCanvas());
  grassTex.wrapS = grassTex.wrapT = THREE.RepeatWrapping;
  grassTex.repeat.set((L + 600) / 12, 700 / 12);
  add(env, new THREE.PlaneGeometry(L + 600, 700), std('#ffffff', { map: grassTex, roughness: 0.95 }), [XC, -0.06, 0], [-Math.PI / 2, 0, 0], false);
  const roadTex = canvasTex(roadCanvas());
  roadTex.wrapS = roadTex.wrapT = THREE.RepeatWrapping;
  roadTex.repeat.set(L / 8, 1);
  add(env, new THREE.PlaneGeometry(L, 8), std('#ffffff', { map: roadTex, roughness: 0.95 }), [XC, 0.015, 0], [-Math.PI / 2, 0, 0], false);
  const white = std('#f4f4f4');
  const yellow = std('#f2c230');
  for (let x = X0; x < X1; x += 4) add(env, new THREE.BoxGeometry(2, 0.01, 0.14), yellow, [x, 0.03, 0], [0, 0, 0], false);
  for (const z of [-3.8, 3.8]) add(env, new THREE.BoxGeometry(L, 0.01, 0.12), white, [XC, 0.03, z], [0, 0, 0], false);
  // calçada portuguesa e meio-fio
  const swTex = canvasTex(sidewalkCanvas());
  swTex.wrapS = swTex.wrapT = THREE.RepeatWrapping;
  swTex.repeat.set(L / 2.4, 1);
  const swM = std('#ffffff', { map: swTex, roughness: 0.9 });
  for (const s of [-1, 1]) {
    add(env, new THREE.BoxGeometry(L, 0.16, 2.4), [std('#bdb6aa'), std('#bdb6aa'), swM, std('#bdb6aa'), std('#bdb6aa'), std('#bdb6aa')], [XC, 0.08, s * 5.2], [0, 0, 0], false);
    add(env, new THREE.BoxGeometry(L, 0.18, 0.15), std('#e8e4dc'), [XC, 0.09, s * 4.05], [0, 0, 0], false);
  }

  // casas coloridas: térreas, sobrados e comércios, com muro, janelas e telhado de barro
  const houseColors = ['#f4d35e', '#ee964b', '#f95738', '#7bc8a4', '#a8dadc', '#f7b2bd', '#fdf6e3', '#c3a6e0', '#90be6d', '#5fb7e5'];
  const roofTex = canvasTex(roofCanvas());
  roofTex.wrapS = roofTex.wrapT = THREE.RepeatWrapping;
  const roofM = std('#ffffff', { map: roofTex, roughness: 0.8 });
  const doorM = std('#6b3e26');
  const frameM = std('#fdfdfd');
  const winM = std('#9fd3f5', { roughness: 0.15, metalness: 0.2 });
  const shutterCols = ['#2d6a4f', '#1d3557', '#9b2226', '#6b4226'];
  const shops = ['PADARIA', 'MERCADINHO', 'SORVETERIA', 'LANCHONETE', 'FARMÁCIA', 'PAPELARIA'];
  let shopI = 0;
  const gable = (w, d, h) => {
    const sh = new THREE.Shape();
    sh.moveTo(-d / 2, 0);
    sh.lineTo(d / 2, 0);
    sh.lineTo(0, h);
    sh.closePath();
    const geo = new THREE.ExtrudeGeometry(sh, { depth: w, bevelEnabled: false });
    geo.translate(0, 0, -w / 2);
    geo.rotateY(Math.PI / 2);
    return geo;
  };
  const windowAt = (g, x, y, z, s, col) => {
    add(g, new THREE.BoxGeometry(1.25, 1.05, 0.08), frameM, [x, y, z], [0, 0, 0], false);
    add(g, new THREE.BoxGeometry(1.05, 0.85, 0.1), winM, [x, y, z], [0, 0, 0], false);
    add(g, new THREE.BoxGeometry(0.06, 0.85, 0.12), frameM, [x, y, z], [0, 0, 0], false);
    for (const q of [-1, 1]) add(g, new THREE.BoxGeometry(0.55, 0.95, 0.05), std(col), [x + q * 0.92, y, z - s * 0.02], [0, 0, 0], false);
  };
  for (const s of [-1, 1]) {
    let x = X0 + R() * 6;
    while (x < X1) {
      const tipo = R();
      const w = 5.5 + R() * 3.5, d = 5.5 + R() * 2;
      const h = tipo > 0.78 ? 5.6 : 3.1 + R() * 0.8;
      const z = s * (10.5 + R() * 1.2 + d / 2);
      const g = new THREE.Group();
      g.position.set(x + w / 2, 0, z);
      env.add(g);
      const wallCol = houseColors[Math.floor(R() * houseColors.length)];
      add(g, new THREE.BoxGeometry(w, h, d), std(wallCol), [0, h / 2, 0]);
      const front = -s * (d / 2 + 0.03);
      // barrado mais escuro na base da parede
      add(g, new THREE.BoxGeometry(w + 0.02, 0.7, 0.04), std(new THREE.Color(wallCol).multiplyScalar(0.72)), [0, 0.35, front], [0, 0, 0], false);
      // telhado de duas águas com beiral
      const roof = add(g, gable(w + 0.7, d + 0.9, 1.5), roofM, [0, h, 0]);
      roof.castShadow = true;
      add(g, new THREE.BoxGeometry(w + 0.75, 0.12, 0.2), std('#f2efe8'), [0, h + 0.02, -s * (d / 2 + 0.42)], [0, 0, 0], false);
      const shutter = shutterCols[Math.floor(R() * shutterCols.length)];
      if (tipo > 0.62 && tipo <= 0.78) {
        // comércio: porta larga, toldo listrado e placa
        add(g, new THREE.BoxGeometry(w * 0.55, 2.3, 0.06), std('#4a4f57', { metalness: 0.3, roughness: 0.5 }), [0, 1.15, front], [0, 0, 0], false);
        const aw = add(g, new THREE.BoxGeometry(w * 0.75, 0.06, 1.2), std('#ffffff', { map: canvasTex(awningCanvas(['#e63946', '#2a9d8f', '#f4a261'][shopI % 3])) }), [0, 2.65, front - s * 0.55], [s * 0.35, 0, 0], true);
        aw.castShadow = true;
        const sign = canvasTex(textCanvas([shops[shopI++ % shops.length]], { w: 512, h: 128, color: '#ffffff', bg: '#1d3557', size: 64 }));
        const signM = mesh2(new THREE.PlaneGeometry(w * 0.7, w * 0.175), std('#ffffff', { map: sign }));
        signM.position.set(0, h - 0.55, front - s * 0.02);
        signM.rotation.y = s > 0 ? Math.PI : 0;
        g.add(signM);
      } else {
        add(g, new THREE.BoxGeometry(1.15, 2.15, 0.08), frameM, [-w * 0.22, 1.08, front], [0, 0, 0], false);
        add(g, new THREE.BoxGeometry(0.95, 2.0, 0.1), doorM, [-w * 0.22, 1.0, front], [0, 0, 0], false);
        windowAt(g, w * 0.2, 1.55, front, s, shutter);
        if (h > 5) {
          windowAt(g, -w * 0.22, 4.1, front, s, shutter);
          windowAt(g, w * 0.2, 4.1, front, s, shutter);
          // sacada
          add(g, new THREE.BoxGeometry(w * 0.5, 0.12, 0.8), frameM, [-w * 0.22, 3.4, front - s * 0.4], [0, 0, 0]);
          add(g, new THREE.BoxGeometry(w * 0.5, 0.6, 0.05), std('#2b2b2b', { metalness: 0.5 }), [-w * 0.22, 3.75, front - s * 0.78], [0, 0, 0], false);
        }
      }
      // muro baixo com portão, rente à calçada
      const muroCol = std(new THREE.Color(wallCol).lerp(new THREE.Color('#ffffff'), 0.35));
      const zm = s * 6.55 - g.position.z;
      const gate = 1.6;
      const seg = (w + 1.5 - gate) / 2;
      for (const q of [-1, 1]) {
        add(g, new THREE.BoxGeometry(seg, 1.0, 0.2), muroCol, [q * (gate / 2 + seg / 2), 0.5, zm]);
        add(g, new THREE.BoxGeometry(seg + 0.06, 0.08, 0.28), frameM, [q * (gate / 2 + seg / 2), 1.04, zm], [0, 0, 0], false);
      }
      for (let k = 0; k < 7; k++) add(g, new THREE.BoxGeometry(0.04, 1.1, 0.04), std('#2b2b2b', { metalness: 0.5 }), [-gate / 2 + 0.12 + k * 0.23, 0.55, zm], [0, 0, 0], false);
      x += w + 1.5 + R() * 1.5;
    }
  }

  // árvores: copas verdes e ipês amarelos/roxos floridos
  const trunk = std('#7a5230');
  const leafs = [std('#3f8f3a'), std('#2f7a34'), std('#5aa547')];
  const ipes = [std('#f6c90e', { roughness: 0.9 }), std('#d66ba0', { roughness: 0.9 })];
  const tree = (x, z, sc, ipe = false) => {
    const g = new THREE.Group();
    g.position.set(x, 0, z);
    g.scale.setScalar(sc);
    g.rotation.y = R() * 6.28;
    env.add(g);
    add(g, new THREE.CylinderGeometry(0.16, 0.26, 2.3, 8), trunk, [0, 1.15, 0]);
    add(g, new THREE.CylinderGeometry(0.07, 0.1, 1.2, 6), trunk, [0.35, 2.3, 0], [0, 0, -0.6]);
    const lm = ipe ? ipes[Math.floor(R() * 2)] : leafs[Math.floor(R() * leafs.length)];
    const blobs = [[0, 3.0, 0, 1.35], [0.8, 2.75, 0.3, 1.0], [-0.7, 2.8, -0.35, 0.95], [0.1, 3.6, -0.2, 0.9], [-0.3, 2.6, 0.7, 0.8]];
    for (const [bx, by, bz, r] of blobs) add(g, new THREE.IcosahedronGeometry(r, 1), lm, [bx, by, bz]);
    if (ipe) add(g, new THREE.IcosahedronGeometry(0.7, 1), leafs[0], [0.5, 2.4, -0.6]);
    // canteiro
    add(g, new THREE.CylinderGeometry(0.55, 0.55, 0.12, 12), std('#6b4f3a'), [0, 0.18, 0], [0, 0, 0], false);
  };
  for (let x = X0; x < X1; x += 8 + R() * 5) {
    const z = (R() < 0.5 ? -1 : 1) * (5.9 + R() * 0.3), sc = 0.85 + R() * 0.4, ipe = R() < 0.35;
    if (!livre(x)) tree(x, z, sc, ipe);
  }
  for (let i = 0; i < 80; i++) tree(X0 + R() * L, (R() < 0.5 ? -1 : 1) * (22 + R() * 40), 1 + R() * 1.2, R() < 0.2);

  // tufos de grama e flores nos quintais (instanciados)
  const tufo = new THREE.InstancedMesh(new THREE.ConeGeometry(0.12, 0.35, 5), std('#4f9a36'), 900);
  const flor = new THREE.InstancedMesh(new THREE.SphereGeometry(0.07, 6, 5), std('#ffffff', { roughness: 0.6 }), 600);
  const mtx = new THREE.Matrix4();
  const florCols = ['#ff4d6d', '#ffd166', '#ffffff', '#c77dff', '#ff8fab'].map((c) => new THREE.Color(c));
  for (let i = 0; i < 900; i++) {
    const s = R() < 0.5 ? -1 : 1;
    mtx.makeScale(1, 0.6 + R() * 0.8, 1).setPosition(X0 + R() * L, 0.1, s * (6.8 + R() * 3.2));
    tufo.setMatrixAt(i, mtx);
  }
  for (let i = 0; i < 600; i++) {
    const s = R() < 0.5 ? -1 : 1;
    mtx.makeTranslation(X0 + R() * L, 0.22 + R() * 0.1, s * (6.8 + R() * 3.2));
    flor.setMatrixAt(i, mtx);
    flor.setColorAt(i, florCols[i % florCols.length]);
  }
  env.add(tufo, flor);

  // postes com fiação
  const pole = std('#5c6670', { roughness: 0.5, metalness: 0.4 });
  const lamp = std('#fff6d0', { emissive: '#fff2b0', emissiveIntensity: 0.4 });
  const wireM = std('#1c1c1c', { roughness: 0.6 });
  for (const s of [-1, 1]) {
    const xs = [];
    for (let x = X0 + (s > 0 ? 8 : 0); x < X1; x += 16) xs.push(x);
    for (const x of xs) {
      add(env, new THREE.CylinderGeometry(0.08, 0.12, 6.5, 8), std('#9a9a92', { roughness: 0.8 }), [x, 3.25, s * 6.3]);
      add(env, new THREE.BoxGeometry(0.1, 0.1, 1.6), pole, [x, 5.6, s * 5.6]);
      add(env, new THREE.BoxGeometry(0.32, 0.12, 0.5), lamp, [x, 5.52, s * 4.9], [0, 0, 0], false);
      add(env, new THREE.BoxGeometry(0.08, 0.08, 1.2), pole, [x, 6.2, s * 6.3]);
    }
    for (let i = 0; i + 1 < xs.length; i++) {
      for (const dz of [-0.5, 0.5]) {
        const a = new THREE.Vector3(xs[i], 6.2, s * 6.3 + dz), b = new THREE.Vector3(xs[i + 1], 6.2, s * 6.3 + dz);
        const mid = a.clone().lerp(b, 0.5);
        mid.y -= 0.45;
        const curve = new THREE.QuadraticBezierCurve3(a, mid, b);
        const w = new THREE.Mesh(new THREE.TubeGeometry(curve, 10, 0.012, 4), wireM);
        env.add(w);
      }
    }
  }

  // carros estacionados do lado esquerdo da rua
  const carCols = ['#d62828', '#f7f7f7', '#1d3557', '#8d99ae', '#fcbf49', '#2a9d8f'];
  const tireM = std('#151515', { roughness: 0.9 });
  const glassM = std('#2b3a4a', { roughness: 0.1, metalness: 0.4 });
  for (let x = X0 + 25; x < finishX - 25; x += 22 + R() * 25) {
    if (livre(x) || livre(x + 2) || livre(x - 2)) continue;
    const g = new THREE.Group();
    g.position.set(x, 0, -3.0);
    env.add(g);
    const body = std(carCols[Math.floor(R() * carCols.length)], { roughness: 0.3, metalness: 0.3 });
    add(g, new THREE.BoxGeometry(3.9, 0.7, 1.7), body, [0, 0.62, 0]);
    add(g, new THREE.BoxGeometry(2.1, 0.6, 1.55), body, [-0.2, 1.25, 0]);
    add(g, new THREE.BoxGeometry(2.0, 0.5, 1.58), glassM, [-0.2, 1.25, 0], [0, 0, 0], false);
    for (const [wx, wz] of [[1.25, 0.8], [-1.25, 0.8], [1.25, -0.8], [-1.25, -0.8]]) add(g, new THREE.CylinderGeometry(0.34, 0.34, 0.25, 14), tireM, [wx, 0.34, wz], [Math.PI / 2, 0, 0]);
    for (const q of [-1, 1]) add(g, new THREE.BoxGeometry(0.05, 0.14, 0.3), std('#fff6c0', { emissive: '#fff2a0', emissiveIntensity: 0.3 }), [1.95, 0.75, q * 0.55], [0, 0, 0], false);
  }

  // bandeirinhas atravessando a rua perto da chegada
  const flagCols = ['#2246a8', '#4dd75d', '#f2c230', '#ffffff', '#e63946'].map((c) => std(c, { side: THREE.DoubleSide, roughness: 0.7 }));
  const tri = new THREE.Shape();
  tri.moveTo(-0.16, 0);
  tri.lineTo(0.16, 0);
  tri.lineTo(0, -0.38);
  tri.closePath();
  const triGeo = new THREE.ShapeGeometry(tri);
  for (let fx = finishX - 45; fx <= finishX - 6; fx += 7) {
    const a = new THREE.Vector3(fx, 5.4, -6.3), b = new THREE.Vector3(fx, 5.4, 6.3);
    const mid = new THREE.Vector3(fx, 4.6, 0);
    const curve = new THREE.QuadraticBezierCurve3(a, mid, b);
    env.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 16, 0.01, 4), wireM));
    for (let k = 1; k < 24; k++) {
      const p = curve.getPoint(k / 24);
      const f = new THREE.Mesh(triGeo, flagCols[k % flagCols.length]);
      f.position.copy(p);
      f.rotation.y = Math.PI / 2;
      env.add(f);
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
    if (s > 0 && livre(g.position.x) && g.position.x > finishX) g.visible = false;
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
