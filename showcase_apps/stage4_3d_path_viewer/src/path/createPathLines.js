import * as THREE from "three";
import { stateColor, VIEWER_COLORS } from "../config/colors.js";
import { displayPositionToVector } from "./pathInterpolator.js";
import { classifyPathSegment, PATH_ROLES } from "./pathRoleClassifier.js";

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

function roleStyle(role, profile) {
  if (role === PATH_ROLES.STATE_TRANSITION) {
    return {
      color: VIEWER_COLORS.stateTransition,
      opacity: profile.auxiliary_path_opacity * 1.15,
    };
  }
  if (role === PATH_ROLES.AUXILIARY_CONNECTION) {
    return {
      color: VIEWER_COLORS.auxiliary,
      opacity: profile.auxiliary_path_opacity,
    };
  }
  return {
    color: VIEWER_COLORS.unknown,
    opacity: profile.future_path_opacity * 0.72,
  };
}

function currentRoleColor(context) {
  if (context.role === PATH_ROLES.MAIN_SCAN) {
    return stateColor(context.processStateId);
  }
  if (context.role === PATH_ROLES.AUXILIARY_CONNECTION) {
    return VIEWER_COLORS.auxiliaryHighlight;
  }
  if (context.role === PATH_ROLES.STATE_TRANSITION) {
    return VIEWER_COLORS.stateTransition;
  }
  return VIEWER_COLORS.unknownWarning;
}

export function createPathLines(pathPoints, profile) {
  const group = new THREE.Group();
  group.name = "stage4-path-lines";
  const vectors = pathPoints.map((point) =>
    displayPositionToVector(point.display_position_mm),
  );
  const stateEntries = new Map();
  const stateGroups = new Map();
  const connectionGroup = new THREE.Group();
  connectionGroup.name = "path-connections";
  connectionGroup.userData.enabled = profile.show_auxiliary_paths_default;
  const roleGroups = new Map(
    [
      PATH_ROLES.AUXILIARY_CONNECTION,
      PATH_ROLES.STATE_TRANSITION,
      PATH_ROLES.UNKNOWN_PATH_ROLE,
    ].map((role) => {
      const roleGroup = new THREE.Group();
      roleGroup.name = `path-${role.toLowerCase()}`;
      connectionGroup.add(roleGroup);
      return [role, roleGroup];
    }),
  );

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
    const roleInfo = classifyPathSegment(pathPoints[index - 1], pathPoints[index]);
    const stateId = pathPoints[index - 1].state_id || "unknown";
    const key = `${roleInfo.role}|${stateId}`;
    if (!activeRun || activeRun.key !== key) {
      activeRun = {
        key,
        role: roleInfo.role,
        stateId,
        points: [vectors[index - 1], vectors[index]],
      };
      roleRuns.push(activeRun);
    } else {
      activeRun.points.push(vectors[index]);
    }
  }

  roleRuns.forEach((run) => {
    let parent;
    let material;
    if (run.role === PATH_ROLES.MAIN_SCAN) {
      const entry = stateEntry(run.stateId);
      parent = entry.group;
      material = lineMaterial(stateColor(run.stateId), profile.future_path_opacity);
      entry.futureMaterials.push(material);
    } else {
      const style = roleStyle(run.role, profile);
      parent = roleGroups.get(run.role);
      material = lineMaterial(style.color, style.opacity);
    }
    material.userData.baseOpacity = material.opacity;
    material.userData.stateId = run.stateId;
    material.userData.role = run.role;
    const line = createLine(run.points, material);
    line.renderOrder = run.role === PATH_ROLES.MAIN_SCAN ? 3 : 2;
    parent.add(line);
  });

  group.add(connectionGroup);
  stateGroups.set("transition", connectionGroup);

  const roleExecuted = new Map();
  for (const role of [
    PATH_ROLES.AUXILIARY_CONNECTION,
    PATH_ROLES.STATE_TRANSITION,
    PATH_ROLES.UNKNOWN_PATH_ROLE,
  ]) {
    const style = roleStyle(role, profile);
    roleExecuted.set(role, {
      positions: [],
      countAtIndex: new Uint32Array(pathPoints.length),
      material: lineMaterial(
        style.color,
        Math.min(profile.executed_path_opacity, style.opacity * 1.45),
        { depthTest: false },
      ),
      line: null,
    });
  }

  pathPoints.forEach((point) => stateEntry(point.state_id || "unknown"));
  stateEntries.forEach((entry) => {
    entry.executedCountAtIndex = new Uint32Array(pathPoints.length);
  });

  for (let index = 1; index < pathPoints.length; index += 1) {
    const roleInfo = classifyPathSegment(pathPoints[index - 1], pathPoints[index]);
    const stateId = pathPoints[index - 1].state_id || "unknown";
    if (roleInfo.role === PATH_ROLES.MAIN_SCAN) {
      stateEntry(stateId).executedPositions.push(vectors[index - 1], vectors[index]);
    } else {
      roleExecuted
        .get(roleInfo.role)
        .positions.push(vectors[index - 1], vectors[index]);
    }
    stateEntries.forEach((entry) => {
      entry.executedCountAtIndex[index] = entry.executedPositions.length;
    });
    roleExecuted.forEach((entry) => {
      entry.countAtIndex[index] = entry.positions.length;
    });
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
  roleExecuted.forEach((entry, role) => {
    entry.line = createLineSegments(entry.positions, entry.material);
    entry.line.name = `executed-${role.toLowerCase()}`;
    entry.line.renderOrder = 6;
    roleGroups.get(role).add(entry.line);
  });

  const currentCapacity = 2;
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
        focusCurrentState && currentStateId && entry.stateId !== currentStateId
          ? profile.inactive_state_opacity_ratio
          : 1;
      entry.futureMaterials.forEach((material) => {
        material.opacity = material.userData.baseOpacity * stateRatio;
      });
      entry.executedMaterial.opacity =
        profile.executed_path_opacity * stateRatio;
      entry.executedLine.visible = executedVisible;
      entry.group.children.forEach((child) => {
        if (child !== entry.executedLine) child.visible = fullPathVisible;
      });
    });
    connectionGroup.visible =
      auxiliaryVisible && (fullPathVisible || executedVisible);
    roleExecuted.forEach((entry) => {
      entry.line.visible = auxiliaryVisible && executedVisible;
    });
    roleGroups.forEach((roleGroup) => {
      roleGroup.children.forEach((child) => {
        if (!child.name.startsWith("executed-")) {
          child.visible = auxiliaryVisible && fullPathVisible;
        }
      });
    });
  }

  function updateCurrentSegment(sample) {
    [sample.fromPosition, sample.toPosition].forEach((point, index) => {
      point.toArray(currentPositions, index * 3);
    });
    currentGeometry.attributes.position.needsUpdate = true;
    currentGeometry.setDrawRange(0, currentCapacity);
  }

  function update(sample, presentationContext) {
    currentStateId =
      presentationContext.processStateId
      || presentationContext.originStateId
      || null;
    const executedIndex = sample.progress >= 1 ? sample.toIndex : sample.fromIndex;
    stateEntries.forEach((entry) => {
      entry.executedLine.geometry.setDrawRange(
        0,
        entry.executedCountAtIndex[executedIndex] || 0,
      );
    });
    roleExecuted.forEach((entry) => {
      entry.line.geometry.setDrawRange(
        0,
        entry.countAtIndex[executedIndex] || 0,
      );
    });
    const color = new THREE.Color(currentRoleColor(presentationContext)).lerp(
      new THREE.Color(VIEWER_COLORS.current),
      presentationContext.role === PATH_ROLES.MAIN_SCAN ? 0.2 : 0.05,
    );
    currentMaterial.color.copy(color);
    currentGlowMaterial.color.copy(color);
    updateCurrentSegment(sample);
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
      connectionGroup.userData.enabled = enabled;
      applyPresentation();
    },
  };
}
