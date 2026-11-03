// Personagem a partir de um modelo 3D pronto (.glb/.gltf ou .fbx do Mixamo), com
// animações tocadas de forma determinística pelo tempo do roteiro. Configuração no
// roteiro (personagem.modelo):
//   "arquivo": "assets/corredor.glb",
//   "altura": 2.0,                         altura final em metros
//   "rotacaoY": 0,                          corrige a frente do modelo (deve olhar para +Z)
//   "animacoes": { "correr": "Running" | "assets/run.fbx", "acenar": ..., "comemorar": ..., "parado": ... },
//   "cores": { "NomeDoMaterial": "#2246a8" },  recolore materiais (uniforme azul)
//   "logo": { "osso": "Torso", "posicao": [0, 0.1, 0.3], "tamanho": 0.3 }
//            posicao em metros a partir do osso, com +Z = frente do personagem
// O mesmo modelo pode ser clonado (clonar) para formar um grupo de corredores.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { FBXLoader } from 'three/addons/loaders/FBXLoader.js';
import { clone as cloneSkinned } from 'three/addons/utils/SkeletonUtils.js';
import { logoCircleCanvas } from './textures.js';

async function carregar(url) {
  if (/\.fbx$/i.test(url)) {
    const obj = await new FBXLoader().loadAsync(url);
    return { cena: obj, clips: obj.animations || [] };
  }
  const g = await new GLTFLoader().loadAsync(url);
  return { cena: g.scene, clips: g.animations || [] };
}

// substitutas quando o modelo não tem a animação pedida
const SUBST = { alongar: ['parado', 'acenar'], parado: ['alongar', 'acenar'], comemorar: ['acenar', 'parado'], acenar: ['comemorar', 'parado'], correr: ['parado'] };

export async function buildModelCharacter(cfg, logoImg) {
  const m = cfg.modelo;
  const { cena: base, clips } = await carregar('/' + m.arquivo);

  // escala para a altura pedida e pés no chão
  base.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(base);
  const k = (m.altura || 2.0) / Math.max(1e-6, box.max.y - box.min.y);
  base.scale.multiplyScalar(k);
  base.position.y -= box.min.y * k;

  // clipes por ação (do próprio modelo ou de arquivos separados)
  const clipes = {};
  for (const [acao, ref] of Object.entries(m.animacoes || {})) {
    let clip = null;
    if (/\.(fbx|glb|gltf)$/i.test(ref)) clip = (await carregar('/' + ref)).clips[0];
    else clip = clips.find((c) => c.name === ref) || clips.find((c) => c.name.toLowerCase().includes(ref.toLowerCase()));
    if (!clip) {
      console.warn(`animação "${ref}" não encontrada para "${acao}"`);
      continue;
    }
    clip = clip.clone();
    // tira o deslocamento da raiz: o motor já move o personagem pela rua
    clip.tracks = clip.tracks.filter((tr) => !(/\.position$/.test(tr.name) && /(hips|root|armature)/i.test(tr.name)) || acao === 'comemorar');
    clipes[acao] = clip;
  }

  const logoTex = logoImg ? new THREE.CanvasTexture(logoCircleCanvas(logoImg, 512)) : null;
  if (logoTex) logoTex.colorSpace = THREE.SRGBColorSpace;

  function instancia(cores = m.cores || {}) {
    const cena = cloneSkinned(base);
    const root = new THREE.Group();
    root.name = 'personagem';
    const corpo = new THREE.Group();
    corpo.rotation.y = m.rotacaoY || 0;
    corpo.add(cena);
    root.add(corpo);

    cena.traverse((o) => {
      if (!o.isMesh) return;
      o.castShadow = o.receiveShadow = true;
      o.frustumCulled = false;
      const mats = (Array.isArray(o.material) ? o.material : [o.material]).map((mt) => {
        const c = mt.clone();
        if (cores[mt.name] && c.color) c.color.set(cores[mt.name]);
        return c;
      });
      o.material = Array.isArray(o.material) ? mats : mats[0];
    });

    // logo da equipe preso a um osso, olhando para a frente do personagem
    if (m.logo && logoTex) {
      let osso = null;
      cena.traverse((o) => {
        if (!osso && o.name && o.name.toLowerCase() === m.logo.osso.toLowerCase()) osso = o;
      });
      cena.traverse((o) => {
        if (!osso && o.name && o.name.toLowerCase().includes(m.logo.osso.toLowerCase())) osso = o;
      });
      if (osso) {
        root.updateMatrixWorld(true);
        const disco = new THREE.Mesh(new THREE.CircleGeometry(0.5, 48), new THREE.MeshStandardMaterial({ map: logoTex, transparent: true, roughness: 0.5 }));
        const alvo = osso.getWorldPosition(new THREE.Vector3()).add(new THREE.Vector3(...(m.logo.posicao || [0, 0, 0.3])));
        const qOsso = osso.getWorldQuaternion(new THREE.Quaternion());
        const sOsso = osso.getWorldScale(new THREE.Vector3());
        disco.position.copy(osso.worldToLocal(alvo));
        disco.quaternion.copy(qOsso.invert());
        disco.scale.setScalar((m.logo.tamanho || 0.3) / sOsso.x);
        osso.add(disco);
      }
    }

    const mixer = new THREE.AnimationMixer(cena);
    const actions = {};
    for (const [acao, clip] of Object.entries(clipes)) {
      const a = mixer.clipAction(clip);
      a.play();
      a.setEffectiveWeight(0);
      actions[acao] = a;
    }

    // pesos e tempos de cada animação no instante pedido
    function anim(pesos, t, phase) {
      const final = {};
      for (const [acao, w] of Object.entries(pesos)) {
        const alvo = actions[acao] ? acao : (SUBST[acao] || []).find((x) => actions[x]);
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

    return { root, joints: {}, modelo: true, anim, acoes: Object.keys(actions) };
  }

  const principal = instancia();
  principal.clonar = instancia;
  principal.clips = clips.map((c) => c.name);
  return principal;
}
