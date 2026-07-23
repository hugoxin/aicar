import * as THREE from "three";

export function createLighting(scene) {
  const hemisphere = new THREE.HemisphereLight(0xeaf6ff, 0x17202a, 2.25);
  const key = new THREE.DirectionalLight(0xffffff, 3.1);
  key.position.set(5, 8, 3);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.camera.left = -8;
  key.shadow.camera.right = 8;
  key.shadow.camera.top = 8;
  key.shadow.camera.bottom = -8;
  const fill = new THREE.DirectionalLight(0x79c9ff, 1.25);
  fill.position.set(-5, 3, -4);
  scene.add(hemisphere, key, fill);
  return { hemisphere, key, fill };
}
