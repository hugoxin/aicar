from __future__ import annotations

from collections import Counter
from typing import Any

from aicar_sim.collision_checker import (
    check_actuator_home_positions,
    check_forbidden_zone_entry,
    check_safety_speed_policy,
    check_static_obstacle_collisions,
    check_swept_volume_collisions,
    check_safe_stop_points,
    check_vehicle_clearance,
    check_vehicle_swept_collisions,
)
from aicar_sim.multi_actuator_scheduler import build_multi_actuator_schedule
from aicar_sim.safe_stop_planner import select_safe_stop_points
from aicar_sim.safety_zone import apply_safety_zone_annotations, resolve_dynamic_safety_zones
from aicar_sim.swept_volume import build_trajectory_swept_volumes
from aicar_sim.task_allocator import allocate_segments_to_actuators, validate_task_assignment


def _deduplicate_issues(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    seen = set()
    for item in items:
        key = (
            item.get("check_id"), item.get("severity"), item.get("actuator_id"),
            item.get("segment_id"), item.get("obstacle_id"),
            item.get("sync_group_id"), item.get("task_id"), item.get("message"),
        )
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _actuator_map(system: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["actuator_id"]: item for item in system.get("actuators", [])}


def build_collision_safety_plan(
    machine_path_plan: dict[str, Any],
    motion_model: dict[str, Any],
    space_model_report: dict[str, Any],
    nozzle_coverage_plan: dict[str, Any],
    safety_layout: dict[str, Any],
    actuator_system: dict[str, Any],
) -> dict[str, Any]:
    del nozzle_coverage_plan  # Reserved for nozzle-specific safety policies in later work.
    vehicle_safe = space_model_report["vehicle_envelope"]["safe_envelope"]
    resolved_layout = resolve_dynamic_safety_zones(safety_layout, vehicle_safe)
    allocation = allocate_segments_to_actuators(machine_path_plan, actuator_system)
    tasks = allocation["tasks"]
    unassigned_tasks = allocation["unassigned_tasks"]
    assignment_issues = validate_task_assignment(tasks, actuator_system)
    annotated_points = apply_safety_zone_annotations(machine_path_plan["trajectory_points"], resolved_layout)
    points_by_index = {int(point["sequence_index"]): point for point in annotated_points}
    actuators = _actuator_map(actuator_system)
    margin = float(safety_layout.get("swept_volume_margin_mm", 0))
    swept_volumes = []
    all_issues = list(assignment_issues)
    all_issues.extend(
        check_actuator_home_positions(
            actuator_system,
            motion_model,
            resolved_layout.get("static_obstacles", []),
            vehicle_safe,
        )
    )

    for task in tasks:
        actuator_id = task["assigned_actuator_id"]
        actuator = actuators[actuator_id]
        task_points = [points_by_index[index] for index in task["path_point_indices"] if index in points_by_index]
        if len(task_points) >= 2:
            swept_volumes.extend(build_trajectory_swept_volumes(task_points, actuator, margin, task["task_id"]))
        all_issues.extend(check_static_obstacle_collisions(task_points, resolved_layout.get("static_obstacles", []), actuator_id))
        all_issues.extend(check_vehicle_clearance(task_points, vehicle_safe, safety_layout["vehicle_clearance_policy"], actuator_id))
        all_issues.extend(check_forbidden_zone_entry(task_points, actuator_id))
        all_issues.extend(check_safety_speed_policy(task_points, actuator_id))

    all_issues.extend(check_swept_volume_collisions(swept_volumes, resolved_layout.get("static_obstacles", [])))
    all_issues.extend(check_vehicle_swept_collisions(swept_volumes, vehicle_safe))
    all_issues = _deduplicate_issues(all_issues)

    schedule = build_multi_actuator_schedule(tasks, actuator_system, swept_volumes, resolved_layout)
    safe_stop_points, safe_stop_violations = select_safe_stop_points(
        actuator_system, motion_model, resolved_layout, vehicle_safe
    )
    all_issues.extend(safe_stop_violations)
    all_issues.extend(check_safe_stop_points(safe_stop_points))

    for task in unassigned_tasks:
        all_issues.append(
            {
                "check_id": "unassigned_task",
                "severity": "CRITICAL",
                "message": "A required machine-path task could not be assigned.",
                "task_id": task["task_id"],
                "state_id": task["state_id"],
                "zone_id": task["zone_id"],
            }
        )
    for conflict in schedule["conflicts_after_resolution"]:
        all_issues.append(
            {
                "check_id": "unresolved_interlock_conflict",
                "severity": "CRITICAL",
                "message": "Shared-resource conflict remains after scheduling.",
                **conflict,
            }
        )
    all_issues.extend(schedule["deadlock_warnings"])
    for group in schedule["sync_groups"]:
        if group["sync_status"] in {"DEGRADED", "BLOCKED_BY_INTERLOCK"}:
            all_issues.append(
                {
                    "check_id": "sync_degraded",
                    "severity": "WARNING",
                    "message": group.get("sync_warning") or "Left/right task synchronization was degraded.",
                    "sync_group_id": group["sync_group_id"],
                }
            )

    explanatory_warnings = [
        {"check_id": "aabb_approximation", "severity": "WARNING", "message": "Static obstacles and swept volumes use conservative AABB approximation."},
        {"check_id": "vehicle_geometry_approximation", "severity": "WARNING", "message": "Vehicle clearance uses a safe-envelope approximation, not real body surfaces."},
        {"check_id": "generic_actuator_model", "severity": "WARNING", "message": "Generic multi-actuator dimensions and timing are used."},
        {"check_id": "unmodeled_uncertainty", "severity": "WARNING", "message": "Sensor error, vehicle placement error, structural deformation, and real execution error are not modeled."},
    ]
    all_issues.extend(explanatory_warnings)
    all_issues = _deduplicate_issues(all_issues)
    violations = [item for item in all_issues if item.get("severity") == "CRITICAL"]
    warnings = [item for item in all_issues if item.get("severity") == "WARNING"]
    status = "FAIL" if violations else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    static_collisions = [item for item in violations if item.get("check_id") in {"static_obstacle_point", "swept_static_obstacle"}]
    vehicle_collisions = [item for item in violations if item.get("check_id") in {"vehicle_clearance", "swept_vehicle_envelope"}]
    forbidden_entries = [item for item in violations if item.get("check_id") == "forbidden_zone"]

    return {
        "plan_version": "stage4.3",
        "validation_status": status,
        "safety_layout_id": safety_layout["layout_id"],
        "actuator_system_id": actuator_system["system_id"],
        "motion_model_id": motion_model["motion_model_id"],
        "vehicle_type": machine_path_plan.get("vehicle_type", "unknown"),
        "wash_profile": machine_path_plan.get("wash_profile", "unknown"),
        "summary": {
            "actuator_count": len(actuator_system.get("actuators", [])),
            "task_count": len(tasks) + len(unassigned_tasks),
            "assigned_task_count": len(tasks),
            "unassigned_task_count": len(unassigned_tasks),
            "swept_volume_count": len(swept_volumes),
            "static_collision_count": len(static_collisions),
            "vehicle_collision_count": len(vehicle_collisions),
            "forbidden_zone_entry_count": len(forbidden_entries),
            "safe_stop_point_count": len(safe_stop_points),
            "warning_count": len(warnings),
            "violation_count": len(violations),
        },
        "clearance_policy": safety_layout["vehicle_clearance_policy"],
        "vehicle_envelope": space_model_report["vehicle_envelope"],
        "annotated_trajectory_points": annotated_points,
        "actuator_tasks": tasks,
        "unassigned_tasks": unassigned_tasks,
        "swept_volumes": swept_volumes,
        "safe_stop_points": safe_stop_points,
        "multi_actuator_schedule": schedule,
        "collisions": static_collisions + vehicle_collisions,
        "warnings": warnings,
        "violations": violations,
        "warning_category_counts": dict(Counter(item.get("check_id", "unknown") for item in warnings)),
        "violation_category_counts": dict(Counter(item.get("check_id", "unknown") for item in violations)),
        "resolved_safety_layout": resolved_layout,
        "limitations": [
            "Collision-safe candidate plan only; not a real-machine collision validation.",
            "Static geometry and swept volumes use AABB approximation.",
            "No real machine geometry, sensor uncertainty, structural deformation, PLC, or hardware control is included.",
        ],
    }
