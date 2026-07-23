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
        "src/main.js",
        "src/styles.css",
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
    require(scene.get("vehicle", {}).get("vehicle_type") == "mpv", "Scene vehicle is not mpv.")
    require(scene.get("vehicle", {}).get("display_only") is True, "Scene vehicle is not display-only.")
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

    print("PASS stage4 3d path viewer")
    print("AI car stage4 3d path viewer check OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"FAIL stage4 3d path viewer: {error}", file=sys.stderr)
        raise SystemExit(1)
