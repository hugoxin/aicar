import { formatTime } from "../animation/timeline.js";
import { stateLabel, zoneLabel } from "../config/labels.js";

function text(id, value, withTitle = false) {
  const element = document.getElementById(id);
  if (!element) return;
  element.textContent = value;
  if (withTitle) element.title = value;
}

function available(value) {
  return value ?? "未提供";
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

  function update(sample, playing) {
    const point = sample.point;
    const position = point.display_position_mm;
    const currentState = point.state_label_zh || stateLabel(point.state_id);
    const currentZone = point.zone_label_zh || zoneLabel(point.zone_id);
    text(
      "playback-state",
      playing ? "播放中" : sample.progress >= 1 ? "已结束" : "已暂停",
    );
    text("current-state", currentState);
    text("current-zone", currentZone);
    text(
      "current-point",
      `${Math.min((point.point_index ?? sample.index) + 1, summary.point_count)} / ${summary.point_count}`,
    );
    text("current-progress", `${(sample.progress * 100).toFixed(1)}%`);
    text(
      "current-speed",
      Number.isFinite(point.speed_mm_s)
        ? `${point.speed_mm_s.toFixed(1)} mm/s`
        : "未提供",
    );
    text(
      "current-execution",
      `当前正在执行：正在对【${currentZone}】进行【${currentState}】。`,
    );

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
    text("current-time", formatTime(sample.time));
    text("point-label-state", currentState);
    text("point-label-zone", currentZone);
  }

  return { update };
}
