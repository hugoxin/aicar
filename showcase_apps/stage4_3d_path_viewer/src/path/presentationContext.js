import { stateLabel, zoneLabel } from "../config/labels.js";
import { classifyPathSegment, PATH_ROLES } from "./pathRoleClassifier.js";

const ROLE_LABELS = Object.freeze({
  [PATH_ROLES.MAIN_SCAN]: "正式扫描",
  [PATH_ROLES.AUXILIARY_CONNECTION]: "辅助移动",
  [PATH_ROLES.STATE_TRANSITION]: "状态切换",
  [PATH_ROLES.UNKNOWN_PATH_ROLE]: "路径角色待确认",
});

function mainContext(segmentIndex, fromPoint) {
  return {
    segmentIndex,
    stateId: fromPoint.state_id,
    stateLabelZh: fromPoint.state_label_zh || stateLabel(fromPoint.state_id),
    regionId: fromPoint.zone_id,
    regionLabelZh: fromPoint.zone_label_zh || zoneLabel(fromPoint.zone_id),
    scanPassId: fromPoint.scan_pass_id,
  };
}

function movementRegion(origin, target) {
  if (origin?.regionLabelZh && target?.regionLabelZh) {
    if (origin.regionId === target.regionId) return `保持${origin.regionLabelZh}`;
    return `${origin.regionLabelZh} → ${target.regionLabelZh}`;
  }
  if (target?.regionLabelZh) return `前往${target.regionLabelZh}`;
  return "区域间移动";
}

function transitionDescription(origin, target) {
  const fromState = origin?.stateLabelZh || "上一工艺";
  const toState = target?.stateLabelZh || "下一工艺";
  if (target?.regionLabelZh && origin?.regionId !== target.regionId) {
    return `正在完成从【${fromState}】到【${toState}】的切换，并移动至【${target.regionLabelZh}】，当前不执行持续喷洗。`;
  }
  return `正在从【${fromState}】切换至【${toState}】，当前不执行持续喷洗。`;
}

export function createPresentationContext(
  activeSegment,
  roleInfo,
  previousMain,
  nextMain,
) {
  const fromPoint = activeSegment.fromPoint;
  const warnings = [];
  const base = {
    role: roleInfo.role,
    roleLabelZh: ROLE_LABELS[roleInfo.role],
    roleConfidence: roleInfo.confidence,
    roleReasons: roleInfo.reasons,
    rawStateId: fromPoint.state_id ?? null,
    rawZoneId: fromPoint.zone_id ?? null,
    originRegionId: previousMain?.regionId ?? null,
    originRegionLabelZh: previousMain?.regionLabelZh ?? null,
    targetRegionId: nextMain?.regionId ?? null,
    targetRegionLabelZh: nextMain?.regionLabelZh ?? null,
    originStateId: previousMain?.stateId ?? null,
    originStateLabelZh: previousMain?.stateLabelZh ?? null,
    targetStateId: nextMain?.stateId ?? null,
    targetStateLabelZh: nextMain?.stateLabelZh ?? null,
    warnings,
  };

  if (roleInfo.role === PATH_ROLES.MAIN_SCAN) {
    const processStateLabel =
      fromPoint.state_label_zh || stateLabel(fromPoint.state_id);
    const regionLabel = fromPoint.zone_label_zh || zoneLabel(fromPoint.zone_id);
    return {
      ...base,
      processStateId: fromPoint.state_id,
      processStateLabelZh: processStateLabel,
      regionId: fromPoint.zone_id,
      regionLabelZh: regionLabel,
      actionLabelZh: "正式扫描",
      scannerLabelPrimary: processStateLabel,
      scannerLabelSecondary: regionLabel,
      executionDescriptionZh: `当前正在执行：正在对【${regionLabel}】进行【${processStateLabel}】。`,
    };
  }

  if (roleInfo.role === PATH_ROLES.AUXILIARY_CONNECTION) {
    const commonState =
      previousMain?.stateId === nextMain?.stateId ? previousMain : null;
    const regionLabel = movementRegion(previousMain, nextMain);
    let description = "当前正在执行：正在进行区域间移动，当前不执行持续喷洗。";
    if (previousMain?.regionLabelZh && nextMain?.regionLabelZh) {
      description = previousMain.regionId === nextMain.regionId
        ? `当前正在执行：正在【${previousMain.regionLabelZh}】区域内进行扫描段间定位移动，当前不执行持续喷洗。`
        : `当前正在执行：正在从【${previousMain.regionLabelZh}】移动至`
          + `【${nextMain.regionLabelZh}】位置，当前不执行持续喷洗。`;
    } else if (nextMain?.regionLabelZh) {
      description =
        `当前正在执行：正在前往【${nextMain.regionLabelZh}】位置，当前不执行持续喷洗。`;
    }
    return {
      ...base,
      processStateId: commonState?.stateId ?? null,
      processStateLabelZh: commonState?.stateLabelZh ?? "辅助移动",
      regionId: null,
      regionLabelZh: regionLabel,
      actionLabelZh: "辅助移动",
      scannerLabelPrimary: "辅助移动",
      scannerLabelSecondary: regionLabel,
      executionDescriptionZh: description,
    };
  }

  if (roleInfo.role === PATH_ROLES.STATE_TRANSITION) {
    const regionLabel = movementRegion(previousMain, nextMain);
    if (fromPoint.state_id === nextMain?.stateId) {
      warnings.push("RAW_TRANSITION_CONTEXT_USES_TARGET_STATE");
    }
    return {
      ...base,
      processStateId: null,
      processStateLabelZh: "状态切换",
      regionId: null,
      regionLabelZh: regionLabel,
      actionLabelZh: "工艺切换",
      scannerLabelPrimary: "状态切换",
      scannerLabelSecondary:
        previousMain && nextMain
          ? `${previousMain.stateLabelZh} → ${nextMain.stateLabelZh}`
          : "工艺切换",
      executionDescriptionZh:
        `当前正在执行：${transitionDescription(previousMain, nextMain)}`,
    };
  }

  warnings.push("UNKNOWN_PATH_ROLE");
  return {
    ...base,
    processStateId: null,
    processStateLabelZh: "语义待确认",
    regionId: null,
    regionLabelZh: "区域待确认",
    actionLabelZh: "路径连接",
    scannerLabelPrimary: "路径连接",
    scannerLabelSecondary: "语义待确认",
    executionDescriptionZh:
      "当前正在执行：当前路径段无法可靠判断为正式扫描或辅助移动，请查看技术详情。",
  };
}

export function createPresentationContextResolver(pathPoints) {
  const segmentRoles = pathPoints.slice(0, -1).map((point, index) =>
    classifyPathSegment(point, pathPoints[index + 1]),
  );
  const previousMain = new Array(segmentRoles.length);
  const nextMain = new Array(segmentRoles.length);
  let lastMain = null;
  segmentRoles.forEach((roleInfo, index) => {
    previousMain[index] = lastMain;
    if (roleInfo.isMainScan) lastMain = mainContext(index, pathPoints[index]);
  });
  lastMain = null;
  for (let index = segmentRoles.length - 1; index >= 0; index -= 1) {
    nextMain[index] = lastMain;
    if (segmentRoles[index].isMainScan) {
      lastMain = mainContext(index, pathPoints[index]);
    }
  }

  function contextFor(sample) {
    const segmentIndex = Math.min(
      segmentRoles.length - 1,
      sample.activeSegment.fromIndex,
    );
    const roleInfo = segmentRoles[segmentIndex];
    const currentMain = roleInfo.isMainScan
      ? mainContext(segmentIndex, sample.activeSegment.fromPoint)
      : null;
    return createPresentationContext(
      sample.activeSegment,
      roleInfo,
      currentMain || previousMain[segmentIndex],
      currentMain || nextMain[segmentIndex],
    );
  }

  return { segmentRoles, previousMain, nextMain, contextFor };
}
