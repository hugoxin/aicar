import "./styles.css";
import * as THREE from "three";
import { loadViewerScene } from "./data/sceneLoader.js";
import { createScene } from "./scene/createScene.js";
import { createMpvVehicle } from "./scene/createMpvVehicle.js";
import { createCameraPresetController } from "./scene/cameraPresets.js";
import { createPathLines } from "./path/createPathLines.js";
import { createScannerPoint } from "./path/createScannerPoint.js";
import { createTrail } from "./path/createTrail.js";
import { createPathInterpolator } from "./path/pathInterpolator.js";
import { createPlaybackController } from "./animation/playbackController.js";
import { adjacentStateTime, stateStartTimes } from "./animation/timeline.js";
import { createInfoPanel } from "./ui/createInfoPanel.js";
import { createLegend } from "./ui/createLegend.js";
import { createControlPanel } from "./ui/createControlPanel.js";
import { createStatusBar } from "./ui/createStatusBar.js";

const container = document.getElementById("scene-container");
const loading = document.getElementById("scene-loading");
const errorPanel = document.getElementById("scene-error");
const errorDetail = document.getElementById("scene-error-detail");
const pointLabel = document.getElementById("point-label");

function showError(error) {
  loading.hidden = true;
  errorPanel.hidden = false;
  errorDetail.textContent = error.message;
  console.error(error);
}

function pointLabelPosition(vector, camera, renderer) {
  const projected = vector.clone().project(camera);
  return {
    x: (projected.x * 0.5 + 0.5) * renderer.domElement.clientWidth,
    y: (-projected.y * 0.5 + 0.5) * renderer.domElement.clientHeight,
    visible: projected.z > -1 && projected.z < 1,
  };
}

async function bootstrap() {
  const sceneData = await loadViewerScene();
  const profile = sceneData.display_profile;
  const stage = createScene(container, profile);
  const mpv = createMpvVehicle(sceneData.vehicle, profile);
  stage.scene.add(mpv.group);

  const interpolator = createPathInterpolator(sceneData.path_points);
  const pathLines = createPathLines(sceneData.path_points, profile);
  const scanner = createScannerPoint(profile);
  const trail = createTrail(sceneData.path_points, interpolator.vectors, profile);
  stage.scene.add(pathLines.group, scanner.group, trail.line);

  const playback = createPlaybackController({
    duration: interpolator.duration,
    defaultSpeed: profile.default_playback_speed,
    loop: profile.loop_playback,
  });
  const cameraPresets = createCameraPresetController(
    stage.camera,
    stage.controls,
    sceneData.camera_presets,
  );
  cameraPresets.moveTo(profile.default_camera, 0.01);

  const infoPanel = createInfoPanel(sceneData, profile);
  const starts = stateStartTimes(sceneData.path_points);
  const statusBar = createStatusBar(profile, {
    play: () => playback.play(),
    pause: () => playback.pause(),
    reset: () => {
      playback.reset();
      trail.clear();
      updateFrame();
    },
    previousState: () => {
      playback.seek(adjacentStateTime(starts, playback.time, -1));
      updateFrame();
    },
    nextState: () => {
      playback.seek(adjacentStateTime(starts, playback.time, 1));
      updateFrame();
    },
    seek: (progress) => {
      playback.seek(progress * interpolator.duration);
      updateFrame();
    },
    speed: (speed) => playback.setSpeed(speed),
    loop: (enabled) => playback.setLoop(enabled),
  });

  let fullPathVisible = profile.show_full_path;
  createLegend(
    document.getElementById("legend"),
    sceneData.states,
    (stateId, visible) => {
      pathLines.setStateVisible(stateId, visible);
    },
    { transition: profile.show_auxiliary_paths_default },
  );

  let showPointLabel = profile.show_point_label;
  createControlPanel(document.getElementById("display-controls"), profile, {
    onMode: (mode) => mpv.setMode(mode),
    onToggle: (key, enabled) => {
      if (key === "vehicle") mpv.group.visible = enabled;
      if (key === "fullPath") {
        fullPathVisible = enabled;
        pathLines.setFullPathVisible(enabled);
      }
      if (key === "executedPath") pathLines.setExecutedVisible(enabled);
      if (key === "trail") trail.line.visible = enabled;
      if (key === "focusCurrentState") pathLines.setFocusCurrentState(enabled);
      if (key === "auxiliaryPaths") {
        pathLines.setAuxiliaryVisible(enabled);
        const legendButton = document.querySelector('[data-state="transition"]');
        legendButton?.classList.toggle("active", enabled);
        legendButton?.setAttribute("aria-pressed", String(enabled));
      }
      if (key === "axes") stage.ground.axes.visible = enabled;
      if (key === "grid") stage.ground.grid.visible = enabled;
      if (key === "pointLabel") showPointLabel = enabled;
      if (key === "lightMode") {
        stage.setLightMode(enabled);
        document.body.classList.toggle("light-mode", enabled);
      }
    },
  });

  document.querySelectorAll("[data-camera]").forEach((button) => {
    button.addEventListener("click", () => cameraPresets.moveTo(button.dataset.camera));
  });
  document.getElementById("auto-rotate-button").addEventListener("click", (event) => {
    stage.controls.autoRotate = !stage.controls.autoRotate;
    stage.controls.autoRotateSpeed = 1.1;
    event.currentTarget.classList.toggle("active", stage.controls.autoRotate);
  });

  let lastSample = interpolator.sample(0);
  let elapsed = 0;
  const clock = new THREE.Clock();
  function updateFrame() {
    lastSample = interpolator.sample(playback.time);
    pathLines.update(lastSample);
    scanner.update(lastSample.position, elapsed, lastSample.point.state_id);
    trail.rebuild(lastSample);
    infoPanel.update(lastSample, playback.playing);
    statusBar.update(lastSample.progress);
  }

  function animate() {
    requestAnimationFrame(animate);
    const delta = Math.min(0.05, clock.getDelta());
    elapsed += delta;
    playback.update(delta);
    updateFrame();
    cameraPresets.update(delta);
    stage.controls.update();

    const label = pointLabelPosition(lastSample.position, stage.camera, stage.renderer);
    pointLabel.hidden = !showPointLabel || !label.visible;
    if (!pointLabel.hidden) {
      pointLabel.style.transform = `translate(${label.x + 16}px, ${label.y - 18}px)`;
    }
    stage.renderer.render(stage.scene, stage.camera);
  }

  const resizeObserver = new ResizeObserver(stage.resize);
  resizeObserver.observe(container);
  window.addEventListener("beforeunload", () => {
    resizeObserver.disconnect();
    stage.renderer.dispose();
  }, { once: true });

  if (sceneData.source.source_mode === "DEMO_SYNTHETIC") {
    document.querySelector(".mapping-notice").textContent =
      "当前为合成演示路径，不是项目正式路径。";
    document.querySelector(".mapping-notice").classList.add("warning");
  }
  loading.hidden = true;
  updateFrame();
  animate();
}

bootstrap().catch(showError);
