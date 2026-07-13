from __future__ import annotations

from copy import deepcopy
from typing import Any

from aicar_sim.obstacle_model import aabb_intersects


EPSILON = 1e-6


def _overlap(start_a: float, end_a: float, start_b: float, end_b: float) -> bool:
    return end_a + EPSILON >= start_b and end_b + EPSILON >= start_a


def build_resource_lock_intervals(
    schedule: list[dict[str, Any]],
    swept_volumes: list[dict[str, Any]],
    safety_layout: dict[str, Any],
) -> list[dict[str, Any]]:
    shared_zones = {zone["zone_id"]: zone for zone in safety_layout.get("safety_zones", []) if zone.get("zone_type") == "shared_interlock"}
    volumes_by_task: dict[str, list[dict[str, Any]]] = {}
    for volume in swept_volumes:
        volumes_by_task.setdefault(str(volume.get("task_id")), []).append(volume)
    intervals = []
    for item in schedule:
        resources = set(item.get("shared_resources", []))
        for resource_id, zone in shared_zones.items():
            if any(aabb_intersects(volume["bounds"], zone["bounds"]) for volume in volumes_by_task.get(item["task_id"], [])):
                resources.add(resource_id)
        for resource_id in sorted(resources):
            relevant = [volume for volume in volumes_by_task.get(item["task_id"], []) if resource_id not in shared_zones or aabb_intersects(volume["bounds"], shared_zones[resource_id]["bounds"])]
            intervals.append(
                {
                    "resource_id": resource_id,
                    "actuator_id": item["actuator_id"],
                    "task_id": item["task_id"],
                    "start_s": item["adjusted_start_s"],
                    "end_s": item["adjusted_end_s"],
                    "entry_point_index": relevant[0]["start_point_index"] if relevant else None,
                    "exit_point_index": relevant[-1]["end_point_index"] if relevant else None,
                }
            )
    return intervals


def detect_time_interval_conflicts(lock_intervals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    conflicts = []
    for index, left in enumerate(lock_intervals):
        for right in lock_intervals[index + 1:]:
            if left["resource_id"] != right["resource_id"] or left["actuator_id"] == right["actuator_id"]:
                continue
            if _overlap(float(left["start_s"]), float(left["end_s"]), float(right["start_s"]), float(right["end_s"])):
                conflicts.append(
                    {
                        "conflict_id": f"conflict_{len(conflicts)+1:04d}",
                        "resource_id": left["resource_id"],
                        "task_a_id": left["task_id"],
                        "task_b_id": right["task_id"],
                        "actuator_a_id": left["actuator_id"],
                        "actuator_b_id": right["actuator_id"],
                        "overlap_start_s": max(float(left["start_s"]), float(right["start_s"])),
                        "overlap_end_s": min(float(left["end_s"]), float(right["end_s"])),
                        "severity": "CRITICAL",
                    }
                )
    return conflicts


def resolve_resource_conflicts(
    schedule: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], float]:
    adjusted = deepcopy(schedule)
    by_id = {item["task_id"]: item for item in adjusted}
    total_delay = 0.0
    for conflict in conflicts:
        first = by_id[conflict["task_a_id"]]
        second = by_id[conflict["task_b_id"]]
        delayed = second if float(second["adjusted_start_s"]) >= float(first["adjusted_start_s"]) else first
        blocker = first if delayed is second else second
        new_start = float(blocker["adjusted_end_s"]) + 0.1
        if new_start <= float(delayed["adjusted_start_s"]):
            continue
        original_start = float(delayed["adjusted_start_s"])
        delay = new_start - original_start
        affected = [
            item
            for item in adjusted
            if item["actuator_id"] == delayed["actuator_id"]
            and float(item["adjusted_start_s"]) >= original_start - EPSILON
        ]
        for item in affected:
            item["adjusted_start_s"] = round(float(item["adjusted_start_s"]) + delay, 6)
            item["adjusted_end_s"] = round(float(item["adjusted_end_s"]) + delay, 6)
            item["schedule_status"] = "DELAYED_BY_INTERLOCK"
            item["delay_reason"] = f"resource lock: {conflict['resource_id']}"
        total_delay += delay * len(affected)
    return adjusted, total_delay


def detect_deadlock_risk(schedule: list[dict[str, Any]]) -> list[dict[str, Any]]:
    warnings = []
    for item in schedule:
        if float(item["adjusted_end_s"]) <= float(item["adjusted_start_s"]):
            warnings.append({"check_id": "deadlock", "severity": "CRITICAL", "message": "Task has a non-positive adjusted interval.", "task_id": item["task_id"]})
    return warnings
