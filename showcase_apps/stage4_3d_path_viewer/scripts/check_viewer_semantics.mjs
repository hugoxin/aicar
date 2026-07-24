import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import {
  classifyPathSegment,
  PATH_ROLES,
} from "../src/path/pathRoleClassifier.js";
import {
  createPresentationContextResolver,
} from "../src/path/presentationContext.js";

const appRoot = resolve(import.meta.dirname, "..");
const scenePath = resolve(appRoot, "public", "data", "viewer_scene.json");
const scene = JSON.parse(await readFile(scenePath, "utf8"));
const points = scene.path_points;
const resolver = createPresentationContextResolver(points);
const duration = points.at(-1).relative_time_s - points[0].relative_time_s;
const roleCounts = Object.fromEntries(
  Object.values(PATH_ROLES).map((role) => [role, 0]),
);
const semanticMismatches = [];
const spatialWarnings = [];
const chineseText = /[\u3400-\u9fff]/;

function requireSemantic(condition, index, code, details = "") {
  if (!condition) {
    semanticMismatches.push({ index, code, details });
  }
}

function sampleAtTime(timeSeconds) {
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
  const fromPoint = points[fromIndex];
  const toPoint = points[toIndex];
  const span = toPoint.relative_time_s - fromPoint.relative_time_s;
  const alpha = span > 0
    ? Math.min(1, (time - fromPoint.relative_time_s) / span)
    : 0;
  return {
    time,
    progress: time / duration,
    fromIndex,
    toIndex,
    alpha,
    fromPoint,
    toPoint,
    point: time >= duration ? toPoint : fromPoint,
    activeSegment: { fromIndex, toIndex, alpha, fromPoint, toPoint },
  };
}

function sampleAtProgress(progress) {
  return sampleAtTime(duration * progress);
}

function checkSpatialSanity(index, point, roleInfo) {
  if (!roleInfo.isMainScan) return;
  const position = point.display_position_mm;
  let reason = null;
  if (point.zone_id === "roof" && position.z_mm < 1800) {
    reason = "roof MAIN_SCAN below expected roof height";
  } else if (point.zone_id === "wheels" && position.z_mm > 1100) {
    reason = "wheels MAIN_SCAN above expected wheel height";
  } else if (point.zone_id === "left_side" && position.x_mm > -900) {
    reason = "left_side MAIN_SCAN outside expected left envelope";
  } else if (point.zone_id === "right_side" && position.x_mm < 900) {
    reason = "right_side MAIN_SCAN outside expected right envelope";
  }
  if (reason) {
    spatialWarnings.push({
      index,
      code: "SOURCE_SEMANTIC_SPATIAL_MISMATCH",
      reason,
      state: point.state_id,
      zone: point.zone_id,
      segment: point.segment_id,
      scanPass: point.scan_pass_id,
      position,
    });
  }
}

for (let index = 0; index < points.length - 1; index += 1) {
  const fromPoint = points[index];
  const toPoint = points[index + 1];
  const roleInfo = classifyPathSegment(fromPoint, toPoint);
  const sample = {
    fromIndex: index,
    toIndex: index + 1,
    alpha: 0.5,
    fromPoint,
    toPoint,
    point: fromPoint,
    activeSegment: {
      fromIndex: index,
      toIndex: index + 1,
      alpha: 0.5,
      fromPoint,
      toPoint,
    },
  };
  const context = resolver.contextFor(sample);
  roleCounts[roleInfo.role] += 1;

  requireSemantic(index + 1 === sample.toIndex, index, "NON_CONSECUTIVE_INDEX");
  requireSemantic(
    toPoint.relative_time_s >= fromPoint.relative_time_s,
    index,
    "TIME_REVERSED",
  );
  requireSemantic(
    chineseText.test(fromPoint.state_label_zh || ""),
    index,
    "STATE_LABEL_MISSING",
  );
  requireSemantic(
    chineseText.test(fromPoint.zone_label_zh || ""),
    index,
    "ZONE_LABEL_MISSING",
  );
  requireSemantic(
    context.role === roleInfo.role,
    index,
    "ROLE_CONTEXT_MISMATCH",
  );
  requireSemantic(
    context.scannerLabelPrimary === context.processStateLabelZh
      || context.role !== PATH_ROLES.MAIN_SCAN,
    index,
    "SCANNER_PRIMARY_MISMATCH",
  );
  requireSemantic(
    context.scannerLabelSecondary === context.regionLabelZh
      || context.role === PATH_ROLES.STATE_TRANSITION,
    index,
    "SCANNER_SECONDARY_MISMATCH",
  );

  if (roleInfo.isMainScan) {
    requireSemantic(
      typeof fromPoint.scan_pass_id === "string"
        && fromPoint.scan_pass_id.length > 0
        && fromPoint.scan_pass_id === toPoint.scan_pass_id,
      index,
      "MAIN_SCAN_PASS_INVALID",
    );
    requireSemantic(
      fromPoint.state_id === toPoint.state_id,
      index,
      "MAIN_STATE_CHANGED",
    );
    requireSemantic(
      fromPoint.zone_id === toPoint.zone_id,
      index,
      "MAIN_ZONE_CHANGED",
    );
    requireSemantic(
      !fromPoint.is_transition && !toPoint.is_transition,
      index,
      "MAIN_MARKED_TRANSITION",
    );
    requireSemantic(
      context.executionDescriptionZh.includes("正在对【"),
      index,
      "MAIN_DESCRIPTION_INVALID",
    );
  } else {
    requireSemantic(
      !context.executionDescriptionZh.includes("正在对【"),
      index,
      `${roleInfo.role}_USES_MAIN_DESCRIPTION`,
    );
  }
  if (roleInfo.isUnknown) {
    requireSemantic(
      context.warnings.includes("UNKNOWN_PATH_ROLE"),
      index,
      "UNKNOWN_NOT_EXPLICIT",
    );
  }
  checkSpatialSanity(index, fromPoint, roleInfo);
}

const transitionRuns = [];
for (let index = 0; index < resolver.segmentRoles.length; index += 1) {
  if (
    resolver.segmentRoles[index].role === PATH_ROLES.STATE_TRANSITION
    && (
      index === 0
      || resolver.segmentRoles[index - 1].role !== PATH_ROLES.STATE_TRANSITION
    )
  ) {
    let end = index;
    while (
      end + 1 < resolver.segmentRoles.length
      && resolver.segmentRoles[end + 1].role === PATH_ROLES.STATE_TRANSITION
    ) {
      end += 1;
    }
    transitionRuns.push({ start: index, end });
  }
}

for (const boundary of transitionRuns) {
  const beforeIndex = Math.max(0, boundary.start - 1);
  const afterIndex = Math.min(
    resolver.segmentRoles.length - 1,
    boundary.end + 1,
  );
  const before = resolver.contextFor({
    activeSegment: {
      fromIndex: beforeIndex,
      toIndex: beforeIndex + 1,
      fromPoint: points[beforeIndex],
      toPoint: points[beforeIndex + 1],
      alpha: 0.99,
    },
  });
  const during = resolver.contextFor({
    activeSegment: {
      fromIndex: boundary.start,
      toIndex: boundary.start + 1,
      fromPoint: points[boundary.start],
      toPoint: points[boundary.start + 1],
      alpha: 0.5,
    },
  });
  const after = resolver.contextFor({
    activeSegment: {
      fromIndex: afterIndex,
      toIndex: afterIndex + 1,
      fromPoint: points[afterIndex],
      toPoint: points[afterIndex + 1],
      alpha: 0,
    },
  });
  requireSemantic(
    during.role === PATH_ROLES.STATE_TRANSITION,
    boundary.start,
    "BOUNDARY_NOT_TRANSITION",
  );
  requireSemantic(
    !during.executionDescriptionZh.includes("正在对【"),
    boundary.start,
    "BOUNDARY_USES_MAIN_DESCRIPTION",
  );
  requireSemantic(
    before.role !== PATH_ROLES.UNKNOWN_PATH_ROLE
      && after.role !== PATH_ROLES.UNKNOWN_PATH_ROLE,
    boundary.start,
    "BOUNDARY_ADJACENT_UNKNOWN",
  );
}

function scenario(name, progress) {
  const sample = sampleAtProgress(progress);
  const context = resolver.contextFor(sample);
  return {
    name,
    progress: `${(progress * 100).toFixed(1)}%`,
    time_s: Number(sample.time.toFixed(6)),
    from_index: sample.fromIndex,
    to_index: sample.toIndex,
    alpha: Number(sample.alpha.toFixed(9)),
    role: context.role,
    raw_state: `${sample.fromPoint.state_id} -> ${sample.toPoint.state_id}`,
    raw_zone: `${sample.fromPoint.zone_id} -> ${sample.toPoint.zone_id}`,
    origin_context:
      `${context.originStateLabelZh ?? "none"} / ${context.originRegionLabelZh ?? "none"}`,
    target_context:
      `${context.targetStateLabelZh ?? "none"} / ${context.targetRegionLabelZh ?? "none"}`,
    presentation_state: context.processStateLabelZh,
    presentation_region: context.regionLabelZh,
    action: context.actionLabelZh,
    scanner_label:
      `${context.scannerLabelPrimary} / ${context.scannerLabelSecondary}`,
    execution: context.executionDescriptionZh,
    highlighted_segment: `${sample.fromIndex} -> ${sample.toIndex}`,
    warnings: context.warnings,
  };
}

const scenarios = [
  scenario("A_START", 0),
  scenario("B_34_8_PERCENT", 0.348),
  scenario("D_84_PERCENT", 0.84),
  scenario("C_91_3_PERCENT", 0.913),
  scenario("END", 1),
];

console.log("Viewer V1.0.2 semantic consistency report");
console.log(`total segments: ${points.length - 1}`);
console.log(`main scan segment count: ${roleCounts.MAIN_SCAN}`);
console.log(
  `auxiliary connection count: ${roleCounts.AUXILIARY_CONNECTION}`,
);
console.log(`state transition count: ${roleCounts.STATE_TRANSITION}`);
console.log(`unknown count: ${roleCounts.UNKNOWN_PATH_ROLE}`);
console.log(`semantic mismatch count: ${semanticMismatches.length}`);
console.log(`spatial warning count: ${spatialWarnings.length}`);
console.log(`state boundary count: ${transitionRuns.length}`);
console.log("scenario checks:");
scenarios.forEach((entry) => console.log(JSON.stringify(entry)));

if (semanticMismatches.length > 0) {
  console.error("semantic mismatches:");
  semanticMismatches.slice(0, 20).forEach((entry) =>
    console.error(JSON.stringify(entry)),
  );
}
if (spatialWarnings.length > 0) {
  console.error("spatial warnings:");
  spatialWarnings.slice(0, 20).forEach((entry) =>
    console.error(JSON.stringify(entry)),
  );
}
if (
  semanticMismatches.length > 0
  || spatialWarnings.length > 0
  || roleCounts.UNKNOWN_PATH_ROLE > 0
) {
  process.exitCode = 1;
} else {
  console.log("AI car viewer semantic check OK");
}
