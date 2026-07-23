import * as THREE from "three";
import { VIEWER_COLORS } from "../config/colors.js";

export function createScannerPoint(radiusMm = 45) {
  const radius = radiusMm * 0.001;
  const group = new THREE.Group();
  group.name = "scanner-point";
  const sphere = new THREE.Mesh(
    new THREE.SphereGeometry(radius, 24, 16),
    new THREE.MeshStandardMaterial({
      color: VIEWER_COLORS.scanner,
      emissive: VIEWER_COLORS.scanner,
      emissiveIntensity: 4.5,
      roughness: 0.28,
    }),
  );
  const halo = new THREE.Mesh(
    new THREE.SphereGeometry(radius * 2.25, 20, 12),
    new THREE.MeshBasicMaterial({
      color: VIEWER_COLORS.scanner,
      transparent: true,
      opacity: 0.15,
      depthWrite: false,
    }),
  );
  const light = new THREE.PointLight(VIEWER_COLORS.scanner, 5, 1.4, 2);
  group.add(sphere, halo, light);

  return {
    group,
    update(position, elapsed) {
      group.position.copy(position);
      halo.scale.setScalar(1 + Math.sin(elapsed * 5) * 0.09);
    },
  };
}
