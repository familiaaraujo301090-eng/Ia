// "Sheets" de produção gerados pelo próprio motor:
//  - personagem: turnaround (frente, 3/4, perfil, costas), detalhes e poses-chave
//  - cenario: mapa do percurso visto de cima + vistas dos ambientes
//  - storyboard: um quadro por cena do roteiro com câmera, ação e notas
import * as THREE from 'three';
import { poseFor, applyPose } from './animation.js';
import { FONT } from './textures.js';

const BG = '#f3f5fa', INK = '#13296b', BLUE = '#2246a8', GREEN = '#4dd75d';

function newCanvas(w, h) {
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  const g = c.getContext('2d');
  g.fillStyle = BG;
  g.fillRect(0, 0, w, h);
  return [c, g];
}

function text(g, s, x, y, { size = 24, color = INK, weight = 'bold', align = 'left', base = 'top' } = {}) {
  g.font = `${weight} ${size}px ${FONT}`;
  g.fillStyle = color;
  g.textAlign = align;
  g.textBaseline = base;
  g.fillText(s, x, y);
}

function para(g, s, x, y, maxW, size = 18, color = '#333', lh = 1.35) {
  g.font = `normal ${size}px ${FONT}`;
  g.fillStyle = color;
  g.textAlign = 'left';
  g.textBaseline = 'top';
  let line = '', yy = y;
  for (const w of s.split(' ')) {
    const tst = line ? line + ' ' + w : w;
    if (g.measureText(tst).width > maxW && line) {
      g.fillText(line, x, yy);
      yy += size * lh;
      line = w;
    } else line = tst;
  }
  if (line) g.fillText(line, x, yy);
  return yy + size * lh;
}

function header(g, W, title, sub, logo) {
  g.fillStyle = BLUE;
  g.fillRect(0, 0, W, 110);
  g.fillStyle = GREEN;
  g.fillRect(0, 110, W, 8);
  g.drawImage(logo, 24, 12, 86, 86);
  text(g, title, 130, 22, { size: 38, color: '#fff' });
  text(g, sub, 130, 68, { size: 20, color: '#cfe0ff', weight: 'normal' });
}

function panel(g, img, x, y, w, h, label) {
  g.save();
  g.fillStyle = '#fff';
  g.shadowColor = 'rgba(0,0,0,0.15)';
  g.shadowBlur = 12;
  g.fillRect(x - 6, y - 6, w + 12, h + 12 + (label ? 34 : 0));
  g.restore();
  g.drawImage(img, x, y, w, h);
  if (label) text(g, label, x + w / 2, y + h + 8, { size: 18, align: 'center' });
}

export function buildSheets(E) {
  const { THREE: T, renderer, scene, camera, char, env, sky, timeline, roteiro } = E;
  const logoC = (() => {
    const c = document.createElement('canvas');
    c.width = c.height = 256;
    const g = c.getContext('2d');
    g.beginPath();
    g.arc(128, 128, 128, 0, Math.PI * 2);
    g.clip();
    g.drawImage(E.logo, -9, -9, 274, 274);
    return c;
  })();

  function snap(w, h, cam = camera) {
    renderer.setSize(w, h);
    if (cam.isPerspectiveCamera) {
      cam.aspect = w / h;
      cam.updateProjectionMatrix();
    }
    renderer.render(scene, cam);
    const c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    c.getContext('2d').drawImage(renderer.domElement, 0, 0);
    return c;
  }

  // estúdio neutro para o model sheet
  function studio(on) {
    env.group.visible = !on;
    sky.visible = !on;
    scene.background = on ? new T.Color('#dfe6f2') : null;
    scene.fog.near = on ? 1e4 : 60;
    scene.fog.far = on ? 2e4 : 420;
    if (on && !E.plinth) {
      E.plinth = new T.Mesh(new T.CircleGeometry(1.6, 48), new T.MeshStandardMaterial({ color: '#c3cde0', roughness: 0.9 }));
      E.plinth.rotation.x = -Math.PI / 2;
      E.plinth.receiveShadow = true;
      scene.add(E.plinth);
    }
    if (E.plinth) E.plinth.visible = on;
  }

  function studioShot(pose, heading, camPos, look, w, h, fov = 30) {
    pose.heading = heading;
    applyPose(char, pose, 0);
    E.sun.position.set(-6, 14, 10);
    E.sun.target.position.set(0, 0, 0);
    camera.fov = fov;
    camera.position.set(...camPos);
    camera.lookAt(...look);
    return snap(w, h);
  }

  const fakeState = (acao, local, phase = 0, u = 0.9) => ({ cena: { acao }, u, local, phase });
  const neutral = () => {
    const p = poseFor(fakeState('neutro', 0));
    p.shoulderL = [0, 0, 0.38];
    p.shoulderR = [0, 0, -0.38];
    return p;
  };

  function personagem() {
    const W = 1800, H = 1250;
    const [c, g] = newCanvas(W, H);
    header(g, W, 'MODEL SHEET · Corredor Amigos do Serginho', 'Personagem 3D procedural · boné, camisa com logo, short e tênis azuis · Buri - SP', logoC);
    studio(true);
    const views = [
      ['FRENTE', 0],
      ['3/4', -Math.PI / 4],
      ['PERFIL', -Math.PI / 2],
      ['COSTAS', Math.PI],
    ];
    text(g, 'TURNAROUND', 40, 140, { size: 26, color: BLUE });
    views.forEach(([lbl, hd], i) => {
      const img = studioShot(neutral(), hd, [0, 1.15, 7.2], [0, 1.0, 0], 300, 520);
      panel(g, img, 40 + i * 330, 180, 300, 520, lbl);
    });
    // detalhes
    text(g, 'DETALHES', 1380, 140, { size: 26, color: BLUE });
    const capImg = studioShot(neutral(), -0.35, [0.35, 2.05, 1.6], [0, 1.98, 0], 380, 240, 30);
    panel(g, capImg, 1380, 180, 380, 240, 'Boné azul com o logo');
    const chestImg = studioShot(neutral(), 0, [0, 1.45, 1.5], [0, 1.42, 0], 380, 240, 30);
    panel(g, chestImg, 1380, 470, 380, 240, 'Camisa: logo Amigos do Serginho');
    // poses-chave
    text(g, 'POSES-CHAVE (animações)', 40, 760, { size: 26, color: BLUE });
    const poses = [
      ['Alongar', poseFor(fakeState('alongar', 1.1, 0, 0.2))],
      ['Correr', poseFor(fakeState('correr', 0, 1.2))],
      ['Comemorar', poseFor(fakeState('chegada', 0.3, 0, 0.9))],
      ['Acenar', poseFor(fakeState('acenar', 1.0, 0, 0.9))],
    ];
    poses.forEach(([lbl, p], i) => {
      const hd = lbl === 'Acenar' ? -0.3 : lbl === 'Correr' ? Math.PI / 2 - 0.5 : -0.5;
      const img = studioShot(p, hd, [0, 1.3, 7.5], [0, 1.1, 0], 300, 380);
      panel(g, img, 40 + i * 330, 800, 300, 380, lbl);
    });
    // paleta
    text(g, 'PALETA', 1380, 760, { size: 26, color: BLUE });
    const pal = [
      ['Uniforme', roteiro.personagem.cores.uniforme],
      ['Detalhes', roteiro.personagem.cores.uniformeEscuro],
      ['Verde logo', GREEN],
      ['Pele', roteiro.personagem.cores.pele],
      ['Solado/meia', '#f2f2f2'],
    ];
    pal.forEach(([n, col], i) => {
      g.fillStyle = col;
      g.fillRect(1380, 805 + i * 72, 90, 56);
      g.strokeStyle = '#999';
      g.strokeRect(1380, 805 + i * 72, 90, 56);
      text(g, n, 1490, 812 + i * 72, { size: 20 });
      text(g, col, 1490, 838 + i * 72, { size: 16, weight: 'normal', color: '#555' });
    });
    studio(false);
    return c;
  }

  function cenario() {
    const W = 1800, H = 1250;
    const [c, g] = newCanvas(W, H);
    header(g, W, 'SHEET DE CENÁRIO · Rua de Buri - SP', `Percurso de ${Math.round(timeline.finishX)} m de corrida até o pórtico de CHEGADA · cenário 100% procedural`, logoC);
    // mapa visto de cima (câmera ortográfica)
    const x0 = -20, x1 = timeline.finishX + 20;
    const mapW = 1720, mapH = 260;
    const half = (x1 - x0) / 2;
    const oc = new T.OrthographicCamera(-half, half, (half * mapH) / mapW, (-half * mapH) / mapW, 1, 500);
    oc.position.set((x0 + x1) / 2, 200, 0);
    oc.up.set(0, 0, -1);
    oc.lookAt((x0 + x1) / 2, 0, 0);
    pose(timeline.at(0.1));
    const map = snap(mapW, mapH, oc);
    text(g, 'MAPA DO PERCURSO (vista de cima) e divisão das cenas', 40, 140, { size: 26, color: BLUE });
    panel(g, map, 40, 180, mapW, mapH);
    const toPx = (x) => 40 + ((x - x0) / (x1 - x0)) * mapW;
    const colors = ['#e8262b', '#f2c230', '#4dd75d', '#2bb3e6', '#a05ce0', '#ff7a1a', '#13296b'];
    timeline.cenas.forEach((cn, i) => {
      const a = timeline.at(cn.inicio + 0.001).x, b = timeline.at(cn.fim - 0.001).x;
      const xa = toPx(a), xb = Math.max(toPx(b), xa + 8);
      g.fillStyle = colors[i % colors.length];
      g.globalAlpha = 0.85;
      g.fillRect(xa, 455, xb - xa, 14);
      g.globalAlpha = 1;
      text(g, `${i + 1}. ${cn.id}`, xa, 476 + (i % 2) * 24, { size: 16, color: colors[i % colors.length] });
    });

    // vistas
    const shots = [
      ['Largada: rua, calçadas, casas e postes', 1.0, [9, 2.6, 2.5], [0, 1.2, -1.5]],
      ['Faixas da equipe e cones de prova', 14, [timeline.at(14).x + 10, 2.6, 2], [timeline.at(14).x + 2, 1.6, -4]],
      ['Pórtico de CHEGADA, fita e torcida', null, null, null],
    ];
    shots.forEach(([lbl, t, cp, lk], i) => {
      if (t === null) {
        pose(timeline.at(timeline.cenas[5].inicio + 0.3));
        const fx = timeline.finishX;
        camera.position.set(fx - 14, 2.2, 3);
        camera.lookAt(fx, 2.2, 0);
      } else {
        pose(t);
        camera.position.set(...cp);
        camera.lookAt(...lk);
      }
      camera.fov = 55;
      const img = snap(540, 440);
      panel(g, img, 40 + i * 590, 560, 540, 440, lbl);
    });
    const items = 'Elementos: asfalto texturizado, faixa amarela central, meio-fio, calçadas, casas coloridas com telhado de barro, árvores, postes, faixas "AMIGOS DO SERGINHO / BURI - SP / BORA CORRER!", cones, morros, nuvens animadas, céu em degradê, sol com sombras, pórtico de chegada com fita que se rompe e torcida pulando.';
    para(g, items, 40, 1060, W - 80, 20);
    return c;
  }

  function storyboard() {
    const cenas = timeline.cenas;
    const cols = 4, tw = 300, th = 533, cw = 430, ch = 820;
    const W = 40 + cols * cw, H = 160 + Math.ceil((cenas.length + 1) / cols) * ch;
    const [c, g] = newCanvas(W, H);
    header(g, W, 'STORYBOARD · ' + roteiro.titulo, `${cenas.length} cenas · ${timeline.total.toFixed(1)} s · ${roteiro.formato.largura}x${roteiro.formato.altura} vertical`, logoC);
    cenas.forEach((cn, i) => {
      const x = 40 + (i % cols) * cw, y = 150 + Math.floor(i / cols) * ch;
      const img = E.renderComposite(cn.inicio + cn.duracao * 0.65, 540, 960);
      panel(g, img, x, y, tw, th);
      text(g, `CENA ${i + 1} · ${cn.id.toUpperCase()}`, x, y + th + 20, { size: 22, color: BLUE });
      text(g, `${cn.inicio.toFixed(1)}s – ${cn.fim.toFixed(1)}s · ação: ${cn.acao} · câmera: ${cn.camera.tipo}`, x, y + th + 50, { size: 15, weight: 'normal', color: '#555' });
      para(g, cn.nota, x, y + th + 76, cw - 40, 16, '#333');
    });
    const i = cenas.length, x = 40 + (i % cols) * cw, y = 150 + Math.floor(i / cols) * ch;
    text(g, 'ROTEIRO (legendas)', x, y, { size: 22, color: BLUE });
    let yy = y + 40;
    cenas.forEach((cn, k) => {
      yy = para(g, `${k + 1}. ${cn.texto}`, x, yy, cw - 40, 14, '#222') + 6;
    });
    renderer.setSize(E.W, E.H);
    return c;
  }

  // pose() do main.js é importada de forma tardia para evitar ciclo de módulos
  const pose = (st) => (typeof st === 'number' ? E.pose(st) : E.pose(st.cena.inicio + st.local));

  return { personagem, cenario, storyboard };
}
