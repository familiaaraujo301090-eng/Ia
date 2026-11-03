// Modo realista (cenario.realista = true): céu físico com dispersão atmosférica,
// iluminação de ambiente vinda do próprio céu (reflexos e luz indireta), sombras
// mais finas e pós-processamento com oclusão de ambiente (GTAO) e um leve brilho.
import * as THREE from 'three';
import { Sky } from 'three/addons/objects/Sky.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

function novoCeu(sol) {
  const sky = new Sky();
  const u = sky.material.uniforms;
  u.turbidity.value = 2.2;
  u.rayleigh.value = 2.6;
  u.mieCoefficient.value = 0.004;
  u.mieDirectionalG.value = 0.82;
  u.sunPosition.value.copy(sol);
  return sky;
}

export function setupRealismo(E) {
  const { renderer, scene, camera, W, H, roteiro } = E;
  const sol = new THREE.Vector3(...(roteiro.cenario.sol || [-12, 22, 14])).normalize();

  scene.remove(E.sky);
  E.sky = novoCeu(sol);
  E.sky.scale.setScalar(1500);
  scene.add(E.sky);

  // luz de ambiente gerada a partir do céu
  const pm = new THREE.PMREMGenerator(renderer);
  const cena = new THREE.Scene();
  cena.add(novoCeu(sol));
  scene.environment = pm.fromScene(cena, 0.03).texture;
  pm.dispose();

  scene.fog = new THREE.Fog(roteiro.cenario.neblina || '#cddcea', 140, 800);
  E.hemi.intensity = 0.25;
  E.sun.intensity = 3.4;
  E.sun.color.set('#fff4e2');
  E.sun.shadow.mapSize.set(2048, 2048);
  E.sun.shadow.radius = 3;
  const sc = E.sun.shadow.camera;
  sc.left = sc.bottom = -20;
  sc.right = sc.top = 20;
  sc.updateProjectionMatrix();
  renderer.toneMappingExposure = 0.88;
  // a luz do céu é forte: dosamos o reflexo/luz indireta em todos os materiais
  scene.traverse((o) => {
    if (!o.isMesh) return;
    for (const m of Array.isArray(o.material) ? o.material : [o.material]) if ('envMapIntensity' in m) m.envMapIntensity = 0.3;
  });

  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  const ao = new GTAOPass(scene, camera, W, H);
  ao.updateGtaoMaterial({ radius: 0.7, distanceExponent: 1.2, thickness: 1.2, scale: 1.1, samples: 6 });
  ao.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 4, rings: 1, samples: 6 });
  composer.addPass(ao);
  composer.addPass(new UnrealBloomPass(new THREE.Vector2(W, H), 0.12, 0.4, 0.97));
  composer.addPass(new OutputPass());
  E.composer = composer;
  E.composerSize = [W, H];
}

export function renderRealista(E, W, H) {
  if (E.composerSize[0] !== W || E.composerSize[1] !== H) {
    E.composer.setSize(W, H);
    E.composerSize = [W, H];
  }
  E.composer.render();
}
