import * as THREE from "three";
import { stateColor } from "../config/colors.js";

export function createTrail(pathPoints, vectors, profile) {
  const count = Math.max(2, Math.min(120, profile.trail_point_count));
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  const background = new THREE.Color("#101419");
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  geometry.setDrawRange(0, 0);
  const line = new THREE.Line(
    geometry,
    new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 1,
      depthTest: false,
      depthWrite: false,
    }),
  );
  line.name = "scanner-trail";
  line.renderOrder = 9;

  function rebuild(sample) {
    const start = Math.max(0, sample.index - count + 2);
    const trailVectors = vectors.slice(start, sample.index + 1);
    trailVectors.push(sample.position);
    const trailPoints = pathPoints.slice(start, sample.index + 1);
    trailPoints.push(sample.point);
    const visibleCount = Math.min(count, trailVectors.length);
    for (let index = 0; index < visibleCount; index += 1) {
      const vector = trailVectors[trailVectors.length - visibleCount + index];
      const point = trailPoints[trailPoints.length - visibleCount + index];
      const progress = visibleCount <= 1 ? 1 : index / (visibleCount - 1);
      const opacity =
        profile.trail_start_opacity
        + (profile.trail_end_opacity - profile.trail_start_opacity) * progress;
      vector.toArray(positions, index * 3);
      background
        .clone()
        .lerp(new THREE.Color(stateColor(point?.state_id)), opacity)
        .toArray(colors, index * 3);
    }
    geometry.attributes.position.needsUpdate = true;
    geometry.attributes.color.needsUpdate = true;
    geometry.setDrawRange(0, visibleCount);
  }

  function clear() {
    geometry.setDrawRange(0, 0);
  }

  return { line, rebuild, clear };
}
