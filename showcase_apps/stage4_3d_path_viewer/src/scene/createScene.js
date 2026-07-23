import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { createLighting } from "./createLighting.js";
import { createGround } from "./createGround.js";

export function createScene(container, profile) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x101419);
  scene.fog = new THREE.Fog(0x101419, 13, 26);

  const camera = new THREE.PerspectiveCamera(42, 1, 0.02, 100);
  camera.position.set(7, 5, 7);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(container.clientWidth, container.clientHeight, false);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.08;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  container.appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.07;
  controls.minDistance = 3.4;
  controls.maxDistance = 22;
  controls.maxPolarAngle = Math.PI * 0.49;
  controls.target.set(0, 0.9, 0);

  createLighting(scene);
  const ground = createGround(scene, {
    showGrid: profile.show_grid,
    showAxes: profile.show_axes,
  });

  function resize() {
    const width = Math.max(1, container.clientWidth);
    const height = Math.max(1, container.clientHeight);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height, false);
  }

  function setLightMode(isLight) {
    scene.background.set(isLight ? 0xe7ecf0 : 0x101419);
    scene.fog.color.set(isLight ? 0xe7ecf0 : 0x101419);
    ground.setLightMode(isLight);
  }

  return { scene, camera, renderer, controls, ground, resize, setLightMode };
}
