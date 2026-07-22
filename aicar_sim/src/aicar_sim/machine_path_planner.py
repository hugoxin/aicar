from __future__ import annotations

import math
from typing import Any

from aicar_sim.motion_model import get_axis_velocity_limits, get_workspace_bounds
from aicar_sim.path_interpolator import calculate_point_distance, interpolate_segment
from aicar_sim.trajectory_timing import parameterize_trajectory


def _vehicle_safe_envelope(space_model_report: dict[str, Any]) -> dict[str, float]:
    envelope = space_model_report.get("vehicle_envelope", {}).get("safe_envelope", {})
    required = (
        "x_min_mm",
        "x_max_mm",
        "y_min_mm",
        "y_max_mm",
        "z_min_mm",
        "z_max_mm",
    )
    missing = [key for key in required if key not in envelope]
    if missing:
        raise ValueError(f"space model safe envelope missing fields: {', '.join(missing)}")
    return {key: float(envelope[key]) for key in required}


def _candidate_point(
    source: dict[str, Any],
    segment: dict[str, Any],
    safe: dict[str, float],
    workspace: dict[str, float],
    clearance: float,
    source_index: int,
) -> dict[str, Any]:
    zone_id = str(segment["zone_id"])
    x = float(source["x_mm"])
    y = float(source["y_mm"])
    z = float(source["z_mm"])
    if zone_id == "roof":
        z = safe["z_max_mm"] + clearance
    elif zone_id == "left_side":
        x = safe["x_min_mm"] - clearance
    elif zone_id == "right_side":
        x = safe["x_max_mm"] + clearance
    elif zone_id == "front":
        y = safe["y_max_mm"] + clearance
    elif zone_id == "rear":
        y = safe["y_min_mm"] - clearance
    elif zone_id == "wheels":
        x = safe["x_min_mm"] - clearance if x < 0 else safe["x_max_mm"] + clearance

    x = min(max(x, workspace["x_min_mm"]), workspace["x_max_mm"])
    y = min(max(y, workspace["y_min_mm"]), workspace["y_max_mm"])
    z = min(max(z, workspace["z_min_mm"]), workspace["z_max_mm"])
    return {
        "x_mm": round(x, 6),
        "y_mm": round(y, 6),
        "z_mm": round(z, 6),
        "segment_id": segment["segment_id"],
        "state_id": segment["state_id"],
        "zone_id": segment["zone_id"],
        "nozzle_id": segment["nozzle_id"],
        "source_point_index": source_index,
        "interpolated": False,
        "is_transition": False,
        "target_speed_mm_s": float(source.get("speed_mm_s", 200.0)),
    }


def _deduplicate_waypoints(points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for point in points:
        if result and calculate_point_distance(result[-1], point) < 1e-9:
            continue
        result.append(point)
    return result


def _expand_internal_safe_transitions(
    points: list[dict[str, Any]],
    zone_id: str,
    safe: dict[str, float],
    clearance: float,
    transition_speed: float,
) -> list[dict[str, Any]]:
    """Route wheel-side changes above the safe envelope instead of through it."""
    if zone_id != "wheels" or len(points) < 2:
        return points
    safe_z = safe["z_max_mm"] + clearance
    expanded = [dict(points[0])]
    for target in points[1:]:
        previous = expanded[-1]
        crosses_vehicle = float(previous["x_mm"]) * float(target["x_mm"]) < 0
        if crosses_vehicle:
            lift = dict(previous)
            lift.update(
                {
                    "z_mm": max(float(previous["z_mm"]), safe_z),
                    "is_transition": True,
                    "target_speed_mm_s": transition_speed,
                }
            )
            overhead = dict(target)
            overhead.update(
                {
                    "z_mm": max(float(target["z_mm"]), safe_z),
                    "is_transition": True,
                    "target_speed_mm_s": transition_speed,
                }
            )
            expanded.extend([lift, overhead])
        expanded.append(dict(target))
    return _deduplicate_waypoints(expanded)


def _transition_segment(
    previous_segment: dict[str, Any],
    next_segment: dict[str, Any],
    safe: dict[str, float],
    clearance: float,
    max_spacing_mm: float,
    transition_speed: float,
    index: int,
) -> dict[str, Any]:
    start = dict(previous_segment["points"][-1])
    end = dict(next_segment["points"][0])
    transition_id = f"transition_{index:03d}_{previous_segment['segment_id']}_to_{next_segment['segment_id']}"
    safe_z = safe["z_max_mm"] + clearance

    def transition_point(x: float, y: float, z: float) -> dict[str, Any]:
        return {
            "x_mm": x,
            "y_mm": y,
            "z_mm": z,
            "segment_id": transition_id,
            "state_id": next_segment["state_id"],
            "zone_id": next_segment["zone_id"],
            "nozzle_id": next_segment["nozzle_id"],
            "source_point_index": 0,
            "interpolated": False,
            "is_transition": True,
            "target_speed_mm_s": transition_speed,
        }

    waypoints = _deduplicate_waypoints(
        [
            transition_point(float(start["x_mm"]), float(start["y_mm"]), float(start["z_mm"])),
            transition_point(float(start["x_mm"]), float(start["y_mm"]), max(float(start["z_mm"]), safe_z)),
            transition_point(float(end["x_mm"]), float(end["y_mm"]), max(float(end["z_mm"]), safe_z)),
            transition_point(float(end["x_mm"]), float(end["y_mm"]), float(end["z_mm"])),
        ]
    )
    points = interpolate_segment(waypoints, max_spacing_mm)
    for point in points:
        point["segment_id"] = transition_id
        point["state_id"] = next_segment["state_id"]
        point["zone_id"] = next_segment["zone_id"]
        point["nozzle_id"] = next_segment["nozzle_id"]
        point["is_transition"] = True
        point["target_speed_mm_s"] = transition_speed
    return {
        "segment_id": transition_id,
        "state_id": next_segment["state_id"],
        "zone_id": next_segment["zone_id"],
        "nozzle_id": next_segment["nozzle_id"],
        "segment_type": "transition",
        "requires_transition": True,
        "points": points,
    }


def _path_length(points: list[dict[str, Any]]) -> float:
    return sum(calculate_point_distance(a, b) for a, b in zip(points, points[1:]))


def build_machine_feasible_path_plan(
    abstract_nozzle_path_plan: dict[str, Any],
    space_model_report: dict[str, Any],
    nozzle_coverage_plan: dict[str, Any],
    motion_model: dict[str, Any],
) -> dict[str, Any]:
    """Convert Stage2 abstract paths into a constrained candidate trajectory."""
    del nozzle_coverage_plan  # Reserved for nozzle-specific limits in later Stage4 work.
    source_segments = abstract_nozzle_path_plan.get("path_segments", [])
    if not source_segments:
        raise ValueError("abstract nozzle path plan has no path_segments")

    constraints = motion_model["path_constraints"]
    clearance = float(constraints["minimum_vehicle_clearance_mm"])
    max_gap = float(constraints["maximum_segment_gap_mm"])
    velocity_limits = get_axis_velocity_limits(motion_model)
    workspace = get_workspace_bounds(motion_model)
    safe = _vehicle_safe_envelope(space_model_report)
    max_spacing_mm = max(
        100.0,
        min(250.0, min(velocity_limits.values()) * float(constraints["sampling_interval_s"]) * 4.0),
    )
    transition_speed = min(velocity_limits.values()) * float(constraints["transition_velocity_scale"])
    warnings: list[dict[str, Any]] = []

    machine_segments: list[dict[str, Any]] = []
    normalized_segments: list[dict[str, Any]] = []
    for segment in source_segments:
        normalized_points = [
            _candidate_point(point, segment, safe, workspace, clearance, index)
            for index, point in enumerate(segment.get("points", []))
        ]
        normalized_points = _expand_internal_safe_transitions(
            normalized_points,
            str(segment["zone_id"]),
            safe,
            clearance,
            transition_speed,
        )
        points = interpolate_segment(normalized_points, max_spacing_mm)
        for point in points:
            point["segment_id"] = segment["segment_id"]
            point["state_id"] = segment["state_id"]
            point["zone_id"] = segment["zone_id"]
            point["nozzle_id"] = segment["nozzle_id"]
            point.setdefault("is_transition", False)
        normalized_segments.append(
            {
                "segment_id": segment["segment_id"],
                "state_id": segment["state_id"],
                "zone_id": segment["zone_id"],
                "nozzle_id": segment["nozzle_id"],
                "segment_type": "process",
                "requires_transition": False,
                "source_point_count": len(segment.get("points", [])),
                "points": points,
            }
        )

    for index, segment in enumerate(normalized_segments):
        if machine_segments:
            previous = machine_segments[-1]
            source_gap = calculate_point_distance(previous["points"][-1], segment["points"][0])
            if source_gap > max_gap:
                warnings.append(
                    {
                        "check_id": "source_segment_gap",
                        "severity": "warning",
                        "message": "Source segment gap exceeded the configured limit; an overhead transition was inserted.",
                        "segment_id": segment["segment_id"],
                        "state_id": segment["state_id"],
                        "zone_id": segment["zone_id"],
                        "measured_value": round(source_gap, 3),
                        "limit_value": max_gap,
                    }
                )
            machine_segments.append(
                _transition_segment(
                    previous,
                    segment,
                    safe,
                    clearance,
                    max_spacing_mm,
                    transition_speed,
                    index,
                )
            )
        machine_segments.append(segment)

    flat_points: list[dict[str, Any]] = []
    segment_summaries: list[dict[str, Any]] = []
    for segment in machine_segments:
        start_index = len(flat_points)
        flat_points.extend(dict(point) for point in segment["points"])
        segment_summaries.append(
            {
                "segment_id": segment["segment_id"],
                "state_id": segment["state_id"],
                "zone_id": segment["zone_id"],
                "nozzle_id": segment["nozzle_id"],
                "segment_type": segment["segment_type"],
                "requires_transition": segment["requires_transition"],
                "point_start_index": start_index,
                "point_end_index": len(flat_points) - 1,
                "point_count": len(segment["points"]),
            }
        )

    if len(flat_points) > 5000:
        raise ValueError(f"candidate trajectory exceeds 5000 points: {len(flat_points)}")
    trajectory_points = parameterize_trajectory(flat_points, motion_model)
    if segment_summaries:
        segment_summaries[-1]["point_end_index"] = len(trajectory_points) - 1
        segment_summaries[-1]["point_count"] += 1

    vehicle = abstract_nozzle_path_plan.get("vehicle", space_model_report.get("vehicle", {}))
    source_summary = abstract_nozzle_path_plan.get("summary", {})
    path_length = _path_length(trajectory_points)
    maximum_velocity = max(float(point["velocity_mm_s"]) for point in trajectory_points)
    maximum_acceleration = max(float(point["acceleration_mm_s2"]) for point in trajectory_points)
    return {
        "plan_version": "stage4.2",
        "motion_model_id": motion_model["motion_model_id"],
        "vehicle_type": vehicle.get("vehicle_type", "unknown"),
        "wash_profile": abstract_nozzle_path_plan.get("wash_profile", vehicle.get("wash_profile", "unknown")),
        "coordinate_system": {
            **motion_model["coordinate_system"],
            "source_assumption": "Stage2 vehicle_center_floor is aligned with wash_bay_center_floor for this demo.",
        },
        "summary": {
            "source_segment_count": int(source_summary.get("segment_count", len(source_segments))),
            "source_point_count": int(source_summary.get("point_count", sum(len(item.get("points", [])) for item in source_segments))),
            "trajectory_point_count": len(trajectory_points),
            "transition_segment_count": len([item for item in segment_summaries if item["segment_type"] == "transition"]),
            "estimated_motion_duration_s": round(float(trajectory_points[-1]["timestamp_s"]), 3),
            "path_length_mm": round(path_length, 3),
            "maximum_velocity_mm_s": round(maximum_velocity, 3),
            "maximum_acceleration_mm_s2": round(maximum_acceleration, 3),
            "interpolation_spacing_mm": round(max_spacing_mm, 3),
            "warning_count": len(warnings),
        },
        "trajectory_points": trajectory_points,
        "segments": segment_summaries,
        "source_path_segments": source_segments,
        "warnings": warnings,
        "limitations": [
            "Machine-feasible candidate path only; not a validated real-machine trajectory.",
            "Generic Cartesian gantry parameters are used.",
            "Vehicle clearance and nozzle standoff use axis-aligned reference surfaces.",
            "No actuator dynamics, inverse kinematics, PLC output, or hardware control is included.",
        ],
    }


def build_prepositioned_machine_path_plan(
    path_segments: list[dict[str, Any]],
    motion_model: dict[str, Any],
    *,
    vehicle_type: str,
    wash_profile: str,
    source_summary: dict[str, Any],
) -> dict[str, Any]:
    """Time-parameterize Stage4.5 waypoints that already include safety offsets."""
    if not path_segments:
        raise ValueError("prepositioned machine path requires path_segments")
    constraints = motion_model["path_constraints"]
    maximum_spacing = min(140.0, float(constraints["maximum_segment_gap_mm"]))
    velocity_limits = get_axis_velocity_limits(motion_model)
    transition_speed = min(velocity_limits.values()) * float(constraints["transition_velocity_scale"])
    machine_segments: list[dict[str, Any]] = []
    flat_points: list[dict[str, Any]] = []

    for source_segment in path_segments:
        segment_type = str(source_segment.get("segment_type", "process"))
        normalized = []
        for source_index, point in enumerate(source_segment.get("points", [])):
            machine = point.get("machine_point")
            if not machine:
                raise ValueError(f"segment {source_segment.get('segment_id')} point missing machine_point")
            item = dict(point)
            item.update(
                {
                    "x_mm": float(machine["x_mm"]),
                    "y_mm": float(machine["y_mm"]),
                    "z_mm": float(machine["z_mm"]),
                    "segment_id": source_segment["segment_id"],
                    "state_id": source_segment["state_id"],
                    "zone_id": source_segment["zone_id"],
                    "nozzle_id": source_segment["nozzle_id"],
                    "source_point_index": source_index,
                    "is_transition": segment_type != "process" or point.get("critical_point_type") in {"PATCH_CONNECTION", "STATE_BOUNDARY"},
                    "target_speed_mm_s": transition_speed if segment_type != "process" else float(point.get("target_speed_mm_s", 200.0)),
                }
            )
            normalized.append(item)
        points = interpolate_segment(_deduplicate_waypoints(normalized), maximum_spacing)
        if flat_points and points and calculate_point_distance(flat_points[-1], points[0]) < 1e-9:
            points = points[1:]
        start_index = len(flat_points)
        flat_points.extend(points)
        machine_segments.append(
            {
                "segment_id": source_segment["segment_id"],
                "state_id": source_segment["state_id"],
                "zone_id": source_segment["zone_id"],
                "nozzle_id": source_segment["nozzle_id"],
                "segment_type": segment_type,
                "requires_transition": segment_type == "transition",
                "point_start_index": start_index,
                "point_end_index": len(flat_points) - 1,
                "point_count": len(points),
                "source_point_count": len(source_segment.get("points", [])),
            }
        )

    if len(flat_points) >= 5000:
        raise ValueError(f"continuous machine trajectory exceeds limit before stop point: {len(flat_points)}")
    trajectory_points = parameterize_trajectory(flat_points, motion_model)
    if machine_segments:
        machine_segments[-1]["point_end_index"] = len(trajectory_points) - 1
        machine_segments[-1]["point_count"] += 1
    path_length = _path_length(trajectory_points)
    return {
        "plan_version": "stage4.5",
        "motion_model_id": motion_model["motion_model_id"],
        "vehicle_type": vehicle_type,
        "wash_profile": wash_profile,
        "coordinate_system": {
            **motion_model["coordinate_system"],
            "source_assumption": "Reference analytic vehicle surface is aligned with wash_bay_center_floor.",
        },
        "summary": {
            "source_segment_count": len([item for item in machine_segments if item["segment_type"] == "process"]),
            "source_point_count": int(source_summary.get("trajectory_point_count", len(flat_points))),
            "trajectory_point_count": len(trajectory_points),
            "transition_segment_count": len([item for item in machine_segments if item["segment_type"] == "transition"]),
            "estimated_motion_duration_s": round(float(trajectory_points[-1]["timestamp_s"]), 3),
            "path_length_mm": round(path_length, 3),
            "maximum_velocity_mm_s": round(max(float(point["velocity_mm_s"]) for point in trajectory_points), 3),
            "maximum_acceleration_mm_s2": round(max(float(point["acceleration_mm_s2"]) for point in trajectory_points), 3),
            "interpolation_spacing_mm": maximum_spacing,
            "warning_count": 0,
        },
        "trajectory_points": trajectory_points,
        "segments": machine_segments,
        "source_path_segments": path_segments,
        "warnings": [],
        "limitations": [
            "Continuous-surface machine candidate only; not a real-machine trajectory.",
            "Safety offsets are based on analytic surface normals and an axis-aligned vehicle envelope.",
            "No actuator dynamics, calibrated kinematics, PLC output, servo command, or hardware control is included.",
        ],
    }
