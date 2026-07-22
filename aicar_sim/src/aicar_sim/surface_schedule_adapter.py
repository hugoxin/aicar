from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import math
from typing import Any

from aicar_sim.obstacle_model import aabb_intersects
from aicar_sim.shared_space_interlock import detect_deadlock_risk, detect_time_interval_conflicts, resolve_resource_conflicts


MINIMUM_LOCK_DURATION_S = 0.001


def map_relative_interval_to_window(
    relative_start_s: float,
    relative_end_s: float,
    source_span_s: float,
    window_start_s: float,
    window_end_s: float,
) -> dict[str, Any]:
    """Map source-relative occupancy proportionally into a schedule window."""
    try:
        window_start = float(window_start_s)
        window_end = float(window_end_s)
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"invalid schedule window values: start={window_start_s}, end={window_end_s}"
        ) from error
    if not math.isfinite(window_start) or not math.isfinite(window_end) or window_end <= window_start:
        raise ValueError(
            "invalid schedule window for shared-resource mapping: "
            f"start={window_start_s}, end={window_end_s}"
        )
    schedule_span = window_end - window_start

    try:
        relative_start = float(relative_start_s)
        relative_end = float(relative_end_s)
        source_span = float(source_span_s)
    except (TypeError, ValueError):
        relative_start = relative_end = source_span = math.nan

    fallback_reason = None
    if not all(math.isfinite(value) for value in (relative_start, relative_end, source_span)):
        fallback_reason = "source interval or source span is not finite"
    elif source_span <= 0:
        fallback_reason = f"source span is not positive: {source_span}"
    elif relative_end <= relative_start:
        fallback_reason = (
            "source-relative interval is not positive: "
            f"start={relative_start}, end={relative_end}"
        )

    if fallback_reason:
        return {
            "start_s": round(window_start, 6),
            "end_s": round(window_end, 6),
            "interval_mapping_mode": "FULL_WINDOW_FALLBACK",
            "source_span_s": source_span if math.isfinite(source_span) else None,
            "schedule_span_s": schedule_span,
            "source_relative_start_s": relative_start if math.isfinite(relative_start) else None,
            "source_relative_end_s": relative_end if math.isfinite(relative_end) else None,
            "normalized_start": None,
            "normalized_end": None,
            "interval_clamped_to_window": False,
            "fallback_reason": fallback_reason,
        }

    raw_normalized_start = relative_start / source_span
    raw_normalized_end = relative_end / source_span
    normalized_start = min(max(raw_normalized_start, 0.0), 1.0)
    normalized_end = min(max(raw_normalized_end, 0.0), 1.0)
    start = window_start + normalized_start * schedule_span
    end = window_start + normalized_end * schedule_span
    was_clamped = (
        abs(normalized_start - raw_normalized_start) > 1e-12
        or abs(normalized_end - raw_normalized_end) > 1e-12
    )
    if not all(math.isfinite(value) for value in (start, end)) or end - start <= 1e-12:
        return {
            "start_s": round(window_start, 6),
            "end_s": round(window_end, 6),
            "interval_mapping_mode": "FULL_WINDOW_FALLBACK",
            "source_span_s": source_span,
            "schedule_span_s": schedule_span,
            "source_relative_start_s": relative_start,
            "source_relative_end_s": relative_end,
            "normalized_start": normalized_start,
            "normalized_end": normalized_end,
            "interval_clamped_to_window": was_clamped,
            "fallback_reason": "proportional mapping degenerated to a non-positive interval",
        }
    return {
        "start_s": round(start, 6),
        "end_s": round(end, 6),
        "interval_mapping_mode": "PROPORTIONAL_SOURCE_TO_SCHEDULE",
        "source_span_s": source_span,
        "schedule_span_s": schedule_span,
        "source_relative_start_s": relative_start,
        "source_relative_end_s": relative_end,
        "normalized_start": normalized_start,
        "normalized_end": normalized_end,
        "interval_clamped_to_window": was_clamped,
        "fallback_reason": None,
    }


def validate_resource_lock_intervals(
    schedule: list[dict[str, Any]],
    resource_locks: list[dict[str, Any]],
) -> None:
    """Reject inverted, negative-duration, or out-of-window resource locks."""
    windows = {item["task_id"]: (float(item["adjusted_start_s"]), float(item["adjusted_end_s"])) for item in schedule}
    for lock in resource_locks:
        resource_id = lock.get("resource_id")
        task_id = lock.get("task_id")
        if task_id not in windows:
            raise ValueError(
                f"resource lock references an unknown schedule task: resource={resource_id}, task={task_id}"
            )
        try:
            start = float(lock["start_s"])
            end = float(lock["end_s"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"resource lock has invalid time data: resource={resource_id}, task={task_id}, "
                f"start={lock.get('start_s')}, end={lock.get('end_s')}"
            ) from error
        if not math.isfinite(start) or not math.isfinite(end):
            raise ValueError(
                f"resource lock has non-finite time data: resource={resource_id}, task={task_id}, "
                f"start={start}, end={end}"
            )
        if end - start <= 0:
            raise ValueError(
                f"resource lock has a non-positive duration: resource={resource_id}, "
                f"task={task_id}, start={start}, end={end}"
            )
        window_start, window_end = windows[task_id]
        if start < window_start - 1e-6 or end > window_end + 1e-6:
            raise ValueError(
                f"resource lock leaves its schedule window: resource={resource_id}, "
                f"task={task_id}, lock=[{start}, {end}], window=[{window_start}, {window_end}]"
            )
        mode = lock.get("interval_mapping_mode")
        if mode in {"FULL_WINDOW_FALLBACK", "FULL_TASK_RESOURCE"}:
            if abs(start - window_start) > 1e-6 or abs(end - window_end) > 1e-6:
                raise ValueError(
                    f"full-window resource lock does not cover its task window: resource={resource_id}, "
                    f"task={task_id}, lock=[{start}, {end}], window=[{window_start}, {window_end}]"
                )
            if mode == "FULL_WINDOW_FALLBACK" and not lock.get("fallback_reason"):
                raise ValueError(
                    f"fallback resource lock has no reason: resource={resource_id}, task={task_id}, "
                    f"lock=[{start}, {end}]"
                )
        elif mode == "PROPORTIONAL_SOURCE_TO_SCHEDULE":
            try:
                source_span = float(lock["source_span_s"])
                stored_schedule_span = float(lock["schedule_span_s"])
                relative_start = float(lock["source_relative_start_s"])
                relative_end = float(lock["source_relative_end_s"])
                stored_normalized_start = float(lock["normalized_start"])
                stored_normalized_end = float(lock["normalized_end"])
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(
                    f"proportional resource lock has invalid mapping metadata: resource={resource_id}, "
                    f"task={task_id}, lock=[{start}, {end}]"
                ) from error
            schedule_span = window_end - window_start
            if not all(
                math.isfinite(value)
                for value in (
                    source_span,
                    stored_schedule_span,
                    relative_start,
                    relative_end,
                    stored_normalized_start,
                    stored_normalized_end,
                )
            ) or source_span <= 0:
                raise ValueError(
                    f"proportional resource lock has unusable mapping metadata: resource={resource_id}, "
                    f"task={task_id}, source_span={source_span}, schedule_span={stored_schedule_span}"
                )
            normalized_start = min(max(relative_start / source_span, 0.0), 1.0)
            normalized_end = min(max(relative_end / source_span, 0.0), 1.0)
            expected_start = window_start + normalized_start * schedule_span
            expected_end = window_start + normalized_end * schedule_span
            if (
                abs(stored_schedule_span - schedule_span) > 2e-6
                or abs(stored_normalized_start - normalized_start) > 2e-6
                or abs(stored_normalized_end - normalized_end) > 2e-6
            ):
                raise ValueError(
                    f"proportional resource lock metadata is inconsistent: resource={resource_id}, "
                    f"task={task_id}, normalized=[{stored_normalized_start}, {stored_normalized_end}], "
                    f"expected_normalized=[{normalized_start}, {normalized_end}], "
                    f"schedule_span={stored_schedule_span}, expected_schedule_span={schedule_span}"
                )
            if abs(start - expected_start) > 2e-6 or abs(end - expected_end) > 2e-6:
                raise ValueError(
                    f"proportional resource lock is inconsistent with source ratios: resource={resource_id}, "
                    f"task={task_id}, lock=[{start}, {end}], expected=[{expected_start}, {expected_end}], "
                    f"source_relative=[{relative_start}, {relative_end}], source_span={source_span}"
                )
        else:
            raise ValueError(
                f"resource lock has an unknown interval mapping mode: resource={resource_id}, "
                f"task={task_id}, mode={mode}, lock=[{start}, {end}]"
            )


def map_surface_tasks_to_scheduler_input(
    tasks: list[dict[str, Any]],
    swept_volumes: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    """Fold same-state connector tasks into the preceding actuator route task."""
    ordered = sorted(tasks, key=lambda item: (float(item["source_start_s"]), item["task_id"]))
    result: list[dict[str, Any]] = []
    aliases: dict[str, str] = {}
    last_by_actuator: dict[str, dict[str, Any]] = {}
    for source in ordered:
        task = deepcopy(source)
        actuator_id = str(task["assigned_actuator_id"])
        if task.get("segment_type") == "connector" and actuator_id in last_by_actuator:
            target = last_by_actuator[actuator_id]
            target["estimated_duration_s"] = round(
                float(target["estimated_duration_s"]) + float(task["estimated_duration_s"]), 6
            )
            target["source_end_s"] = max(float(target["source_end_s"]), float(task["source_end_s"]))
            target["path_point_end_index"] = max(int(target["path_point_end_index"]), int(task["path_point_end_index"]))
            target["path_point_indices"] = sorted(set(target["path_point_indices"] + task["path_point_indices"]))
            target.setdefault("merged_connector_task_ids", []).append(task["task_id"])
            aliases[task["task_id"]] = target["task_id"]
            continue
        task["merged_connector_task_ids"] = []
        result.append(task)
        last_by_actuator[actuator_id] = task
        aliases[task["task_id"]] = task["task_id"]
    adapted_volumes = []
    for volume in swept_volumes:
        item = deepcopy(volume)
        item["task_id"] = aliases.get(str(item.get("task_id")), str(item.get("task_id")))
        adapted_volumes.append(item)
    return result, adapted_volumes, aliases


def _initial_schedule(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    state_order = []
    for task in sorted(tasks, key=lambda item: (float(item["source_start_s"]), item["task_id"])):
        if task["state_id"] not in state_order:
            state_order.append(task["state_id"])
    state_cursor = 0.0
    schedule = []
    for state_id in state_order:
        state_tasks = [item for item in tasks if item["state_id"] == state_id]
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
                    "source_start_s": float(task["source_start_s"]),
                    "source_end_s": float(task["source_end_s"]),
                    "schedule_status": "PLANNED",
                    "delay_reason": None,
                }
            )
            actuator_cursor[actuator_id] = end
            state_end = max(state_end, end)
        state_cursor = state_end
    return schedule


def calculate_actual_shared_zone_intervals(
    schedule: list[dict[str, Any]],
    swept_volumes: list[dict[str, Any]],
    safety_layout: dict[str, Any],
    trajectory_points: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    point_times = {int(item["sequence_index"]): float(item["timestamp_s"]) for item in trajectory_points}
    shared_zones = {
        item["zone_id"]: item
        for item in safety_layout.get("safety_zones", [])
        if item.get("zone_type") == "shared_interlock"
    }
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for volume in swept_volumes:
        by_task[str(volume.get("task_id"))].append(volume)
    locks = []
    warnings: list[dict[str, Any]] = []
    for item in schedule:
        task_volumes = by_task.get(item["task_id"], [])
        for resource_id in sorted(set(item.get("shared_resources", [])) - set(shared_zones)):
            window_start = float(item["adjusted_start_s"])
            window_end = float(item["adjusted_end_s"])
            locks.append(
                {
                    "resource_id": resource_id,
                    "actuator_id": item["actuator_id"],
                    "task_id": item["task_id"],
                    "start_s": item["adjusted_start_s"],
                    "end_s": item["adjusted_end_s"],
                    "entry_point_index": None,
                    "exit_point_index": None,
                    "interval_source": "full_owned_resource",
                    "interval_mapping_mode": "FULL_TASK_RESOURCE",
                    "source_span_s": float(item["source_end_s"]) - float(item["source_start_s"]),
                    "schedule_span_s": window_end - window_start,
                    "source_relative_start_s": 0.0,
                    "source_relative_end_s": float(item["source_end_s"]) - float(item["source_start_s"]),
                    "normalized_start": 0.0,
                    "normalized_end": 1.0,
                    "interval_clamped_to_window": False,
                    "fallback_reason": None,
                }
            )
        for resource_id, zone in shared_zones.items():
            relevant = [volume for volume in task_volumes if aabb_intersects(volume["bounds"], zone["bounds"])]
            if not relevant:
                continue
            first = min(int(item["start_point_index"]) for item in relevant)
            last = max(int(item["end_point_index"]) for item in relevant)
            source_start = float(item["source_start_s"])
            source_span = float(item["source_end_s"]) - source_start
            relative_start = point_times.get(first, source_start) - source_start
            relative_end = point_times.get(last, source_start) - source_start
            mapping = map_relative_interval_to_window(
                relative_start,
                relative_end,
                source_span,
                float(item["adjusted_start_s"]),
                float(item["adjusted_end_s"]),
            )
            if mapping["interval_mapping_mode"] == "FULL_WINDOW_FALLBACK":
                warnings.append(
                    {
                        "check_id": "shared_interval_full_window_fallback",
                        "severity": "WARNING",
                        "message": (
                            "Shared-zone occupancy could not be mapped reliably; the resource is "
                            "conservatively locked for the full adjusted task window."
                        ),
                        "resource_id": resource_id,
                        "task_id": item["task_id"],
                        "source_relative_start_s": mapping["source_relative_start_s"],
                        "source_relative_end_s": mapping["source_relative_end_s"],
                        "source_span_s": mapping["source_span_s"],
                        "mapped_start_s": mapping["start_s"],
                        "mapped_end_s": mapping["end_s"],
                        "fallback_reason": mapping["fallback_reason"],
                    }
                )
            elif mapping["interval_clamped_to_window"]:
                warnings.append(
                    {
                        "check_id": "shared_interval_clamped_to_source_span",
                        "severity": "WARNING",
                        "message": (
                            "Shared-zone occupancy exceeded the source task span and was clamped before "
                            "proportional mapping into the adjusted schedule window."
                        ),
                        "resource_id": resource_id,
                        "task_id": item["task_id"],
                        "source_relative_start_s": mapping["source_relative_start_s"],
                        "source_relative_end_s": mapping["source_relative_end_s"],
                        "source_span_s": mapping["source_span_s"],
                        "normalized_start": mapping["normalized_start"],
                        "normalized_end": mapping["normalized_end"],
                        "mapped_start_s": mapping["start_s"],
                        "mapped_end_s": mapping["end_s"],
                    }
                )
            locks.append(
                {
                    "resource_id": resource_id,
                    "actuator_id": item["actuator_id"],
                    "task_id": item["task_id"],
                    "start_s": mapping["start_s"],
                    "end_s": mapping["end_s"],
                    "entry_point_index": first,
                    "exit_point_index": last,
                    "interval_source": "actual_shared_zone_swept_interval",
                    "interval_mapping_mode": mapping["interval_mapping_mode"],
                    "source_span_s": mapping["source_span_s"],
                    "schedule_span_s": mapping["schedule_span_s"],
                    "source_relative_start_s": mapping["source_relative_start_s"],
                    "source_relative_end_s": mapping["source_relative_end_s"],
                    "normalized_start": mapping["normalized_start"],
                    "normalized_end": mapping["normalized_end"],
                    "interval_clamped_to_window": mapping["interval_clamped_to_window"],
                    "fallback_reason": mapping["fallback_reason"],
                }
            )
    validate_resource_lock_intervals(schedule, locks)
    return locks, warnings


def build_surface_task_resource_intervals(
    schedule: list[dict[str, Any]],
    swept_volumes: list[dict[str, Any]],
    safety_layout: dict[str, Any],
    trajectory_points: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return calculate_actual_shared_zone_intervals(schedule, swept_volumes, safety_layout, trajectory_points)


def _sync_groups(schedule: list[dict[str, Any]], actuator_system: dict[str, Any]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in schedule:
        if item.get("sync_group_id"):
            groups[str(item["sync_group_id"])].append(item)
    maximum_offset = max(
        [float(item.get("maximum_start_offset_s", 1.0)) for item in actuator_system.get("synchronization_rules", [])]
        or [1.0]
    )
    result = []
    for group_id, items in sorted(groups.items()):
        left = next((item for item in items if item["actuator_id"] == "left_side_actuator"), None)
        right = next((item for item in items if item["actuator_id"] == "right_side_actuator"), None)
        if not left or not right:
            result.append({"sync_group_id": group_id, "sync_status": "NOT_APPLICABLE", "left_task_id": left["task_id"] if left else None, "right_task_id": right["task_id"] if right else None, "start_offset_s": None})
            continue
        offset = abs(float(left["adjusted_start_s"]) - float(right["adjusted_start_s"]))
        delayed = left["schedule_status"] == "DELAYED_BY_INTERLOCK" or right["schedule_status"] == "DELAYED_BY_INTERLOCK"
        status = "SYNCHRONIZED" if offset <= maximum_offset else "BLOCKED_BY_INTERLOCK" if delayed else "DEGRADED"
        result.append({"sync_group_id": group_id, "sync_status": status, "left_task_id": left["task_id"], "right_task_id": right["task_id"], "start_offset_s": round(offset, 6)})
    return result


def validate_surface_schedule_adapter(schedule: dict[str, Any]) -> dict[str, Any]:
    summary = schedule["summary"]
    windows = {
        item["task_id"]: (float(item["adjusted_start_s"]), float(item["adjusted_end_s"]))
        for item in schedule.get("schedule_items", [])
    }
    locks = schedule.get("resource_locks", [])
    checks = {
        "no_unresolved_conflicts": int(summary["unresolved_conflict_count"]) == 0,
        "no_deadlock": int(summary["deadlock_warning_count"]) == 0,
        "positive_duration": float(summary["total_schedule_duration_s"]) > 0,
        "actual_interval_locks": all(item.get("interval_source") for item in locks),
        "lock_durations_positive": all(float(item["end_s"]) - float(item["start_s"]) > 0 for item in locks),
        "locks_within_task_windows": all(
            item["task_id"] in windows
            and windows[item["task_id"]][0] - 1e-6 <= float(item["start_s"])
            and float(item["end_s"]) <= windows[item["task_id"]][1] + 1e-6
            for item in locks
        ),
    }
    return {"validation_status": "PASS" if all(checks.values()) else "FAIL", "checks": checks}


def build_surface_repair_schedule(
    tasks: list[dict[str, Any]],
    actuator_system: dict[str, Any],
    swept_volumes: list[dict[str, Any]],
    safety_layout: dict[str, Any],
    trajectory_points: list[dict[str, Any]],
) -> dict[str, Any]:
    adapted_tasks, adapted_volumes, aliases = map_surface_tasks_to_scheduler_input(tasks, swept_volumes)
    schedule = _initial_schedule(adapted_tasks)
    initial_locks, _ = build_surface_task_resource_intervals(schedule, adapted_volumes, safety_layout, trajectory_points)
    conflicts_before = detect_time_interval_conflicts(initial_locks)
    total_delay = 0.0
    for _ in range(50):
        locks, _ = build_surface_task_resource_intervals(schedule, adapted_volumes, safety_layout, trajectory_points)
        conflicts = detect_time_interval_conflicts(locks)
        if not conflicts:
            break
        schedule, delay = resolve_resource_conflicts(schedule, conflicts)
        total_delay += delay
    resource_locks, interval_warnings = build_surface_task_resource_intervals(
        schedule, adapted_volumes, safety_layout, trajectory_points
    )
    conflicts_after = detect_time_interval_conflicts(resource_locks)
    deadlocks = detect_deadlock_risk(schedule)
    sync_groups = _sync_groups(schedule, actuator_system)
    parallel_pairs = sum(
        1
        for index, left in enumerate(schedule)
        for right in schedule[index + 1 :]
        if left["actuator_id"] != right["actuator_id"]
        and float(left["adjusted_end_s"]) > float(right["adjusted_start_s"])
        and float(right["adjusted_end_s"]) > float(left["adjusted_start_s"])
    )
    result = {
        "schedule_version": "stage4.5-r",
        "actuator_system_id": actuator_system["system_id"],
        "summary": {
            "actuator_count": len(actuator_system.get("actuators", [])),
            "task_count": len(adapted_tasks),
            "parallel_group_count": parallel_pairs,
            "synchronized_group_count": sum(1 for item in sync_groups if item["sync_status"] == "SYNCHRONIZED"),
            "blocked_sync_group_count": sum(1 for item in sync_groups if item["sync_status"] == "BLOCKED_BY_INTERLOCK"),
            "conflict_count_before_resolution": len(conflicts_before),
            "conflict_count_after_resolution": len(conflicts_after),
            "unresolved_conflict_count": len(conflicts_after),
            "total_schedule_duration_s": round(max([float(item["adjusted_end_s"]) for item in schedule] or [0]), 3),
            "total_delay_s": round(total_delay, 3),
            "deadlock_warning_count": len(deadlocks),
            "resource_lock_count": len(resource_locks),
            "interval_mapping_warning_count": len(interval_warnings),
        },
        "actuator_timelines": {
            item["actuator_id"]: [entry for entry in schedule if entry["actuator_id"] == item["actuator_id"]]
            for item in actuator_system.get("actuators", [])
        },
        "schedule_items": schedule,
        "sync_groups": sync_groups,
        "resource_locks": resource_locks,
        "conflicts_before_resolution": conflicts_before,
        "conflicts_after_resolution": conflicts_after,
        "deadlock_warnings": deadlocks,
        "interval_mapping_warnings": interval_warnings,
        "task_aliases": aliases,
        "limitations": [
            "Reference surface-route schedule only.",
            "Shared interlock locks use swept-volume entry and exit intervals.",
            "No real controller timing or PLC communication.",
        ],
    }
    result["adapter_validation"] = validate_surface_schedule_adapter(result)
    return result
