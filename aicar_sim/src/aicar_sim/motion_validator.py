from __future__ import annotations

import math
from collections import Counter
from typing import Any

from aicar_sim.motion_model import (
    get_axis_acceleration_limits,
    get_axis_velocity_limits,
    get_workspace_bounds,
    is_point_inside_workspace,
)
from aicar_sim.path_interpolator import calculate_point_distance


VALIDATION_STATUSES = {"PASS", "PASS_WITH_WARNINGS", "FAIL"}


def _issue(
    check_id: str,
    severity: str,
    message: str,
    point: dict[str, Any] | None = None,
    point_index: int | None = None,
    measured_value: Any = None,
    limit_value: Any = None,
) -> dict[str, Any]:
    point = point or {}
    return {
        "check_id": check_id,
        "severity": severity,
        "message": message,
        "point_index": point_index,
        "segment_id": point.get("segment_id"),
        "state_id": point.get("state_id"),
        "zone_id": point.get("zone_id"),
        "measured_value": measured_value,
        "limit_value": limit_value,
    }


def _bay_bounds(space_model_report: dict[str, Any]) -> dict[str, float]:
    dimensions = space_model_report.get("wash_bay", {}).get("bay_dimensions", {})
    width = float(dimensions.get("width_mm", 0))
    length = float(dimensions.get("length_mm", 0))
    height = float(dimensions.get("height_mm", 0))
    if min(width, length, height) <= 0:
        raise ValueError("space model wash bay dimensions must be greater than 0")
    return {
        "x_min_mm": -width / 2,
        "x_max_mm": width / 2,
        "y_min_mm": -length / 2,
        "y_max_mm": length / 2,
        "z_min_mm": 0.0,
        "z_max_mm": height,
    }


def _inside_bounds(point: dict[str, Any], bounds: dict[str, float]) -> bool:
    return (
        bounds["x_min_mm"] <= float(point["x_mm"]) <= bounds["x_max_mm"]
        and bounds["y_min_mm"] <= float(point["y_mm"]) <= bounds["y_max_mm"]
        and bounds["z_min_mm"] <= float(point["z_mm"]) <= bounds["z_max_mm"]
    )


def _distance_to_box(point: dict[str, Any], bounds: dict[str, float]) -> float:
    x = float(point["x_mm"])
    y = float(point["y_mm"])
    z = float(point["z_mm"])
    dx = max(bounds["x_min_mm"] - x, 0.0, x - bounds["x_max_mm"])
    dy = max(bounds["y_min_mm"] - y, 0.0, y - bounds["y_max_mm"])
    dz = max(bounds["z_min_mm"] - z, 0.0, z - bounds["z_max_mm"])
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def _zone_reference_standoff(
    point: dict[str, Any],
    zone_bounds: dict[str, Any],
) -> float | None:
    zone_id = point.get("zone_id")
    x = float(point["x_mm"])
    y = float(point["y_mm"])
    z = float(point["z_mm"])
    if zone_id == "roof":
        return abs(z - float(zone_bounds["z_max_mm"]))
    if zone_id in {"left_side", "right_side"}:
        reference = float(zone_bounds["x_min_mm"] if zone_id == "left_side" else zone_bounds["x_max_mm"])
        return abs(x - reference)
    if zone_id in {"front", "rear"}:
        reference = float(zone_bounds["y_max_mm"] if zone_id == "front" else zone_bounds["y_min_mm"])
        return abs(y - reference)
    if zone_id == "wheels":
        return min(abs(x - float(zone_bounds["x_min_mm"])), abs(x - float(zone_bounds["x_max_mm"])))
    return None


def _summary_by(points: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    counts = Counter(str(point.get(key, "unknown")) for point in points)
    return [{key: name, "trajectory_point_count": count} for name, count in sorted(counts.items())]


def validate_machine_path(
    machine_path_plan: dict[str, Any],
    motion_model: dict[str, Any],
    space_model_report: dict[str, Any],
    nozzle_coverage_plan: dict[str, Any],
) -> dict[str, Any]:
    """Validate a machine-feasible candidate path against Stage4 constraints."""
    del nozzle_coverage_plan  # Reserved for nozzle-specific constraints in later Stage4 work.
    points = machine_path_plan.get("trajectory_points", [])
    if not points:
        raise ValueError("machine path plan has no trajectory_points")

    violations: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    workspace = get_workspace_bounds(motion_model)
    bay_bounds = _bay_bounds(space_model_report)
    safe = {
        key: float(value)
        for key, value in space_model_report.get("vehicle_envelope", {}).get("safe_envelope", {}).items()
    }
    if not safe:
        raise ValueError("space model missing vehicle safe_envelope")
    constraints = motion_model["path_constraints"]
    velocity_limits = get_axis_velocity_limits(motion_model)
    acceleration_limits = get_axis_acceleration_limits(motion_model)
    minimum_clearance = float(constraints["minimum_vehicle_clearance_mm"])
    preferred_standoff = float(constraints["preferred_nozzle_standoff_mm"])
    maximum_standoff = float(constraints["maximum_nozzle_standoff_mm"])
    maximum_gap = float(constraints["maximum_segment_gap_mm"])
    total_velocity_limit = math.sqrt(sum(value**2 for value in velocity_limits.values()))
    total_acceleration_limit = math.sqrt(sum(value**2 for value in acceleration_limits.values()))
    min_clearance_measured = math.inf
    max_gap_measured = 0.0
    max_axis_velocity = {axis: 0.0 for axis in ("x", "y", "z")}
    max_axis_acceleration = {axis: 0.0 for axis in ("x", "y", "z")}

    required_fields = ("state_id", "zone_id", "nozzle_id", "segment_id")
    previous: dict[str, Any] | None = None
    previous_axis_velocity = {axis: 0.0 for axis in ("x", "y", "z")}
    for index, point in enumerate(points):
        missing = [key for key in required_fields if not point.get(key)]
        if missing:
            violations.append(_issue("data_integrity", "violation", f"Missing required fields: {', '.join(missing)}", point, index))

        if not is_point_inside_workspace(point, motion_model):
            violations.append(_issue("workspace", "violation", "Point is outside the configured motion workspace.", point, index, {axis: point.get(f"{axis}_mm") for axis in ("x", "y", "z")}, workspace))
        if not _inside_bounds(point, bay_bounds):
            violations.append(_issue("wash_bay", "violation", "Point is outside the demo wash bay bounds.", point, index, {axis: point.get(f"{axis}_mm") for axis in ("x", "y", "z")}, bay_bounds))

        clearance = _distance_to_box(point, safe)
        min_clearance_measured = min(min_clearance_measured, clearance)
        if clearance + 1e-6 < minimum_clearance:
            violations.append(_issue("clearance", "violation", "Point is closer to the axis-aligned vehicle safe envelope than allowed.", point, index, round(clearance, 3), minimum_clearance))

        total_velocity = abs(float(point.get("velocity_mm_s", 0.0)))
        if total_velocity > total_velocity_limit + 1e-6:
            violations.append(_issue("velocity", "violation", "Total Cartesian velocity exceeds the derived vector limit.", point, index, total_velocity, total_velocity_limit))
        for axis in ("x", "y", "z"):
            measured = abs(float(point.get(f"velocity_{axis}_mm_s", 0.0)))
            max_axis_velocity[axis] = max(max_axis_velocity[axis], measured)
            if measured > velocity_limits[axis] + 1e-6:
                violations.append(_issue(f"velocity_{axis}", "violation", f"{axis}-axis velocity exceeds the configured limit.", point, index, measured, velocity_limits[axis]))

        delta_time = float(point.get("delta_time_s", 0.0))
        if delta_time <= 0:
            violations.append(_issue("timestamp", "violation", "delta_time_s must be greater than 0.", point, index, delta_time, "> 0"))
        if previous is not None:
            timestamp = float(point.get("timestamp_s", 0.0))
            previous_timestamp = float(previous.get("timestamp_s", 0.0))
            if timestamp <= previous_timestamp:
                violations.append(_issue("timestamp", "violation", "Timestamps must be strictly increasing.", point, index, timestamp, f"> {previous_timestamp}"))
            gap = calculate_point_distance(previous, point)
            max_gap_measured = max(max_gap_measured, gap)
            if gap > maximum_gap + 1e-6:
                violations.append(_issue("continuity", "violation", "Adjacent trajectory points exceed maximum_segment_gap_mm.", point, index, round(gap, 3), maximum_gap))

            if delta_time > 0:
                for axis in ("x", "y", "z"):
                    current_velocity = float(point.get(f"velocity_{axis}_mm_s", 0.0))
                    acceleration = abs((current_velocity - previous_axis_velocity[axis]) / delta_time)
                    max_axis_acceleration[axis] = max(max_axis_acceleration[axis], acceleration)
                    if acceleration > acceleration_limits[axis] + 1e-4:
                        violations.append(_issue(f"acceleration_{axis}", "violation", f"{axis}-axis acceleration exceeds the configured limit.", point, index, round(acceleration, 3), acceleration_limits[axis]))
                if float(point.get("acceleration_mm_s2", 0.0)) > total_acceleration_limit + 1e-4:
                    violations.append(_issue("acceleration", "violation", "Total Cartesian acceleration exceeds the derived vector limit.", point, index, point.get("acceleration_mm_s2"), round(total_acceleration_limit, 3)))

        previous_axis_velocity = {
            axis: float(point.get(f"velocity_{axis}_mm_s", 0.0)) for axis in ("x", "y", "z")
        }
        previous = point

    warnings.append(
        _issue(
            "clearance_model",
            "warning",
            "Vehicle clearance uses an axis-aligned safe-envelope approximation; no real CAD collision model is loaded.",
            measured_value=round(min_clearance_measured, 3),
            limit_value=minimum_clearance,
        )
    )
    warnings.append(
        _issue(
            "standoff_model",
            "warning",
            "Nozzle standoff uses zone reference surfaces and fixed zone normals; real body curvature and nozzle orientation are not modeled.",
            measured_value="approximate",
            limit_value=maximum_standoff,
        )
    )

    zone_map = {
        zone.get("zone_id"): zone.get("bounds", {})
        for zone in space_model_report.get("vehicle_envelope", {}).get("surface_zones", [])
    }
    checked_segments: set[str] = set()
    for index, point in enumerate(points):
        if point.get("is_transition"):
            continue
        segment_id = str(point.get("segment_id"))
        if segment_id in checked_segments:
            continue
        checked_segments.add(segment_id)
        bounds = zone_map.get(point.get("zone_id"))
        if not bounds:
            warnings.append(_issue("standoff", "warning", "No zone reference surface was available for standoff estimation.", point, index))
            continue
        standoff = _zone_reference_standoff(point, bounds)
        if standoff is None:
            warnings.append(_issue("standoff", "warning", "Zone standoff model is not defined for this point.", point, index))
        elif standoff > maximum_standoff + 1e-6:
            violations.append(_issue("standoff", "violation", "Approximate nozzle standoff exceeds the configured maximum.", point, index, round(standoff, 3), maximum_standoff))
        elif abs(standoff - preferred_standoff) > 100:
            warnings.append(_issue("standoff", "warning", "Approximate nozzle standoff differs from the preferred reference value.", point, index, round(standoff, 3), preferred_standoff))

    for warning in machine_path_plan.get("warnings", []):
        warnings.append(
            _issue(
                warning.get("check_id", "candidate_path"),
                "warning",
                warning.get("message", "Candidate path warning."),
                warning,
                measured_value=warning.get("measured_value"),
                limit_value=warning.get("limit_value"),
            )
        )

    status = "FAIL" if violations else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    summary = machine_path_plan.get("summary", {})
    metric_summary = {
        "workspace": {"passed": not any(item["check_id"] == "workspace" for item in violations), "bounds": workspace},
        "wash_bay": {"passed": not any(item["check_id"] == "wash_bay" for item in violations), "bounds": bay_bounds},
        "velocity": {"passed": not any(item["check_id"].startswith("velocity") for item in violations), "maximum_axis_velocity_mm_s": {axis: round(value, 3) for axis, value in max_axis_velocity.items()}, "axis_limits_mm_s": velocity_limits},
        "acceleration": {"passed": not any(item["check_id"].startswith("acceleration") for item in violations), "maximum_axis_acceleration_mm_s2": {axis: round(value, 3) for axis, value in max_axis_acceleration.items()}, "axis_limits_mm_s2": acceleration_limits},
        "clearance": {"passed": not any(item["check_id"] == "clearance" for item in violations), "minimum_measured_mm": round(min_clearance_measured, 3), "minimum_required_mm": minimum_clearance, "model": "axis_aligned_safe_envelope_approximation"},
        "continuity": {"passed": not any(item["check_id"] == "continuity" for item in violations), "maximum_adjacent_gap_mm": round(max_gap_measured, 3), "limit_mm": maximum_gap},
        "timestamp": {"passed": not any(item["check_id"] == "timestamp" for item in violations), "strictly_monotonic_required": True},
        "standoff": {"passed": not any(item["check_id"] == "standoff" for item in violations), "preferred_mm": preferred_standoff, "maximum_mm": maximum_standoff, "model": "zone_reference_surface_approximation"},
    }
    return {
        "report_version": "stage4.2",
        "validation_status": status,
        "motion_model_id": motion_model["motion_model_id"],
        "vehicle_type": machine_path_plan.get("vehicle_type", "unknown"),
        "wash_profile": machine_path_plan.get("wash_profile", "unknown"),
        "summary": {
            "trajectory_point_count": len(points),
            "path_length_mm": summary.get("path_length_mm"),
            "estimated_motion_duration_s": summary.get("estimated_motion_duration_s"),
            "violation_count": len(violations),
            "warning_count": len(warnings),
        },
        "violation_count": len(violations),
        "warning_count": len(warnings),
        "violations": violations,
        "warnings": warnings,
        "metric_summary": metric_summary,
        "zone_summary": _summary_by(points, "zone_id"),
        "state_summary": _summary_by(points, "state_id"),
        "limitations": [
            "This report validates a machine-feasible candidate path only.",
            "The motion model is a generic Cartesian reference model.",
            "No real actuator parameters, dynamics, CAD collision geometry, PLC, or hardware are used.",
            "The candidate path cannot be sent directly to a PLC, servo drive, or robot controller.",
        ],
    }
