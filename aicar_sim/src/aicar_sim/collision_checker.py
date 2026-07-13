from __future__ import annotations

from typing import Any

from aicar_sim.motion_model import is_point_inside_workspace
from aicar_sim.obstacle_model import (
    aabb_intersects,
    distance_point_to_aabb,
    point_inside_aabb,
)


def check_actuator_home_positions(
    actuator_system: dict[str, Any],
    motion_model: dict[str, Any],
    static_obstacles: list[dict[str, Any]],
    vehicle_forbidden_bounds: dict[str, Any],
) -> list[dict[str, Any]]:
    issues = []
    for actuator in actuator_system.get("actuators", []):
        actuator_id = actuator["actuator_id"]
        point = actuator["home_position"]
        reasons = []
        if not is_point_inside_workspace(point, motion_model):
            reasons.append("outside motion workspace")
        if any(point_inside_aabb(point, obstacle["bounds"]) for obstacle in static_obstacles):
            reasons.append("inside static obstacle")
        if point_inside_aabb(point, vehicle_forbidden_bounds):
            reasons.append("inside vehicle forbidden envelope")
        if reasons:
            issues.append(
                _result(
                    "actuator_home_position",
                    "CRITICAL",
                    "Actuator home position is invalid: " + ", ".join(reasons) + ".",
                    point,
                    actuator_id,
                )
            )
    return issues


def check_safe_stop_points(points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "safe_stop",
            "severity": "CRITICAL",
            "message": "Selected safe-stop point failed validation.",
            "actuator_id": item.get("actuator_id"),
            "safe_stop_id": item.get("safe_stop_id"),
        }
        for item in points
        if item.get("validation_status") != "PASS"
    ]


def _result(
    check_id: str,
    severity: str,
    message: str,
    point: dict[str, Any] | None = None,
    actuator_id: str | None = None,
    obstacle_id: str | None = None,
    measured_value: Any = None,
    limit_value: Any = None,
) -> dict[str, Any]:
    point = point or {}
    return {
        "check_id": check_id,
        "severity": severity,
        "message": message,
        "actuator_id": actuator_id,
        "point_index": point.get("sequence_index"),
        "segment_id": point.get("segment_id"),
        "state_id": point.get("state_id"),
        "zone_id": point.get("zone_id"),
        "obstacle_id": obstacle_id,
        "measured_value": measured_value,
        "limit_value": limit_value,
        "time_s": point.get("timestamp_s"),
    }


def check_static_obstacle_collisions(
    points: list[dict[str, Any]],
    static_obstacles: list[dict[str, Any]],
    actuator_id: str,
) -> list[dict[str, Any]]:
    issues = []
    for point in points:
        for obstacle in static_obstacles:
            if point_inside_aabb(point, obstacle["bounds"]):
                issues.append(_result("static_obstacle_point", "CRITICAL", "Trajectory point enters a static obstacle.", point, actuator_id, obstacle["obstacle_id"]))
    return issues


def check_swept_volume_collisions(
    swept_volumes: list[dict[str, Any]],
    static_obstacles: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    issues = []
    for volume in swept_volumes:
        for obstacle in static_obstacles:
            if aabb_intersects(volume["bounds"], obstacle["bounds"]):
                issues.append(
                    {
                        "check_id": "swept_static_obstacle",
                        "severity": "CRITICAL",
                        "message": "Conservative swept AABB intersects a static obstacle.",
                        "actuator_id": volume["actuator_id"],
                        "point_index": volume["end_point_index"],
                        "segment_id": volume["segment_id"],
                        "state_id": volume["state_id"],
                        "zone_id": volume["zone_id"],
                        "obstacle_id": obstacle["obstacle_id"],
                        "measured_value": "AABB intersection",
                        "limit_value": "no intersection",
                        "time_s": volume["end_time_s"],
                    }
                )
    return issues


def check_vehicle_swept_collisions(
    swept_volumes: list[dict[str, Any]],
    vehicle_safe_envelope: dict[str, Any],
) -> list[dict[str, Any]]:
    issues = []
    for volume in swept_volumes:
        if aabb_intersects(volume["bounds"], vehicle_safe_envelope):
            issues.append(
                {
                    "check_id": "swept_vehicle_envelope",
                    "severity": "CRITICAL",
                    "message": "Conservative actuator swept AABB intersects the vehicle safe envelope.",
                    "actuator_id": volume["actuator_id"],
                    "point_index": volume["end_point_index"],
                    "segment_id": volume["segment_id"],
                    "state_id": volume["state_id"],
                    "zone_id": volume["zone_id"],
                    "obstacle_id": "vehicle_safe_envelope",
                    "measured_value": "AABB intersection",
                    "limit_value": "no intersection",
                    "time_s": volume["end_time_s"],
                }
            )
    return issues


def check_vehicle_clearance(
    points: list[dict[str, Any]],
    vehicle_safe_envelope: dict[str, Any],
    clearance_policy: dict[str, Any],
    actuator_id: str,
) -> list[dict[str, Any]]:
    hard = float(clearance_policy["hard_minimum_mm"])
    warning = float(clearance_policy["warning_threshold_mm"])
    recommended = float(clearance_policy["recommended_mm"])
    issues = []
    for point in points:
        distance = distance_point_to_aabb(point, vehicle_safe_envelope)
        if distance < hard - 1e-6:
            issues.append(_result("vehicle_clearance", "CRITICAL", "Vehicle clearance is below the hard minimum.", point, actuator_id, measured_value=round(distance, 3), limit_value=hard))
        elif distance < warning - 1e-6:
            issue = _result("vehicle_clearance", "WARNING", "Vehicle clearance is in the critical warning band.", point, actuator_id, measured_value=round(distance, 3), limit_value=warning)
            issue["warning_level"] = "critical"
            issues.append(issue)
        elif distance < recommended - 1e-6:
            issues.append(_result("vehicle_clearance", "WARNING", "Vehicle clearance is below the recommended value.", point, actuator_id, measured_value=round(distance, 3), limit_value=recommended))
    return issues


def check_forbidden_zone_entry(
    points: list[dict[str, Any]],
    actuator_id: str,
) -> list[dict[str, Any]]:
    return [
        _result("forbidden_zone", "CRITICAL", "Trajectory point enters a forbidden safety zone.", point, actuator_id)
        for point in points
        if point.get("forbidden")
    ]


def check_safety_speed_policy(
    points: list[dict[str, Any]],
    actuator_id: str,
) -> list[dict[str, Any]]:
    issues = []
    for point in points:
        scale = float(point.get("speed_scale", 1.0))
        original = float(point.get("velocity_mm_s", 0.0))
        adjusted = float(point.get("adjusted_velocity_mm_s", original))
        if adjusted > original * scale + 1e-6:
            issues.append(_result("safety_speed_policy", "CRITICAL", "Adjusted velocity does not respect the safety-zone speed scale.", point, actuator_id, measured_value=adjusted, limit_value=original * scale))
    return issues
