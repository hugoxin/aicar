import { validateViewerScene } from "./sceneValidator.js";

export async function loadViewerScene(url = "/data/viewer_scene.json") {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`无法读取 ${url}（HTTP ${response.status}）`);
  }
  let data;
  try {
    data = await response.json();
  } catch (error) {
    throw new Error(`轨迹 JSON 无法解析：${error.message}`);
  }
  return validateViewerScene(data);
}
