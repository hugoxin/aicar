import * as THREE from "three";

const MM_TO_M = 0.001;

function toThreePosition(values) {
  return new THREE.Vector3(
    values[0] * MM_TO_M,
    values[2] * MM_TO_M,
    -values[1] * MM_TO_M,
  );
}

export function createCameraPresetController(camera, controls, presets) {
  let transition = null;

  function moveTo(name, duration = 0.7) {
    const preset = presets[name];
    if (!preset) return;
    transition = {
      elapsed: 0,
      duration,
      fromPosition: camera.position.clone(),
      toPosition: toThreePosition(preset.position_mm),
      fromTarget: controls.target.clone(),
      toTarget: toThreePosition(preset.target_mm),
    };
  }

  function update(deltaSeconds) {
    if (!transition) return;
    transition.elapsed += deltaSeconds;
    const raw = Math.min(1, transition.elapsed / transition.duration);
    const eased = raw < 0.5 ? 2 * raw * raw : 1 - Math.pow(-2 * raw + 2, 2) / 2;
    camera.position.lerpVectors(transition.fromPosition, transition.toPosition, eased);
    controls.target.lerpVectors(transition.fromTarget, transition.toTarget, eased);
    if (raw >= 1) transition = null;
  }

  return { moveTo, update };
}
