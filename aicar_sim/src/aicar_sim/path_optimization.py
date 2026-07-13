from __future__ import annotations

from collections import Counter
from typing import Any

from aicar_sim.collision_safety_planner import build_collision_safety_plan
from aicar_sim.motion_validator import validate_machine_path
from aicar_sim.path_interpolator import calculate_point_distance
from aicar_sim.path_metrics import calculate_path_metrics, compare_path_metrics
from aicar_sim.path_simplifier import (
    preserve_critical_points,
    remove_duplicate_points,
    resample_path,
    simplify_collinear_points,
)
from aicar_sim.schedule_optimizer import optimize_schedule
from aicar_sim.task_sequence_optimizer import validate_task_order
from aicar_sim.trajectory_timing import parameterize_trajectory
from aicar_sim.transition_optimizer import optimize_transitions


VALID_STATUSES = {
    "ACCEPTED", "ACCEPTED_WITH_WARNINGS", "NO_MEANINGFUL_IMPROVEMENT",
    "REJECTED_SAFETY_REGRESSION", "FAILED",
}


def _path_length(points: list[dict[str, Any]]) -> float:
    return sum(calculate_point_distance(a, b) for a, b in zip(points, points[1:]))


def _state_order(segments: list[dict[str, Any]]) -> list[str]:
    result = []
    for segment in segments:
        state_id = str(segment["state_id"])
        if state_id not in result:
            result.append(state_id)
    return result


def _segment_points(plan: dict[str, Any], segment: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(item) for item in plan["trajectory_points"][segment["point_start_index"]:segment["point_end_index"] + 1]]


def _build_candidate_path(
    machine_path_plan: dict[str, Any],
    collision_safety_plan: dict[str, Any],
    motion_model: dict[str, Any],
    space_model_report: dict[str, Any],
    safety_layout: dict[str, Any],
    actuator_system: dict[str, Any],
    profile: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    transition_data = optimize_transitions(
        machine_path_plan, collision_safety_plan, motion_model, space_model_report,
        safety_layout, actuator_system, profile,
    )
    geometry = profile["geometry"]
    new_segment_points: dict[str, list[dict[str, Any]]] = {}
    removed_points = []
    critical_global = {
        int(item["point_index"])
        for item in collision_safety_plan.get("warnings", []) + collision_safety_plan.get("violations", [])
        if item.get("point_index") is not None
    }
    for segment in machine_path_plan["segments"]:
        segment_id = segment["segment_id"]
        original = _segment_points(machine_path_plan, segment)
        if segment["segment_type"] == "transition":
            selected = transition_data["optimized_transition_points"].get(segment_id, original)
        else:
            local_critical = {
                index - int(segment["point_start_index"])
                for index in critical_global
                if int(segment["point_start_index"]) <= index <= int(segment["point_end_index"])
            }
            preserved = preserve_critical_points(original, {"critical_indices": local_critical})
            deduplicated, duplicate_removals = remove_duplicate_points(original, float(geometry["duplicate_point_tolerance_mm"]))
            if len(deduplicated) != len(original):
                preserved = preserve_critical_points(deduplicated)
            simplified, collinear_removals = simplify_collinear_points(
                deduplicated,
                float(geometry["collinear_distance_tolerance_mm"]),
                float(geometry["collinear_angle_tolerance_deg"]),
                preserved,
            )
            selected = resample_path(simplified, float(geometry["maximum_output_point_spacing_mm"]))
            removed_points.extend(duplicate_removals + collinear_removals)
        for point in selected:
            point.update({
                "segment_id": segment_id,
                "state_id": segment["state_id"],
                "zone_id": segment["zone_id"],
                "nozzle_id": segment["nozzle_id"],
                "is_transition": segment["segment_type"] == "transition" or bool(point.get("is_transition")),
            })
        new_segment_points[segment_id] = selected

    flat_points = []
    new_segments = []
    for segment in machine_path_plan["segments"]:
        selected = new_segment_points[segment["segment_id"]]
        start = len(flat_points)
        flat_points.extend(dict(point) for point in selected)
        new_segments.append({
            **{key: segment[key] for key in ("segment_id", "state_id", "zone_id", "nozzle_id", "segment_type", "requires_transition")},
            "point_start_index": start,
            "point_end_index": len(flat_points) - 1,
            "point_count": len(selected),
        })
    if len(flat_points) > int(geometry["maximum_trajectory_points"]):
        raise ValueError(f"optimized candidate exceeds maximum_trajectory_points: {len(flat_points)}")
    trajectory = parameterize_trajectory(flat_points, motion_model)
    if new_segments:
        new_segments[-1]["point_end_index"] = len(trajectory) - 1
        new_segments[-1]["point_count"] += 1
    summary = dict(machine_path_plan["summary"])
    summary.update({
        "trajectory_point_count": len(trajectory),
        "transition_segment_count": len([item for item in new_segments if item["segment_type"] == "transition"]),
        "path_length_mm": round(_path_length(trajectory), 3),
        "estimated_motion_duration_s": round(float(trajectory[-1]["timestamp_s"]), 3),
        "maximum_velocity_mm_s": round(max(float(item["velocity_mm_s"]) for item in trajectory), 3),
        "maximum_acceleration_mm_s2": round(max(float(item["acceleration_mm_s2"]) for item in trajectory), 3),
        "interpolation_spacing_mm": float(geometry["maximum_output_point_spacing_mm"]),
    })
    candidate = {
        **{key: machine_path_plan[key] for key in ("motion_model_id", "vehicle_type", "wash_profile", "coordinate_system", "source_path_segments")},
        "plan_version": "stage4.4-candidate",
        "summary": summary,
        "trajectory_points": trajectory,
        "segments": new_segments,
        "warnings": list(machine_path_plan.get("warnings", [])),
        "limitations": list(machine_path_plan.get("limitations", [])),
    }
    # Update transition durations after the candidate receives new timestamps.
    result_map = {item["segment_id"]: item for item in transition_data["transition_results"]}
    for segment in new_segments:
        result = result_map.get(segment["segment_id"])
        if result:
            points = trajectory[segment["point_start_index"]:segment["point_end_index"] + 1]
            result["optimized_duration_s"] = round(max(0.0, float(points[-1]["timestamp_s"]) - float(points[0]["timestamp_s"])), 6)
    transition_data["removed_points"] = removed_points
    return candidate, transition_data


def build_optimized_machine_path(
    machine_path_plan: dict[str, Any],
    collision_safety_plan: dict[str, Any],
    multi_actuator_schedule: dict[str, Any],
    motion_model: dict[str, Any],
    space_model_report: dict[str, Any],
    nozzle_coverage_plan: dict[str, Any],
    safety_layout: dict[str, Any],
    actuator_system: dict[str, Any],
    optimization_profile: dict[str, Any],
) -> dict[str, Any]:
    candidate, transition_data = _build_candidate_path(
        machine_path_plan, collision_safety_plan, motion_model, space_model_report,
        safety_layout, actuator_system, optimization_profile,
    )
    motion_validation = validate_machine_path(candidate, motion_model, space_model_report, nozzle_coverage_plan)
    candidate_collision = build_collision_safety_plan(
        candidate, motion_model, space_model_report, nozzle_coverage_plan,
        safety_layout, actuator_system,
    )
    candidate_schedule = optimize_schedule(
        candidate_collision["actuator_tasks"], actuator_system,
        candidate_collision["swept_volumes"], candidate_collision["resolved_safety_layout"],
        multi_actuator_schedule, optimization_profile,
        candidate_collision["multi_actuator_schedule"],
    )
    baseline_metrics = calculate_path_metrics(machine_path_plan, collision_safety_plan, multi_actuator_schedule, space_model_report)
    optimized_metrics = calculate_path_metrics(candidate, candidate_collision, candidate_schedule, space_model_report)
    comparisons = compare_path_metrics(baseline_metrics, optimized_metrics)
    original_tasks = collision_safety_plan["actuator_tasks"]
    optimized_tasks = candidate_collision["actuator_tasks"]
    task_order_validation = validate_task_order(original_tasks, optimized_tasks)
    state_order_unchanged = _state_order(machine_path_plan["segments"]) == _state_order(candidate["segments"])
    conditions = {
        "motion_validation_passed": motion_validation["violation_count"] == 0,
        "collision_violations_zero": candidate_collision["summary"]["violation_count"] == 0,
        "static_collisions_zero": candidate_collision["summary"]["static_collision_count"] == 0,
        "vehicle_collisions_zero": candidate_collision["summary"]["vehicle_collision_count"] == 0,
        "forbidden_entries_zero": candidate_collision["summary"]["forbidden_zone_entry_count"] == 0,
        "unassigned_tasks_zero": candidate_collision["summary"]["unassigned_task_count"] == 0,
        "schedule_conflicts_zero": candidate_schedule["summary"]["conflict_count_after_resolution"] == 0,
        "unresolved_conflicts_zero": candidate_schedule["summary"]["unresolved_conflict_count"] == 0,
        "deadlock_warnings_zero": candidate_schedule["summary"]["deadlock_warning_count"] == 0,
        "safe_stop_points_valid": candidate_collision["summary"]["safe_stop_point_count"] >= len(actuator_system["actuators"]),
        "minimum_clearance_not_reduced": optimized_metrics["minimum_vehicle_clearance_mm"] + 1e-6 >= baseline_metrics["minimum_vehicle_clearance_mm"],
        "clearance_warnings_not_increased": optimized_metrics["clearance_warning_count"] <= baseline_metrics["clearance_warning_count"],
        "task_set_unchanged": task_order_validation["task_id_set_unchanged"],
        "task_count_unchanged": task_order_validation["task_count_unchanged"],
        "wash_state_order_unchanged": state_order_unchanged and task_order_validation["state_order_unchanged"],
    }
    accepted = all(conditions.values())
    improvement_values = [comparisons[key]["improvement_percent"] for key in ("path_length_mm", "estimated_motion_duration_s", "total_schedule_duration_s", "total_delay_s")]
    meaningful = any(value is not None and value > 0.1 for value in improvement_values)
    if not accepted:
        status = "REJECTED_SAFETY_REGRESSION"
        final_plan = machine_path_plan
        final_metrics = baseline_metrics
        final_schedule = multi_actuator_schedule
    else:
        status = "ACCEPTED_WITH_WARNINGS" if candidate_collision["summary"]["warning_count"] or transition_data["rejected_candidates"] else ("ACCEPTED" if meaningful else "NO_MEANINGFUL_IMPROVEMENT")
        final_plan = candidate
        final_metrics = optimized_metrics
        final_schedule = candidate_schedule
    target_results = {}
    target_map = {
        "path_length_mm": "preferred_path_length_reduction_percent",
        "estimated_motion_duration_s": "preferred_motion_duration_reduction_percent",
        "total_schedule_duration_s": "preferred_schedule_duration_reduction_percent",
        "transition_segment_count": "preferred_transition_reduction_percent",
        "total_delay_s": "preferred_total_delay_reduction_percent",
    }
    for metric, target_key in target_map.items():
        improvement = comparisons[metric]["improvement_percent"]
        target = float(optimization_profile["targets"][target_key])
        target_results[metric] = {"target_percent": target, "actual_percent": improvement, "status": "TARGET_REACHED" if improvement is not None and improvement >= target else "TARGET_NOT_REACHED"}
    warnings = list(candidate_collision.get("warnings", []))
    warnings.extend({"check_id": "target_not_reached", "severity": "WARNING", "message": f"{metric} optimization target was not reached.", "metric": metric} for metric, item in target_results.items() if item["status"] == "TARGET_NOT_REACHED")
    return {
        "plan_version": "stage4.4",
        "optimization_profile_id": optimization_profile["profile_id"],
        "optimization_status": status,
        "safety_validation_status": "PASS_WITH_WARNINGS" if accepted and warnings else ("PASS" if accepted else "FAIL"),
        "baseline_validation_status": collision_safety_plan["validation_status"],
        "optimized_validation_status": candidate_collision["validation_status"],
        "accepted_optimization": accepted,
        "rejection_reasons": [name for name, passed in conditions.items() if not passed],
        "baseline_summary": baseline_metrics,
        "optimized_summary": final_metrics,
        "candidate_summary": optimized_metrics,
        "improvement_summary": comparisons,
        "target_results": target_results,
        "summary": final_plan["summary"],
        "trajectory_points": final_plan["trajectory_points"],
        "segments": final_plan["segments"],
        "optimized_segments": final_plan["segments"],
        "transition_results": transition_data["transition_results"],
        "removed_points": transition_data["removed_points"],
        "rejected_candidates": transition_data["rejected_candidates"],
        "task_order_changes": [],
        "task_order_validation": task_order_validation,
        "safety_validation": {
            "conditions": conditions,
            "motion_validation": {"validation_status": motion_validation["validation_status"], "violation_count": motion_validation["violation_count"], "warning_count": motion_validation["warning_count"]},
            "collision_validation": {"validation_status": candidate_collision["validation_status"], **candidate_collision["summary"]},
            "schedule_validation": candidate_schedule["safety_validation"],
        },
        "optimized_schedule": final_schedule,
        "candidate_schedule_summary": candidate_schedule["summary"],
        "warning_category_counts": dict(Counter(item.get("check_id", "unknown") for item in warnings)),
        "warnings": warnings,
        "violations": candidate_collision["violations"] if not accepted else [],
        "limitations": [
            "Safety-first heuristic optimization only; no global optimum guarantee.",
            "Generic actuator parameters and conservative AABB geometry are used.",
            "No real machine calibration, PLC, servo, SDK, or hardware output is included.",
        ],
    }
