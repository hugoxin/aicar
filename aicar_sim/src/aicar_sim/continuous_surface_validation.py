from __future__ import annotations

from typing import Any

from aicar_sim.collision_safety_planner import build_collision_safety_plan
from aicar_sim.motion_validator import validate_machine_path


def build_continuous_surface_validation(
    surface_plan: dict[str, Any],
    machine_plan: dict[str, Any],
    motion_model: dict[str, Any],
    space_model: dict[str, Any],
    nozzle_plan: dict[str, Any],
    safety_layout: dict[str, Any],
    actuator_system: dict[str, Any],
    baseline_metrics: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    motion_validation = validate_machine_path(machine_plan, motion_model, space_model, nozzle_plan)
    collision_plan = build_collision_safety_plan(
        machine_plan, motion_model, space_model, nozzle_plan, safety_layout, actuator_system
    )
    schedule = collision_plan["multi_actuator_schedule"]
    surface_validation = surface_plan["validation"]
    collision_summary = collision_plan["summary"]
    schedule_summary = schedule["summary"]
    minimum_clearance = float(motion_validation["metric_summary"]["clearance"]["minimum_measured_mm"])
    final_velocity = float(machine_plan["trajectory_points"][-1]["velocity_mm_s"])
    timestamps_valid = all(
        float(current["timestamp_s"]) > float(previous["timestamp_s"]) and float(current["delta_time_s"]) > 0
        for previous, current in zip(machine_plan["trajectory_points"], machine_plan["trajectory_points"][1:])
    )
    conditions = {
        "surface_validation_passed": surface_validation["validation_status"] in {"PASS", "PASS_WITH_WARNINGS"} and surface_validation["violation_count"] == 0,
        "motion_validation_passed": motion_validation["validation_status"] in {"PASS", "PASS_WITH_WARNINGS"} and motion_validation["violation_count"] == 0,
        "collision_validation_passed": collision_plan["validation_status"] in {"PASS", "PASS_WITH_WARNINGS"} and collision_summary["violation_count"] == 0,
        "static_collision_count_zero": collision_summary["static_collision_count"] == 0,
        "vehicle_collision_count_zero": collision_summary["vehicle_collision_count"] == 0,
        "forbidden_zone_entry_count_zero": collision_summary["forbidden_zone_entry_count"] == 0,
        "unassigned_task_count_zero": collision_summary["unassigned_task_count"] == 0,
        "conflict_count_after_resolution_zero": schedule_summary["conflict_count_after_resolution"] == 0,
        "unresolved_conflict_count_zero": schedule_summary["unresolved_conflict_count"] == 0,
        "deadlock_warning_count_zero": schedule_summary["deadlock_warning_count"] == 0,
        "safe_stop_per_actuator": collision_summary["safe_stop_point_count"] >= len(actuator_system.get("actuators", [])),
        "minimum_clearance_preserved": minimum_clearance >= 250,
        "coverage_thresholds_passed": float(surface_plan["coverage_summary"]["total_coverage_percent"]) >= 92 and all(float(item["zone_coverage_percent"]) >= 90 for item in surface_plan["coverage_summary"]["zone_coverage"]),
        "trajectory_point_limit_passed": len(machine_plan["trajectory_points"]) <= 5000,
        "timestamps_valid": timestamps_valid,
        "final_velocity_zero": abs(final_velocity) <= 1e-6,
    }
    hard_safety_passed = all(conditions.values())
    baseline_path = float(baseline_metrics["path_length_mm"])
    baseline_motion = float(baseline_metrics["estimated_motion_duration_s"])
    continuous_path = float(machine_plan["summary"]["path_length_mm"])
    continuous_motion = float(machine_plan["summary"]["estimated_motion_duration_s"])
    if not hard_safety_passed:
        reconstruction_status = "REJECTED_SAFETY_REGRESSION"
    elif continuous_path >= baseline_path and continuous_motion >= baseline_motion:
        reconstruction_status = "NO_MEANINGFUL_IMPROVEMENT"
    else:
        reconstruction_status = "ACCEPTED_WITH_WARNINGS"

    violations = [
        *surface_validation.get("violations", []),
        *motion_validation.get("violations", []),
        *collision_plan.get("violations", []),
    ]
    warnings = [
        *surface_validation.get("warnings", []),
        *motion_validation.get("warnings", []),
        *collision_plan.get("warnings", []),
    ]
    if reconstruction_status == "NO_MEANINGFUL_IMPROVEMENT":
        warnings.append(
            {
                "check_id": "no_meaningful_improvement",
                "severity": "WARNING",
                "message": "The continuous path preserved safety and coverage but increased both path length and motion duration relative to the Stage4 frozen baseline.",
            }
        )
    report = {
        "report_version": "stage4.5",
        "reconstruction_status": reconstruction_status,
        "surface_validation_status": surface_validation["validation_status"],
        "motion_validation_status": motion_validation["validation_status"],
        "collision_validation_status": collision_plan["validation_status"],
        "summary": {
            "trajectory_point_count": machine_plan["summary"]["trajectory_point_count"],
            "transition_count": machine_plan["summary"]["transition_segment_count"],
            "path_length_mm": machine_plan["summary"]["path_length_mm"],
            "motion_duration_s": machine_plan["summary"]["estimated_motion_duration_s"],
            "schedule_duration_s": schedule_summary["total_schedule_duration_s"],
            "total_delay_s": schedule_summary["total_delay_s"],
            "coverage_percent": surface_plan["coverage_summary"]["total_coverage_percent"],
            "minimum_clearance_mm": minimum_clearance,
            "clearance_warning_count": collision_plan.get("warning_category_counts", {}).get("vehicle_clearance", 0),
            "static_collision_count": collision_summary["static_collision_count"],
            "vehicle_collision_count": collision_summary["vehicle_collision_count"],
            "forbidden_zone_entry_count": collision_summary["forbidden_zone_entry_count"],
            "unassigned_task_count": collision_summary["unassigned_task_count"],
            "conflict_count_after_resolution": schedule_summary["conflict_count_after_resolution"],
            "unresolved_conflict_count": schedule_summary["unresolved_conflict_count"],
            "deadlock_warning_count": schedule_summary["deadlock_warning_count"],
            "safe_stop_point_count": collision_summary["safe_stop_point_count"],
            "warning_count": len(warnings),
            "violation_count": len(violations),
        },
        "motion_validation": motion_validation,
        "collision_validation": {
            "validation_status": collision_plan["validation_status"],
            "summary": collision_summary,
            "warning_category_counts": collision_plan.get("warning_category_counts", {}),
            "violation_category_counts": collision_plan.get("violation_category_counts", {}),
        },
        "schedule_validation": {
            "summary": schedule_summary,
            "sync_groups": schedule.get("sync_groups", []),
            "conflicts_after_resolution": schedule.get("conflicts_after_resolution", []),
            "deadlock_warnings": schedule.get("deadlock_warnings", []),
        },
        "acceptance_conditions": conditions,
        "warning_count": len(warnings),
        "violation_count": len(violations),
        "warnings": warnings,
        "violations": violations,
        "limitations": [
            "Safety validation uses analytic surfaces, AABB obstacles, conservative swept volumes, and generic actuators.",
            "No CAD, point cloud, real vehicle placement error, actuator dynamics, PLC, servo, SDK, or hardware control is included.",
            "This report cannot replace real-machine validation or safety certification.",
        ],
    }
    return report, collision_plan, schedule
