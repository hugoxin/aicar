from __future__ import annotations

from typing import Any

from aicar_sim.motion_model import is_point_inside_workspace
from aicar_sim.obstacle_model import distance_point_to_aabb, point_inside_aabb


def evaluate_clearance(points: list[dict[str, Any]], vehicle_safe_envelope: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    distances = [distance_point_to_aabb(point, vehicle_safe_envelope) for point in points]
    hard = float(policy["hard_minimum_mm"])
    warning = float(policy["warning_threshold_mm"])
    recommended = float(policy["recommended_mm"])
    return {
        "minimum_clearance_mm": round(min(distances), 6) if distances else None,
        "hard_violation_count": len([value for value in distances if value < hard - 1e-6]),
        "critical_warning_count": len([value for value in distances if hard - 1e-6 <= value < warning - 1e-6]),
        "warning_count": len([value for value in distances if warning - 1e-6 <= value < recommended - 1e-6]),
    }


def validate_clearance_candidate(
    baseline_points: list[dict[str, Any]],
    candidate_points: list[dict[str, Any]],
    vehicle_safe_envelope: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    baseline = evaluate_clearance(baseline_points, vehicle_safe_envelope, policy)
    candidate = evaluate_clearance(candidate_points, vehicle_safe_envelope, policy)
    accepted = candidate["hard_violation_count"] == 0
    if policy.get("reject_if_minimum_clearance_decreases") and candidate["minimum_clearance_mm"] + 1e-6 < baseline["minimum_clearance_mm"]:
        accepted = False
    baseline_warning = baseline["critical_warning_count"] + baseline["warning_count"]
    candidate_warning = candidate["critical_warning_count"] + candidate["warning_count"]
    if policy.get("reject_if_clearance_warning_count_increases") and candidate_warning > baseline_warning:
        accepted = False
    return {"accepted": accepted, "baseline": baseline, "candidate": candidate, "rejection_reason": None if accepted else "vehicle clearance regressed"}


def adjust_point_toward_safety(
    point: dict[str, Any],
    adjustment_vector: dict[str, float],
    motion_model: dict[str, Any],
    static_obstacles: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate = dict(point)
    for axis in ("x", "y", "z"):
        candidate[f"{axis}_mm"] = float(point[f"{axis}_mm"]) + float(adjustment_vector.get(f"{axis}_mm", 0))
    valid = is_point_inside_workspace(candidate, motion_model) and not any(point_inside_aabb(candidate, obstacle["bounds"]) for obstacle in static_obstacles)
    return {
        "baseline_clearance_mm": None,
        "optimized_clearance_mm": None,
        "adjustment_vector": adjustment_vector,
        "adjustment_status": "APPLIED" if valid else "REJECTED",
        "rejection_reason": None if valid else "adjusted point leaves workspace or enters obstacle",
        "point": candidate if valid else dict(point),
    }
