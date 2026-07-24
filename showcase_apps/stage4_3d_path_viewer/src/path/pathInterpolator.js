import * as THREE from "three";

const MM_TO_M = 0.001;

export function displayPositionToVector(position) {
  return new THREE.Vector3(
    position.x_mm * MM_TO_M,
    position.z_mm * MM_TO_M,
    -position.y_mm * MM_TO_M,
  );
}

export function createPathInterpolator(points) {
  const startTime = points[0].relative_time_s;
  const duration = Math.max(0.001, points.at(-1).relative_time_s - startTime);
  const vectors = points.map((point) => displayPositionToVector(point.display_position_mm));

  function sample(timeSeconds) {
    const time = Math.max(0, Math.min(duration, timeSeconds));
    let low = 0;
    let high = points.length - 1;
    while (low < high) {
      const middle = Math.ceil((low + high) / 2);
      if (points[middle].relative_time_s <= time) low = middle;
      else high = middle - 1;
    }
    const fromIndex = Math.min(low, points.length - 2);
    const toIndex = fromIndex + 1;
    const current = points[fromIndex];
    const next = points[toIndex];
    const span = next.relative_time_s - current.relative_time_s;
    const alpha = span > 0 ? Math.min(1, (time - current.relative_time_s) / span) : 0;
    return {
      time,
      progress: time / duration,
      index: fromIndex,
      nextIndex: toIndex,
      fromIndex,
      toIndex,
      alpha,
      point: time >= duration ? next : current,
      fromPoint: current,
      toPoint: next,
      position: vectors[fromIndex].clone().lerp(vectors[toIndex], alpha),
      fromPosition: vectors[fromIndex],
      toPosition: vectors[toIndex],
      activeSegment: {
        fromIndex,
        toIndex,
        alpha,
        fromPoint: current,
        toPoint: next,
      },
    };
  }

  return { sample, duration, vectors };
}
