from __future__ import annotations

import math
from typing import Any

from aicar_sim.obstacle_model import distance_point_to_aabb
from aicar_sim.path_interpolator import calculate_point_distance


METRIC_KEYS = (
    "trajectory_point_count", "source_segment_count", "transition_segment_count",
    "path_length_mm", "estimated_motion_duration_s", "maximum_velocity_mm_s",
    "maximum_resultant_acceleration_mm_s2", "maximum_x_acceleration_mm_s2",
    "maximum_y_acceleration_mm_s2", "maximum_z_acceleration_mm_s2",
    "minimum_vehicle_clearance_mm", "clearance_warning_count",
    "static_collision_count", "vehicle_collision_count", "forbidden_zone_entry_count",
    "task_count", "assigned_task_count", "unassigned_task_count",
    "synchronized_group_count", "blocked_sync_group_count",
    "conflict_count_before_resolution", "conflict_count_after_resolution",
    "total_schedule_duration_s", "total_delay_s", "safe_stop_point_count",
)


def percentage_change(before: Any, after: Any) -> float | None:
    if before is None or after is None:
        return None
    before_value = float(before)
    if abs(before_value) < 1e-12:
        return 0.0 if abs(float(after)) < 1e-12 else None
    return round((before_value - float(after)) / before_value * 100.0, 3)


def _maximum_axis_acceleration(points: list[dict[str, Any]], axis: str) -> float | None:
    if len(points) < 2:
        return None
    values = []
    for previous, current in zip(points, points[1:]):
        delta_time = float(current.get("delta_time_s", 0))
        if delta_time > 0:
            values.append(abs(float(current.get(f"velocity_{axis}_mm_s", 0)) - float(previous.get(f"velocity_{axis}_mm_s", 0))) / delta_time)
    return round(max(values), 6) if values else None


def calculate_path_metrics(
    machine_path_plan: dict[str, Any],
    collision_safety_plan: dict[str, Any] | None = None,
    schedule: dict[str, Any] | None = None,
    space_model_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    points = machine_path_plan.get("trajectory_points", [])
    summary = machine_path_plan.get("summary", {})
    collision_summary = (collision_safety_plan or {}).get("summary", {})
    schedule_summary = (schedule or {}).get("summary", {})
    vehicle_safe = (space_model_report or {}).get("vehicle_envelope", {}).get("safe_envelope")
    minimum_clearance = None
    if points and vehicle_safe:
        minimum_clearance = round(min(distance_point_to_aabb(point, vehicle_safe) for point in points), 6)
    path_length = round(sum(calculate_point_distance(a, b) for a, b in zip(points, points[1:])), 6) if points else None
    blocked = None
    if schedule is not None:
        blocked = len([item for item in schedule.get("sync_groups", []) if item.get("sync_status") == "BLOCKED_BY_INTERLOCK"])
    metrics = {
        "trajectory_point_count": len(points) if points else None,
        "source_segment_count": summary.get("source_segment_count"),
        "transition_segment_count": len([item for item in machine_path_plan.get("segments", []) if item.get("segment_type") == "transition"]) if machine_path_plan.get("segments") is not None else None,
        "path_length_mm": path_length,
        "estimated_motion_duration_s": round(float(points[-1]["timestamp_s"]), 6) if points and "timestamp_s" in points[-1] else summary.get("estimated_motion_duration_s"),
        "maximum_velocity_mm_s": round(max(abs(float(point.get("velocity_mm_s", 0))) for point in points), 6) if points else None,
        "maximum_resultant_acceleration_mm_s2": round(max(abs(float(point.get("acceleration_mm_s2", 0))) for point in points), 6) if points else None,
        "maximum_x_acceleration_mm_s2": _maximum_axis_acceleration(points, "x"),
        "maximum_y_acceleration_mm_s2": _maximum_axis_acceleration(points, "y"),
        "maximum_z_acceleration_mm_s2": _maximum_axis_acceleration(points, "z"),
        "minimum_vehicle_clearance_mm": minimum_clearance,
        "clearance_warning_count": (collision_safety_plan or {}).get("warning_category_counts", {}).get("vehicle_clearance") if collision_safety_plan is not None else None,
        "static_collision_count": collision_summary.get("static_collision_count"),
        "vehicle_collision_count": collision_summary.get("vehicle_collision_count"),
        "forbidden_zone_entry_count": collision_summary.get("forbidden_zone_entry_count"),
        "task_count": collision_summary.get("task_count", schedule_summary.get("task_count")),
        "assigned_task_count": collision_summary.get("assigned_task_count"),
        "unassigned_task_count": collision_summary.get("unassigned_task_count"),
        "synchronized_group_count": schedule_summary.get("synchronized_group_count"),
        "blocked_sync_group_count": blocked,
        "conflict_count_before_resolution": schedule_summary.get("conflict_count_before_resolution"),
        "conflict_count_after_resolution": schedule_summary.get("conflict_count_after_resolution"),
        "total_schedule_duration_s": schedule_summary.get("total_schedule_duration_s"),
        "total_delay_s": schedule_summary.get("total_delay_s"),
        "safe_stop_point_count": collision_summary.get("safe_stop_point_count"),
    }
    return {key: metrics.get(key) for key in METRIC_KEYS}


def compare_path_metrics(baseline_metrics: dict[str, Any], optimized_metrics: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for key in METRIC_KEYS:
        before = baseline_metrics.get(key)
        after = optimized_metrics.get(key)
        result[key] = {"baseline": before, "optimized": after, "improvement_percent": percentage_change(before, after)}
    return result
