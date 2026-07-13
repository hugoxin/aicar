from __future__ import annotations

from typing import Any


def build_task_dependencies(tasks: list[dict[str, Any]]) -> dict[str, list[str]]:
    ordered = sorted(tasks, key=lambda item: (float(item.get("source_start_s", 0)), item["task_id"]))
    state_order = []
    for task in ordered:
        if task["state_id"] not in state_order:
            state_order.append(task["state_id"])
    dependencies: dict[str, list[str]] = {task["task_id"]: [] for task in tasks}
    for state_index, state_id in enumerate(state_order[1:], 1):
        previous_ids = [task["task_id"] for task in tasks if task["state_id"] == state_order[state_index - 1]]
        for task in tasks:
            if task["state_id"] == state_id:
                dependencies[task["task_id"]].extend(previous_ids)
    return dependencies


def calculate_task_transition_cost(task_a: dict[str, Any], task_b: dict[str, Any]) -> float:
    return abs(float(task_b.get("source_start_s", 0)) - float(task_a.get("source_end_s", 0)))


def optimize_task_order(tasks: list[dict[str, Any]], dependencies: dict[str, list[str]], constraints: dict[str, Any]) -> list[dict[str, Any]]:
    del dependencies
    if not constraints.get("allow_local_task_swap", True):
        return sorted(tasks, key=lambda item: (float(item.get("source_start_s", 0)), item["task_id"]))
    state_order = []
    for task in sorted(tasks, key=lambda item: float(item.get("source_start_s", 0))):
        if task["state_id"] not in state_order:
            state_order.append(task["state_id"])
    result = []
    for state_id in state_order:
        state_tasks = [task for task in tasks if task["state_id"] == state_id]
        result.extend(sorted(state_tasks, key=lambda item: (float(item.get("source_start_s", 0)), item["assigned_actuator_id"], item["task_id"])))
    return result


def validate_task_order(original_tasks: list[dict[str, Any]], optimized_tasks: list[dict[str, Any]]) -> dict[str, Any]:
    original_ids = {item["task_id"] for item in original_tasks}
    optimized_ids = {item["task_id"] for item in optimized_tasks}
    def states(items: list[dict[str, Any]]) -> list[str]:
        result = []
        for item in items:
            if item["state_id"] not in result:
                result.append(item["state_id"])
        return result
    valid = len(original_tasks) == len(optimized_tasks) and original_ids == optimized_ids and states(original_tasks) == states(optimized_tasks)
    return {"valid": valid, "task_count_unchanged": len(original_tasks) == len(optimized_tasks), "task_id_set_unchanged": original_ids == optimized_ids, "state_order_unchanged": states(original_tasks) == states(optimized_tasks)}
