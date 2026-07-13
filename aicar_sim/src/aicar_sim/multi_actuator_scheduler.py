from __future__ import annotations

from collections import defaultdict
from typing import Any

from aicar_sim.shared_space_interlock import (
    build_resource_lock_intervals,
    detect_deadlock_risk,
    detect_time_interval_conflicts,
    resolve_resource_conflicts,
)


def _initial_schedule(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    state_order = []
    for task in sorted(tasks, key=lambda item: (float(item["source_start_s"]), item["task_id"])):
        if task["state_id"] not in state_order:
            state_order.append(task["state_id"])
    state_cursor = 0.0
    schedule = []
    for state_id in state_order:
        state_tasks = [task for task in tasks if task["state_id"] == state_id]
        actuator_cursor: dict[str, float] = defaultdict(lambda: state_cursor)
        state_end = state_cursor
        for task in sorted(state_tasks, key=lambda item: (float(item["source_start_s"]), item["task_id"])):
            actuator_id = task["assigned_actuator_id"]
            start = actuator_cursor[actuator_id]
            duration = max(0.2, float(task["estimated_duration_s"]))
            end = start + duration
            schedule.append(
                {
                    "schedule_item_id": f"schedule_{task['task_id']}",
                    "task_id": task["task_id"],
                    "actuator_id": actuator_id,
                    "state_id": state_id,
                    "zone_id": task["zone_id"],
                    "planned_start_s": round(start, 6),
                    "planned_end_s": round(end, 6),
                    "adjusted_start_s": round(start, 6),
                    "adjusted_end_s": round(end, 6),
                    "duration_s": round(duration, 6),
                    "shared_resources": task.get("shared_resources", []),
                    "sync_group_id": task.get("sync_group_id"),
                    "schedule_status": "PLANNED",
                    "delay_reason": None,
                }
            )
            actuator_cursor[actuator_id] = end
            state_end = max(state_end, end)
        state_cursor = state_end
    return schedule


def _sync_groups(schedule: list[dict[str, Any]], actuator_system: dict[str, Any]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in schedule:
        if item.get("sync_group_id"):
            groups[item["sync_group_id"]].append(item)
    maximum_offset = max([float(rule.get("maximum_start_offset_s", 1.0)) for rule in actuator_system.get("synchronization_rules", [])] or [1.0])
    result = []
    for group_id, items in sorted(groups.items()):
        left = next((item for item in items if item["actuator_id"] == "left_side_actuator"), None)
        right = next((item for item in items if item["actuator_id"] == "right_side_actuator"), None)
        if not left or not right:
            result.append({"sync_group_id": group_id, "left_task_id": left["task_id"] if left else None, "right_task_id": right["task_id"] if right else None, "start_offset_s": None, "sync_status": "NOT_APPLICABLE", "sync_warning": "Both left and right tasks were not available."})
            continue
        offset = abs(float(left["adjusted_start_s"]) - float(right["adjusted_start_s"]))
        delayed = left.get("schedule_status") == "DELAYED_BY_INTERLOCK" or right.get("schedule_status") == "DELAYED_BY_INTERLOCK"
        status = "SYNCHRONIZED" if offset <= maximum_offset else ("BLOCKED_BY_INTERLOCK" if delayed else "DEGRADED")
        result.append({"sync_group_id": group_id, "left_task_id": left["task_id"], "right_task_id": right["task_id"], "start_offset_s": round(offset, 6), "sync_status": status, "sync_warning": None if status == "SYNCHRONIZED" else "Task-level synchronization was degraded by schedule constraints."})
    return result


def build_multi_actuator_schedule(
    tasks: list[dict[str, Any]],
    actuator_system: dict[str, Any],
    swept_volumes: list[dict[str, Any]],
    safety_layout: dict[str, Any],
) -> dict[str, Any]:
    schedule = _initial_schedule(tasks)
    locks = build_resource_lock_intervals(schedule, swept_volumes, safety_layout)
    conflicts_before = detect_time_interval_conflicts(locks)
    total_delay = 0.0
    for _ in range(50):
        conflicts = detect_time_interval_conflicts(build_resource_lock_intervals(schedule, swept_volumes, safety_layout))
        if not conflicts:
            break
        schedule, delay = resolve_resource_conflicts(schedule, conflicts)
        total_delay += delay
    resource_locks = build_resource_lock_intervals(schedule, swept_volumes, safety_layout)
    conflicts_after = detect_time_interval_conflicts(resource_locks)
    deadlock_warnings = detect_deadlock_risk(schedule)
    sync_groups = _sync_groups(schedule, actuator_system)
    timelines = {
        actuator["actuator_id"]: [item for item in schedule if item["actuator_id"] == actuator["actuator_id"]]
        for actuator in actuator_system.get("actuators", [])
    }
    parallel_pairs = 0
    for index, left in enumerate(schedule):
        for right in schedule[index + 1:]:
            if left["actuator_id"] != right["actuator_id"] and float(left["adjusted_end_s"]) > float(right["adjusted_start_s"]) and float(right["adjusted_end_s"]) > float(left["adjusted_start_s"]):
                parallel_pairs += 1
    return {
        "schedule_version": "stage4.3",
        "actuator_system_id": actuator_system["system_id"],
        "summary": {
            "actuator_count": len(actuator_system.get("actuators", [])),
            "task_count": len(tasks),
            "parallel_group_count": parallel_pairs,
            "synchronized_group_count": len([item for item in sync_groups if item["sync_status"] == "SYNCHRONIZED"]),
            "conflict_count_before_resolution": len(conflicts_before),
            "conflict_count_after_resolution": len(conflicts_after),
            "unresolved_conflict_count": len(conflicts_after),
            "total_schedule_duration_s": round(max([float(item["adjusted_end_s"]) for item in schedule] or [0.0]), 3),
            "total_delay_s": round(total_delay, 3),
            "deadlock_warning_count": len(deadlock_warnings),
        },
        "actuator_timelines": timelines,
        "schedule_items": schedule,
        "sync_groups": sync_groups,
        "resource_locks": resource_locks,
        "conflicts_before_resolution": conflicts_before,
        "conflicts_after_resolution": conflicts_after,
        "deadlock_warnings": deadlock_warnings,
        "limitations": ["Reference multi-actuator schedule only.", "No real controller timing or PLC communication."]
    }
