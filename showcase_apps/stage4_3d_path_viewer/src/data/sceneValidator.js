const REQUIRED_PRESETS = ["isometric", "top", "left", "right", "front", "rear"];

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

export function validateViewerScene(scene) {
  assert(scene?.scene_version === "viewer-v1", "scene_version 必须为 viewer-v1");
  assert(scene?.vehicle?.vehicle_type === "mpv", "vehicle_type 必须为 mpv");
  assert(scene?.vehicle?.display_only === true, "车辆必须标记为 display_only");
  assert(Array.isArray(scene.path_points) && scene.path_points.length > 1, "轨迹点不足");
  assert(
    scene.path_summary?.point_count === scene.path_points.length,
    "point_count 与轨迹数组长度不一致",
  );
  assert(
    REQUIRED_PRESETS.every((name) => scene.camera_presets?.[name]),
    "相机预设不完整",
  );
  let lastTime = -Infinity;
  scene.path_points.forEach((point, index) => {
    assert(point.point_index === index, `point_index 在 ${index} 处不连续`);
    assert(Number.isFinite(point.timestamp_s), `点 ${index} 缺少有效时间戳`);
    assert(point.timestamp_s >= lastTime, `点 ${index} 时间戳倒序`);
    lastTime = point.timestamp_s;
    const position = point.display_position_mm;
    assert(
      ["x_mm", "y_mm", "z_mm"].every((axis) => Number.isFinite(position?.[axis])),
      `点 ${index} 显示坐标无效`,
    );
  });
  return scene;
}
