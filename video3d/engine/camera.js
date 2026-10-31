// Movimentos de câmera declarados no roteiro. Coordenadas são relativas à
// posição do personagem (x = direção da corrida, z = lado da câmera).
import * as THREE from 'three';

const { lerp, smoothstep, degToRad } = THREE.MathUtils;
const ease = (u) => smoothstep(u, 0, 1);
const v3 = (a) => new THREE.Vector3(...a);

export function cameraFor(cena, u, x, t) {
  const c = cena.camera;
  const e = ease(u);
  const pos = new THREE.Vector3();
  const look = new THREE.Vector3(x, 1.2, 0);
  let fov = 50;
  // leve "respiração" de câmera na mão
  const shake = new THREE.Vector3(Math.sin(t * 1.7) * 0.03, Math.sin(t * 2.3) * 0.02, 0);

  switch (c.tipo) {
    case 'grua':
    case 'aproximar':
      pos.copy(v3(c.de).lerp(v3(c.para), e)).add(new THREE.Vector3(x, 0, 0));
      look.copy(v3(c.alvo)).add(new THREE.Vector3(x, 0, 0));
      break;
    case 'lateral':
      pos.set(x + c.avanco, c.altura, c.distancia);
      look.set(x + c.avanco, 0.75, 0);
      fov = 45;
      break;
    case 'frontal': {
      const d = lerp(c.distanciaDe, c.distanciaPara, e);
      pos.set(x + d, c.altura, 0.6);
      look.set(x, lerp(0.75, 1.05, e), 0);
      fov = lerp(50, 38, e);
      break;
    }
    case 'orbita':
    case 'baixa': {
      const a = degToRad(lerp(c.anguloDe, c.anguloPara, e));
      pos.set(x + Math.cos(a) * c.raio, c.altura, Math.sin(a) * c.raio);
      look.set(x, c.tipo === 'baixa' ? 1.3 : 0.8, 0);
      fov = c.tipo === 'baixa' ? 58 : 48;
      break;
    }
    case 'drone':
      pos.set(x - lerp(c.atras, c.atrasPara, e), lerp(c.altura, c.alturaPara, e), 1.2);
      look.set(x + 1.5, 0.4, 0);
      break;
  }
  pos.add(shake);
  if (pos.y < 0.25) pos.y = 0.25;
  return { pos, look, fov };
}
