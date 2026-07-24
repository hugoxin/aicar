import { formatTime } from "../animation/timeline.js";

function text(id, value, withTitle = false) {
  const element = document.getElementById(id);
  if (!element) return;
  element.textContent = value;
  if (withTitle) element.title = value;
}

function available(value) {
  return value ?? "未提供";
}

function interpolatedDisplayPosition(sample) {
  const from = sample.fromPoint.display_position_mm;
  const to = sample.toPoint.display_position_mm;
  return {
    x_mm: from.x_mm + (to.x_mm - from.x_mm) * sample.alpha,
    y_mm: from.y_mm + (to.y_mm - from.y_mm) * sample.alpha,
    z_mm: from.z_mm + (to.z_mm - from.z_mm) * sample.alpha,
  };
}

export function createInfoPanel(sceneData, profile) {
  const summary = sceneData.path_summary;
  text("total-path", `${(summary.path_length_mm / 1000).toFixed(1)} m`);
  text(
    "total-duration",
    `${formatTime(summary.duration_s)} (${(summary.duration_s / 60).toFixed(1)} min)`,
  );
  text("total-time", formatTime(summary.duration_s));
  text(
    "source-name",
    sceneData.source.source_mode === "DEMO_SYNTHETIC"
      ? "数据来源：合成演示路径"
      : "数据来源：Stage4.5 连续清洗面路径",
  );
  text(
    "mode-name",
    sceneData.source.source_mode === "DEMO_SYNTHETIC"
      ? "当前模式：合成数据"
      : "当前模式：通用MPV演示映射",
  );
  text(
    "demo-source",
    sceneData.source.source_mode === "DEMO_SYNTHETIC"
      ? "合成演示路径"
      : "Stage4.5 连续清洗面路径",
  );
  const technicalDetails = document.getElementById("technical-details");
  technicalDetails.open = profile.technical_details_expanded_default;

  function update(sample, presentationContext, playing) {
    const point = sample.point;
    const fromPoint = sample.fromPoint;
    const toPoint = sample.toPoint;
    const position = interpolatedDisplayPosition(sample);
    text(
      "playback-state",
      playing ? "播放中" : sample.progress >= 1 ? "已结束" : "已暂停",
    );
    text("current-state", presentationContext.processStateLabelZh);
    text("current-zone", presentationContext.regionLabelZh);
    text("current-action", presentationContext.actionLabelZh);
    text(
      "current-point",
      `${Math.min((point.point_index ?? sample.fromIndex) + 1, summary.point_count)} / ${summary.point_count}`,
    );
    text("current-progress", `${(sample.progress * 100).toFixed(1)}%`);
    text(
      "current-speed",
      Number.isFinite(fromPoint.speed_mm_s)
        ? `${fromPoint.speed_mm_s.toFixed(1)} mm/s`
        : "未提供",
    );
    text("current-execution", presentationContext.executionDescriptionZh);

    text(
      "current-coordinate",
      `X ${position.x_mm.toFixed(0)} · Y ${position.y_mm.toFixed(0)} · Z ${position.z_mm.toFixed(0)}`,
      true,
    );
    text("current-state-id", available(point.state_id), true);
    text("current-zone-id", available(point.zone_id), true);
    text("current-segment", available(point.segment_id), true);
    text("current-scan-pass", available(point.scan_pass_id), true);
    text("current-surface-task", available(point.surface_task_id), true);
    text("current-critical-type", available(point.critical_point_type), true);
    text(
      "current-source-index",
      String(available(point.source_sequence_index)),
      true,
    );
    text(
      "current-timestamp",
      Number.isFinite(point.timestamp_s)
        ? `${point.timestamp_s.toFixed(3)} s`
        : "未提供",
      true,
    );
    text("active-from-index", String(sample.fromIndex), true);
    text("active-to-index", String(sample.toIndex), true);
    text("interpolation-alpha", sample.alpha.toFixed(6), true);
    text("display-role", presentationContext.role, true);
    text(
      "role-confidence",
      presentationContext.roleConfidence.toFixed(3),
      true,
    );
    text(
      "role-reasons",
      presentationContext.roleReasons.join(", ") || "none",
      true,
    );
    text("raw-from-state", available(fromPoint.state_id), true);
    text("raw-to-state", available(toPoint.state_id), true);
    text("raw-from-zone", available(fromPoint.zone_id), true);
    text("raw-to-zone", available(toPoint.zone_id), true);
    text(
      "presentation-state",
      `${presentationContext.processStateLabelZh} (${available(presentationContext.processStateId)})`,
      true,
    );
    text("presentation-region", presentationContext.regionLabelZh, true);
    text("origin-region", available(presentationContext.originRegionLabelZh), true);
    text("target-region", available(presentationContext.targetRegionLabelZh), true);
    text(
      "presentation-warnings",
      presentationContext.warnings.join(", ") || "none",
      true,
    );
    text("current-time", formatTime(sample.time));
    text("point-label-state", presentationContext.scannerLabelPrimary);
    text("point-label-zone", presentationContext.scannerLabelSecondary);
  }

  return { update };
}
