import { formatTime } from "../animation/timeline.js";
import { stateLabel, zoneLabel } from "../config/labels.js";

function text(id, value) {
  const element = document.getElementById(id);
  if (element) element.textContent = value;
}

export function createInfoPanel(sceneData) {
  const summary = sceneData.path_summary;
  text("total-path", `${(summary.path_length_mm / 1000).toFixed(1)} m`);
  text("total-duration", `${formatTime(summary.duration_s)} (${(summary.duration_s / 60).toFixed(1)} min)`);
  text("total-time", formatTime(summary.duration_s));
  text(
    "source-name",
    sceneData.source.source_mode === "DEMO_SYNTHETIC"
      ? "合成演示路径"
      : "Stage4.5连续清洗面路径",
  );
  text(
    "mode-name",
    sceneData.source.source_mode === "DEMO_SYNTHETIC"
      ? "合成数据模式"
      : "MPV演示映射",
  );

  function update(sample, playing) {
    const point = sample.point;
    const position = point.display_position_mm;
    text("playback-state", playing ? "播放中" : sample.progress >= 1 ? "已结束" : "已暂停");
    text("current-state", point.state_label_zh || stateLabel(point.state_id));
    text("current-state-id", point.state_id ?? "—");
    text("current-zone", point.zone_label_zh || zoneLabel(point.zone_id));
    text("current-zone-id", point.zone_id ?? "—");
    text("current-point", `${Math.min(sample.index + 1, summary.point_count)} / ${summary.point_count}`);
    text("current-progress", `${(sample.progress * 100).toFixed(1)}%`);
    text(
      "current-coordinate",
      `X ${position.x_mm.toFixed(0)} · Y ${position.y_mm.toFixed(0)} · Z ${position.z_mm.toFixed(0)}`,
    );
    text(
      "current-speed",
      Number.isFinite(point.speed_mm_s) ? `${point.speed_mm_s.toFixed(1)} mm/s` : "未提供",
    );
    text("current-segment", point.segment_id ?? "未提供");
    text("current-scan-pass", point.scan_pass_id ?? "未提供");
    text("current-time", formatTime(sample.time));
    text("point-label-state", point.state_label_zh || stateLabel(point.state_id));
    text("point-label-zone", point.zone_label_zh || zoneLabel(point.zone_id));
  }

  return { update };
}
