from __future__ import annotations

import math
from typing import Any


def _path_length(points: list[dict[str, Any]], key: str = "machine_point") -> float:
    return sum(
        math.sqrt(
            sum(
                (float(right[key][f"{axis}_mm"]) - float(left[key][f"{axis}_mm"])) ** 2
                for axis in ("x", "y", "z")
            )
        )
        for left, right in zip(points, points[1:])
    )


def build_surface_route_task(
    state_id: str,
    surface_route_id: str,
    actuator_id: str,
    nozzle_id: str,
    route_result: dict[str, Any],
    sequence: int,
) -> dict[str, Any]:
    scan_passes = [item for choice in route_result["patch_choices"] for item in choice["scan_passes"]]
    local_connections = [item for choice in route_result["patch_choices"] for item in choice["local_connections"]]
    patch_connections = route_result["connections"]
    points = route_result["path"]
    zones = list(dict.fromkeys(item["zone_id"] for item in scan_passes))
    scan_length = sum(float(item["estimated_length_mm"]) for item in scan_passes)
    connection_length = sum(float(item["length_mm"]) for item in local_connections + patch_connections)
    surface_task_id = f"surface_route_task_{sequence:03d}_{state_id}_{surface_route_id}_{nozzle_id}"
    return {
        "surface_task_id": surface_task_id,
        "segment_id": surface_task_id,
        "state_id": state_id,
        "surface_route_id": surface_route_id,
        "actuator_id": actuator_id,
        "preferred_actuator_id": actuator_id,
        "nozzle_id": nozzle_id,
        "zone_id": zones[0],
        "zone_ids": zones,
        "patch_ids": route_result["patch_order"],
        "patch_directions": route_result["patch_directions"],
        "scan_pass_ids": [item["scan_pass_id"] for item in scan_passes],
        "connection_ids": [item.get("connection_id") for item in local_connections + patch_connections],
        "trajectory_point_start_index": None,
        "trajectory_point_end_index": None,
        "point_count": len(points),
        "scan_length_mm": round(scan_length, 3),
        "connection_length_mm": round(connection_length, 3),
        "total_length_mm": round(_path_length(points), 3),
        "estimated_duration_s": round(_path_length(points) / 200.0, 3),
        "shared_resources": [],
        "task_semantics": {
            "state_id": state_id,
            "zone_ids": zones,
            "patch_ids": route_result["patch_order"],
            "nozzle_id": nozzle_id,
            "actuator_id": actuator_id,
        },
        "aggregation_reason": "Grouped scan passes by state, surface route, actuator, and nozzle.",
        "candidate_count": route_result.get("candidate_count", 1),
        "rejected_candidate_count": route_result.get("rejected_candidate_count", 0),
        "points": points,
    }


def aggregate_scan_passes_to_surface_tasks(route_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tasks = []
    for index, group in enumerate(route_groups, start=1):
        tasks.append(
            build_surface_route_task(
                group["state_id"],
                group["surface_route_id"],
                group["actuator_id"],
                group["nozzle_id"],
                group["route_result"],
                index,
            )
        )
    return tasks


def validate_surface_task_aggregation(
    scan_passes: list[dict[str, Any]],
    surface_tasks: list[dict[str, Any]],
    required_states: list[str],
    required_zones: list[str],
    required_patches: list[str],
) -> dict[str, Any]:
    source_ids = {item["scan_pass_id"] for item in scan_passes}
    aggregated_ids = [item for task in surface_tasks for item in task["scan_pass_ids"]]
    task_states = {item["state_id"] for item in surface_tasks}
    task_zones = {zone for item in surface_tasks for zone in item["zone_ids"]}
    task_patches = {patch for item in surface_tasks for patch in item["patch_ids"]}
    checks = {
        "scan_pass_ids_preserved": source_ids == set(aggregated_ids) and len(aggregated_ids) == len(source_ids),
        "motion_states_preserved": set(required_states) <= task_states,
        "zones_preserved": set(required_zones) <= task_zones,
        "patches_preserved": set(required_patches) <= task_patches,
        "tasks_nonempty": bool(surface_tasks) and all(item["point_count"] > 0 for item in surface_tasks),
        "durations_nonnegative": all(item["estimated_duration_s"] >= 0 for item in surface_tasks),
        "task_count_reduced": len(surface_tasks) < len(scan_passes),
    }
    return {
        "validation_status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "source_scan_pass_count": len(scan_passes),
        "aggregated_surface_task_count": len(surface_tasks),
        "missing_scan_pass_ids": sorted(source_ids - set(aggregated_ids)),
        "duplicate_scan_pass_count": len(aggregated_ids) - len(set(aggregated_ids)),
    }


def convert_surface_tasks_to_abstract_path_segments(surface_tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "segment_id": task["segment_id"],
            "state_id": task["state_id"],
            "zone_id": task["zone_id"],
            "zone_ids": task["zone_ids"],
            "nozzle_id": task["nozzle_id"],
            "segment_type": "process",
            "preferred_actuator_id": task["actuator_id"],
            "surface_route_id": task["surface_route_id"],
            "patch_ids": task["patch_ids"],
            "scan_pass_ids": task["scan_pass_ids"],
            "points": task["points"],
        }
        for task in surface_tasks
    ]
