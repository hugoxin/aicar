"""Validate the standalone Stage4 3D path viewer and generated scene contract."""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path


EXPECTED_STATES = {
    "pre_rinse",
    "foam",
    "dwell",
    "top_clean",
    "side_clean",
    "wheel_clean",
    "air_dry",
}
EXPECTED_ZONES = {"roof", "left_side", "right_side", "front", "rear", "wheels"}
EXPECTED_PRESETS = {"isometric", "top", "left", "right", "front", "rear"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_ignored(root: Path, relative_path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", relative_path],
        cwd=root,
        check=False,
    )
    return result.returncode == 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    app = Path(__file__).resolve().parents[1]
    root = app.parents[1]
    required = [
        "README.md",
        "package.json",
        "vite.config.js",
        "index.html",
        "start_viewer.bat",
        "config/demo_mpv_dimensions.json",
        "config/viewer_display_profile.json",
        "tools/export_viewer_scene.py",
        "tools/generate_demo_mpv_scene.py",
        "scripts/check_viewer_scene.mjs",
        "scripts/check_viewer_semantics.mjs",
        "src/main.js",
        "src/styles.css",
        "src/path/pathRoleClassifier.js",
        "src/path/presentationContext.js",
        "src/path/pathInterpolator.js",
        "docs/VIEWER_V1_0_1_VISUAL_PATCH.md",
        "docs/VIEWER_V1_0_2_SEMANTIC_CONSISTENCY_FIX.md",
        "public/data/.gitkeep",
        "outputs/.gitkeep",
    ]
    missing = [relative for relative in required if not (app / relative).exists()]
    require(not missing, f"Missing viewer files: {', '.join(missing)}")

    vehicle = json.loads(
        (app / "config" / "demo_mpv_dimensions.json").read_text(encoding="utf-8")
    )
    display = json.loads(
        (app / "config" / "viewer_display_profile.json").read_text(encoding="utf-8")
    )
    require(vehicle.get("vehicle_type") == "mpv", "Vehicle profile must be mpv.")
    require(vehicle.get("display_only") is True, "Vehicle profile must be display-only.")
    dimensions = vehicle.get("dimensions") or {}
    require(
        all(dimensions.get(key, 0) > 0 for key in ("length_mm", "width_mm", "height_mm")),
        "Vehicle dimensions must be positive.",
    )
    require(
        display.get("maximum_viewer_points", 0) >= 2500,
        "maximum_viewer_points is too small for the frozen Stage4.5-R path.",
    )
    required_display_keys = {
        "scanner_point_radius",
        "scanner_point_pulse_scale",
        "scanner_point_pulse_duration_s",
        "scanner_halo_radius_ratio",
        "scanner_halo_opacity",
        "scanner_crosshair_enabled",
        "current_segment_opacity",
        "executed_path_opacity",
        "future_path_opacity",
        "auxiliary_path_opacity",
        "inactive_state_opacity_ratio",
        "focus_current_state_default",
        "show_auxiliary_paths_default",
        "trail_point_count",
        "trail_start_opacity",
        "trail_end_opacity",
        "vehicle_body_opacity",
        "vehicle_wireframe_opacity",
        "technical_details_expanded_default",
    }
    require(
        required_display_keys <= display.keys(),
        "Viewer display profile keys are incomplete.",
    )
    require(
        display["current_segment_opacity"]
        > display["executed_path_opacity"]
        > display["future_path_opacity"]
        > display["auxiliary_path_opacity"],
        "Path opacity hierarchy must be current > executed > future > auxiliary.",
    )
    require(
        display["focus_current_state_default"] is True,
        "Current-state focus must be enabled by default.",
    )
    require(
        display["show_auxiliary_paths_default"] is False,
        "Auxiliary paths must be hidden by default.",
    )
    require(
        display["technical_details_expanded_default"] is False,
        "Technical details must be collapsed by default.",
    )
    require(
        display["trail_point_count"] <= 120,
        "Trail point count exceeds the V1 limit.",
    )

    index_text = (app / "index.html").read_text(encoding="utf-8")
    controls_text = (app / "src" / "ui" / "createControlPanel.js").read_text(
        encoding="utf-8"
    )
    main_text = (app / "src" / "main.js").read_text(encoding="utf-8")
    info_text = (app / "src" / "ui" / "createInfoPanel.js").read_text(
        encoding="utf-8"
    )
    scanner_text = (app / "src" / "path" / "createScannerPoint.js").read_text(
        encoding="utf-8"
    )
    path_lines_text = (app / "src" / "path" / "createPathLines.js").read_text(
        encoding="utf-8"
    )
    semantics_text = (
        app / "scripts" / "check_viewer_semantics.mjs"
    ).read_text(encoding="utf-8")
    require("阶段4 · 离线轨迹展示" in index_text, "Chinese-first title is missing.")
    require("当前正在执行" in index_text, "Current execution sentence is missing.")
    require("当前动作" in index_text, "Current action field is missing.")
    require("技术详情" in index_text, "Technical details panel is missing.")
    require(
        "辅助连接线表示不同扫描区域之间的移动，不代表持续喷洗" in controls_text,
        "Auxiliary path explanation is missing.",
    )
    require(
        "不连接PLC或真实设备" in index_text,
        "Real-device boundary notice is missing.",
    )
    require(
        "presentationResolver.contextFor(lastSample)" in main_text,
        "Main UI does not resolve one presentation context.",
    )
    require(
        "pathLines.update(lastSample, lastPresentation)" in main_text,
        "Path highlighter does not receive presentation context.",
    )
    require(
        "scanner.update(lastSample.position, elapsed, lastPresentation)" in main_text,
        "Scanner does not receive presentation context.",
    )
    require(
        "infoPanel.update(lastSample, lastPresentation, playback.playing)" in main_text,
        "Info panel does not receive presentation context.",
    )
    require(
        "presentationContext.executionDescriptionZh" in info_text,
        "Info panel does not use presentation context description.",
    )
    require(
        "scannerColor(presentationContext)" in scanner_text,
        "Scanner color does not use presentation context.",
    )
    require(
        "[sample.fromPosition, sample.toPosition]" in path_lines_text,
        "Current highlighter is not the exact active segment.",
    )
    require(
        'scenario("B_34_8_PERCENT", 0.348)' in semantics_text,
        "34.8 percent semantic scenario is missing.",
    )
    require(
        "transitionRuns" in semantics_text,
        "State transition boundary checks are missing.",
    )

    exporter = app / "tools" / "export_viewer_scene.py"
    result = subprocess.run([sys.executable, str(exporter)], cwd=root, check=False)
    require(result.returncode == 0, "Viewer scene exporter failed.")
    scene_path = app / "public" / "data" / "viewer_scene.json"
    require(scene_path.exists(), "viewer_scene.json was not generated.")
    scene = json.loads(scene_path.read_text(encoding="utf-8"))

    points = scene.get("path_points") or []
    summary = scene.get("path_summary") or {}
    require(scene.get("scene_version") == "viewer-v1", "Invalid scene_version.")
    require(
        scene.get("source", {}).get("source_mode") == "STAGE4_5_MACHINE_PATH",
        "Formal viewer data must use STAGE4_5_MACHINE_PATH.",
    )
    require(summary.get("point_count") == len(points), "point_count mismatch.")
    require(len(points) == 2503, "Frozen Stage4.5-R viewer point count changed.")
    require(summary.get("source_point_count") == 2503, "Source point count changed.")
    require(summary.get("state_count") == 7, "State count changed.")
    require(summary.get("zone_count") == 6, "Zone count changed.")
    require(
        math.isclose(summary.get("path_length_mm", 0), 328502.099, abs_tol=0.001),
        "Frozen path length changed.",
    )
    require(
        math.isclose(summary.get("duration_s", 0), 2570.902629, abs_tol=0.001),
        "Frozen duration changed.",
    )
    require(len(scene.get("warnings") or []) == 0, "Export warnings changed.")
    require(len(points) > 1, "Path points are missing.")
    require(
        [point.get("point_index") for point in points] == list(range(len(points))),
        "point_index is not contiguous.",
    )
    timestamps = [point.get("timestamp_s") for point in points]
    require(
        all(isinstance(value, (int, float)) for value in timestamps),
        "A timestamp is missing.",
    )
    require(
        all(current >= previous for previous, current in zip(timestamps, timestamps[1:])),
        "Timestamps are not monotonic.",
    )
    for point in points:
        position = point.get("display_position_mm") or {}
        require(
            all(
                isinstance(position.get(axis), (int, float))
                and math.isfinite(position[axis])
                for axis in ("x_mm", "y_mm", "z_mm")
            ),
            f"Invalid display position at point {point.get('point_index')}.",
        )

    states = {item.get("state_id"): item for item in scene.get("states") or []}
    require(EXPECTED_STATES <= states.keys(), "Seven state semantics are not complete.")
    require(
        states["dwell"].get("has_motion_path") is False
        and states["dwell"].get("viewer_note"),
        "dwell missing-motion semantics are not explained.",
    )
    zones = {item.get("zone_id") for item in scene.get("zones") or []}
    require(zones == EXPECTED_ZONES, f"Unexpected zones: {sorted(zones)}")
    require(
        EXPECTED_PRESETS <= scene.get("camera_presets", {}).keys(),
        "Camera presets are incomplete.",
    )
    require(
        scene.get("vehicle", {}).get("vehicle_type") == "mpv",
        "Scene vehicle is not mpv.",
    )
    require(
        scene.get("vehicle", {}).get("display_only") is True,
        "Scene vehicle is not display-only.",
    )
    limitations = " ".join(scene.get("limitations") or []).lower()
    require(
        "display transform" in limitations and "safety" in limitations,
        "Display transform limitations are incomplete.",
    )

    scene_relative = scene_path.relative_to(root).as_posix()
    require(git_ignored(root, scene_relative), "Generated viewer_scene.json is not ignored.")
    require(
        git_ignored(
            root,
            "showcase_apps/stage4_3d_path_viewer/node_modules/example.tmp",
        ),
        "node_modules is not ignored.",
    )
    require(
        git_ignored(root, "showcase_apps/stage4_3d_path_viewer/outputs/example.log"),
        "viewer outputs are not ignored.",
    )

    semantic_result = subprocess.run(
        ["node", "scripts/check_viewer_semantics.mjs"],
        cwd=app,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    print(semantic_result.stdout, end="")
    if semantic_result.stderr:
        print(semantic_result.stderr, end="")
    require(semantic_result.returncode == 0, "Node semantic check failed.")

    print("PASS stage4 3d path viewer")
    print("PASS source/viewer points: 2503 / 2503")
    print("PASS states/zones: 7 / 6")
    print("PASS path length: 328.502099 m")
    print("PASS duration: 2570.902629 s")
    print("PASS export warnings: 0")
    print("AI car stage4 3d path viewer check OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"FAIL stage4 3d path viewer: {error}", file=sys.stderr)
        raise SystemExit(1)
