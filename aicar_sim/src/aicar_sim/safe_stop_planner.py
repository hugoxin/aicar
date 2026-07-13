from __future__ import annotations

from typing import Any

from aicar_sim.motion_model import is_point_inside_workspace
from aicar_sim.obstacle_model import point_inside_aabb
from aicar_sim.safety_zone import classify_point_safety_zones


def _zone_candidate(zone: dict[str, Any], actuator_id: str) -> dict[str, float]:
    bounds = zone["bounds"]
    x_min, x_max = float(bounds["x_min_mm"]), float(bounds["x_max_mm"])
    if actuator_id.startswith("left"):
        x = x_min + (x_max - x_min) * 0.25
    elif actuator_id.startswith("right"):
        x = x_max - (x_max - x_min) * 0.25
    else:
        x = (x_min + x_max) / 2
    return {
        "x_mm": x,
        "y_mm": (float(bounds["y_min_mm"]) + float(bounds["y_max_mm"])) / 2,
        "z_mm": (float(bounds["z_min_mm"]) + float(bounds["z_max_mm"])) / 2,
    }


def generate_safe_stop_candidates(
    actuator: dict[str, Any],
    safety_layout: dict[str, Any],
) -> list[dict[str, Any]]:
    candidates = [
        {
            "point": dict(actuator["home_position"]),
            "source_type": "home_position",
            "source_zone_id": None,
        }
    ]
    preferred_prefix = "top" if actuator["actuator_id"].startswith("top") else ("left" if actuator["actuator_id"].startswith("left") else "right")
    zones = [zone for zone in safety_layout.get("safety_zones", []) if zone.get("zone_type") == "safe_stop"]
    zones.sort(key=lambda zone: 0 if str(zone.get("zone_id", "")).startswith(preferred_prefix) else 1)
    for zone in zones:
        candidates.append(
            {
                "point": _zone_candidate(zone, actuator["actuator_id"]),
                "source_type": "configured_safe_stop_zone",
                "source_zone_id": zone["zone_id"],
            }
        )
    return candidates


def validate_safe_stop_point(
    candidate: dict[str, Any],
    actuator: dict[str, Any],
    motion_model: dict[str, Any],
    safety_layout: dict[str, Any],
    vehicle_forbidden_bounds: dict[str, Any],
) -> dict[str, Any]:
    point = candidate["point"]
    inside_workspace = is_point_inside_workspace(point, motion_model)
    outside_obstacles = not any(point_inside_aabb(point, item["bounds"]) for item in safety_layout.get("static_obstacles", []))
    outside_vehicle = not point_inside_aabb(point, vehicle_forbidden_bounds)
    zones = classify_point_safety_zones(point, safety_layout)
    inside_safe_stop = any(zone.get("zone_type") == "safe_stop" for zone in zones)
    warnings = []
    if not inside_safe_stop:
        warnings.append("Point is valid as a home/wait point but is not inside a configured safe-stop zone.")
    passed = inside_workspace and outside_obstacles and outside_vehicle
    return {
        "safe_stop_id": f"{actuator['actuator_id']}_{candidate['source_type']}_{candidate.get('source_zone_id') or 'home'}",
        "actuator_id": actuator["actuator_id"],
        "point": point,
        "source_type": candidate["source_type"],
        "related_state_id": None,
        "related_task_id": None,
        "timestamp_s": 0.0,
        "inside_workspace": inside_workspace,
        "outside_static_obstacles": outside_obstacles,
        "outside_vehicle_forbidden_zone": outside_vehicle,
        "inside_safe_stop_zone": inside_safe_stop,
        "reachable_from_previous_point": inside_workspace,
        "validation_status": "PASS" if passed else "FAIL",
        "warnings": warnings,
    }


def select_safe_stop_points(
    actuator_system: dict[str, Any],
    motion_model: dict[str, Any],
    safety_layout: dict[str, Any],
    vehicle_forbidden_bounds: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected = []
    violations = []
    for actuator in actuator_system.get("actuators", []):
        validated = [
            validate_safe_stop_point(candidate, actuator, motion_model, safety_layout, vehicle_forbidden_bounds)
            for candidate in generate_safe_stop_candidates(actuator, safety_layout)
        ]
        preferred = next((item for item in validated if item["validation_status"] == "PASS" and item["inside_safe_stop_zone"]), None)
        chosen = preferred or next((item for item in validated if item["validation_status"] == "PASS"), None)
        if chosen:
            selected.append(chosen)
        else:
            violations.append(
                {
                    "check_id": "safe_stop",
                    "severity": "CRITICAL",
                    "message": "No valid safe-stop point is available for the actuator.",
                    "actuator_id": actuator["actuator_id"],
                }
            )
    return selected, violations
