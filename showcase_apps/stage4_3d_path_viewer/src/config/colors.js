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
  current: "#ffffff",
  executed: "#dcebf5",
  future: "#9fb5c3",
  auxiliary: "#83929d",
  auxiliaryHighlight: "#f2f7fa",
  stateTransition: "#f0c66b",
  unknown: "#a8b2ba",
  unknownWarning: "#ff8b7c",
  scanner: "#fff7b2",
  scannerHalo: "#ffffff",
  currentSegment: "#ffffff",
  labelText: "#edf6fa",
  labelBackground: "#111a20",
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
    ? VIEWER_COLORS.auxiliary
    : STATE_COLORS[stateId] ?? VIEWER_COLORS.unknown;
}

export function stateColor(stateId) {
  return STATE_COLORS[stateId] ?? VIEWER_COLORS.unknown;
}
