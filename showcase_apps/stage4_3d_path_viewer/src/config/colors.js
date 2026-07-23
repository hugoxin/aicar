export const STATE_COLORS = Object.freeze({
  pre_rinse: "#36a3ff",
  foam: "#54d68b",
  dwell: "#9aa4ad",
  top_clean: "#ffad3d",
  side_clean: "#b978ff",
  wheel_clean: "#ff5d68",
  air_dry: "#32d7d0",
  transition: "#e8edf2",
});

export const VIEWER_COLORS = Object.freeze({
  executed: "#fff27a",
  scanner: "#fff7b2",
  currentSegment: "#ffffff",
  body: "#6d8294",
  bodyWire: "#b6c7d6",
  windows: "#1f3947",
  tire: "#11161b",
  rim: "#a5b0b9",
  groundDark: "#182028",
  groundLight: "#d8dde2",
});

export function pathColor(stateId, isTransition = false) {
  return isTransition
    ? STATE_COLORS.transition
    : STATE_COLORS[stateId] ?? "#ffffff";
}
