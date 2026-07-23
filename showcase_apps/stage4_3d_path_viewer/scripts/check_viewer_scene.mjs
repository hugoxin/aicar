import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

const appRoot = resolve(import.meta.dirname, "..");
const scenePath = resolve(appRoot, "public", "data", "viewer_scene.json");
const scene = JSON.parse(await readFile(scenePath, "utf8"));
const requireValue = (condition, message) => {
  if (!condition) throw new Error(message);
};

requireValue(scene.scene_version === "viewer-v1", "scene_version invalid");
requireValue(scene.vehicle?.vehicle_type === "mpv", "vehicle_type invalid");
requireValue(scene.vehicle?.display_only === true, "display_only missing");
requireValue(
  ["length_mm", "width_mm", "height_mm"].every(
    (key) => Number.isFinite(scene.vehicle?.dimensions_mm?.[key]),
  ),
  "vehicle dimensions invalid",
);
requireValue(Array.isArray(scene.path_points), "path_points missing");
requireValue(
  scene.path_summary?.point_count === scene.path_points.length,
  "point count mismatch",
);

const stateColors = new Map(
  (scene.states ?? []).map((state) => [state.state_id, state.color]),
);
const chineseText = /[\u3400-\u9fff]/;
let previousTime = -Infinity;
scene.path_points.forEach((point, index) => {
  requireValue(point.point_index === index, `point_index invalid at ${index}`);
  requireValue(point.timestamp_s >= previousTime, `time order invalid at ${index}`);
  previousTime = point.timestamp_s;
  requireValue(
    ["x_mm", "y_mm", "z_mm"].every((key) =>
      Number.isFinite(point.display_position_mm?.[key]),
    ),
    `position invalid at ${index}`,
  );
  requireValue(chineseText.test(point.state_label_zh), `state label invalid at ${index}`);
  requireValue(chineseText.test(point.zone_label_zh), `zone label invalid at ${index}`);
  requireValue(
    point.is_transition || stateColors.has(point.state_id),
    `state color missing for ${point.state_id}`,
  );
});

for (const preset of ["isometric", "top", "left", "right", "front", "rear"]) {
  requireValue(scene.camera_presets?.[preset], `camera preset missing: ${preset}`);
}
const limitations = (scene.limitations ?? []).join(" ").toLowerCase();
requireValue(limitations.includes("display transform"), "display transform limitation missing");
requireValue(limitations.includes("real device"), "real-device limitation missing");

console.log(`PASS viewer scene: ${scene.path_points.length} points`);
console.log(`source mode: ${scene.source.source_mode}`);
console.log("AI car viewer scene Node check OK");
