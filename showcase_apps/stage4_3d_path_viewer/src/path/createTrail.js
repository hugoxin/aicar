import * as THREE from "three";
import { VIEWER_COLORS } from "../config/colors.js";

export function createTrail(vectors, maximumPoints = 80) {
  const count = Math.max(2, maximumPoints);
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  const dim = new THREE.Color(0x756f47);
  const bright = new THREE.Color(VIEWER_COLORS.scanner);
  for (let index = 0; index < count; index += 1) {
    dim.clone().lerp(bright, index / (count - 1)).toArray(colors, index * 3);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  geometry.setDrawRange(0, 0);
  const line = new THREE.Line(
    geometry,
    new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      depthTest: false,
    }),
  );
  line.renderOrder = 9;

  function rebuild(sample) {
    const start = Math.max(0, sample.index - count + 2);
    const trailVectors = vectors.slice(start, sample.index + 1);
    trailVectors.push(sample.position);
    const offset = Math.max(0, count - trailVectors.length);
    const anchor = trailVectors[0] ?? sample.position;
    for (let index = 0; index < count; index += 1) {
      const vector = index < offset ? anchor : trailVectors[index - offset];
      vector.toArray(positions, index * 3);
    }
    geometry.attributes.position.needsUpdate = true;
    geometry.setDrawRange(offset, trailVectors.length);
  }

  function clear() {
    geometry.setDrawRange(0, 0);
  }

  return { line, rebuild, clear };
}
