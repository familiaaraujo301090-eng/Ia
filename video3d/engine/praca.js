// Cenário "Praça Matriz de Buri": igreja matriz com torre do relógio, calçada
// portuguesa em ondas, figueiras grandes, palmeiras-imperiais de tronco caiado,
// postes brancos em Y, chafariz em degraus com água iluminada e bancos azuis
// "EU ♥ BURI". O corredor atravessa a praça em direção à igreja (eixo +X).
import * as THREE from 'three';
import { add, canvasTex, paisagemDistante, porticoDeChegada, rng, std } from './environment.js';
import { calcadaMaps, cascaMaps, folhagemCanvas, frondeCanvas, rebocoMaps, roofCanvas, textCanvas, FONT } from './textures.js';

function lajotasCanvas() {
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const g = c.getContext('2d');
  g.fillStyle = '#b9b4ab';
  g.fillRect(0, 0, 256, 256);
  g.strokeStyle = '#8f8a81';
  g.lineWidth = 3;
  for (let i = 0; i <= 256; i += 64) {
    g.beginPath();
    g.moveTo(i, 0);
    g.lineTo(i, 256);
    g.moveTo(0, i);
    g.lineTo(256, i);
    g.stroke();
  }
  return c;
}

function bancoCanvas() {
  const c = document.createElement('canvas');
  c.width = 512;
  c.height = 128;
  const g = c.getContext('2d');
  g.fillStyle = '#2a6fd6';
  g.fillRect(0, 0, 512, 128);
  g.fillStyle = '#ffffff';
  g.font = `bold 70px ${FONT}`;
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.fillText('EU ♥ BURI', 256, 68);
  return c;
}

function relogioCanvas() {
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const g = c.getContext('2d');
  g.fillStyle = '#fbfbf6';
  g.beginPath();
  g.arc(128, 128, 124, 0, Math.PI * 2);
  g.fill();
  g.strokeStyle = '#222';
  g.lineWidth = 8;
  g.stroke();
  for (let i = 0; i < 12; i++) {
    const a = (i / 12) * Math.PI * 2;
    g.fillStyle = '#222';
    g.fillRect(128 + Math.sin(a) * 100 - 4, 128 - Math.cos(a) * 100 - 10, 8, 20);
  }
  g.lineCap = 'round';
  g.lineWidth = 10;
  g.beginPath();
  g.moveTo(128, 128);
  g.lineTo(128 + 50, 128 - 30);
  g.stroke();
  g.lineWidth = 6;
  g.beginPath();
  g.moveTo(128, 128);
  g.lineTo(128 - 10, 128 - 90);
  g.stroke();
  return c;
}

// Igreja matriz: nave com frontão, portas e janelas em arco, telhado de barro e torre com relógio.
function igreja(env, x0, olhaPara = 1) {
  const g = new THREE.Group();
  g.position.set(x0, 0, 0);
  g.rotation.y = olhaPara > 0 ? 0 : Math.PI; // fachada voltada para +X (início da corrida) ou -X
  env.add(g);
  const reb = rebocoMaps('#f0d9bf');
  const parede = std('#ffffff', { map: canvasTex(reb.cor), normalMap: canvasTex(reb.normal), roughness: 0.9 });
  for (const t of [parede.map, parede.normalMap]) {
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.repeat.set(4, 2);
  }
  const friso = std('#fbf6ee', { roughness: 0.7 });
  const madeira = std('#5a3a22');
  const vidro = std('#3c4a5a', { roughness: 0.3 });
  const telha = std('#ffffff', { map: canvasTex(roofCanvas()), roughness: 0.8 });
  telha.map.wrapS = telha.map.wrapT = THREE.RepeatWrapping;
  telha.map.repeat.set(4, 2);
  const L = 26, W = 13, H = 9;
  // nave (comprimento ao longo de +Z local... usamos X local; fachada em x = +L/2 após o giro)
  add(g, new THREE.BoxGeometry(L, H, W), parede, [0, H / 2, 0]);
  const sh = new THREE.Shape();
  sh.moveTo(-W / 2 - 0.5, 0);
  sh.lineTo(W / 2 + 0.5, 0);
  sh.lineTo(0, 4.2);
  sh.closePath();
  const tel = new THREE.ExtrudeGeometry(sh, { depth: L + 0.6, bevelEnabled: false });
  tel.translate(0, 0, -(L + 0.6) / 2);
  tel.rotateY(Math.PI / 2);
  add(g, tel, telha, [0, H, 0]);
  // frontão (fachada) com frisos
  const fx = L / 2 + 0.05;
  const front = new THREE.Shape();
  front.moveTo(-W / 2, 0);
  front.lineTo(W / 2, 0);
  front.lineTo(W / 2, H);
  front.lineTo(0, H + 4.6);
  front.lineTo(-W / 2, H);
  front.closePath();
  const fg = new THREE.ExtrudeGeometry(front, { depth: 0.6, bevelEnabled: false });
  fg.rotateY(Math.PI / 2);
  add(g, fg, parede, [fx - 0.6, 0, 0]);
  for (const zz of [-W / 2 + 0.3, -2.3, 2.3, W / 2 - 0.3]) add(g, new THREE.BoxGeometry(0.2, H, 0.55), friso, [fx + 0.1, H / 2, zz]);
  add(g, new THREE.BoxGeometry(0.25, 0.4, W + 0.2), friso, [fx + 0.1, H, 0]);
  const arcoPorta = (z, w, h, y0 = 0) => {
    add(g, new THREE.BoxGeometry(0.2, h, w), madeira, [fx + 0.05, y0 + h / 2, z], [0, 0, 0], false);
    add(g, new THREE.CylinderGeometry(w / 2, w / 2, 0.2, 20, 1, false, 0, Math.PI), madeira, [fx + 0.05, y0 + h, z], [0, 0, Math.PI / 2], false);
    add(g, new THREE.TorusGeometry(w / 2 + 0.12, 0.1, 6, 20, Math.PI), friso, [fx + 0.12, y0 + h, z], [0, Math.PI / 2, 0], false);
  };
  arcoPorta(0, 2.2, 3.2);
  arcoPorta(-4, 1.6, 2.6);
  arcoPorta(4, 1.6, 2.6);
  for (const z of [-4, 0, 4]) {
    add(g, new THREE.BoxGeometry(0.2, 1.4, 0.9), vidro, [fx + 0.05, 6.3, z], [0, 0, 0], false);
    add(g, new THREE.CylinderGeometry(0.45, 0.45, 0.2, 16, 1, false, 0, Math.PI), vidro, [fx + 0.05, 7.0, z], [0, 0, Math.PI / 2], false);
  }
  add(g, new THREE.CircleGeometry(0.8, 24), vidro, [fx + 0.12, 10.6, 0], [0, Math.PI / 2, 0], false);
  // cruz no topo do frontão
  const cruz = std('#d9d4c8', { metalness: 0.3 });
  add(g, new THREE.BoxGeometry(0.2, 1.6, 0.2), cruz, [fx - 0.3, H + 5.3, 0]);
  add(g, new THREE.BoxGeometry(0.2, 0.2, 0.9), cruz, [fx - 0.3, H + 5.6, 0]);
  // janelas laterais em arco
  for (let k = -3; k <= 3; k++) for (const s of [-1, 1]) {
    add(g, new THREE.BoxGeometry(1.0, 1.8, 0.15), vidro, [k * 3.2, 5.4, s * (W / 2 + 0.03)], [0, 0, 0], false);
    add(g, new THREE.CylinderGeometry(0.5, 0.5, 0.15, 14, 1, false, -Math.PI / 2, Math.PI), vidro, [k * 3.2, 6.3, s * (W / 2 + 0.03)], [-Math.PI / 2, 0, 0], false);
  }
  // torre do sino com relógio, à direita da fachada (lado +Z do mundo)
  const T = new THREE.Group();
  T.position.set(fx - 2.4, 0, -(W / 2 + 2.1)); // à direita de quem olha a fachada
  g.add(T);
  const TH = 26, TW = 4.2;
  add(T, new THREE.BoxGeometry(TW, TH, TW), parede, [0, TH / 2, 0]);
  for (const [dx, dz, w, d] of [[TW / 2 + 0.02, 0, 0.1, 1.2], [0, TW / 2 + 0.02, 1.2, 0.1], [0, -TW / 2 - 0.02, 1.2, 0.1], [-TW / 2 - 0.02, 0, 0.1, 1.2]]) {
    add(T, new THREE.BoxGeometry(w, TH - 8, d), std('#e3c9ab'), [dx, (TH - 8) / 2 + 3, dz], [0, 0, 0], false);
  }
  for (let y = 4; y < TH - 6; y += 4) add(T, new THREE.BoxGeometry(TW + 0.15, 0.18, TW + 0.15), friso, [0, y, 0], [0, 0, 0], false);
  const relTex = canvasTex(relogioCanvas());
  const relM = std('#ffffff', { map: relTex, roughness: 0.5, emissive: '#ffffff', emissiveMap: relTex, emissiveIntensity: 0.25 });
  for (const [dx, dz, ry] of [[TW / 2 + 0.06, 0, Math.PI / 2], [0, TW / 2 + 0.06, 0], [0, -TW / 2 - 0.06, Math.PI], [-TW / 2 - 0.06, 0, -Math.PI / 2]]) {
    const r = new THREE.Mesh(new THREE.CircleGeometry(1.1, 40), relM);
    r.position.set(dx, TH - 4.2, dz);
    r.rotation.y = ry;
    T.add(r);
    add(T, new THREE.BoxGeometry(dx ? 0.15 : 0.8, 1.6, dx ? 0.8 : 0.15), std('#2b2b2b'), [dx * 1.0, TH - 1.6, dz * 1.0], [0, 0, 0], false);
  }
  add(T, new THREE.BoxGeometry(TW + 0.5, 0.4, TW + 0.5), friso, [0, TH + 0.2, 0]);
  add(T, new THREE.BoxGeometry(TW - 0.6, 0.6, TW - 0.6), parede, [0, TH + 0.7, 0]);
  add(T, new THREE.BoxGeometry(0.22, 2.2, 0.22), cruz, [0, TH + 2.1, 0]);
  add(T, new THREE.BoxGeometry(0.22, 0.22, 1.2), cruz, [0, TH + 2.5, 0]);
  // muro baixo com grade preta na frente da igreja
  const grade = std('#151515', { metalness: 0.5, roughness: 0.4 });
  add(g, new THREE.BoxGeometry(0.4, 0.7, W + 6), std('#f3e6d6'), [fx + 3.2, 0.35, -1.5]);
  for (let z = -W / 2 - 4; z < W / 2 + 1; z += 0.35) add(g, new THREE.BoxGeometry(0.05, 1.3, 0.05), grade, [fx + 3.2, 1.35, z], [0, 0, 0], false);
  add(g, new THREE.BoxGeometry(0.08, 0.08, W + 6), grade, [fx + 3.2, 1.98, -1.5], [0, 0, 0], false);
  return g;
}

// Coletor de folhagem instanciada: cada árvore registra seus "cartões" de folhas e,
// no fim, tudo vira poucas InstancedMesh (rápido mesmo com milhares de folhas).
function novaFolhagem() {
  const itens = [];
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), v = new THREE.Vector3(), sc = new THREE.Vector3();
  return {
    add(px, py, pz, tam, R, tom = 1) {
      e.set(R() * 6.28, R() * 6.28, R() * 6.28);
      q.setFromEuler(e);
      m4.compose(v.set(px, py, pz), q, sc.set(tam, tam, tam));
      itens.push({ m: m4.clone(), c: new THREE.Color().setHSL(0.27 + (R() - 0.5) * 0.04, 0.45, (0.26 + R() * 0.1) * tom) });
    },
    criar(env, mats) {
      const porMat = mats.map(() => []);
      itens.forEach((it, i) => porMat[i % mats.length].push(it));
      porMat.forEach((lista, k) => {
        const im = new THREE.InstancedMesh(new THREE.PlaneGeometry(1, 1), mats[k], lista.length);
        lista.forEach((it, i) => {
          im.setMatrixAt(i, it.m);
          im.setColorAt(i, it.c);
        });
        // as folhas recebem sombra, mas quem projeta a sombra da copa é o miolo (bem mais barato)
        im.receiveShadow = true;
        env.add(im);
      });
    },
  };
}

let FOL = null;
let CASCA = null;

function figueira(env, R, x, z, sc) {
  const g = new THREE.Group();
  g.position.set(x, 0, z);
  g.scale.setScalar(sc);
  g.rotation.y = R() * 6.28;
  env.add(g);
  add(g, new THREE.CylinderGeometry(0.38, 0.62, 3.4, 14), CASCA, [0, 1.7, 0]);
  add(g, new THREE.CylinderGeometry(0.63, 0.65, 1.1, 14), std('#f1eee6', { roughness: 0.9 }), [0, 0.55, 0]); // tronco caiado
  // galhos curvos saindo do tronco
  const pontas = [];
  for (let i = 0; i < 6; i++) {
    const a = (i / 6) * Math.PI * 2 + R() * 0.5, r = 2.4 + R() * 1.6;
    const fim = new THREE.Vector3(Math.cos(a) * r, 5.2 + R() * 1.5, Math.sin(a) * r);
    const meio = new THREE.Vector3(Math.cos(a) * r * 0.35, 4.2 + R() * 0.6, Math.sin(a) * r * 0.35);
    const curva = new THREE.QuadraticBezierCurve3(new THREE.Vector3(0, 3.1, 0), meio, fim);
    const galho = new THREE.Mesh(new THREE.TubeGeometry(curva, 8, 0.16 + R() * 0.08, 6), CASCA);
    galho.castShadow = true;
    g.add(galho);
    pontas.push(fim);
  }
  // miolo escuro para a copa não ficar vazada
  for (let i = 0; i < 5; i++) {
    const a = (i / 5) * Math.PI * 2;
    add(g, new THREE.IcosahedronGeometry(1.8, 1), std('#1f4a1b', { roughness: 1 }), [Math.cos(a) * 1.8, 5.9, Math.sin(a) * 1.8]);
  }
  // cartões de folhas espalhados numa copa achatada (como as figueiras da praça)
  g.updateMatrixWorld(true);
  const p = new THREE.Vector3();
  for (let i = 0; i < 520; i++) {
    const u = R() * Math.PI * 2, w = Math.acos(1 - R() * 1.15), r = 0.72 + R() * 0.32;
    p.set(Math.sin(w) * Math.cos(u) * 4.6 * r, 5.6 + Math.cos(w) * 2.6 * r, Math.sin(w) * Math.sin(u) * 4.6 * r);
    p.applyMatrix4(g.matrixWorld);
    FOL.add(p.x, p.y, p.z, (1.5 + R() * 0.8) * sc, R, w > 1.2 ? 0.75 : 1);
  }
}

function palmeira(env, R, x, z, h) {
  const g = new THREE.Group();
  g.position.set(x, 0, z);
  env.add(g);
  const tronco = add(g, new THREE.CylinderGeometry(0.24, 0.32, h, 14, 8), CASCA, [0, h / 2, 0]);
  tronco.material = CASCA.clone();
  tronco.material.color = new THREE.Color('#b8b2a6');
  add(g, new THREE.CylinderGeometry(0.33, 0.33, 1.3, 14), std('#f6f3ec', { roughness: 0.9 }), [0, 0.65, 0]);
  add(g, new THREE.CylinderGeometry(0.27, 0.25, 1.6, 12), std('#6f9a3a', { roughness: 0.7 }), [0, h + 0.6, 0]);
  // frondes recortadas e arqueadas
  const geo = new THREE.PlaneGeometry(1.1, 4.8, 1, 12);
  const pos = geo.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    const y = pos.getY(i) + 2.4; // 0 na base, 4.8 na ponta
    pos.setY(i, y);
    pos.setZ(i, -0.06 * y * y);
  }
  geo.computeVertexNormals();
  for (let i = 0; i < 16; i++) {
    const f = new THREE.Mesh(geo, PALMA);
    f.position.set(0, h + 1.3, 0);
    f.rotation.set(0, (i / 16) * Math.PI * 2 + R() * 0.2, 0);
    f.rotateX(-(0.35 + (i % 3) * 0.3 + R() * 0.2));
    f.castShadow = true;
    g.add(f);
  }
}

let PALMA = null;

function posteY(env, x, z) {
  const branco = std('#f2f2f2', { roughness: 0.4, metalness: 0.2 });
  const luz = std('#fffbe6', { emissive: '#fff3c0', emissiveIntensity: 0.5 });
  add(env, new THREE.CylinderGeometry(0.08, 0.12, 5.2, 10), branco, [x, 2.6, z]);
  for (const s of [-1, 1]) {
    add(env, new THREE.CylinderGeometry(0.05, 0.05, 1.4, 8), branco, [x + s * 0.45, 5.6, z], [0, 0, -s * 0.7]);
    add(env, new THREE.BoxGeometry(0.7, 0.1, 0.35), luz, [x + s * 0.95, 6.05, z], [0, 0, s * 0.12], false);
  }
}

function banco(env, x, z, ry, mat) {
  const g = new THREE.Group();
  g.position.set(x, 0, z);
  g.rotation.y = ry;
  env.add(g);
  const pe = std('#3a3a3a', { metalness: 0.4 });
  add(g, new THREE.BoxGeometry(2.2, 0.1, 0.55), std('#2a6fd6'), [0, 0.48, 0]);
  add(g, new THREE.BoxGeometry(2.2, 0.55, 0.08), mat, [0, 0.85, -0.26], [-0.1, 0, 0]);
  for (const s of [-1, 1]) add(g, new THREE.BoxGeometry(0.08, 0.48, 0.5), pe, [s * 0.95, 0.24, 0]);
}

function chafariz(env, x, z) {
  const g = new THREE.Group();
  g.position.set(x, 0, z);
  env.add(g);
  const pedra = std('#8c8f92', { roughness: 0.7 });
  const agua = new THREE.MeshStandardMaterial({ color: '#3fd6c8', emissive: '#22b8b0', emissiveIntensity: 0.35, roughness: 0.1, metalness: 0.1, transparent: true, opacity: 0.85 });
  add(g, new THREE.BoxGeometry(7, 0.7, 7), pedra, [0, 0.35, 0]);
  add(g, new THREE.BoxGeometry(6.4, 0.05, 6.4), agua, [0, 0.62, 0], [0, 0, 0], false);
  add(g, new THREE.BoxGeometry(3.6, 1.5, 3.6), pedra, [0, 0.75, 0]);
  add(g, new THREE.BoxGeometry(3.1, 0.05, 3.1), agua, [0, 1.52, 0], [0, 0, 0], false);
  add(g, new THREE.BoxGeometry(1.6, 2.3, 1.6), pedra, [0, 1.15, 0]);
  const jatoM = new THREE.MeshStandardMaterial({ color: '#d8fbff', emissive: '#7ff3ff', emissiveIntensity: 0.6, transparent: true, opacity: 0.7, roughness: 0.1 });
  const jatos = [];
  const jato = (px, pz, h, r) => {
    const m = new THREE.Mesh(new THREE.ConeGeometry(r, 1, 10, 1, true), jatoM);
    m.position.set(px, 0, pz);
    m.rotation.x = Math.PI;
    g.add(m);
    jatos.push({ m, h, base: m.position.y });
    return m;
  };
  jato(0, 0, 2.4, 0.22).userData.y0 = 2.3;
  for (const [px, pz] of [[-1.2, -1.2], [1.2, -1.2], [-1.2, 1.2], [1.2, 1.2]]) jato(px, pz, 1.2, 0.12).userData.y0 = 1.55;
  for (let i = 0; i < 8; i++) {
    const a = (i / 8) * Math.PI * 2;
    jato(Math.cos(a) * 2.6, Math.sin(a) * 2.6, 0.9, 0.08).userData.y0 = 0.64;
  }
  return (t) => {
    jatos.forEach((j, i) => {
      const h = j.h * (0.85 + 0.15 * Math.sin(t * 3 + i));
      j.m.scale.set(1, h, 1);
      j.m.position.y = j.m.userData.y0 + h / 2;
    });
  };
}

export function buildPraca(cfg, logoImg, finishX, livres = []) {
  const R = rng(19550101);
  FOL = novaFolhagem();
  const casca = cascaMaps();
  CASCA = std('#ffffff', { map: canvasTex(casca.cor), normalMap: canvasTex(casca.normal), roughness: 0.95 });
  CASCA.map.wrapS = CASCA.map.wrapT = CASCA.normalMap.wrapS = CASCA.normalMap.wrapT = THREE.RepeatWrapping;
  CASCA.map.repeat.set(2, 3);
  CASCA.normalMap.repeat.set(2, 3);
  const frond = canvasTex(frondeCanvas());
  PALMA = new THREE.MeshStandardMaterial({ map: frond, alphaTest: 0.4, side: THREE.DoubleSide, roughness: 0.75 });
  const livre = (x) => livres.some(([a, b]) => x > a && x < b);
  const env = new THREE.Group();
  env.name = 'praca-matriz';
  const X0 = -70, X1 = finishX + 70, L = X1 - X0, XC = (X0 + X1) / 2;

  // chão: grama ao longe, praça em calçada portuguesa e faixa central de lajotas
  add(env, new THREE.PlaneGeometry(L + 600, 700), std('#6aa845'), [XC, -0.06, 0], [-Math.PI / 2, 0, 0], false);
  const calc = calcadaMaps();
  const ondas = canvasTex(calc.cor), relevo = canvasTex(calc.normal);
  for (const t of [ondas, relevo]) {
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.repeat.set(L / 4, 60 / 4);
  }
  add(env, new THREE.PlaneGeometry(L, 60), std('#ffffff', { map: ondas, normalMap: relevo, normalScale: new THREE.Vector2(0.8, 0.8), roughness: 0.9 }), [XC, 0.0, 0], [-Math.PI / 2, 0, 0], false);
  // faixas de lajotas cinza nas bordas, como na praça real
  const laj = canvasTex(lajotasCanvas());
  laj.wrapS = laj.wrapT = THREE.RepeatWrapping;
  laj.repeat.set(L / 4, 1);
  for (const s of [-1, 1]) add(env, new THREE.PlaneGeometry(L, 4), std('#ffffff', { map: laj, roughness: 0.8 }), [XC, 0.012, s * 27], [-Math.PI / 2, 0, 0], false);
  for (const s of [-1, 1]) add(env, new THREE.BoxGeometry(L, 0.06, 0.2), std('#d8d3ca'), [XC, 0.03, s * 3.4], [0, 0, 0], false);
  // ruas em volta da praça
  for (const s of [-1, 1]) {
    add(env, new THREE.PlaneGeometry(L, 9), std('#4a4d52', { roughness: 0.95 }), [XC, 0.006, s * 34.5], [-Math.PI / 2, 0, 0], false);
    add(env, new THREE.BoxGeometry(L, 0.2, 0.3), std('#e8e4dc'), [XC, 0.1, s * 30.1], [0, 0, 0], false);
  }

  // igreja matriz no início da corrida, de frente para o percurso; chafariz no adro
  const xIgreja = -24;
  igreja(env, xIgreja, 1);
  const animaChafariz = chafariz(env, -2, 11);
  const adro = (x, z) => x < -6 && Math.abs(z) < 16; // área livre em frente à igreja
  // canteiros com sebe e flores
  const sebe = std('#3d7a2c', { roughness: 0.9 });
  const canteiros = [];
  const florCols = ['#ff4d6d', '#ffd166', '#ffffff', '#c77dff'];
  for (let x = X0 + 10; x < X1 - 30; x += 22) {
    for (const s of [-1, 1]) {
      const cz = s * (13 + R() * 6);
      if (livre(x) || adro(x, cz) || (x > -8 && x < 4 && s > 0)) continue;
      canteiros.push([x, cz]);
      add(env, new THREE.BoxGeometry(6, 0.25, 3.2), std('#4a3a2b', { roughness: 1 }), [x, 0.12, cz], [0, 0, 0], false);
      add(env, new THREE.BoxGeometry(6.2, 0.6, 0.4), sebe, [x, 0.3, cz - 1.6]);
      add(env, new THREE.BoxGeometry(6.2, 0.6, 0.4), sebe, [x, 0.3, cz + 1.6]);
      for (let k = 0; k < 14; k++) add(env, new THREE.SphereGeometry(0.12, 6, 5), std(florCols[k % 4]), [x - 2.6 + R() * 5.2, 0.35, cz - 1.1 + R() * 2.2], [0, 0, 0], false);
    }
  }

  // figueiras e palmeiras-imperiais: fileira densa junto ao caminho e mais árvores ao fundo
  for (let x = X0; x < X1 - 10; x += 6.5 + R() * 3) {
    for (const s of [-1, 1]) {
      const z = s * (7 + R() * 3);
      if (adro(x, z) || (livre(x) && Math.abs(z) < 9) || (s > 0 && x > -9 && x < 5)) continue;
      if (R() < 0.22) palmeira(env, R, x, z, 9 + R() * 4);
      else figueira(env, R, x, z, 1.0 + R() * 0.4);
    }
  }
  for (let i = 0; i < 70; i++) {
    const x = X0 + R() * (L - 10), s = R() < 0.5 ? -1 : 1, z = s * (12 + R() * 12);
    if (adro(x, z) || (s > 0 && x > -9 && x < 5 && z < 16)) continue;
    if (R() < 0.25) palmeira(env, R, x, z, 10 + R() * 4);
    else figueira(env, R, x, z, 1.0 + R() * 0.5);
  }
  // palmeiras-imperiais ladeando o adro da igreja
  palmeira(env, R, xIgreja + 17, -7, 12);
  palmeira(env, R, xIgreja + 23, -7, 13);
  palmeira(env, R, xIgreja + 15, 15, 12.5)

  // postes brancos em Y e bancos "EU ♥ BURI" ao longo do caminho
  const bancoM = std('#ffffff', { map: canvasTex(bancoCanvas()), roughness: 0.6 });
  for (let x = X0 + 4; x < X1 - 30; x += 13) {
    if (x < -9) continue;
    posteY(env, x, 4.4);
    posteY(env, x + 6.5, -4.4);
    if (!livre(x + 3)) {
      banco(env, x + 3, 5.2, Math.PI, bancoM);
      banco(env, x + 9.5, -5.2, 0, bancoM);
    }
  }
  // banco vermelho de madeira "EU ♥ BURI" em frente ao chafariz
  const vermelho = std('#9b2226');
  const bv = new THREE.Group();
  bv.position.set(-2, 0, 6.6);
  bv.rotation.y = Math.PI;
  env.add(bv);
  add(bv, new THREE.BoxGeometry(2.4, 0.12, 0.7), vermelho, [0, 0.5, 0]);
  for (let k = 0; k < 6; k++) add(bv, new THREE.BoxGeometry(0.28, 1.1, 0.06), vermelho, [-1.0 + k * 0.4, 1.1, -0.32]);
  const placa = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 0.3), std('#ffffff', { map: canvasTex(textCanvas(['EU ♥ BURI'], { w: 512, h: 96, color: '#ffffff', bg: '#c1121f', size: 64 })) }));
  placa.position.set(0, 1.75, -0.3);
  bv.add(placa);

  // casas em volta da praça (do outro lado das ruas)
  const cores = ['#f4d35e', '#ee964b', '#7bc8a4', '#a8dadc', '#f7b2bd', '#fdf6e3', '#5fb7e5', '#c3a6e0'];
  const telha = std('#b5532f');
  for (const s of [-1, 1]) {
    for (let x = X0; x < X1; x += 6 + R() * 3) {
      const w = 5 + R() * 2.5, h = 3.2 + R() * 2.5, d = 7;
      add(env, new THREE.BoxGeometry(w, h, d), std(cores[Math.floor(R() * cores.length)]), [x + w / 2, h / 2, s * (42 + d / 2)]);
      add(env, new THREE.BoxGeometry(w + 0.4, 0.5, d + 0.4), telha, [x + w / 2, h + 0.25, s * (42 + d / 2)]);
    }
  }
  // carros estacionados nas ruas laterais
  const carCols = ['#d62828', '#f7f7f7', '#1d3557', '#8d99ae', '#fcbf49'];
  for (const s of [-1, 1]) for (let x = X0 + 10; x < X1; x += 14 + R() * 14) {
    const car = new THREE.Group();
    car.position.set(x, 0, s * 32.2);
    env.add(car);
    const body = std(carCols[Math.floor(R() * carCols.length)], { roughness: 0.3, metalness: 0.3 });
    add(car, new THREE.BoxGeometry(3.9, 0.7, 1.7), body, [0, 0.62, 0]);
    add(car, new THREE.BoxGeometry(2.1, 0.6, 1.55), body, [-0.2, 1.25, 0]);
    for (const [wx, wz] of [[1.25, 0.8], [-1.25, 0.8], [1.25, -0.8], [-1.25, -0.8]]) add(car, new THREE.CylinderGeometry(0.34, 0.34, 0.25, 12), std('#151515'), [wx, 0.34, wz], [Math.PI / 2, 0, 0]);
  }

  // folhagem instanciada (3 tons de cartão de folhas)
  const cartoes = [3, 9, 17].map((seed, k) => new THREE.MeshStandardMaterial({
    map: canvasTex(folhagemCanvas(undefined, 256, seed)), alphaTest: 0.45, side: THREE.DoubleSide, roughness: 0.8,
  }));
  FOL.criar(env, cartoes);

  // grama nos canteiros
  const capim = new THREE.InstancedMesh(new THREE.ConeGeometry(0.035, 0.32, 3), std('#4f8f2f', { roughness: 0.9 }), 6000);
  const mtx = new THREE.Matrix4();
  let nCapim = 0;
  for (const [cx, cz] of canteiros) for (let k = 0; k < 400 && nCapim < 6000; k++) {
    mtx.makeRotationZ((R() - 0.5) * 0.5).setPosition(cx - 2.8 + R() * 5.6, 0.38, cz - 1.3 + R() * 2.6);
    capim.setMatrixAt(nCapim++, mtx);
  }
  capim.count = nCapim;
  env.add(capim);

  const fundo = paisagemDistante(env, R, X0, L);
  const chegada = cfg.semChegada ? null : porticoDeChegada(env, R, finishX, logoImg, livre, cfg.textoChegada || 'CHEGADA');

  function update(t, charX) {
    fundo.update(t);
    animaChafariz(t);
    if (chegada) chegada.update(t, charX);
  }
  return { group: env, update, arch: chegada?.arch };
}
