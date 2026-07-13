from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_actuator_system(path: str | Path) -> dict[str, Any]:
    system_path = Path(path)
    if not system_path.exists():
        raise FileNotFoundError(f"actuator system not found: {system_path}")
    system = json.loads(system_path.read_text(encoding="utf-8"))
    validate_actuator_system(system)
    return system


def validate_actuator_system(system: dict[str, Any]) -> None:
    if not system.get("system_id"):
        raise ValueError("actuator system requires system_id")
    resource_ids = {item.get("resource_id") for item in system.get("resources", [])}
    if None in resource_ids:
        raise ValueError("every resource requires resource_id")
    actuator_ids: set[str] = set()
    for actuator in system.get("actuators", []):
        actuator_id = actuator.get("actuator_id")
        if not actuator_id:
            raise ValueError("every actuator requires actuator_id")
        if actuator_id in actuator_ids:
            raise ValueError(f"duplicate actuator_id: {actuator_id}")
        actuator_ids.add(actuator_id)
        if not actuator.get("allowed_zones"):
            raise ValueError(f"actuator {actuator_id} requires allowed_zones")
        missing_resources = set(actuator.get("shared_resources", [])) - resource_ids
        if missing_resources:
            raise ValueError(f"actuator {actuator_id} references unknown resources: {', '.join(sorted(missing_resources))}")
    for rule in system.get("synchronization_rules", []):
        missing = set(rule.get("actuator_ids", [])) - actuator_ids
        if missing:
            raise ValueError(f"sync rule references unknown actuators: {', '.join(sorted(missing))}")
        if rule.get("mode") not in {"preferred_parallel"}:
            raise ValueError(f"unsupported synchronization mode: {rule.get('mode')}")
    for rule in system.get("interlock_rules", []):
        if rule.get("resource_id") not in resource_ids:
            raise ValueError(f"interlock rule references unknown resource: {rule.get('resource_id')}")


def _actuator_map(system: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["actuator_id"]: item for item in system.get("actuators", [])}


def _choose_actuator(zone_id: str, points: list[dict[str, Any]], system: dict[str, Any]) -> tuple[str | None, str]:
    actuators = _actuator_map(system)
    preferred = {
        "roof": "top_actuator",
        "left_side": "left_side_actuator",
        "right_side": "right_side_actuator",
    }.get(zone_id)
    if zone_id == "wheels" and points:
        average_x = sum(float(point["x_mm"]) for point in points) / len(points)
        preferred = "left_side_actuator" if average_x < 0 else "right_side_actuator"
    if zone_id in {"front", "rear"} and points:
        average_x = sum(float(point["x_mm"]) for point in points) / len(points)
        preferred = "top_actuator" if abs(average_x) < 500 else ("left_side_actuator" if average_x < 0 else "right_side_actuator")
    if preferred in actuators and zone_id in actuators[preferred].get("allowed_zones", []):
        return preferred, f"preferred mapping for {zone_id}"
    allowed = [item["actuator_id"] for item in system.get("actuators", []) if zone_id in item.get("allowed_zones", [])]
    if len(allowed) == 1:
        return allowed[0], f"only allowed actuator for {zone_id}"
    return None, f"no deterministic actuator mapping for {zone_id}"


def _task_from_points(
    segment: dict[str, Any],
    points: list[dict[str, Any]],
    point_indices: list[int],
    actuator_system: dict[str, Any],
    task_suffix: str = "",
) -> dict[str, Any] | None:
    if not points:
        return None
    actuator_id, reason = _choose_actuator(str(segment["zone_id"]), points, actuator_system)
    actuators = _actuator_map(actuator_system)
    allowed = [item["actuator_id"] for item in actuator_system.get("actuators", []) if segment["zone_id"] in item.get("allowed_zones", [])]
    actuator = actuators.get(actuator_id or "", {})
    start_time = min(float(point["timestamp_s"]) for point in points)
    end_time = max(float(point["timestamp_s"]) for point in points)
    state_id = str(segment["state_id"])
    zone_id = str(segment["zone_id"])
    requires_sync = (
        segment.get("segment_type") == "process"
        and state_id in {"side_clean", "air_dry"}
        and zone_id in {"left_side", "right_side"}
    )
    # Rail locks are always held by their owning actuator. Shared-space locks
    # are added later from the task's actual swept-volume intersection.
    resources = [
        resource_id
        for resource_id in actuator.get("shared_resources", [])
        if resource_id not in {"center_shared_space", "front_rear_crossing"}
    ]
    if zone_id in {"front", "rear"} and "front_rear_crossing" not in resources:
        resources.append("front_rear_crossing")
    return {
        "task_id": f"task_{segment['segment_id']}{task_suffix}",
        "source_segment_id": segment["segment_id"],
        "segment_type": segment.get("segment_type", "process"),
        "state_id": state_id,
        "zone_id": zone_id,
        "nozzle_id": segment["nozzle_id"],
        "assigned_actuator_id": actuator_id,
        "preferred_actuator_id": actuator_id,
        "allowed_actuator_ids": allowed,
        "estimated_duration_s": max(0.2, end_time - start_time),
        "source_start_s": start_time,
        "source_end_s": end_time,
        "path_point_start_index": min(point_indices),
        "path_point_end_index": max(point_indices),
        "path_point_indices": point_indices,
        "shared_resources": resources,
        "assignment_reason": reason,
        "requires_sync": requires_sync,
        "sync_group_id": f"{state_id}_left_right" if requires_sync else None,
    }


def allocate_segments_to_actuators(
    machine_path_plan: dict[str, Any],
    actuator_system: dict[str, Any],
) -> dict[str, Any]:
    validate_actuator_system(actuator_system)
    trajectory = machine_path_plan.get("trajectory_points", [])
    tasks = []
    unassigned = []
    for segment in machine_path_plan.get("segments", []):
        start = int(segment["point_start_index"])
        end = min(int(segment["point_end_index"]), len(trajectory) - 1)
        indices = list(range(start, end + 1))
        points = [trajectory[index] for index in indices]
        task_items = []
        if segment.get("zone_id") == "wheels" and segment.get("segment_type") == "process":
            for side, predicate in (("left", lambda p: float(p["x_mm"]) < 0), ("right", lambda p: float(p["x_mm"]) >= 0)):
                selected = [(index, trajectory[index]) for index in indices if predicate(trajectory[index])]
                if selected:
                    task_items.append(_task_from_points(segment, [item[1] for item in selected], [item[0] for item in selected], actuator_system, f"_{side}"))
        else:
            task_items.append(_task_from_points(segment, points, indices, actuator_system))
        for task in [item for item in task_items if item]:
            if task["assigned_actuator_id"]:
                tasks.append(task)
            else:
                unassigned.append(task)
    return {"tasks": tasks, "unassigned_tasks": unassigned}


def validate_task_assignment(tasks: list[dict[str, Any]], actuator_system: dict[str, Any]) -> list[dict[str, Any]]:
    actuators = _actuator_map(actuator_system)
    issues = []
    for task in tasks:
        actuator_id = task.get("assigned_actuator_id")
        if actuator_id not in actuators:
            issues.append({"check_id": "task_assignment", "severity": "CRITICAL", "message": "Task has no valid assigned actuator.", "task_id": task.get("task_id")})
        elif task.get("zone_id") not in actuators[actuator_id].get("allowed_zones", []):
            issues.append({"check_id": "task_assignment", "severity": "CRITICAL", "message": "Assigned actuator is not allowed for the task zone.", "task_id": task.get("task_id"), "actuator_id": actuator_id})
    return issues
