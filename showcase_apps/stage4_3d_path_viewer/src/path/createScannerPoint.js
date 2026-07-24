import * as THREE from "three";
import { stateColor, VIEWER_COLORS } from "../config/colors.js";

function createCrosshairTexture() {
  const canvas = document.createElement("canvas");
  canvas.width = 128;
  canvas.height = 128;
  const context = canvas.getContext("2d");
  context.clearRect(0, 0, 128, 128);
  context.strokeStyle = "#ffffff";
  context.lineWidth = 3;
  context.globalAlpha = 0.9;
  context.beginPath();
  context.arc(64, 64, 42, 0, Math.PI * 2);
  context.moveTo(64, 8);
  context.lineTo(64, 34);
  context.moveTo(64, 94);
  context.lineTo(64, 120);
  context.moveTo(8, 64);
  context.lineTo(34, 64);
  context.moveTo(94, 64);
  context.lineTo(120, 64);
  context.stroke();
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

export function createScannerPoint(profile) {
  const radius = profile.scanner_point_radius * 0.001;
  const group = new THREE.Group();
  group.name = "scanner-point";
  group.renderOrder = 14;
  const sphereMaterial = new THREE.MeshStandardMaterial({
    color: VIEWER_COLORS.scanner,
    emissive: VIEWER_COLORS.scanner,
    emissiveIntensity: 4.8,
    roughness: 0.22,
  });
  const sphere = new THREE.Mesh(
    new THREE.SphereGeometry(radius, 24, 16),
    sphereMaterial,
  );
  sphere.renderOrder = 14;
  const haloMaterial = new THREE.MeshBasicMaterial({
    color: VIEWER_COLORS.scannerHalo,
    transparent: true,
    opacity: profile.scanner_halo_opacity,
    depthWrite: false,
  });
  const halo = new THREE.Mesh(
    new THREE.SphereGeometry(radius * profile.scanner_halo_radius_ratio, 20, 12),
    haloMaterial,
  );
  halo.renderOrder = 13;
  const light = new THREE.PointLight(VIEWER_COLORS.scanner, 5, 1.4, 2);
  const crosshair = new THREE.Sprite(
    new THREE.SpriteMaterial({
      map: createCrosshairTexture(),
      color: VIEWER_COLORS.scanner,
      transparent: true,
      opacity: 0.94,
      depthTest: false,
      depthWrite: false,
    }),
  );
  const crosshairSize = radius * profile.scanner_halo_radius_ratio * 2.25;
  crosshair.scale.setScalar(crosshairSize);
  crosshair.visible = profile.scanner_crosshair_enabled;
  crosshair.renderOrder = 15;
  group.add(sphere, halo, crosshair, light);

  return {
    group,
    update(position, elapsed, stateId) {
      group.position.copy(position);
      const color = new THREE.Color(stateColor(stateId));
      const highlighted = color.clone().lerp(new THREE.Color("#ffffff"), 0.34);
      sphereMaterial.color.copy(highlighted);
      sphereMaterial.emissive.copy(highlighted);
      haloMaterial.color.copy(highlighted);
      crosshair.material.color.copy(highlighted);
      light.color.copy(highlighted);

      const phase = (elapsed / profile.scanner_point_pulse_duration_s) * Math.PI * 2;
      const normalized = (Math.sin(phase) + 1) * 0.5;
      const pulse = 1 + (profile.scanner_point_pulse_scale - 1) * normalized;
      halo.scale.setScalar(pulse);
      crosshair.scale.setScalar(crosshairSize * (1 + (pulse - 1) * 0.55));
      sphereMaterial.emissiveIntensity = 4.4 + normalized * 1.1;
      haloMaterial.opacity = profile.scanner_halo_opacity * (0.78 + normalized * 0.22);
    },
  };
}
