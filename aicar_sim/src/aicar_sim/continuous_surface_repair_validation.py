from __future__ import annotations

from collections import Counter
from typing import Any

from aicar_sim.collision_safety_planner import build_collision_safety_plan
from aicar_sim.surface_schedule_adapter import build_surface_repair_schedule


def build_continuous_surface_repair_validation(
    surface_plan: dict[str, Any],
    machine_plan: dict[str, Any],
    motion_model: dict[str, Any],
    space_model_report: dict[str, Any],
    nozzle_coverage_plan: dict[str, Any],
    safety_layout: dict[str, Any],
    actuator_system: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    collision_plan = build_collision_safety_plan(
        machine_plan,
        motion_model,
        space_model_report,
        nozzle_coverage_plan,
        safety_layout,
        actuator_system,
    )
    schedule = build_surface_repair_schedule(
        collision_plan["actuator_tasks"],
        actuator_system,
        collision_plan["swept_volumes"],
        collision_plan["resolved_safety_layout"],
        machine_plan["trajectory_points"],
    )
    collision_plan["plan_version"] = "stage4.5-r"
    collision_plan["multi_actuator_schedule"] = schedule
    collision_plan["warnings"] = [item for item in collision_plan["warnings"] if item.get("check_id") != "sync_degraded"]
    collision_plan["warnings"].extend(schedule.get("interval_mapping_warnings", []))
    for group in schedule["sync_groups"]:
        if group["sync_status"] in {"DEGRADED", "BLOCKED_BY_INTERLOCK"}:
            collision_plan["warnings"].append(
                {
                    "check_id": "sync_degraded",
                    "severity": "WARNING",
                    "message": "Surface-route left/right synchronization was degraded by actual-interval interlocks.",
                    "sync_group_id": group["sync_group_id"],
                }
            )
    if schedule["summary"]["conflict_count_after_resolution"]:
        collision_plan["violations"].append(
            {
                "check_id": "unresolved_interlock_conflict",
                "severity": "CRITICAL",
                "message": "Surface repair schedule still has shared-resource conflicts.",
            }
        )
    collision_plan["summary"]["warning_count"] = len(collision_plan["warnings"])
    collision_plan["summary"]["violation_count"] = len(collision_plan["violations"])
    collision_plan["warning_category_counts"] = dict(Counter(item.get("check_id", "unknown") for item in collision_plan["warnings"]))
    collision_plan["violation_category_counts"] = dict(Counter(item.get("check_id", "unknown") for item in collision_plan["violations"]))
    collision_plan["validation_status"] = "FAIL" if collision_plan["violations"] else "PASS_WITH_WARNINGS" if collision_plan["warnings"] else "PASS"

    motion_validation = machine_plan["motion_validation"]
    motion_summary = motion_validation["metric_summary"]
    collision_summary = collision_plan["summary"]
    schedule_summary = schedule["summary"]
    source_validation = surface_plan["validation"]
    minimum_clearance = float(motion_summary["clearance"]["minimum_measured_mm"])
    safety_conditions = {
        "source_path_valid": source_validation["violation_count"] == 0,
        "motion_violations_zero": motion_validation["violation_count"] == 0,
        "collision_violations_zero": collision_summary["violation_count"] == 0,
        "static_collision_zero": collision_summary["static_collision_count"] == 0,
        "vehicle_collision_zero": collision_summary["vehicle_collision_count"] == 0,
        "forbidden_entry_zero": collision_summary["forbidden_zone_entry_count"] == 0,
        "unassigned_task_zero": collision_summary["unassigned_task_count"] == 0,
        "conflict_after_resolution_zero": schedule_summary["conflict_count_after_resolution"] == 0,
        "unresolved_conflict_zero": schedule_summary["unresolved_conflict_count"] == 0,
        "deadlock_zero": schedule_summary["deadlock_warning_count"] == 0,
        "safe_stop_at_least_three": collision_summary["safe_stop_point_count"] >= 3,
        "minimum_clearance_preserved": minimum_clearance >= 250,
        "point_count_within_limit": machine_plan["summary"]["trajectory_point_count"] <= 5000,
        "state_zone_patch_task_complete": all(source_validation["checks"].values()),
    }
    violations = [
        *source_validation["violations"],
        *motion_validation["violations"],
        *collision_plan["violations"],
    ]
    warnings = [
        *source_validation["warnings"],
        *motion_validation["warnings"],
        *collision_plan["warnings"],
    ]
    report = {
        "report_version": "stage4.5-r",
        "safety_status": "REJECTED_SAFETY_REGRESSION" if violations or not all(safety_conditions.values()) else "PASS_WITH_WARNINGS" if warnings else "PASS",
        "surface_validation_status": source_validation["validation_status"],
        "motion_validation_status": motion_validation["validation_status"],
        "collision_validation_status": collision_plan["validation_status"],
        "summary": {
            "trajectory_point_count": machine_plan["summary"]["trajectory_point_count"],
            "transition_count": machine_plan["summary"]["transition_segment_count"],
            "machine_path_length_mm": machine_plan["summary"]["path_length_mm"],
            "motion_duration_s": machine_plan["summary"]["estimated_motion_duration_s"],
            "schedule_task_count": schedule_summary["task_count"],
            "parallel_group_count": schedule_summary["parallel_group_count"],
            "synchronized_group_count": schedule_summary["synchronized_group_count"],
            "blocked_sync_group_count": schedule_summary["blocked_sync_group_count"],
            "resource_lock_count": schedule_summary["resource_lock_count"],
            "schedule_duration_s": schedule_summary["total_schedule_duration_s"],
            "total_delay_s": schedule_summary["total_delay_s"],
            "minimum_clearance_mm": minimum_clearance,
            "clearance_warning_count": collision_plan.get("warning_category_counts", {}).get("vehicle_clearance", 0),
            "static_collision_count": collision_summary["static_collision_count"],
            "vehicle_collision_count": collision_summary["vehicle_collision_count"],
            "forbidden_zone_entry_count": collision_summary["forbidden_zone_entry_count"],
            "unassigned_task_count": collision_summary["unassigned_task_count"],
            "conflict_count_before_resolution": schedule_summary["conflict_count_before_resolution"],
            "conflict_count_after_resolution": schedule_summary["conflict_count_after_resolution"],
            "unresolved_conflict_count": schedule_summary["unresolved_conflict_count"],
            "deadlock_warning_count": schedule_summary["deadlock_warning_count"],
            "safe_stop_point_count": collision_summary["safe_stop_point_count"],
            "warning_count": len(warnings),
            "violation_count": len(violations),
        },
        "safety_conditions": safety_conditions,
        "source_validation": source_validation,
        "motion_validation": motion_validation,
        "collision_validation": {
            "validation_status": collision_plan["validation_status"],
            "summary": collision_summary,
            "warning_category_counts": collision_plan["warning_category_counts"],
            "violation_category_counts": collision_plan["violation_category_counts"],
        },
        "schedule_validation": {
            "validation_status": schedule["adapter_validation"]["validation_status"],
            "summary": schedule_summary,
            "sync_groups": schedule["sync_groups"],
            "schedule_items": schedule["schedule_items"],
            "resource_locks": schedule["resource_locks"],
        },
        "warning_count": len(warnings),
        "violation_count": len(violations),
        "warnings": warnings,
        "violations": violations,
        "limitations": [
            "Reference analytic surface and generic actuator validation only.",
            "Collision geometry uses AABB and conservative swept-volume approximations.",
            "No real PLC, servo, controller timing, hardware, or safety certification is included.",
        ],
    }
    return report, collision_plan, schedule
