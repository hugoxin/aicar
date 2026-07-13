from __future__ import annotations

from typing import Any

from aicar_sim.clearance_aware_optimizer import validate_clearance_candidate
from aicar_sim.collision_checker import (
    check_forbidden_zone_entry,
    check_static_obstacle_collisions,
    check_swept_volume_collisions,
    check_vehicle_clearance,
    check_vehicle_swept_collisions,
)
from aicar_sim.motion_model import get_workspace_bounds
from aicar_sim.path_interpolator import calculate_point_distance, interpolate_segment
from aicar_sim.safety_zone import apply_safety_zone_annotations, resolve_dynamic_safety_zones
from aicar_sim.swept_volume import build_trajectory_swept_volumes


def _length(points: list[dict[str, Any]]) -> float:
    return sum(calculate_point_distance(a, b) for a, b in zip(points, points[1:]))


def _duration(points: list[dict[str, Any]]) -> float:
    if len(points) < 2:
        return 0.0
    return max(0.0, float(points[-1].get("timestamp_s", 0)) - float(points[0].get("timestamp_s", 0)))


def _metadata_point(source: dict[str, Any], x: float, y: float, z: float) -> dict[str, Any]:
    point = dict(source)
    point.update({"x_mm": x, "y_mm": y, "z_mm": z, "is_transition": True, "interpolated": False})
    return point


def classify_transition(
    previous_segment: dict[str, Any] | None,
    transition_segment: dict[str, Any],
    next_segment: dict[str, Any] | None,
    previous_actuator_id: str | None = None,
    next_actuator_id: str | None = None,
) -> str:
    if previous_segment and next_segment and previous_segment.get("state_id") != next_segment.get("state_id"):
        return "STATE_BOUNDARY_TRANSITION"
    if previous_actuator_id and next_actuator_id and previous_actuator_id != next_actuator_id:
        return "ACTUATOR_CHANGE_TRANSITION"
    if transition_segment.get("requires_interlock"):
        return "SHARED_SPACE_TRANSITION"
    if previous_segment and next_segment and previous_segment.get("zone_id") == next_segment.get("zone_id") and previous_segment.get("nozzle_id") == next_segment.get("nozzle_id"):
        return "MERGEABLE_TRANSITION"
    return "DIRECT_CONNECTION_ALLOWED"


def build_direct_transition_candidate(points: list[dict[str, Any]], maximum_spacing_mm: float) -> list[dict[str, Any]]:
    if len(points) < 2:
        return [dict(item) for item in points]
    return interpolate_segment([dict(points[0]), dict(points[-1])], maximum_spacing_mm)


def build_adaptive_safe_transition(
    points: list[dict[str, Any]],
    vehicle_safe_envelope: dict[str, Any],
    motion_model: dict[str, Any],
    actuator: dict[str, Any],
    safety_layout: dict[str, Any],
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    if len(points) < 2:
        return [dict(item) for item in points]
    config = profile["transition"]
    workspace = get_workspace_bounds(motion_model)
    carriage = actuator["end_effector"]["carriage_half_size_mm"]
    swept_margin = float(safety_layout.get("swept_volume_margin_mm", 0))
    geometry_margin = max(float(value) for value in carriage.values()) + swept_margin
    safe_z = max(
        float(config["minimum_safe_height_mm"]),
        float(vehicle_safe_envelope["z_max_mm"]) + float(profile["clearance"]["recommended_mm"]) + geometry_margin + float(config["transition_clearance_margin_mm"]),
    )
    safe_z = min(safe_z, float(config["maximum_safe_height_mm"]), workspace["z_max_mm"] - swept_margin)
    start, end = points[0], points[-1]
    waypoints = [
        dict(start),
        _metadata_point(start, float(start["x_mm"]), float(start["y_mm"]), max(float(start["z_mm"]), safe_z)),
        _metadata_point(end, float(end["x_mm"]), float(end["y_mm"]), max(float(end["z_mm"]), safe_z)),
        dict(end),
    ]
    deduplicated = [waypoints[0]]
    for point in waypoints[1:]:
        if calculate_point_distance(deduplicated[-1], point) > 1e-6:
            deduplicated.append(point)
    return interpolate_segment(deduplicated, float(profile["geometry"]["maximum_output_point_spacing_mm"]))


def validate_transition_candidate(
    baseline_points: list[dict[str, Any]],
    candidate_points: list[dict[str, Any]],
    actuator: dict[str, Any],
    vehicle_safe_envelope: dict[str, Any],
    safety_layout: dict[str, Any],
    profile: dict[str, Any],
    task_id: str,
) -> dict[str, Any]:
    resolved = resolve_dynamic_safety_zones(safety_layout, vehicle_safe_envelope)
    annotated = apply_safety_zone_annotations(candidate_points, resolved)
    volumes = build_trajectory_swept_volumes(annotated, actuator, float(safety_layout.get("swept_volume_margin_mm", 0)), task_id)
    issues = []
    issues.extend(check_static_obstacle_collisions(annotated, resolved.get("static_obstacles", []), actuator["actuator_id"]))
    issues.extend(check_vehicle_clearance(annotated, vehicle_safe_envelope, profile["clearance"], actuator["actuator_id"]))
    issues.extend(check_forbidden_zone_entry(annotated, actuator["actuator_id"]))
    issues.extend(check_swept_volume_collisions(volumes, resolved.get("static_obstacles", [])))
    issues.extend(check_vehicle_swept_collisions(volumes, vehicle_safe_envelope))
    clearance = validate_clearance_candidate(baseline_points, annotated, vehicle_safe_envelope, profile["clearance"])
    critical = [item for item in issues if item.get("severity") == "CRITICAL"]
    accepted = not critical and clearance["accepted"]
    return {
        "accepted": accepted,
        "validation_status": "PASS" if accepted else "FAIL",
        "critical_issue_count": len(critical),
        "issues": critical[:10],
        "clearance": clearance,
        "rejection_reason": None if accepted else (clearance.get("rejection_reason") or (critical[0]["message"] if critical else "candidate failed safety validation")),
    }


def optimize_transitions(
    machine_path_plan: dict[str, Any],
    collision_safety_plan: dict[str, Any],
    motion_model: dict[str, Any],
    space_model_report: dict[str, Any],
    safety_layout: dict[str, Any],
    actuator_system: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    points = machine_path_plan["trajectory_points"]
    segments = machine_path_plan["segments"]
    tasks = {task["source_segment_id"]: task for task in collision_safety_plan["actuator_tasks"]}
    actuators = {item["actuator_id"]: item for item in actuator_system["actuators"]}
    vehicle_safe = space_model_report["vehicle_envelope"]["safe_envelope"]
    max_spacing = float(profile["geometry"]["maximum_output_point_spacing_mm"])
    minimum_length = float(profile["geometry"]["minimum_meaningful_segment_length_mm"])
    optimized: dict[str, list[dict[str, Any]]] = {}
    results = []
    rejected = []
    process_segments = [item for item in segments if item["segment_type"] == "process"]
    process_index = {item["segment_id"]: index for index, item in enumerate(process_segments)}

    for index, segment in enumerate(segments):
        if segment["segment_type"] != "transition":
            continue
        original = [dict(item) for item in points[segment["point_start_index"]:segment["point_end_index"] + 1]]
        previous = segments[index - 1] if index else None
        following = segments[index + 1] if index + 1 < len(segments) else None
        task = tasks.get(segment["segment_id"])
        actuator = actuators.get((task or {}).get("assigned_actuator_id"))
        previous_task = tasks.get(previous["segment_id"]) if previous else None
        next_task = tasks.get(following["segment_id"]) if following else None
        classification = classify_transition(previous, segment, following, (previous_task or {}).get("assigned_actuator_id"), (next_task or {}).get("assigned_actuator_id"))
        original_length = _length(original)
        selected = original
        status = "UNCHANGED"
        rejection_reason = None
        validation = {"accepted": True, "validation_status": "PASS", "rejection_reason": None}

        if classification == "STATE_BOUNDARY_TRANSITION":
            status = "REQUIRED"
            rejection_reason = "wash state boundary is preserved"
        elif not actuator:
            status = "REJECTED"
            rejection_reason = "transition task has no assigned actuator"
        else:
            candidates: list[tuple[str, list[dict[str, Any]]]] = []
            endpoint_distance = calculate_point_distance(original[0], original[-1])
            if endpoint_distance <= float(profile["transition"]["maximum_direct_connection_distance_mm"]):
                candidates.append(("direct", build_direct_transition_candidate(original, max_spacing)))
            if profile["transition"].get("use_adaptive_safe_height"):
                candidates.append(("adaptive_safe_height", build_adaptive_safe_transition(original, vehicle_safe, motion_model, actuator, safety_layout, profile)))
            accepted_candidates = []
            candidate_failures = []
            for candidate_type, candidate in candidates[: int(profile["transition"]["maximum_transition_search_candidates"])]:
                check = validate_transition_candidate(original, candidate, actuator, vehicle_safe, safety_layout, profile, task["task_id"])
                if check["accepted"]:
                    accepted_candidates.append((candidate_type, candidate, check))
                else:
                    candidate_failures.append({"candidate_type": candidate_type, "reason": check["rejection_reason"]})
            if accepted_candidates:
                candidate_type, candidate, validation = min(accepted_candidates, key=lambda item: _length(item[1]))
                reduction = original_length - _length(candidate)
                if reduction >= minimum_length:
                    selected = candidate
                    status = "MERGED" if candidate_type == "direct" and classification == "MERGEABLE_TRANSITION" else "SHORTENED"
                else:
                    status = "UNCHANGED"
                    rejection_reason = "safe candidate did not provide meaningful length reduction"
            elif candidates:
                status = "REJECTED"
                rejection_reason = "; ".join(item["reason"] for item in candidate_failures) or "all candidates failed"
                rejected.append({"segment_id": segment["segment_id"], "classification": classification, "rejection_reason": rejection_reason})
            else:
                status = "REQUIRED"
                rejection_reason = "no candidate type allowed by profile"

        for point in selected:
            point.update({"segment_id": segment["segment_id"], "state_id": segment["state_id"], "zone_id": segment["zone_id"], "nozzle_id": segment["nozzle_id"], "is_transition": True})
        optimized[segment["segment_id"]] = selected
        optimized_length = _length(selected)
        results.append({
            "segment_id": segment["segment_id"],
            "transition_classification": classification,
            "original_length_mm": round(original_length, 6),
            "optimized_length_mm": round(optimized_length, 6),
            "original_duration_s": round(_duration(original), 6),
            "optimized_duration_s": None,
            "optimization_status": status,
            "reduction_percent": round((original_length - optimized_length) / original_length * 100, 3) if original_length > 0 else 0.0,
            "rejection_reason": rejection_reason,
            "safety_validation": validation,
        })
    return {"optimized_transition_points": optimized, "transition_results": results, "rejected_candidates": rejected}
