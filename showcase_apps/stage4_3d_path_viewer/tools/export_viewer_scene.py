"""Export frozen Stage4.5-R path data into the viewer-v1 scene contract."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATE_LABELS = {
    "pre_rinse": "预冲洗",
    "foam": "泡沫喷涂",
    "dwell": "静置等待",
    "top_clean": "顶部清洗",
    "side_clean": "侧面清洗",
    "wheel_clean": "车轮清洗",
    "air_dry": "风干",
}

ZONE_LABELS = {
    "roof": "车顶",
    "left_side": "左侧车身",
    "right_side": "右侧车身",
    "front": "车头",
    "rear": "车尾",
    "wheels": "车轮",
}

STATE_COLORS = {
    "pre_rinse": "#3b82f6",
    "foam": "#3ddc97",
    "dwell": "#8b95a5",
    "top_clean": "#ff9f43",
    "side_clean": "#a879ff",
    "wheel_clean": "#ff5d67",
    "air_dry": "#24d6d1",
    "transition": "#e8edf5",
}

SOURCE_REFERENCE_DIMENSIONS = {
    "length_mm": 4700.0,
    "width_mm": 1800.0,
    "height_mm": 1450.0,
}


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def finite_number(value: Any) -> float | None:
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def position_from_point(point: dict[str, Any]) -> dict[str, float] | None:
    machine = point.get("machine_point") or {}
    values = (
        finite_number(machine.get("x_mm", point.get("x_mm"))),
        finite_number(machine.get("y_mm", point.get("y_mm"))),
        finite_number(machine.get("z_mm", point.get("z_mm"))),
    )
    if any(value is None for value in values):
        return None
    return {"x_mm": values[0], "y_mm": values[1], "z_mm": values[2]}


def bbox(positions: list[dict[str, float]]) -> dict[str, dict[str, float]]:
    return {
        "min": {
            axis: round(min(position[axis] for position in positions), 6)
            for axis in ("x_mm", "y_mm", "z_mm")
        },
        "max": {
            axis: round(max(position[axis] for position in positions), 6)
            for axis in ("x_mm", "y_mm", "z_mm")
        },
    }


def path_length(points: list[dict[str, Any]], key: str) -> float:
    total = 0.0
    for previous, current in zip(points, points[1:]):
        a = previous[key]
        b = current[key]
        total += math.dist(
            (a["x_mm"], a["y_mm"], a["z_mm"]),
            (b["x_mm"], b["y_mm"], b["z_mm"]),
        )
    return round(total, 6)


def ensure_stage4_5_outputs(root: Path, machine_path: Path, surface_path: Path) -> None:
    if machine_path.exists() and surface_path.exists():
        return

    scripts = [
        root / "aicar_sim" / "scripts" / "generate_continuous_surface_path_r.py",
        root / "aicar_sim" / "scripts" / "generate_continuous_machine_path_r.py",
    ]
    missing_scripts = [str(path) for path in scripts if not path.exists()]
    if missing_scripts:
        raise FileNotFoundError(
            "Stage4.5-R outputs are missing and generation scripts were not found: "
            + ", ".join(missing_scripts)
        )
    for script in scripts:
        subprocess.run([sys.executable, str(script)], cwd=root, check=True)
    if not machine_path.exists() or not surface_path.exists():
        raise FileNotFoundError("Stage4.5-R generation completed without required outputs.")


def important_indices(points: list[dict[str, Any]]) -> set[int]:
    keep = {0, len(points) - 1}
    for index, point in enumerate(points):
        if point.get("is_transition"):
            keep.add(index)
        if point.get("critical_point_type") in {"PASS_START", "PASS_END"}:
            keep.add(index)
        if index and (
            point.get("state_id") != points[index - 1].get("state_id")
            or point.get("scan_pass_id") != points[index - 1].get("scan_pass_id")
            or point.get("segment_id") != points[index - 1].get("segment_id")
        ):
            keep.update({index - 1, index})
    return keep


def downsample_indices(points: list[dict[str, Any]], maximum: int) -> list[int]:
    if len(points) <= maximum:
        return list(range(len(points)))
    required = important_indices(points)
    if len(required) >= maximum:
        raise ValueError(
            f"maximum_viewer_points={maximum} is too small for {len(required)} required boundaries."
        )
    ordinary = [index for index in range(len(points)) if index not in required]
    slots = maximum - len(required)
    if slots:
        sampled = {
            ordinary[round(position * (len(ordinary) - 1) / max(slots - 1, 1))]
            for position in range(slots)
        }
    else:
        sampled = set()
    return sorted(required | sampled)


def parser() -> argparse.ArgumentParser:
    root = workspace_root()
    app = root / "showcase_apps" / "stage4_3d_path_viewer"
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--source-machine-path",
        type=Path,
        default=root
        / "aicar_sim"
        / "outputs"
        / "continuous_machine_path_r"
        / "continuous_machine_path_plan_r.json",
    )
    result.add_argument(
        "--source-surface-path",
        type=Path,
        default=root
        / "aicar_sim"
        / "outputs"
        / "continuous_surface_path_r"
        / "continuous_surface_path_plan_r.json",
    )
    result.add_argument(
        "--vehicle-profile",
        type=Path,
        default=app / "config" / "demo_mpv_dimensions.json",
    )
    result.add_argument(
        "--display-profile",
        type=Path,
        default=app / "config" / "viewer_display_profile.json",
    )
    result.add_argument(
        "--output",
        type=Path,
        default=app / "public" / "data" / "viewer_scene.json",
    )
    result.add_argument("--max-points", type=int)
    result.add_argument("--force-regenerate", action="store_true")
    return result


def export_scene(args: argparse.Namespace) -> tuple[dict[str, Any], list[str]]:
    root = workspace_root()
    machine_path = args.source_machine_path.resolve()
    surface_path = args.source_surface_path.resolve()
    if args.force_regenerate:
        # Existing Stage4.5 scripts own regeneration. The exporter never edits source files.
        for script_name in (
            "generate_continuous_surface_path_r.py",
            "generate_continuous_machine_path_r.py",
        ):
            script = root / "aicar_sim" / "scripts" / script_name
            if not script.exists():
                raise FileNotFoundError(f"Required regeneration script missing: {script}")
            subprocess.run([sys.executable, str(script)], cwd=root, check=True)
    else:
        ensure_stage4_5_outputs(root, machine_path, surface_path)

    machine = read_json(machine_path)
    surface = read_json(surface_path)
    vehicle_profile = read_json(args.vehicle_profile.resolve())
    display_profile = read_json(args.display_profile.resolve())
    warnings: list[str] = list(machine.get("warnings") or [])

    machine_points = machine.get("trajectory_points") or []
    if not machine_points:
        raise ValueError("Machine path contains no trajectory_points.")

    clean_points: list[dict[str, Any]] = []
    for source_index, point in enumerate(machine_points):
        source_position = position_from_point(point)
        if source_position is None:
            warnings.append(f"Skipped point {source_index}: invalid machine position.")
            continue
        clean_points.append(
            {
                "source_index": source_index,
                "raw": point,
                "source_position_mm": source_position,
            }
        )
    if len(clean_points) < 2:
        raise ValueError("Fewer than two valid machine path points were found.")

    dimensions = vehicle_profile["dimensions"]
    display_scale = {
        "x": dimensions["width_mm"] / SOURCE_REFERENCE_DIMENSIONS["width_mm"],
        "y": dimensions["length_mm"] / SOURCE_REFERENCE_DIMENSIONS["length_mm"],
        "z": dimensions["height_mm"] / SOURCE_REFERENCE_DIMENSIONS["height_mm"],
    }
    display_translation = {"x_mm": 0.0, "y_mm": 0.0, "z_mm": 0.0}
    for item in clean_points:
        source = item["source_position_mm"]
        item["display_position_mm"] = {
            "x_mm": round(source["x_mm"] * display_scale["x"], 6),
            "y_mm": round(source["y_mm"] * display_scale["y"], 6),
            "z_mm": round(source["z_mm"] * display_scale["z"], 6),
        }

    max_points = args.max_points or int(display_profile["maximum_viewer_points"])
    selected = downsample_indices([item["raw"] for item in clean_points], max_points)
    selected_items = [clean_points[index] for index in selected]
    first_timestamp = finite_number(selected_items[0]["raw"].get("timestamp_s")) or 0.0

    path_points: list[dict[str, Any]] = []
    for point_index, item in enumerate(selected_items):
        raw = item["raw"]
        timestamp = finite_number(raw.get("timestamp_s"))
        if timestamp is None:
            timestamp = float(item["source_index"])
            warnings.append(
                f"Point {item['source_index']} has no timestamp; source index was used."
            )
        state_id = raw.get("state_id")
        zone_id = raw.get("zone_id")
        segment_id = raw.get("segment_id")
        path_points.append(
            {
                "point_index": point_index,
                "source_sequence_index": raw.get("sequence_index", item["source_index"]),
                "source_point_index": item["source_index"],
                "timestamp_s": round(timestamp, 6),
                "relative_time_s": round(max(0.0, timestamp - first_timestamp), 6),
                "source_position_mm": item["source_position_mm"],
                "display_position_mm": item["display_position_mm"],
                "state_id": state_id,
                "state_label_zh": STATE_LABELS.get(state_id, "未提供"),
                "zone_id": zone_id,
                "zone_label_zh": ZONE_LABELS.get(zone_id, "未提供"),
                "segment_id": segment_id,
                "scan_pass_id": raw.get("scan_pass_id"),
                "surface_task_id": segment_id,
                "critical_point_type": raw.get("critical_point_type"),
                "speed_mm_s": finite_number(
                    raw.get("velocity_mm_s", raw.get("target_speed_mm_s"))
                ),
                "is_transition": bool(raw.get("is_transition")),
            }
        )

    surface_states = surface.get("states") or []
    states = []
    for state in surface_states:
        state_id = state["state_id"]
        states.append(
            {
                **state,
                "label_zh": STATE_LABELS.get(state_id, state_id),
                "color": STATE_COLORS.get(state_id, "#ffffff"),
                "viewer_note": (
                    "该状态无运动轨迹，仅保留流程语义。"
                    if not state.get("has_motion_path", True)
                    else None
                ),
            }
        )
    present_states = {state["state_id"] for state in states}
    for state_id in STATE_LABELS:
        if state_id not in present_states:
            warnings.append(f"Stage semantic missing from surface source: {state_id}")

    zone_ids = sorted(
        {
            point["zone_id"]
            for point in path_points
            if isinstance(point.get("zone_id"), str)
        }
        | {
            zone
            for state in surface_states
            for zone in state.get("target_zone_ids", [])
        }
    )
    zones = [
        {"zone_id": zone_id, "label_zh": ZONE_LABELS.get(zone_id, zone_id)}
        for zone_id in zone_ids
    ]

    source_positions = [item["source_position_mm"] for item in clean_points]
    display_positions = [point["display_position_mm"] for point in path_points]
    source_bbox = bbox(source_positions)
    display_bbox = bbox(display_positions)
    duration = path_points[-1]["relative_time_s"]
    source_length = finite_number(machine.get("summary", {}).get("path_length_mm"))
    if source_length is None:
        source_length = path_length(clean_points, "source_position_mm")

    camera_distance = max(dimensions["length_mm"], dimensions["width_mm"]) * 1.45
    camera_height = dimensions["height_mm"] * 1.7
    camera_presets = {
        "isometric": {"position_mm": [camera_distance, camera_distance, camera_height]},
        "top": {"position_mm": [0, 0, camera_distance * 1.2]},
        "left": {"position_mm": [-camera_distance, 0, camera_height * 0.55]},
        "right": {"position_mm": [camera_distance, 0, camera_height * 0.55]},
        "front": {"position_mm": [0, -camera_distance, camera_height * 0.55]},
        "rear": {"position_mm": [0, camera_distance, camera_height * 0.55]},
    }
    for preset in camera_presets.values():
        preset["target_mm"] = [0, 0, dimensions["height_mm"] * 0.45]

    limitations = [
        "Display transform only; this is not a replanned or safety-validated MPV path.",
        "The generic MPV body is display-only and is not manufacturer-specific CAD.",
        "Stage4.5 safety metrics must not be applied to the scaled display geometry.",
        "Offline visualization only; no PLC, actuator, robot, or real device connection.",
    ]
    scene = {
        "scene_version": "viewer-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "source_mode": "STAGE4_5_MACHINE_PATH",
            "source_file": str(machine_path.relative_to(root)).replace("\\", "/"),
            "surface_source_file": str(surface_path.relative_to(root)).replace("\\", "/"),
            "source_commit_or_tag": "stage4-continuous-surface-baseline",
            "display_transform_applied": True,
        },
        "vehicle": {
            "vehicle_type": "mpv",
            "vehicle_profile_id": vehicle_profile["vehicle_profile_id"],
            "display_only": True,
            "dimensions_mm": dimensions,
            "body_proportions": vehicle_profile["body_proportions"],
            "limitations": vehicle_profile.get("limitations", []),
        },
        "coordinate_system": {
            "unit": "mm",
            "x_axis": "vehicle_width",
            "y_axis": "vehicle_length",
            "z_axis": "height",
            "three_js_mapping": "Three.js (x, y, z) = source (x, z, -y)",
        },
        "display_transform": {
            "type": "axis_scale",
            "source_reference_dimensions_mm": SOURCE_REFERENCE_DIMENSIONS,
            "display_scale": {key: round(value, 9) for key, value in display_scale.items()},
            "display_translation_mm": display_translation,
            "purpose": "visualization_only",
        },
        "display_profile": display_profile,
        "path_summary": {
            "point_count": len(path_points),
            "state_count": len(states),
            "zone_count": len(zones),
            "segment_count": len(
                {point["segment_id"] for point in path_points if point["segment_id"]}
            ),
            "duration_s": duration,
            "path_length_mm": round(source_length, 6),
            "display_path_length_mm": path_length(path_points, "display_position_mm"),
            "source_point_count": len(clean_points),
            "downsampled": len(path_points) < len(clean_points),
            "source_bbox_mm": source_bbox,
            "display_bbox_mm": display_bbox,
        },
        "states": states,
        "zones": zones,
        "camera_presets": camera_presets,
        "path_points": path_points,
        "warnings": sorted(set(warnings)),
        "limitations": limitations,
    }
    return scene, warnings


def validate_scene(scene: dict[str, Any]) -> None:
    points = scene["path_points"]
    summary = scene["path_summary"]
    if summary["point_count"] != len(points):
        raise ValueError("path_summary.point_count does not match path_points length.")
    if not points:
        raise ValueError("No path points were exported.")
    if [point["point_index"] for point in points] != list(range(len(points))):
        raise ValueError("point_index is not contiguous.")
    timestamps = [point["timestamp_s"] for point in points]
    if any(current < previous for previous, current in zip(timestamps, timestamps[1:])):
        raise ValueError("timestamps are not monotonic.")
    for point in points:
        values = point["display_position_mm"].values()
        if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in values):
            raise ValueError(f"Invalid display position at point {point['point_index']}.")


def main() -> int:
    args = parser().parse_args()
    scene, warnings = export_scene(args)
    validate_scene(scene)
    output = args.output.resolve()
    write_json(output, scene)
    summary = scene["path_summary"]
    print(f"source mode: {scene['source']['source_mode']}")
    print(f"source point count: {summary['source_point_count']}")
    print(f"viewer point count: {summary['point_count']}")
    print(f"state count: {summary['state_count']}")
    print(f"zone count: {summary['zone_count']}")
    print(f"source bbox: {summary['source_bbox_mm']}")
    print(f"display bbox: {summary['display_bbox_mm']}")
    print(f"path length: {summary['path_length_mm']:.3f} mm")
    print(f"duration: {summary['duration_s']:.3f} s")
    print(f"downsampled: {summary['downsampled']}")
    print(f"output path: {output}")
    print(f"warnings: {len(set(warnings))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
