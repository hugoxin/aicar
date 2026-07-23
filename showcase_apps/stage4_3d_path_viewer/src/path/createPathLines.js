import * as THREE from "three";
import { pathColor, VIEWER_COLORS } from "../config/colors.js";
import { displayPositionToVector } from "./pathInterpolator.js";

function makeLine(points, material) {
  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  return new THREE.Line(geometry, material);
}

export function createPathLines(pathPoints, profile) {
  const group = new THREE.Group();
  group.name = "stage4-path-lines";
  const stateGroups = new Map();
  const vectors = pathPoints.map((point) =>
    displayPositionToVector(point.display_position_mm),
  );

  let run = [];
  let runKey = null;
  function flushRun() {
    if (run.length < 2 || !runKey) {
      run = [];
      return;
    }
    const [stateId, transitionFlag] = runKey.split("|");
    const isTransition = transitionFlag === "1";
    const line = makeLine(
      run,
      new THREE.LineBasicMaterial({
        color: pathColor(stateId, isTransition),
        transparent: true,
        opacity: profile.path_opacity,
        depthTest: false,
      }),
    );
    line.renderOrder = isTransition ? 4 : 3;
    const key = isTransition ? "transition" : stateId;
    if (!stateGroups.has(key)) {
      const stateGroup = new THREE.Group();
      stateGroup.name = `path-${key}`;
      stateGroups.set(key, stateGroup);
      group.add(stateGroup);
    }
    stateGroups.get(key).add(line);
    run = [];
  }

  pathPoints.forEach((point, index) => {
    const key = `${point.state_id ?? "transition"}|${point.is_transition ? 1 : 0}`;
    if (key !== runKey) {
      flushRun();
      runKey = key;
      if (index > 0) run.push(vectors[index - 1]);
    }
    run.push(vectors[index]);
  });
  flushRun();

  const executedPositions = new Float32Array(vectors.length * 3);
  vectors.forEach((vector, index) => vector.toArray(executedPositions, index * 3));
  const executedGeometry = new THREE.BufferGeometry();
  executedGeometry.setAttribute(
    "position",
    new THREE.BufferAttribute(executedPositions, 3),
  );
  executedGeometry.setDrawRange(0, 1);
  const executedLine = new THREE.Line(
    executedGeometry,
    new THREE.LineBasicMaterial({
      color: VIEWER_COLORS.executed,
      transparent: true,
      opacity: 0.92,
      depthTest: false,
    }),
  );
  executedLine.renderOrder = 7;

  const highlightPositions = new Float32Array(6);
  const highlightGeometry = new THREE.BufferGeometry();
  highlightGeometry.setAttribute(
    "position",
    new THREE.BufferAttribute(highlightPositions, 3),
  );
  const highlightLine = new THREE.Line(
    highlightGeometry,
    new THREE.LineBasicMaterial({
      color: VIEWER_COLORS.currentSegment,
      transparent: true,
      opacity: 1,
      depthTest: false,
    }),
  );
  highlightLine.renderOrder = 8;
  group.add(executedLine, highlightLine);

  function update(sample) {
    executedGeometry.setDrawRange(0, Math.max(1, sample.index + 1));
    sample.fromPosition.toArray(highlightPositions, 0);
    sample.toPosition.toArray(highlightPositions, 3);
    highlightGeometry.attributes.position.needsUpdate = true;
  }

  return {
    group,
    stateGroups,
    executedLine,
    highlightLine,
    update,
    setStateVisible(stateId, visible) {
      const stateGroup = stateGroups.get(stateId);
      if (stateGroup) stateGroup.visible = visible;
    },
    setFullPathVisible(visible) {
      stateGroups.forEach((stateGroup) => {
        stateGroup.visible = visible && stateGroup.userData.enabled !== false;
      });
    },
  };
}
