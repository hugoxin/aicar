import * as THREE from "three";
import { VIEWER_COLORS } from "../config/colors.js";

export function createGround(scene, { showGrid = true, showAxes = false } = {}) {
  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(18, 18),
    new THREE.MeshStandardMaterial({
      color: VIEWER_COLORS.groundDark,
      roughness: 0.95,
      metalness: 0.02,
    }),
  );
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.015;
  ground.receiveShadow = true;

  const grid = new THREE.GridHelper(18, 36, 0x527084, 0x293a46);
  grid.material.transparent = true;
  grid.material.opacity = 0.46;
  grid.visible = showGrid;

  const axes = new THREE.AxesHelper(2.5);
  axes.visible = showAxes;
  scene.add(ground, grid, axes);

  return {
    ground,
    grid,
    axes,
    setLightMode(isLight) {
      ground.material.color.set(isLight ? VIEWER_COLORS.groundLight : VIEWER_COLORS.groundDark);
      grid.material.color?.set(isLight ? 0x8e9aa4 : 0x293a46);
    },
  };
}
