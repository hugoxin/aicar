"""Generate an explicitly synthetic fallback scene for viewer development only."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path


def create_path_points() -> list[dict]:
    points: list[dict] = []
    index = 0
    timestamp = 0.0
    specs = [
        ("top_clean", "roof", 1750.0, "#ff9f43"),
        ("side_clean", "left_side", 1000.0, "#a879ff"),
        ("side_clean", "right_side", 1000.0, "#a879ff"),
    ]
    for state_id, zone_id, height, _ in specs:
        for step in range(121):
            ratio = step / 120
            x = 0.0
            if zone_id == "left_side":
                x = -1180.0
            elif zone_id == "right_side":
                x = 1180.0
            else:
                x = math.sin(ratio * math.pi * 6) * 900.0
            y = -2500.0 + ratio * 5000.0
            z = height
            points.append(
                {
                    "point_index": index,
                    "source_sequence_index": index,
                    "source_point_index": index,
                    "timestamp_s": timestamp,
                    "relative_time_s": timestamp,
                    "source_position_mm": {"x_mm": x, "y_mm": y, "z_mm": z},
                    "display_position_mm": {"x_mm": x, "y_mm": y, "z_mm": z},
                    "state_id": state_id,
                    "state_label_zh": {
                        "top_clean": "顶部清洗",
                        "side_clean": "侧面清洗",
                    }[state_id],
                    "zone_id": zone_id,
                    "zone_label_zh": {
                        "roof": "车顶",
                        "left_side": "左侧车身",
                        "right_side": "右侧车身",
                    }[zone_id],
                    "segment_id": f"demo_{zone_id}",
                    "scan_pass_id": f"demo_{zone_id}_pass",
                    "surface_task_id": f"demo_{zone_id}",
                    "critical_point_type": "PASS_START" if step == 0 else "PASS_END" if step == 120 else None,
                    "speed_mm_s": 180.0,
                    "is_transition": False,
                }
            )
            index += 1
            timestamp = round(timestamp + 0.12, 6)
    return points


def main() -> int:
    app = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=app / "public" / "data" / "viewer_scene.json",
    )
    args = parser.parse_args()
    profile = json.loads(
        (app / "config" / "demo_mpv_dimensions.json").read_text(encoding="utf-8")
    )
    display = json.loads(
        (app / "config" / "viewer_display_profile.json").read_text(encoding="utf-8")
    )
    points = create_path_points()
    scene = {
        "scene_version": "viewer-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "source_mode": "DEMO_SYNTHETIC",
            "source_file": None,
            "surface_source_file": None,
            "source_commit_or_tag": None,
            "display_transform_applied": False,
        },
        "vehicle": {
            "vehicle_type": "mpv",
            "vehicle_profile_id": profile["vehicle_profile_id"],
            "display_only": True,
            "dimensions_mm": profile["dimensions"],
            "body_proportions": profile["body_proportions"],
            "limitations": profile["limitations"],
        },
        "coordinate_system": {
            "unit": "mm",
            "x_axis": "vehicle_width",
            "y_axis": "vehicle_length",
            "z_axis": "height",
            "three_js_mapping": "Three.js (x, y, z) = source (x, z, -y)",
        },
        "display_transform": {
            "type": "identity",
            "display_scale": {"x": 1, "y": 1, "z": 1},
            "display_translation_mm": {"x_mm": 0, "y_mm": 0, "z_mm": 0},
            "purpose": "synthetic_development_only",
        },
        "display_profile": display,
        "path_summary": {
            "point_count": len(points),
            "state_count": 2,
            "zone_count": 3,
            "segment_count": 3,
            "duration_s": points[-1]["relative_time_s"],
            "path_length_mm": 15000,
            "display_path_length_mm": 15000,
            "source_point_count": len(points),
            "downsampled": False,
            "source_bbox_mm": None,
            "display_bbox_mm": None,
        },
        "states": [
            {"state_id": "top_clean", "label_zh": "顶部清洗", "color": "#ff9f43"},
            {"state_id": "side_clean", "label_zh": "侧面清洗", "color": "#a879ff"},
        ],
        "zones": [
            {"zone_id": "roof", "label_zh": "车顶"},
            {"zone_id": "left_side", "label_zh": "左侧车身"},
            {"zone_id": "right_side", "label_zh": "右侧车身"},
        ],
        "camera_presets": {
            "isometric": {"position_mm": [7000, 7000, 3500], "target_mm": [0, 0, 800]},
            "top": {"position_mm": [0, 0, 7000], "target_mm": [0, 0, 800]},
            "left": {"position_mm": [-7000, 0, 1200], "target_mm": [0, 0, 800]},
            "right": {"position_mm": [7000, 0, 1200], "target_mm": [0, 0, 800]},
            "front": {"position_mm": [0, -7000, 1200], "target_mm": [0, 0, 800]},
            "rear": {"position_mm": [0, 7000, 1200], "target_mm": [0, 0, 800]},
        },
        "path_points": points,
        "warnings": ["Synthetic development fallback; not the formal Stage4.5-R path."],
        "limitations": [
            "Synthetic development-only path.",
            "Not planned or safety validated.",
            "Offline visualization only; no real device connection.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(scene, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("DEMO_SYNTHETIC viewer scene saved:", args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
