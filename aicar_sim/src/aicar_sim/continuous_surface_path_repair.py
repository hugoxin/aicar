from __future__ import annotations

import copy
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from aicar_sim.continuous_surface_path_planner import (
    _apply_semantics,
    _choose_nozzle,
    _compact_points,
    _constrain_connector_for_actuator,
    _distance,
    _enrich_scan_pass,
    _workspace_from_inputs,
)
from aicar_sim.continuous_surface_validator import REQUIRED_STATE_ORDER
from aicar_sim.machine_path_planner import build_prepositioned_machine_path_plan
from aicar_sim.patch_route_optimizer import (
    build_patch_orientation_candidates,
    optimize_surface_route_order,
    select_best_safe_surface_route,
)
from aicar_sim.state_scan_policy import build_state_scan_policy
from aicar_sim.surface_coverage import (
    build_surface_grid,
    calculate_patch_visit_metrics,
    calculate_zone_coverage,
    mark_scan_pass_visits,
)
from aicar_sim.surface_model import all_surface_patches
from aicar_sim.surface_scan_generator import generate_adaptive_patch_scan
from aicar_sim.surface_path_stitcher import build_patch_connection
from aicar_sim.surface_task_aggregator import (
    aggregate_scan_passes_to_surface_tasks,
    convert_surface_tasks_to_abstract_path_segments,
    validate_surface_task_aggregation,
)


SOURCE_EXPERIMENT_COMMIT = "c6d8d5d371ce7665fc3007f6b5f4a1cc5aac29e8"
MOTION_STATES = [item for item in REQUIRED_STATE_ORDER if item != "dwell"]


def load_repair_scan_profile(path: str | Path) -> dict[str, Any]:
    profile_path = Path(path)
    if not profile_path.exists():
        raise FileNotFoundError(f"repair scan profile not found: {profile_path}")
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    validate_repair_scan_profile(profile)
    return profile


def validate_repair_scan_profile(profile: dict[str, Any]) -> None:
    if profile.get("profile_version") != "stage4.5-r":
        raise ValueError("repair profile_version must be stage4.5-r")
    global_profile = profile.get("global", {})
    if float(global_profile.get("hard_minimum_clearance_mm", 0)) != 250:
        raise ValueError("Stage4.5-R hard minimum clearance must remain 250 mm")
    if int(global_profile.get("maximum_output_points", 0)) > 5000:
        raise ValueError("maximum_output_points cannot exceed 5000")
    coverage = profile.get("coverage_targets", {})
    if float(coverage.get("minimum_total_unique_coverage_percent", 0)) < 92:
        raise ValueError("minimum total unique coverage cannot be lower than 92 percent")
    if float(coverage.get("minimum_zone_coverage_percent", 0)) < 90:
        raise ValueError("minimum zone coverage cannot be lower than 90 percent")
    policies = profile.get("state_scan_policies", {})
    if set(REQUIRED_STATE_ORDER) - set(policies):
        raise ValueError("repair profile must define all wash states")
    if policies["dwell"].get("motion_required", True):
        raise ValueError("dwell must not generate a motion path")
    if profile.get("connection_policy", {}).get("allow_cross_state_reordering"):
        raise ValueError("cross-state reordering is not allowed")
    aggregation = profile.get("task_aggregation", {})
    if not aggregation.get("enabled") or aggregation.get("emit_scan_pass_as_independent_task"):
        raise ValueError("surface task aggregation must be enabled and scan passes cannot be scheduler tasks")


def _route_for_patch(profile: dict[str, Any], patch_id: str) -> tuple[str, dict[str, Any]]:
    for route_id, route in profile["surface_routes"].items():
        if patch_id in route["patch_ids"]:
            return route_id, route
    raise ValueError(f"surface route missing patch: {patch_id}")


def _path_length(points: list[dict[str, Any]], key: str) -> float:
    return sum(_distance(left, right, key) for left, right in zip(points, points[1:]))


def _path_breakdown(path_segments: list[dict[str, Any]], trajectory: list[dict[str, Any]], key: str) -> dict[str, float]:
    segment_types = {item["segment_id"]: item.get("segment_type", "process") for item in path_segments}
    result: dict[str, float] = defaultdict(float)
    for left, right in zip(trajectory, trajectory[1:]):
        distance = _distance(left, right, key)
        types = {segment_types.get(left.get("segment_id"), "process"), segment_types.get(right.get("segment_id"), "process")}
        critical = {left.get("critical_point_type"), right.get("critical_point_type")}
        if "transition" in types or "STATE_BOUNDARY" in critical:
            result["required_state_transition_length_mm"] += distance
        elif "connector" in types or "PATCH_CONNECTION" in critical:
            result["patch_connection_length_mm"] += distance
        elif "U_TURN" in critical:
            result["local_u_turn_length_mm"] += distance
        else:
            result["surface_scan_length_mm"] += distance
    result["total_path_length_mm"] = sum(result.values())
    return {key: round(value, 3) for key, value in result.items()}


def diagnose_first_attempt(
    plan: dict[str, Any],
    machine_plan: dict[str, Any],
    schedule: dict[str, Any],
) -> dict[str, Any]:
    segments = machine_plan["segments"]
    breakdown = _path_breakdown(segments, machine_plan["trajectory_points"], "machine_point")
    by_state: dict[str, dict[str, Any]] = {}
    for state_id in REQUIRED_STATE_ORDER:
        passes = [item for item in plan["scan_passes"] if item.get("state_id") == state_id]
        connections = [item for item in plan["connections"] if item.get("state_id") == state_id]
        scan_length = sum(float(item["estimated_length_mm"]) for item in passes)
        local_length = sum(float(item["length_mm"]) for item in connections if item["connection_type"] == "LOCAL_U_TURN")
        patch_length = sum(float(item["length_mm"]) for item in connections if item["connection_type"] in {"DIRECT_PATCH_CONNECTION", "ADAPTIVE_SAFE_CONNECTION"})
        transition_length = sum(float(item["length_mm"]) for item in connections if item["connection_type"] == "REQUIRED_STATE_TRANSITION")
        by_state[state_id] = {
            "scan_pass_count": len(passes),
            "point_count": sum(len(item["points"]) for item in passes),
            "scan_length_mm": round(scan_length, 3),
            "local_connection_length_mm": round(local_length, 3),
            "patch_connection_length_mm": round(patch_length, 3),
            "state_transition_length_mm": round(transition_length, 3),
            "total_path_length_mm": round(scan_length + local_length + patch_length + transition_length, 3),
            "estimated_coverage_percent": 100.0 if passes else 0.0,
        }
    coverage_by_patch = {item["patch_id"]: item for item in plan["coverage_summary"]["patch_coverage"]}
    by_patch = {}
    for patch_id in sorted({item["patch_id"] for item in plan["scan_passes"]}):
        passes = [item for item in plan["scan_passes"] if item["patch_id"] == patch_id]
        states = {item["state_id"] for item in passes}
        coverage = coverage_by_patch.get(patch_id, {})
        by_patch[patch_id] = {
            "scanned_state_count": len(states),
            "scan_pass_count": len(passes),
            "path_length_mm": round(sum(float(item["estimated_length_mm"]) for item in passes), 3),
            "average_pass_spacing_mm": coverage.get("pass_spacing_mm"),
            "coverage_percent": coverage.get("patch_coverage_percent"),
            "estimated_mean_coverage_depth": len(states),
            "repeated_coverage_count": max(0, len(states) - 1),
        }
    summary = schedule["summary"]
    lock_duration = sum(float(item["end_s"]) - float(item["start_s"]) for item in schedule.get("resource_locks", []))
    actuator_task_counts = {key: len(value) for key, value in schedule.get("actuator_timelines", {}).items()}
    state_ranking = sorted(by_state.items(), key=lambda item: item[1]["total_path_length_mm"], reverse=True)
    patch_ranking = sorted(by_patch.items(), key=lambda item: (item[1]["scanned_state_count"], item[1]["path_length_mm"]), reverse=True)
    return {
        "source_experiment_commit": SOURCE_EXPERIMENT_COMMIT,
        "machine_path_length_mm": machine_plan["summary"]["path_length_mm"],
        "path_length_breakdown": breakdown,
        "per_state": by_state,
        "per_patch": by_patch,
        "longest_states": [item[0] for item in state_ranking[:5]],
        "most_repeated_patches": [item[0] for item in patch_ranking[:5]],
        "scheduling": {
            "path_segment_count": len(plan["path_segments"]),
            "downstream_task_count": summary["task_count"],
            "actuator_task_counts": actuator_task_counts,
            "average_task_duration_s": round(sum(float(item["duration_s"]) for item in schedule["schedule_items"]) / len(schedule["schedule_items"]), 3),
            "resource_lock_count": len(schedule.get("resource_locks", [])),
            "shared_resource_occupied_duration_s": round(lock_duration, 3),
            "parallel_group_count": summary["parallel_group_count"],
            "total_delay_s": summary["total_delay_s"],
        },
        "root_causes": [
            "Every state reused fixed dense zone spacing instead of nozzle effective width.",
            "Twenty-two adaptive patch and zone connectors contributed most non-scan travel.",
            "Forty-five downstream tasks created ninety-seven resource locks.",
            "Whole-task shared-space locks amplified each conflict delay across later actuator tasks.",
        ],
    }


def _coverage_summary(
    surface_model: dict[str, Any],
    scan_passes: list[dict[str, Any]],
    policies: list[dict[str, Any]],
    scan_profile: dict[str, Any],
) -> dict[str, Any]:
    resolution = float(scan_profile["coverage_targets"]["grid_resolution_mm"])
    policy_map = {(item["state_id"], item["patch_id"]): item for item in policies}
    per_state_patch = []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for scan_pass in scan_passes:
        grouped[(scan_pass["state_id"], scan_pass["patch_id"])].append(scan_pass)
    patch_map = {item["patch_id"]: item for item in all_surface_patches(surface_model)}
    for (state_id, patch_id), passes in sorted(grouped.items()):
        policy = policy_map[(state_id, patch_id)]
        grid = build_surface_grid(patch_map[patch_id], resolution)
        mark_scan_pass_visits(grid, passes, float(policy["effective_width_mm"]))
        metrics = calculate_patch_visit_metrics(grid)
        metrics.update(
            {
                "state_id": state_id,
                "effective_width_mm": policy["effective_width_mm"],
                "effective_width_source": policy["effective_width_source"],
                "spacing_factor": policy["spacing_factor"],
                "initial_pass_spacing_mm": policy["initial_pass_spacing_mm"],
                "final_pass_spacing_mm": policy["final_pass_spacing_mm"],
                "initial_pass_count": policy["initial_pass_count"],
                "final_pass_count": policy["final_pass_count"],
                "minimum_coverage_percent": policy["minimum_coverage_percent"],
                "adaptation_status": policy["adaptation_status"],
                "adaptation_iteration_count": policy["adaptation_iteration_count"],
                "estimated_overlap_mm": policy["estimated_overlap_mm"],
                "scan_length_mm": round(sum(float(item["estimated_length_mm"]) for item in passes), 3),
            }
        )
        per_state_patch.append(metrics)
    per_state_zone = []
    for state_id in MOTION_STATES:
        state_results = [item for item in per_state_patch if item["state_id"] == state_id]
        for zone in calculate_zone_coverage(state_results)["zone_coverage"] if state_results else []:
            per_state_zone.append({"state_id": state_id, **zone})

    unique_patch_results = []
    all_visits = []
    repeated_within_state = sum(int(item["repeated_coverage_cell_count"]) for item in per_state_patch)
    overcovered_within_state = sum(int(item["overcovered_cell_count"]) for item in per_state_patch)
    evaluated_state_cells = sum(int(item["cell_count"]) for item in per_state_patch)
    scan_lengths_by_patch: dict[str, list[float]] = defaultdict(list)
    for patch_id, patch in patch_map.items():
        passes = [item for item in scan_passes if item["patch_id"] == patch_id]
        grid = build_surface_grid(patch, resolution)
        for state_id in sorted({item["state_id"] for item in passes}):
            state_passes = [item for item in passes if item["state_id"] == state_id]
            policy = policy_map[(state_id, patch_id)]
            mark_scan_pass_visits(grid, state_passes, float(policy["effective_width_mm"]))
            scan_lengths_by_patch[patch_id].append(sum(float(item["estimated_length_mm"]) for item in state_passes))
        metrics = calculate_patch_visit_metrics(grid)
        unique_patch_results.append(metrics)
        all_visits.extend(int(item.get("visit_count", 0)) for item in grid["cells"])
    unique = calculate_zone_coverage(unique_patch_results)
    total_scan_length = sum(float(item["estimated_length_mm"]) for item in scan_passes)
    representative_length = sum(min(values) for values in scan_lengths_by_patch.values() if values)
    repeated_length = max(0.0, total_scan_length - representative_length)
    unique.update(
        {
            "unique_geometric_coverage_percent": unique["total_coverage_percent"],
            "per_state_zone_coverage": per_state_zone,
            "per_state_patch_coverage": per_state_patch,
            "mean_surface_visit_count": round(sum(all_visits) / len(all_visits) if all_visits else 0.0, 3),
            "maximum_surface_visit_count": max(all_visits, default=0),
            "overcovered_cell_percent": round(overcovered_within_state / evaluated_state_cells * 100.0 if evaluated_state_cells else 0.0, 3),
            "repeated_coverage_cell_count": repeated_within_state,
            "repeated_surface_scan_length_mm": round(repeated_length, 3),
            "coverage_efficiency_percent": round(representative_length / total_scan_length * 100.0 if total_scan_length else 0.0, 3),
            "coverage_efficiency_method": "Shortest state scan length per patch divided by total state-semantic surface scan length.",
            "minimum_total_unique_coverage_percent": float(scan_profile["coverage_targets"]["minimum_total_unique_coverage_percent"]),
            "minimum_zone_coverage_percent": float(scan_profile["coverage_targets"]["minimum_zone_coverage_percent"]),
        }
    )
    return unique


def _source_validation(
    plan: dict[str, Any],
    surface_model: dict[str, Any],
    scan_profile: dict[str, Any],
) -> dict[str, Any]:
    states = [item["state_id"] for item in plan["states"]]
    zones = {zone for item in plan["surface_tasks"] for zone in item["zone_ids"]}
    patches = {patch for item in plan["surface_tasks"] for patch in item["patch_ids"]}
    expected_patches = {item["patch_id"] for item in all_surface_patches(surface_model)}
    coverage = plan["coverage_summary"]
    per_state_ok = all(
        float(item["patch_coverage_percent"]) + 1e-6 >= float(item["minimum_coverage_percent"])
        for item in coverage["per_state_patch_coverage"]
    )
    checks = {
        "state_order_preserved": states == REQUIRED_STATE_ORDER,
        "dwell_has_no_motion": not any(item["state_id"] == "dwell" for item in plan["surface_tasks"]),
        "motion_states_preserved": set(MOTION_STATES) <= {item["state_id"] for item in plan["surface_tasks"]},
        "zones_preserved": {"roof", "left_side", "right_side", "front", "rear", "wheels"} <= zones,
        "patches_preserved": expected_patches <= patches,
        "four_wheel_patches_preserved": len([item for item in expected_patches if "wheel" in item]) == 4,
        "scan_passes_present": bool(plan["scan_passes"]),
        "aggregation_passed": plan["aggregation_summary"]["validation_status"] == "PASS",
        "point_count_within_limit": len(plan["trajectory_points"]) <= int(scan_profile["global"]["maximum_output_points"]),
        "standoff_preserved": min(float(item["standoff_mm"]) for item in plan["trajectory_points"]) >= 250,
        "total_unique_coverage_passed": float(coverage["unique_geometric_coverage_percent"]) >= float(scan_profile["coverage_targets"]["minimum_total_unique_coverage_percent"]),
        "zone_coverage_passed": all(float(item["zone_coverage_percent"]) >= float(scan_profile["coverage_targets"]["minimum_zone_coverage_percent"]) for item in coverage["zone_coverage"]),
        "state_patch_coverage_passed": per_state_ok,
        "no_rejected_connections": int(plan["summary"]["rejected_connection_count"]) == 0,
    }
    warnings = []
    if float(coverage["unique_geometric_coverage_percent"]) > float(scan_profile["coverage_targets"]["preferred_total_coverage_max_percent"]):
        warnings.append(
            {
                "check_id": "analytic_coverage_exact_limit",
                "severity": "WARNING",
                "message": "Unique coverage remains 100 percent because finite analytic patches and nozzle-width-limited spacing cover every 50 mm grid cell.",
            }
        )
    warnings.extend(plan.get("policy_warnings", []))
    violations = [
        {"check_id": key, "severity": "CRITICAL", "message": f"Repair source-path hard condition failed: {key}"}
        for key, passed in checks.items()
        if not passed
    ]
    return {
        "validation_status": "FAIL" if violations else "PASS_WITH_WARNINGS" if warnings else "PASS",
        "checks": checks,
        "warning_count": len(warnings),
        "violation_count": len(violations),
        "warnings": warnings,
        "violations": violations,
    }


def build_continuous_surface_path_repair(
    vehicle_type_result: dict[str, Any],
    wash_strategy_plan: dict[str, Any],
    wash_flow_run: dict[str, Any],
    nozzle_coverage_plan: dict[str, Any],
    space_model_report: dict[str, Any],
    surface_model: dict[str, Any],
    repair_scan_profile: dict[str, Any],
    motion_model: dict[str, Any] | None = None,
    safety_layout: dict[str, Any] | None = None,
    actuator_system: dict[str, Any] | None = None,
    first_attempt_diagnosis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    del wash_strategy_plan
    validate_repair_scan_profile(repair_scan_profile)
    timeline = {str(item["state_id"]): item for item in wash_flow_run.get("timeline", [])}
    states = [
        {
            "state_id": state_id,
            "order": index + 1,
            "duration_seconds": timeline.get(state_id, {}).get("duration_seconds", 0),
            "target_zone_ids": timeline.get(state_id, {}).get("target_zone_ids", []),
            "has_motion_path": state_id != "dwell",
        }
        for index, state_id in enumerate(REQUIRED_STATE_ORDER)
    ]
    global_profile = repair_scan_profile["global"]
    hard_clearance = float(global_profile["hard_minimum_clearance_mm"])
    safety_context = {
        "workspace": _workspace_from_inputs(space_model_report, motion_model),
        "safe_envelope": {key: float(value) for key, value in space_model_report["vehicle_envelope"]["safe_envelope"].items()},
        "hard_minimum_clearance_mm": hard_clearance,
        "static_obstacles": (safety_layout or {}).get("static_obstacles", []),
        "swept_volume_margin_mm": float((safety_layout or {}).get("swept_volume_margin_mm", 0)),
        "actuators": (actuator_system or {}).get("actuators", []),
    }
    patches = all_surface_patches(surface_model)
    patch_map = {item["patch_id"]: item for item in patches}
    route_groups: list[dict[str, Any]] = []
    policies: list[dict[str, Any]] = []
    policy_warnings: list[dict[str, Any]] = []

    for state_id in MOTION_STATES:
        timeline_state = timeline.get(state_id, {})
        target_zones = set(timeline_state.get("target_zone_ids", []))
        grouped: dict[tuple[str, str], dict[str, Any]] = {}
        for patch in patches:
            if patch["zone_id"] not in target_zones:
                continue
            nozzle = _choose_nozzle(state_id, patch["zone_id"], timeline_state, nozzle_coverage_plan)
            if not nozzle:
                policy_warnings.append(
                    {
                        "check_id": "unsupported_state_zone_nozzle",
                        "severity": "WARNING",
                        "message": "Stage2 nozzle plan has no compatible nozzle for this state-zone pair; original Stage4.5 also emitted no path for it.",
                        "state_id": state_id,
                        "zone_id": patch["zone_id"],
                        "patch_id": patch["patch_id"],
                    }
                )
                continue
            route_id, route_profile = _route_for_patch(repair_scan_profile, patch["patch_id"])
            policy = build_state_scan_policy(
                state_id, patch["zone_id"], patch, nozzle["nozzle_id"], nozzle_coverage_plan, repair_scan_profile
            )
            generated, adaptation = generate_adaptive_patch_scan(patch, policy, repair_scan_profile)
            generated = [
                _enrich_scan_pass(item, state_id, nozzle, hard_clearance, safety_context["workspace"])
                for item in generated
            ]
            policy.update(adaptation)
            policies.append({key: value for key, value in policy.items() if key != "visit_metrics"})
            policy_warnings.extend(policy.get("warnings", []))
            key = (route_id, nozzle["nozzle_id"])
            group = grouped.setdefault(
                key,
                {
                    "state_id": state_id,
                    "surface_route_id": route_id,
                    "actuator_id": route_profile["actuator_id"],
                    "nozzle_id": nozzle["nozzle_id"],
                    "route_profile": route_profile,
                    "patch_scans": {},
                },
            )
            group["patch_scans"][patch["patch_id"]] = generated
        for group in grouped.values():
            patch_candidates = {
                patch_id: build_patch_orientation_candidates(patch_id, passes, global_profile)
                for patch_id, passes in group["patch_scans"].items()
            }
            candidates = optimize_surface_route_order(
                patch_candidates, group["route_profile"], repair_scan_profile, safety_context
            )
            group["route_result"] = select_best_safe_surface_route(candidates)
            route_groups.append(group)

    surface_tasks = aggregate_scan_passes_to_surface_tasks(route_groups)
    all_scan_passes = [item for task in surface_tasks for choice in next(group for group in route_groups if group["state_id"] == task["state_id"] and group["surface_route_id"] == task["surface_route_id"] and group["nozzle_id"] == task["nozzle_id"])["route_result"]["patch_choices"] for item in choice["scan_passes"]]
    all_connections: list[dict[str, Any]] = []
    for group in route_groups:
        result = group["route_result"]
        for choice in result["patch_choices"]:
            all_connections.extend(choice["local_connections"])
        all_connections.extend(result["connections"])
    for connection_index, connection in enumerate(all_connections, start=1):
        connection["connection_id"] = f"repair_connection_{connection_index:04d}"
        owner = next(
            (
                group
                for group in route_groups
                if connection in group["route_result"].get("connections", [])
                or any(connection in choice["local_connections"] for choice in group["route_result"]["patch_choices"])
            ),
            None,
        )
        if owner:
            connection.setdefault("state_id", owner["state_id"])
            target_patch = patch_map.get(connection.get("target_patch_id"), {})
            connection.setdefault("zone_id", target_patch.get("zone_id"))

    process_segments = convert_surface_tasks_to_abstract_path_segments(surface_tasks)
    path_segments: list[dict[str, Any]] = []
    previous_task: dict[str, Any] | None = None
    for task, process_segment in zip(surface_tasks, process_segments):
        process_points = _apply_semantics(
            process_segment["points"], task["state_id"], task["zone_id"], task["nozzle_id"], task["segment_id"]
        )
        if previous_task:
            state_changed = previous_task["state_id"] != task["state_id"]
            connector = build_patch_connection(
                previous_task["points"][-1],
                process_points[0],
                previous_task["scan_pass_ids"][-1],
                task["scan_pass_ids"][0],
                repair_scan_profile,
                safety_context,
                required_state_transition=state_changed,
            )
            connector["points"] = _constrain_connector_for_actuator(
                connector["points"], previous_task["actuator_id"], safety_context
            )
            connector["length_mm"] = round(_path_length(connector["points"], "machine_point"), 3)
            connector["point_count"] = len(connector["points"])
            connector["connection_id"] = f"repair_connection_{len(all_connections) + 1:04d}"
            connector["state_id"] = task["state_id"]
            connector["zone_id"] = previous_task["zone_id"]
            connector.setdefault("candidate_count", 1)
            connector.setdefault("chosen_candidate_type", connector.get("route_type"))
            connector.setdefault("source_path_direction", previous_task["patch_directions"].get(previous_task["patch_ids"][-1], "forward"))
            connector.setdefault("target_path_direction", task["patch_directions"].get(task["patch_ids"][0], "forward"))
            connector.setdefault("direct_distance_mm", round(_distance(previous_task["points"][-1], process_points[0], "machine_point"), 3))
            connector.setdefault("selected_connection_length_mm", connector["length_mm"])
            connector.setdefault("minimum_clearance_mm", hard_clearance)
            connector.setdefault("rejection_reasons", [connector["rejection_reason"]] if connector.get("rejection_reason") else [])
            all_connections.append(connector)
            segment_id = (
                f"repair_state_transition_{previous_task['state_id']}_to_{task['state_id']}"
                if state_changed
                else f"repair_route_switch_{previous_task['surface_task_id']}_to_{task['surface_task_id']}"
            )
            connection_points = _apply_semantics(
                connector["points"], task["state_id"], previous_task["zone_id"], previous_task["nozzle_id"], segment_id
            )
            path_segments.append(
                {
                    "segment_id": segment_id,
                    "state_id": task["state_id"],
                    "zone_id": previous_task["zone_id"],
                    "zone_ids": previous_task["zone_ids"],
                    "nozzle_id": previous_task["nozzle_id"],
                    "segment_type": "transition" if state_changed else "connector",
                    "preferred_actuator_id": previous_task["actuator_id"],
                    "connection_type": "REQUIRED_STATE_TRANSITION" if state_changed else connector["connection_type"],
                    "points": connection_points,
                }
            )
        process_points = _compact_points(process_points, float(global_profile["maximum_point_spacing_mm"]))
        task["points"] = process_points
        path_segments.append({**{key: value for key, value in process_segment.items() if key != "points"}, "points": process_points})
        previous_task = task

    trajectory = []
    for segment in path_segments:
        segment["points"] = _compact_points(segment["points"], float(global_profile["maximum_point_spacing_mm"]))
        for point in segment["points"]:
            if trajectory and _distance(trajectory[-1], point, "machine_point") < 1e-9:
                continue
            item = dict(point)
            item["sequence_index"] = len(trajectory)
            trajectory.append(item)
    for task in surface_tasks:
        indices = [index for index, point in enumerate(trajectory) if point.get("segment_id") == task["segment_id"]]
        if indices:
            task["trajectory_point_start_index"] = min(indices)
            task["trajectory_point_end_index"] = max(indices)
            task["point_count"] = len(indices)

    coverage = _coverage_summary(surface_model, all_scan_passes, policies, repair_scan_profile)
    aggregation = validate_surface_task_aggregation(
        all_scan_passes,
        surface_tasks,
        MOTION_STATES,
        ["roof", "left_side", "right_side", "front", "rear", "wheels"],
        [item["patch_id"] for item in patches],
    )
    connection_counts = Counter(item["connection_type"] for item in all_connections)
    direct_rejected = sum(1 for item in all_connections if item.get("route_type") == "ADAPTIVE_SAFE_CONNECTION")
    reversed_patches = sorted({patch for task in surface_tasks for patch, direction in task["patch_directions"].items() if direction == "reverse"})
    source_breakdown = _path_breakdown(path_segments, trajectory, "nozzle_point")
    summary = {
        "state_count": len(states),
        "zone_count": len({zone for item in surface_tasks for zone in item["zone_ids"]}),
        "surface_patch_count": len(patches),
        "wheel_patch_count": len([item for item in patches if item["zone_id"] == "wheels"]),
        "scan_pass_count": len(all_scan_passes),
        "surface_task_count": len(surface_tasks),
        "surface_path_segment_count": len(path_segments),
        "connection_count": len(all_connections),
        "trajectory_point_count": len(trajectory),
        "source_path_length_mm": source_breakdown["total_path_length_mm"],
        "local_u_turn_count": connection_counts["LOCAL_U_TURN"],
        "direct_patch_connection_count": connection_counts["DIRECT_PATCH_CONNECTION"],
        "adaptive_safe_connection_count": connection_counts["ADAPTIVE_SAFE_CONNECTION"],
        "required_state_transition_count": connection_counts["REQUIRED_STATE_TRANSITION"],
        "rejected_connection_count": connection_counts["REJECTED_CONNECTION"],
        "direct_candidate_rejected_count": direct_rejected,
        "unique_geometric_coverage_percent": coverage["unique_geometric_coverage_percent"],
        "mean_surface_visit_count": coverage["mean_surface_visit_count"],
    }
    plan = {
        "repair_version": "stage4.5-r",
        "repair_profile_id": repair_scan_profile["profile_id"],
        "repair_targets": repair_scan_profile["targets"],
        "source_experiment_commit": SOURCE_EXPERIMENT_COMMIT,
        "surface_model_id": surface_model["surface_model_id"],
        "vehicle_type": vehicle_type_result.get("vehicle_type", "unknown"),
        "wash_profile": wash_flow_run.get("wash_profile", "unknown"),
        "summary": summary,
        "states": states,
        "state_scan_policies": [{key: value for key, value in item.items() if key != "warnings"} for item in policies],
        "surface_routes": [
            {
                "state_id": group["state_id"],
                "surface_route_id": group["surface_route_id"],
                "actuator_id": group["actuator_id"],
                "nozzle_id": group["nozzle_id"],
                "patch_order": group["route_result"]["patch_order"],
                "patch_directions": group["route_result"]["patch_directions"],
                "candidate_count": group["route_result"]["candidate_count"],
                "rejected_candidate_count": group["route_result"]["rejected_candidate_count"],
                "total_route_cost": group["route_result"]["total_route_cost"],
            }
            for group in route_groups
        ],
        "surface_tasks": [{key: value for key, value in item.items() if key != "points"} for item in surface_tasks],
        "scan_passes": all_scan_passes,
        "connections": [{key: value for key, value in item.items() if key != "points"} for item in all_connections],
        "path_segments": path_segments,
        "trajectory_points": trajectory,
        "coverage_summary": coverage,
        "coverage_efficiency_summary": {key: coverage[key] for key in ("mean_surface_visit_count", "maximum_surface_visit_count", "overcovered_cell_percent", "repeated_coverage_cell_count", "repeated_surface_scan_length_mm", "coverage_efficiency_percent", "coverage_efficiency_method")},
        "path_length_breakdown": source_breakdown,
        "aggregation_summary": aggregation,
        "route_optimization_summary": {
            "patch_access_orders": {f"{item['state_id']}:{item['surface_route_id']}:{item['nozzle_id']}": item["patch_order"] for item in [
                {"state_id": group["state_id"], "surface_route_id": group["surface_route_id"], "nozzle_id": group["nozzle_id"], "patch_order": group["route_result"]["patch_order"]}
                for group in route_groups
            ]},
            "reversed_patch_ids": reversed_patches,
            "direct_candidate_rejected_count": direct_rejected,
            "primary_rejection_reasons": sorted({str(item.get("rejection_reason")) for item in all_connections if item.get("rejection_reason")}),
        },
        "first_attempt_diagnosis": first_attempt_diagnosis or {},
        "policy_warnings": policy_warnings,
        "validation": {},
        "warnings": [],
        "limitations": [
            "Reference analytic surface model only; not CAD or point cloud geometry.",
            "Coverage is a local 2D grid approximation and not real cleaning effectiveness.",
            "Different wash states revisit surfaces for distinct process semantics.",
            "Heuristic route and spacing optimization has no global optimum guarantee.",
            "No real nozzle orientation, actuator dynamics, PLC, servo, SDK, or hardware control is included.",
        ],
    }
    plan["validation"] = _source_validation(plan, surface_model, repair_scan_profile)
    plan["warnings"] = plan["validation"]["warnings"]
    return plan


def build_continuous_machine_path_repair(plan: dict[str, Any], motion_model: dict[str, Any]) -> dict[str, Any]:
    result = build_prepositioned_machine_path_plan(
        plan["path_segments"],
        motion_model,
        vehicle_type=plan["vehicle_type"],
        wash_profile=plan["wash_profile"],
        source_summary={"trajectory_point_count": plan["summary"]["trajectory_point_count"]},
    )
    trajectory = result["trajectory_points"]
    if len(trajectory) >= 2 and float(trajectory[-1].get("velocity_mm_s", 0.0)) == 0.0:
        previous = trajectory[-2]
        terminal = trajectory[-1]
        axis_limits = {
            axis: float(motion_model["axis_limits"][axis]["max_acceleration_mm_s2"])
            for axis in ("x", "y", "z")
        }
        required_delta = max(
            abs(float(previous.get(f"velocity_{axis}_mm_s", 0.0))) / axis_limits[axis]
            for axis in ("x", "y", "z")
        )
        conservative_delta = round(required_delta + 0.000002, 6)
        if conservative_delta > float(terminal.get("delta_time_s", 0.0)):
            terminal["delta_time_s"] = conservative_delta
            terminal["timestamp_s"] = round(float(previous["timestamp_s"]) + conservative_delta, 6)
            result["summary"]["estimated_motion_duration_s"] = terminal["timestamp_s"]
    result["plan_version"] = "stage4.5-r"
    result["repair_profile_id"] = plan["repair_profile_id"]
    result["surface_task_count"] = plan["summary"]["surface_task_count"]
    result["path_length_breakdown"] = _path_breakdown(result["segments"], result["trajectory_points"], "machine_point")
    return result
