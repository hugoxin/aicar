from __future__ import annotations

from typing import Any


def build_swept_aabb(
    point_a: dict[str, Any],
    point_b: dict[str, Any],
    end_effector: dict[str, Any],
    margin_mm: float,
) -> dict[str, float]:
    radius = float(end_effector.get("radius_mm", 0))
    half = end_effector.get("carriage_half_size_mm", {})
    expansion = {
        axis: max(radius, float(half.get(axis, 0))) + float(margin_mm)
        for axis in ("x", "y", "z")
    }
    return {
        f"{axis}_min_mm": min(float(point_a[f"{axis}_mm"]), float(point_b[f"{axis}_mm"])) - expansion[axis]
        for axis in ("x", "y", "z")
    } | {
        f"{axis}_max_mm": max(float(point_a[f"{axis}_mm"]), float(point_b[f"{axis}_mm"])) + expansion[axis]
        for axis in ("x", "y", "z")
    }


def build_trajectory_swept_volumes(
    points: list[dict[str, Any]],
    actuator: dict[str, Any],
    margin_mm: float,
    task_id: str | None = None,
) -> list[dict[str, Any]]:
    volumes = []
    actuator_id = actuator["actuator_id"]
    for index, (point_a, point_b) in enumerate(zip(points, points[1:])):
        volumes.append(
            {
                "swept_volume_id": f"{actuator_id}_{task_id or 'path'}_swept_{index:05d}",
                "actuator_id": actuator_id,
                "task_id": task_id,
                "start_point_index": point_a.get("sequence_index"),
                "end_point_index": point_b.get("sequence_index"),
                "segment_id": point_b.get("segment_id"),
                "state_id": point_b.get("state_id"),
                "zone_id": point_b.get("zone_id"),
                "start_time_s": float(point_a.get("timestamp_s", 0)),
                "end_time_s": float(point_b.get("timestamp_s", 0)),
                "bounds": build_swept_aabb(point_a, point_b, actuator["end_effector"], margin_mm),
                "approximation_type": "conservative_aabb",
                "margin_mm": float(margin_mm),
            }
        )
    return volumes
