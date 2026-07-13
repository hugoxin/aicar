from __future__ import annotations

from collections import defaultdict
from typing import Any

from aicar_sim.obstacle_model import aabb_intersects
from aicar_sim.shared_space_interlock import (
    build_resource_lock_intervals,
    detect_deadlock_risk,
    detect_time_interval_conflicts,
)
from aicar_sim.task_sequence_optimizer import build_task_dependencies, optimize_task_order


EPSILON = 1e-6


def _overlap(start_a: float, end_a: float, start_b: float, end_b: float) -> bool:
    return end_a + EPSILON >= start_b and end_b + EPSILON >= start_a


def find_earliest_feasible_start(
    earliest_start_s: float,
    duration_s: float,
    resource_ids: set[str],
    existing_locks: list[dict[str, Any]],
    margin_s: float,
    actuator_id: str | None = None,
) -> float:
    candidate = float(earliest_start_s)
    for _ in range(1000):
        blocking_ends = [
            float(lock["end_s"]) + margin_s
            for lock in existing_locks
            if lock["resource_id"] in resource_ids
            and (actuator_id is None or lock.get("actuator_id") != actuator_id)
            and _overlap(candidate, candidate + duration_s, float(lock["start_s"]), float(lock["end_s"]))
        ]
        if not blocking_ends:
            return candidate
        candidate = max(blocking_ends)
    raise ValueError("unable to find an earliest feasible resource-lock start")


def _resources_by_task(
    tasks: list[dict[str, Any]],
    swept_volumes: list[dict[str, Any]],
    safety_layout: dict[str, Any],
) -> dict[str, set[str]]:
    shared_zones = {
        zone["zone_id"]: zone
        for zone in safety_layout.get("safety_zones", [])
        if zone.get("zone_type") == "shared_interlock"
    }
    volumes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for volume in swept_volumes:
        volumes[str(volume.get("task_id"))].append(volume)
    result = {}
    for task in tasks:
        resources = set(task.get("shared_resources", []))
        for resource_id, zone in shared_zones.items():
            if any(aabb_intersects(volume["bounds"], zone["bounds"]) for volume in volumes.get(task["task_id"], [])):
                resources.add(resource_id)
        result[task["task_id"]] = resources
    return result


def try_local_task_swap(tasks: list[dict[str, Any]], constraints: dict[str, Any]) -> list[dict[str, Any]]:
    dependencies = build_task_dependencies(tasks)
    return optimize_task_order(tasks, dependencies, constraints)


def try_parallel_execution(
    left_task: dict[str, Any],
    right_task: dict[str, Any],
    resources: dict[str, set[str]],
) -> dict[str, Any]:
    shared = resources[left_task["task_id"]] & resources[right_task["task_id"]]
    return {
        "allowed": not shared and left_task["assigned_actuator_id"] != right_task["assigned_actuator_id"],
        "blocked_resources": sorted(shared),
    }


def optimize_resource_lock_intervals(lock_intervals: list[dict[str, Any]], margin_s: float) -> list[dict[str, Any]]:
    del margin_s
    return [dict(item) for item in lock_intervals]


def _schedule_item(task: dict[str, Any], start: float, baseline_item: dict[str, Any] | None, status: str, reason: str | None) -> dict[str, Any]:
    duration = max(0.2, float(task["estimated_duration_s"]))
    return {
        "schedule_item_id": f"schedule_{task['task_id']}",
        "task_id": task["task_id"],
        "actuator_id": task["assigned_actuator_id"],
        "state_id": task["state_id"],
        "zone_id": task["zone_id"],
        "planned_start_s": float((baseline_item or {}).get("planned_start_s", start)),
        "planned_end_s": float((baseline_item or {}).get("planned_end_s", start + duration)),
        "adjusted_start_s": round(start, 6),
        "adjusted_end_s": round(start + duration, 6),
        "duration_s": round(duration, 6),
        "shared_resources": list(task.get("shared_resources", [])),
        "sync_group_id": task.get("sync_group_id"),
        "schedule_status": status,
        "delay_reason": reason,
    }


def validate_optimized_schedule(schedule: dict[str, Any]) -> dict[str, Any]:
    issues = []
    by_actuator: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in schedule.get("schedule_items", []):
        if float(item["duration_s"]) <= 0 or float(item["adjusted_end_s"]) <= float(item["adjusted_start_s"]):
            issues.append({"check_id": "duration", "task_id": item["task_id"], "message": "non-positive task duration"})
        by_actuator[item["actuator_id"]].append(item)
    for actuator_id, items in by_actuator.items():
        ordered = sorted(items, key=lambda item: float(item["adjusted_start_s"]))
        for left, right in zip(ordered, ordered[1:]):
            if float(left["adjusted_end_s"]) > float(right["adjusted_start_s"]) + EPSILON:
                issues.append({"check_id": "same_actuator_overlap", "actuator_id": actuator_id, "task_id": right["task_id"], "message": "same actuator tasks overlap"})
    if schedule.get("conflicts_after_resolution"):
        issues.append({"check_id": "resource_conflict", "message": "resource conflict remains"})
    if schedule.get("deadlock_warnings"):
        issues.append({"check_id": "deadlock", "message": "deadlock warning remains"})
    return {"valid": not issues, "issues": issues}


def optimize_schedule(
    tasks: list[dict[str, Any]],
    actuator_system: dict[str, Any],
    swept_volumes: list[dict[str, Any]],
    safety_layout: dict[str, Any],
    baseline_schedule: dict[str, Any],
    profile: dict[str, Any],
    alternative_schedule: dict[str, Any] | None = None,
) -> dict[str, Any]:
    constraints = profile["schedule"]
    ordered_tasks = try_local_task_swap(tasks, constraints)
    resources = _resources_by_task(ordered_tasks, swept_volumes, safety_layout)
    baseline_items = {item["task_id"]: item for item in baseline_schedule.get("schedule_items", [])}
    state_order = []
    for task in sorted(ordered_tasks, key=lambda item: (float(item.get("source_start_s", 0)), item["task_id"])):
        if task["state_id"] not in state_order:
            state_order.append(task["state_id"])
    margin = float(constraints["maximum_resource_lock_margin_s"])
    schedule_items = []
    manual_locks: list[dict[str, Any]] = []
    actuator_cursor: dict[str, float] = defaultdict(float)
    state_start = 0.0
    sync_results = []
    handled: set[str] = set()
    interlock_delay = 0.0

    def add_item(task: dict[str, Any], start: float, status: str, reason: str | None) -> dict[str, Any]:
        item = _schedule_item(task, start, baseline_items.get(task["task_id"]), status, reason)
        schedule_items.append(item)
        actuator_cursor[item["actuator_id"]] = float(item["adjusted_end_s"])
        for resource_id in resources[task["task_id"]]:
            manual_locks.append({"resource_id": resource_id, "actuator_id": item["actuator_id"], "task_id": item["task_id"], "start_s": item["adjusted_start_s"], "end_s": item["adjusted_end_s"], "entry_point_index": None, "exit_point_index": None})
        return item

    for state_id in state_order:
        state_tasks = [task for task in ordered_tasks if task["state_id"] == state_id]
        state_end = state_start
        for task in state_tasks:
            if task["task_id"] in handled:
                continue
            sync_id = task.get("sync_group_id")
            partner = None
            if sync_id and constraints.get("allow_sync_start_adjustment"):
                partner = next((item for item in state_tasks if item["task_id"] not in handled and item["task_id"] != task["task_id"] and item.get("sync_group_id") == sync_id and item["assigned_actuator_id"] != task["assigned_actuator_id"]), None)
            if partner:
                parallel = try_parallel_execution(task, partner, resources)
                if parallel["allowed"]:
                    common = max(state_start, actuator_cursor[task["assigned_actuator_id"]], actuator_cursor[partner["assigned_actuator_id"]])
                    for _ in range(int(constraints["maximum_iterations"])):
                        left_start = find_earliest_feasible_start(common, float(task["estimated_duration_s"]), resources[task["task_id"]], manual_locks, margin, task["assigned_actuator_id"])
                        right_start = find_earliest_feasible_start(common, float(partner["estimated_duration_s"]), resources[partner["task_id"]], manual_locks, margin, partner["assigned_actuator_id"])
                        next_common = max(left_start, right_start)
                        if abs(next_common - common) <= EPSILON:
                            break
                        common = next_common
                    left_item = add_item(task, common, "SYNCHRONIZED", "safe disjoint-resource parallel execution")
                    right_item = add_item(partner, common, "SYNCHRONIZED", "safe disjoint-resource parallel execution")
                    sync_results.append({"sync_group_id": sync_id, "left_task_id": left_item["task_id"] if left_item["actuator_id"].startswith("left") else right_item["task_id"], "right_task_id": right_item["task_id"] if right_item["actuator_id"].startswith("right") else left_item["task_id"], "baseline_sync_status": next((item.get("sync_status") for item in baseline_schedule.get("sync_groups", []) if item.get("sync_group_id") == sync_id), None), "optimized_sync_status": "SYNCHRONIZED", "baseline_start_offset_s": next((item.get("start_offset_s") for item in baseline_schedule.get("sync_groups", []) if item.get("sync_group_id") == sync_id), None), "optimized_start_offset_s": 0.0, "sync_status": "SYNCHRONIZED", "parallel_execution_enabled": True, "blocked_reason": None, "safety_validation": "PASS"})
                    handled.update({task["task_id"], partner["task_id"]})
                    state_end = max(state_end, float(left_item["adjusted_end_s"]), float(right_item["adjusted_end_s"]))
                    continue
                sync_results.append({"sync_group_id": sync_id, "left_task_id": task["task_id"] if task["assigned_actuator_id"].startswith("left") else partner["task_id"], "right_task_id": partner["task_id"] if partner["assigned_actuator_id"].startswith("right") else task["task_id"], "baseline_sync_status": next((item.get("sync_status") for item in baseline_schedule.get("sync_groups", []) if item.get("sync_group_id") == sync_id), None), "optimized_sync_status": "BLOCKED_BY_INTERLOCK", "baseline_start_offset_s": next((item.get("start_offset_s") for item in baseline_schedule.get("sync_groups", []) if item.get("sync_group_id") == sync_id), None), "optimized_start_offset_s": None, "sync_status": "BLOCKED_BY_INTERLOCK", "parallel_execution_enabled": False, "blocked_reason": ", ".join(parallel["blocked_resources"]), "safety_validation": "PASS"})
            earliest = max(state_start, actuator_cursor[task["assigned_actuator_id"]])
            start = find_earliest_feasible_start(earliest, float(task["estimated_duration_s"]), resources[task["task_id"]], manual_locks, margin, task["assigned_actuator_id"])
            interlock_delay += max(0.0, start - earliest)
            item = add_item(task, start, "OPTIMIZED_EARLIEST_START", "earliest feasible start with local resource lock")
            handled.add(task["task_id"])
            state_end = max(state_end, float(item["adjusted_end_s"]))
        state_start = state_end

    resource_locks = optimize_resource_lock_intervals(build_resource_lock_intervals(schedule_items, swept_volumes, safety_layout), margin)
    conflicts_after = detect_time_interval_conflicts(resource_locks)
    deadlocks = detect_deadlock_risk(schedule_items)
    timelines = {item["actuator_id"]: [task for task in schedule_items if task["actuator_id"] == item["actuator_id"]] for item in actuator_system["actuators"]}
    parallel_pairs = sum(1 for index, left in enumerate(schedule_items) for right in schedule_items[index + 1:] if left["actuator_id"] != right["actuator_id"] and float(left["adjusted_end_s"]) > float(right["adjusted_start_s"]) and float(right["adjusted_end_s"]) > float(left["adjusted_start_s"]))
    total_delay = interlock_delay
    adjustments = []
    for item in schedule_items:
        baseline = baseline_items.get(item["task_id"])
        if not baseline:
            continue
        adjustments.append({"task_id": item["task_id"], "original_start_s": baseline["adjusted_start_s"], "optimized_start_s": item["adjusted_start_s"], "original_end_s": baseline["adjusted_end_s"], "optimized_end_s": item["adjusted_end_s"], "delay_change_s": round(float(item["adjusted_start_s"]) - float(baseline["adjusted_start_s"]), 6), "reason": item["delay_reason"], "affected_resource": ",".join(sorted(resources[item["task_id"]])), "safety_validated": not conflicts_after})
    schedule = {
        "schedule_version": "stage4.4",
        "optimization_profile_id": profile["profile_id"],
        "optimization_status": "ACCEPTED_WITH_WARNINGS" if not conflicts_after and not deadlocks else "REJECTED_SAFETY_REGRESSION",
        "actuator_system_id": actuator_system["system_id"],
        "baseline_summary": baseline_schedule["summary"],
        "summary": {
            "actuator_count": len(actuator_system["actuators"]), "task_count": len(tasks),
            "assigned_task_count": len(tasks), "unassigned_task_count": 0,
            "parallel_group_count": parallel_pairs,
            "synchronized_group_count": len([item for item in sync_results if item["sync_status"] == "SYNCHRONIZED"]),
            "conflict_count_before_resolution": len(baseline_schedule.get("conflicts_before_resolution", [])),
            "conflict_count_after_resolution": len(conflicts_after), "unresolved_conflict_count": len(conflicts_after),
            "total_schedule_duration_s": round(max([float(item["adjusted_end_s"]) for item in schedule_items] or [0]), 3),
            "total_delay_s": round(total_delay, 3), "deadlock_warning_count": len(deadlocks),
        },
        "optimized_summary": {},
        "actuator_timelines": timelines,
        "schedule_items": schedule_items,
        "sync_groups": sync_results,
        "resource_locks": resource_locks,
        "adjustments": adjustments,
        "rejected_adjustments": [],
        "conflicts_before_resolution": baseline_schedule.get("conflicts_before_resolution", []),
        "conflicts_after_resolution": conflicts_after,
        "deadlock_warnings": deadlocks,
        "safety_validation": {},
        "limitations": ["Heuristic earliest-feasible-start schedule only.", "No real controller timing, PLC, or hardware output."],
    }
    schedule["optimized_summary"] = dict(schedule["summary"])
    schedule["safety_validation"] = validate_optimized_schedule(schedule)
    if not schedule["safety_validation"]["valid"]:
        schedule["optimization_status"] = "REJECTED_SAFETY_REGRESSION"
    if alternative_schedule:
        alternative_validation = validate_optimized_schedule(alternative_schedule)
        weights = profile["objective_weights"]
        def score(item: dict[str, Any]) -> float:
            summary = item["summary"]
            return float(summary["total_schedule_duration_s"]) * float(weights["schedule_duration"]) + float(summary["total_delay_s"]) * float(weights["total_delay"])
        if alternative_validation["valid"] and score(alternative_schedule) < score(schedule):
            alt = dict(alternative_schedule)
            alt_summary = dict(alt["summary"])
            alt_summary.update({"assigned_task_count": len(tasks), "unassigned_task_count": 0})
            baseline_items = {item["task_id"]: item for item in baseline_schedule.get("schedule_items", [])}
            adjustments = []
            for item in alt.get("schedule_items", []):
                baseline = baseline_items.get(item["task_id"])
                if baseline:
                    adjustments.append({"task_id": item["task_id"], "original_start_s": baseline["adjusted_start_s"], "optimized_start_s": item["adjusted_start_s"], "original_end_s": baseline["adjusted_end_s"], "optimized_end_s": item["adjusted_end_s"], "delay_change_s": round(float(item["adjusted_start_s"]) - float(baseline["adjusted_start_s"]), 6), "reason": "selected lower weighted schedule objective", "affected_resource": item.get("delay_reason"), "safety_validated": True})
            return {
                **alt,
                "schedule_version": "stage4.4",
                "optimization_profile_id": profile["profile_id"],
                "optimization_status": "ACCEPTED_WITH_WARNINGS",
                "baseline_summary": baseline_schedule["summary"],
                "summary": alt_summary,
                "optimized_summary": alt_summary,
                "adjustments": adjustments,
                "rejected_adjustments": [{"candidate": "forced_sync_earliest_feasible_start", "reason": "higher weighted schedule objective", "candidate_summary": schedule["summary"]}],
                "safety_validation": alternative_validation,
                "limitations": ["Safety-first weighted selection between valid heuristic schedules.", "No global optimum, PLC, or hardware timing guarantee."],
            }
    return schedule
