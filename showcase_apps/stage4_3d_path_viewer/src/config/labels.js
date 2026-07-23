export const STATE_LABELS = Object.freeze({
  pre_rinse: "预冲洗",
  foam: "泡沫喷涂",
  dwell: "静置等待",
  top_clean: "顶部清洗",
  side_clean: "侧面清洗",
  wheel_clean: "车轮清洗",
  air_dry: "风干",
  transition: "状态切换",
});

export const ZONE_LABELS = Object.freeze({
  roof: "车顶",
  left_side: "左侧车身",
  right_side: "右侧车身",
  front: "车头",
  rear: "车尾",
  wheels: "车轮",
});

export function stateLabel(stateId) {
  return STATE_LABELS[stateId] ?? "未提供";
}

export function zoneLabel(zoneId) {
  return ZONE_LABELS[zoneId] ?? "未提供";
}
