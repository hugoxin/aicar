import * as THREE from "three";
import { stateColor, VIEWER_COLORS } from "../config/colors.js";
import { displayPositionToVector } from "./pathInterpolator.js";

export const DISPLAY_ROLES = Object.freeze({
  MAIN_SCAN: "MAIN_SCAN",
  AUXILIARY_CONNECTION: "AUXILIARY_CONNECTION",
  UNKNOWN_PATH_ROLE: "UNKNOWN_PATH_ROLE",
});

const AUXILIARY_ID_PATTERN = /(transition|connection|connector|patch_link|local_link)/i;

function hasValue(value) {
  return typeof value === "string" && value.trim().length > 0;
}

export function classifyDisplayRole(previous, current) {
  const identifiers = [
    previous.segment_id,
    current.segment_id,
    previous.surface_task_id,
    current.surface_task_id,
  ].filter(Boolean);
  if (
    previous.is_transition
    || current.is_transition
    || identifiers.some((value) => AUXILIARY_ID_PATTERN.test(value))
    || previous.critical_point_type === "STATE_BOUNDARY"
    || current.critical_point_type === "STATE_BOUNDARY"
  ) {
    return DISPLAY_ROLES.AUXILIARY_CONNECTION;
  }
  if (
    hasValue(previous.scan_pass_id)
    && previous.scan_pass_id === current.scan_pass_id
    && previous.state_id === current.state_id
  ) {
    return DISPLAY_ROLES.MAIN_SCAN;
  }
  if (hasValue(previous.scan_pass_id) && hasValue(current.scan_pass_id)) {
    return DISPLAY_ROLES.AUXILIARY_CONNECTION;
  }
  return DISPLAY_ROLES.UNKNOWN_PATH_ROLE;
}

function lineMaterial(color, opacity, options = {}) {
  return new THREE.LineBasicMaterial({
    color,
    transparent: true,
    opacity,
    depthTest: options.depthTest ?? true,
    depthWrite: false,
    blending: options.blending ?? THREE.NormalBlending,
  });
}

function createLine(points, material) {
  return new THREE.Line(
    new THREE.BufferGeometry().setFromPoints(points),
    material,
  );
}

function createLineSegments(positions, material) {
  const geometry = new THREE.BufferGeometry().setFromPoints(positions);
  geometry.setDrawRange(0, 0);
  return new THREE.LineSegments(geometry, material);
}

function makeStateEntry(stateId, profile) {
  const group = new THREE.Group();
  group.name = `path-${stateId}`;
  group.userData.enabled = true;
  return {
    stateId,
    group,
    futureMaterials: [],
    executedPositions: [],
    executedCountAtIndex: null,
    executedLine: null,
    executedMaterial: lineMaterial(
      stateColor(stateId),
      profile.executed_path_opacity,
      { depthTest: false },
    ),
  };
}

export function createPathLines(pathPoints, profile) {
  const group = new THREE.Group();
  group.name = "stage4-path-lines";
  const vectors = pathPoints.map((point) =>
    displayPositionToVector(point.display_position_mm),
  );
  const stateEntries = new Map();
  const stateGroups = new Map();
  const auxiliaryGroup = new THREE.Group();
  auxiliaryGroup.name = "path-auxiliary-connections";
  auxiliaryGroup.userData.enabled = profile.show_auxiliary_paths_default;
  const unknownGroup = new THREE.Group();
  unknownGroup.name = "path-unknown-role";

  function stateEntry(stateId) {
    if (!stateEntries.has(stateId)) {
      const entry = makeStateEntry(stateId, profile);
      stateEntries.set(stateId, entry);
      stateGroups.set(stateId, entry.group);
      group.add(entry.group);
    }
    return stateEntries.get(stateId);
  }

  const roleRuns = [];
  let activeRun = null;
  for (let index = 1; index < pathPoints.length; index += 1) {
    const previous = pathPoints[index - 1];
    const current = pathPoints[index];
    const role = classifyDisplayRole(previous, current);
    const stateId = current.state_id || previous.state_id || "unknown";
    const key = `${role}|${stateId}`;
    if (!activeRun || activeRun.key !== key) {
      activeRun = {
        key,
        role,
        stateId,
        points: [vectors[index - 1], vectors[index]],
      };
      roleRuns.push(activeRun);
    } else {
      activeRun.points.push(vectors[index]);
    }
  }

  roleRuns.forEach((run) => {
    let color = stateColor(run.stateId);
    let opacity = profile.future_path_opacity;
    let parent = stateEntry(run.stateId).group;
    if (run.role === DISPLAY_ROLES.AUXILIARY_CONNECTION) {
      color = VIEWER_COLORS.auxiliary;
      opacity = profile.auxiliary_path_opacity;
      parent = auxiliaryGroup;
    } else if (run.role === DISPLAY_ROLES.UNKNOWN_PATH_ROLE) {
      color = VIEWER_COLORS.unknown;
      opacity = profile.future_path_opacity * 0.72;
      parent = unknownGroup;
    }
    const material = lineMaterial(color, opacity);
    material.userData.baseOpacity = opacity;
    material.userData.stateId = run.stateId;
    material.userData.role = run.role;
    const line = createLine(run.points, material);
    line.renderOrder = run.role === DISPLAY_ROLES.MAIN_SCAN ? 3 : 2;
    parent.add(line);
    if (run.role === DISPLAY_ROLES.MAIN_SCAN) {
      stateEntry(run.stateId).futureMaterials.push(material);
    }
  });

  group.add(auxiliaryGroup, unknownGroup);
  stateGroups.set("transition", auxiliaryGroup);

  const auxiliaryExecutedPositions = [];
  const auxiliaryExecutedCountAtIndex = new Uint32Array(pathPoints.length);
  pathPoints.forEach((point) => stateEntry(point.state_id || "unknown"));
  stateEntries.forEach((entry) => {
    entry.executedCountAtIndex = new Uint32Array(pathPoints.length);
  });

  for (let index = 1; index < pathPoints.length; index += 1) {
    const previous = pathPoints[index - 1];
    const current = pathPoints[index];
    const role = classifyDisplayRole(previous, current);
    const stateId = current.state_id || previous.state_id || "unknown";
    if (role === DISPLAY_ROLES.MAIN_SCAN) {
      stateEntry(stateId).executedPositions.push(vectors[index - 1], vectors[index]);
    } else if (role === DISPLAY_ROLES.AUXILIARY_CONNECTION) {
      auxiliaryExecutedPositions.push(vectors[index - 1], vectors[index]);
    }
    stateEntries.forEach((entry) => {
      entry.executedCountAtIndex[index] = entry.executedPositions.length;
    });
    auxiliaryExecutedCountAtIndex[index] = auxiliaryExecutedPositions.length;
  }

  stateEntries.forEach((entry) => {
    entry.executedLine = createLineSegments(
      entry.executedPositions,
      entry.executedMaterial,
    );
    entry.executedLine.name = `executed-${entry.stateId}`;
    entry.executedLine.renderOrder = 7;
    entry.group.add(entry.executedLine);
  });
  const auxiliaryExecutedMaterial = lineMaterial(
    VIEWER_COLORS.auxiliary,
    Math.min(profile.executed_path_opacity, profile.auxiliary_path_opacity * 1.45),
    { depthTest: false },
  );
  const auxiliaryExecutedLine = createLineSegments(
    auxiliaryExecutedPositions,
    auxiliaryExecutedMaterial,
  );
  auxiliaryExecutedLine.renderOrder = 6;
  auxiliaryGroup.add(auxiliaryExecutedLine);

  const currentCapacity = 10;
  const currentPositions = new Float32Array(currentCapacity * 3);
  const currentGeometry = new THREE.BufferGeometry();
  currentGeometry.setAttribute(
    "position",
    new THREE.BufferAttribute(currentPositions, 3),
  );
  currentGeometry.setDrawRange(0, 0);
  const currentGlowMaterial = lineMaterial(
    VIEWER_COLORS.current,
    profile.current_segment_opacity * 0.34,
    { depthTest: false, blending: THREE.AdditiveBlending },
  );
  const currentMaterial = lineMaterial(
    VIEWER_COLORS.current,
    profile.current_segment_opacity,
    { depthTest: false },
  );
  const currentGlowLine = new THREE.Line(currentGeometry, currentGlowMaterial);
  const currentLine = new THREE.Line(currentGeometry, currentMaterial);
  currentGlowLine.renderOrder = 10;
  currentLine.renderOrder = 11;
  group.add(currentGlowLine, currentLine);

  let fullPathVisible = true;
  let executedVisible = true;
  let focusCurrentState = profile.focus_current_state_default;
  let auxiliaryVisible = profile.show_auxiliary_paths_default;
  let currentStateId = pathPoints[0]?.state_id;

  function applyPresentation() {
    stateEntries.forEach((entry) => {
      const enabled = entry.group.userData.enabled !== false;
      entry.group.visible = enabled && (fullPathVisible || executedVisible);
      const stateRatio =
        focusCurrentState && entry.stateId !== currentStateId
          ? profile.inactive_state_opacity_ratio
          : 1;
      entry.futureMaterials.forEach((material) => {
        material.opacity = material.userData.baseOpacity * stateRatio;
      });
      entry.executedMaterial.opacity =
        profile.executed_path_opacity * stateRatio;
      if (entry.executedLine) entry.executedLine.visible = executedVisible;
      entry.group.children.forEach((child) => {
        if (child !== entry.executedLine) child.visible = fullPathVisible;
      });
    });
    auxiliaryGroup.visible = auxiliaryVisible && fullPathVisible;
    auxiliaryExecutedLine.visible = auxiliaryVisible && executedVisible;
    unknownGroup.visible = fullPathVisible;
  }

  function updateCurrentWindow(sample) {
    const start = Math.max(0, sample.index - 3);
    const end = Math.min(vectors.length - 1, sample.index + 5);
    const points = [];
    for (let index = start; index <= sample.index; index += 1) {
      points.push(vectors[index]);
    }
    points.push(sample.position);
    for (let index = sample.nextIndex; index <= end; index += 1) {
      points.push(vectors[index]);
    }
    points.slice(0, currentCapacity).forEach((point, index) => {
      point.toArray(currentPositions, index * 3);
    });
    currentGeometry.attributes.position.needsUpdate = true;
    currentGeometry.setDrawRange(0, Math.min(points.length, currentCapacity));
  }

  function update(sample) {
    currentStateId = sample.point.state_id;
    const executedIndex = sample.progress >= 1 ? sample.nextIndex : sample.index;
    stateEntries.forEach((entry) => {
      entry.executedLine.geometry.setDrawRange(
        0,
        entry.executedCountAtIndex[executedIndex] || 0,
      );
    });
    auxiliaryExecutedLine.geometry.setDrawRange(
      0,
      auxiliaryExecutedCountAtIndex[executedIndex] || 0,
    );
    const color = new THREE.Color(stateColor(currentStateId)).lerp(
      new THREE.Color(VIEWER_COLORS.current),
      0.2,
    );
    currentMaterial.color.copy(color);
    currentGlowMaterial.color.copy(color);
    updateCurrentWindow(sample);
    applyPresentation();
  }

  applyPresentation();
  return {
    group,
    stateGroups,
    currentLine,
    currentGlowLine,
    update,
    setStateVisible(stateId, visible) {
      const target = stateGroups.get(stateId);
      if (target) target.userData.enabled = visible;
      if (stateId === "transition") auxiliaryVisible = visible;
      applyPresentation();
    },
    setFullPathVisible(visible) {
      fullPathVisible = visible;
      applyPresentation();
    },
    setExecutedVisible(visible) {
      executedVisible = visible;
      applyPresentation();
    },
    setFocusCurrentState(enabled) {
      focusCurrentState = enabled;
      applyPresentation();
    },
    setAuxiliaryVisible(enabled) {
      auxiliaryVisible = enabled;
      auxiliaryGroup.userData.enabled = enabled;
      applyPresentation();
    },
  };
}
