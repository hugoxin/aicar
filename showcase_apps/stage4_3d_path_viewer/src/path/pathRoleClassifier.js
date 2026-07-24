const STATE_TRANSITION_PATTERN = /(state[_-]?transition|process[_-]?transition)/i;
const CONNECTION_PATTERN =
  /(connection|connector|transfer|move|patch[_-]?link|local[_-]?link|route[_-]?link)/i;

export const PATH_ROLES = Object.freeze({
  MAIN_SCAN: "MAIN_SCAN",
  AUXILIARY_CONNECTION: "AUXILIARY_CONNECTION",
  STATE_TRANSITION: "STATE_TRANSITION",
  UNKNOWN_PATH_ROLE: "UNKNOWN_PATH_ROLE",
});

function hasValue(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function rawContext(point) {
  return {
    pointIndex: point.point_index,
    stateId: point.state_id ?? null,
    zoneId: point.zone_id ?? null,
    segmentId: point.segment_id ?? null,
    scanPassId: point.scan_pass_id ?? null,
    surfaceTaskId: point.surface_task_id ?? null,
    criticalPointType: point.critical_point_type ?? null,
    isTransition: point.is_transition === true,
  };
}

export function classifyPathSegment(fromPoint, toPoint) {
  const reasons = [];
  const identifiers = [
    fromPoint.segment_id,
    toPoint.segment_id,
    fromPoint.surface_task_id,
    toPoint.surface_task_id,
  ].filter(Boolean);
  const stateChanged = fromPoint.state_id !== toPoint.state_id;
  const zoneChanged = fromPoint.zone_id !== toPoint.zone_id;
  const sameScanPass =
    hasValue(fromPoint.scan_pass_id)
    && fromPoint.scan_pass_id === toPoint.scan_pass_id;
  const transitionFlag =
    fromPoint.is_transition === true || toPoint.is_transition === true;
  const stateBoundary =
    fromPoint.critical_point_type === "STATE_BOUNDARY"
    || toPoint.critical_point_type === "STATE_BOUNDARY";
  const namedStateTransition = identifiers.some((value) =>
    STATE_TRANSITION_PATTERN.test(value),
  );
  const namedConnection = identifiers.some((value) =>
    CONNECTION_PATTERN.test(value),
  );

  let role = PATH_ROLES.UNKNOWN_PATH_ROLE;
  let confidence = 0.3;

  if (
    namedStateTransition
    || (transitionFlag && stateChanged)
    || (stateBoundary && transitionFlag)
    || (stateChanged && !sameScanPass)
  ) {
    role = PATH_ROLES.STATE_TRANSITION;
    confidence = namedStateTransition ? 1 : 0.92;
    if (namedStateTransition) reasons.push("NAMED_STATE_TRANSITION");
    if (transitionFlag) reasons.push("TRANSITION_FLAG");
    if (stateBoundary) reasons.push("STATE_BOUNDARY");
    if (stateChanged) reasons.push("STATE_CHANGED");
  } else if (
    sameScanPass
    && !stateChanged
    && !zoneChanged
    && !transitionFlag
    && !stateBoundary
    && !namedConnection
  ) {
    role = PATH_ROLES.MAIN_SCAN;
    confidence = 1;
    reasons.push("SAME_VALID_SCAN_PASS", "STATE_AND_ZONE_STABLE");
  } else if (
    namedConnection
    || transitionFlag
    || zoneChanged
    || !sameScanPass
    || !hasValue(fromPoint.scan_pass_id)
    || !hasValue(toPoint.scan_pass_id)
  ) {
    role = PATH_ROLES.AUXILIARY_CONNECTION;
    confidence = namedConnection || transitionFlag ? 0.95 : 0.84;
    if (namedConnection) reasons.push("NAMED_CONNECTION");
    if (transitionFlag) reasons.push("TRANSITION_FLAG");
    if (zoneChanged) reasons.push("ZONE_CHANGED");
    if (!sameScanPass) reasons.push("SCAN_PASS_CHANGED_OR_MISSING");
  } else {
    reasons.push("NO_RELIABLE_ROLE_RULE");
  }

  return {
    role,
    confidence,
    reasons,
    rawFromContext: rawContext(fromPoint),
    rawToContext: rawContext(toPoint),
    isMainScan: role === PATH_ROLES.MAIN_SCAN,
    isAuxiliary: role === PATH_ROLES.AUXILIARY_CONNECTION,
    isStateTransition: role === PATH_ROLES.STATE_TRANSITION,
    isUnknown: role === PATH_ROLES.UNKNOWN_PATH_ROLE,
  };
}
