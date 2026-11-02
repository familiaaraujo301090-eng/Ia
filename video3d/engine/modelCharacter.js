// Personagem a partir de um modelo 3D pronto (.glb/.gltf ou .fbx do Mixamo), com
// animações tocadas de forma determinística pelo tempo do roteiro. Configuração no
// roteiro (personagem.modelo):
//   "arquivo": "assets/corredor.glb",
//   "altura": 2.0,                         altura final em metros
//   "rotacaoY": 0,                          corrige a frente do modelo (deve olhar para +Z)
//   "animacoes": { "correr": "Running" | "assets/run.fbx", "acenar": ..., "comemorar": ..., "parado": ... },
//   "cores": { "NomeDoMaterial": "#2246a8" },  recolore materiais (uniforme azul)
//   "logo": { "osso": "Spine2", "posicao": [0, 0.1, 0.15], "tamanho": 0.22 }
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { FBXLoader } from 'three/addons/loaders/FBXLoader.js';
import { logoCircleCanvas } from './textures.js';

async function carregar(url) {
  if (/\.fbx$/i.test(url)) {
    const obj = await new FBXLoader().loadAsync(url);
    return { cena: obj, clips: obj.animations || [] };
  }
  const g = await new GLTFLoader().loadAsync(url);
  return { cena: g.scene, clips: g.animations || [] };
}

export async function buildModelCharacter(cfg, logoImg) {
  const m = cfg.modelo;
  const { cena, clips } = await carregar('/' + m.arquivo);
  const root = new THREE.Group();
  root.name = 'personagem';
  const corpo = new THREE.Group();
  corpo.rotation.y = m.rotacaoY || 0;
  corpo.add(cena);
  root.add(corpo);

  // escala para a altura pedida e pés no chão
  cena.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(cena);
  const k = (m.altura || 2.0) / Math.max(1e-6, box.max.y - box.min.y);
  cena.scale.multiplyScalar(k);
  cena.position.y -= box.min.y * k;

  const recolor = m.cores || {};
  cena.traverse((o) => {
    if (!o.isMesh) return;
    o.castShadow = o.receiveShadow = true;
    o.frustumCulled = false;
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    mats.forEach((mt) => {
      if (recolor[mt.name] && mt.color) mt.color.set(recolor[mt.name]);
    });
  });

  // logo preso a um osso (ex.: peito)
  if (m.logo && logoImg) {
    let osso = null;
    cena.traverse((o) => {
      if (!osso && o.name && o.name.toLowerCase().includes(m.logo.osso.toLowerCase())) osso = o;
    });
    if (osso) {
      const tex = new THREE.CanvasTexture(logoCircleCanvas(logoImg, 512));
      tex.colorSpace = THREE.SRGBColorSpace;
      const disco = new THREE.Mesh(new THREE.CircleGeometry(0.5, 48), new THREE.MeshStandardMaterial({ map: tex, transparent: true, roughness: 0.6 }));
      const ws = new THREE.Vector3();
      osso.getWorldScale(ws);
      const t = (m.logo.tamanho || 0.22) / ws.x;
      disco.scale.setScalar(t);
      disco.position.set(...(m.logo.posicao || [0, 0, 0.15])).divideScalar(ws.x);
      if (m.logo.rotacao) disco.rotation.set(...m.logo.rotacao);
      osso.add(disco);
    }
  }

  // animações: nome de clipe do próprio modelo ou arquivo separado (1º clipe do arquivo)
  const mixer = new THREE.AnimationMixer(cena);
  const actions = {};
  for (const [acao, ref] of Object.entries(m.animacoes || {})) {
    let clip = null;
    if (/\.(fbx|glb|gltf)$/i.test(ref)) clip = (await carregar('/' + ref)).clips[0];
    else clip = clips.find((c) => c.name === ref) || clips.find((c) => c.name.toLowerCase().includes(ref.toLowerCase()));
    if (!clip) {
      console.warn(`animação "${ref}" não encontrada para "${acao}"`);
      continue;
    }
    // remove o deslocamento da raiz (o motor já move o personagem pela rua)
    clip = clip.clone();
    clip.tracks = clip.tracks.filter((tr) => !(/\.position$/.test(tr.name) && /(hips|root|armature)/i.test(tr.name)) || acao === 'comemorar');
    const a = mixer.clipAction(clip);
    a.play();
    a.setEffectiveWeight(0);
    actions[acao] = a;
  }

  // define pesos e tempos de cada animação para o instante pedido. Ações ausentes no
  // modelo caem em substitutas (alongar -> parado, comemorar -> acenar/parado...).
  const subst = { alongar: ['parado', 'acenar'], parado: ['alongar', 'acenar'], comemorar: ['acenar', 'parado'], acenar: ['comemorar', 'parado'], correr: ['parado'] };
  function anim(pesos, t, phase) {
    const final = {};
    for (const [acao, w] of Object.entries(pesos)) {
      const alvo = actions[acao] ? acao : (subst[acao] || []).find((x) => actions[x]);
      if (alvo) final[alvo] = (final[alvo] || 0) + w;
    }
    for (const [acao, a] of Object.entries(actions)) {
      const w = final[acao] || 0;
      const dur = a.getClip().duration;
      a.setEffectiveWeight(w);
      // a corrida acompanha a cadência do motor (1 ciclo de passada por volta da fase)
      a.time = w <= 0 ? 0 : acao === 'correr' ? ((phase / (Math.PI * 2)) % 1) * dur : t % dur;
    }
    mixer.update(0);
  }

  return { root, joints: {}, modelo: true, anim, acoes: Object.keys(actions), clips: clips.map((c) => c.name) };
}
