from __future__ import annotations

import copy
import json
import math
from pathlib import Path
from typing import Any

from aicar_sim.continuous_surface_validator import REQUIRED_STATE_ORDER, validate_continuous_surface_path
from aicar_sim.machine_path_planner import build_prepositioned_machine_path_plan
from aicar_sim.surface_coverage import build_surface_grid, calculate_patch_coverage, calculate_zone_coverage, mark_scan_coverage
from aicar_sim.surface_model import all_surface_patches, get_patches_by_zone
from aicar_sim.surface_patch import add_machine_clearance
from aicar_sim.surface_path_stitcher import build_patch_connection, stitch_scan_passes, stitch_surface_patches
from aicar_sim.surface_scan_generator import generate_patch_scan_path


def load_continuous_path_profile(path: str | Path) -> dict[str, Any]:
    profile_path = Path(path)
    if not profile_path.exists():
        raise FileNotFoundError(f"continuous path profile not found: {profile_path}")
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    validate_continuous_path_profile(profile)
    return profile


def validate_continuous_path_profile(profile: dict[str, Any]) -> None:
    global_profile = profile.get("global", {})
    hard = float(global_profile.get("hard_minimum_clearance_mm", 0))
    warning = float(global_profile.get("warning_clearance_mm", 0))
    preferred = float(global_profile.get("preferred_standoff_mm", 0))
    if hard != 250:
        raise ValueError("Stage4.5 hard minimum clearance must remain 250 mm")
    if not hard < warning <= preferred:
        raise ValueError("clearance values must satisfy hard < warning <= preferred")
    if int(global_profile.get("maximum_output_points", 0)) > 5000:
        raise ValueError("maximum_output_points cannot exceed 5000")
    if profile.get("connection_policy", {}).get("allow_cross_state_reordering"):
        raise ValueError("cross-state reordering is not allowed")
    for zone_id, zone_profile in profile.get("zone_profiles", {}).items():
        spacing = zone_profile.get("pass_spacing_mm", zone_profile.get("ring_spacing_mm", 0))
        if float(spacing) <= 0:
            raise ValueError(f"zone {zone_id} requires positive scan spacing")
    coverage = profile.get("coverage", {})
    if not 0 < float(coverage.get("minimum_zone_coverage_percent", 0)) <= 100:
        raise ValueError("minimum_zone_coverage_percent must be in (0, 100]")
    if not 0 < float(coverage.get("minimum_total_coverage_percent", 0)) <= 100:
        raise ValueError("minimum_total_coverage_percent must be in (0, 100]")


def _distance(a: dict[str, Any], b: dict[str, Any], key: str = "nozzle_point") -> float:
    return math.sqrt(sum((float(b[key][f"{axis}_mm"]) - float(a[key][f"{axis}_mm"])) ** 2 for axis in ("x", "y", "z")))


def _workspace_from_inputs(space_model: dict[str, Any], motion_model: dict[str, Any] | None) -> dict[str, float]:
    if motion_model:
        return {key: float(value) for key, value in motion_model["workspace"].items()}
    dimensions = space_model["wash_bay"]["bay_dimensions"]
    return {
        "x_min_mm": -float(dimensions["width_mm"]) / 2,
        "x_max_mm": float(dimensions["width_mm"]) / 2,
        "y_min_mm": -float(dimensions["length_mm"]) / 2,
        "y_max_mm": float(dimensions["length_mm"]) / 2,
        "z_min_mm": 0.0,
        "z_max_mm": float(dimensions["height_mm"]),
    }


def _nozzle_map(nozzle_plan: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return {str(item["zone_id"]): list(item.get("assigned_nozzles", [])) for item in nozzle_plan.get("zone_coverage", [])}


def _choose_nozzle(state_id: str, zone_id: str, timeline_state: dict[str, Any], nozzle_plan: dict[str, Any]) -> dict[str, Any] | None:
    candidates = _nozzle_map(nozzle_plan).get(zone_id, [])
    allowed_ids = set(timeline_state.get("assigned_nozzles", []))
    allowed = [item for item in candidates if item.get("nozzle_id") in allowed_ids]
    preferences = {
        "foam": ["foam_nozzle"],
        "top_clean": ["top_high_pressure"],
        "side_clean": ["side_high_pressure"],
        "wheel_clean": ["wheel_focused_nozzle"],
        "air_dry": ["air_dry_nozzle"],
        "pre_rinse": ["wheel_focused_nozzle"] if zone_id == "wheels" else (["top_high_pressure"] if zone_id == "roof" else ["side_high_pressure", "top_high_pressure"]),
    }.get(state_id, [])
    for nozzle_id in preferences:
        for item in allowed:
            if item.get("nozzle_id") == nozzle_id:
                return item
    return allowed[0] if allowed else None


def _enrich_scan_pass(
    source_pass: dict[str, Any],
    state_id: str,
    nozzle: dict[str, Any],
    hard_clearance: float,
    workspace: dict[str, float],
) -> dict[str, Any]:
    result = copy.deepcopy(source_pass)
    result["scan_pass_id"] = f"{state_id}_{source_pass['scan_pass_id']}"
    result["state_id"] = state_id
    result["nozzle_id"] = nozzle["nozzle_id"]
    result["effective_width_mm"] = float(nozzle["effective_width_mm"])
    points = []
    for point_index, source in enumerate(result["points"]):
        point = add_machine_clearance(source, hard_clearance)
        for axis in ("x", "y", "z"):
            key = f"{axis}_mm"
            point["machine_point"][key] = min(max(float(point["machine_point"][key]), float(workspace[f"{axis}_min_mm"])), float(workspace[f"{axis}_max_mm"]))
        point.update(
            {
                "scan_pass_id": result["scan_pass_id"],
                "state_id": state_id,
                "nozzle_id": nozzle["nozzle_id"],
                "sequence_index": point_index,
                "target_speed_mm_s": 200.0,
            }
        )
        points.append(point)
    result["points"] = points
    result["entry_point"] = points[0]
    result["exit_point"] = points[-1]
    return result


def _apply_semantics(points: list[dict[str, Any]], state_id: str, zone_id: str, nozzle_id: str, segment_id: str) -> list[dict[str, Any]]:
    result = []
    for source in points:
        point = dict(source)
        point.update({"state_id": state_id, "zone_id": zone_id, "nozzle_id": nozzle_id, "segment_id": segment_id})
        result.append(point)
    return result


def _deduplicate(points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for point in points:
        if result and _distance(result[-1], point, "machine_point") < 1e-9:
            continue
        result.append(point)
    return result


def _constrain_connector_for_actuator(
    points: list[dict[str, Any]],
    actuator_id: str | None,
    safety_context: dict[str, Any],
) -> list[dict[str, Any]]:
    actuators = {item["actuator_id"]: item for item in safety_context.get("actuators", [])}
    actuator = actuators.get(actuator_id or "")
    if not actuator:
        return points
    end_effector = actuator["end_effector"]
    half = end_effector.get("carriage_half_size_mm", {})
    expansion_x = max(float(end_effector.get("radius_mm", 0)), float(half.get("x", 0))) + float(safety_context.get("swept_volume_margin_mm", 0)) + 5.0
    x_min = float(safety_context["workspace"]["x_min_mm"])
    x_max = float(safety_context["workspace"]["x_max_mm"])
    for obstacle in safety_context.get("static_obstacles", []):
        bounds = obstacle["bounds"]
        if obstacle.get("obstacle_type") == "wall" and float(bounds["x_max_mm"]) <= 0:
            x_min = max(x_min, float(bounds["x_max_mm"]) + expansion_x)
        if obstacle.get("obstacle_type") == "wall" and float(bounds["x_min_mm"]) >= 0:
            x_max = min(x_max, float(bounds["x_min_mm"]) - expansion_x)
    result = copy.deepcopy(points)
    for point in result:
        point["machine_point"]["x_mm"] = min(max(float(point["machine_point"]["x_mm"]), x_min), x_max)
    return result


def _compact_points(points: list[dict[str, Any]], maximum_spacing_mm: float) -> list[dict[str, Any]]:
    """Remove locally redundant samples without exceeding the configured spacing."""
    if len(points) < 3:
        return points
    preserved_types = {"PASS_START", "PASS_END", "STATE_BOUNDARY", "PATCH_ENTRY", "PATCH_EXIT"}
    result = [points[0]]
    for index in range(1, len(points) - 1):
        current = points[index]
        following = points[index + 1]
        if current.get("critical_point_type") in preserved_types or _distance(result[-1], following, "machine_point") > maximum_spacing_mm + 1e-6:
            result.append(current)
    result.append(points[-1])
    return _deduplicate(result)


def _coverage_summary(
    surface_model: dict[str, Any],
    representative_scans: dict[str, list[dict[str, Any]]],
    representative_widths: dict[str, float],
    scan_profile: dict[str, Any],
) -> dict[str, Any]:
    patch_results = []
    resolution = float(scan_profile["coverage"]["grid_resolution_mm"])
    for patch in all_surface_patches(surface_model):
        patch_id = patch["patch_id"]
        scan_points = [point for scan_pass in representative_scans[patch_id] for point in scan_pass["points"]]
        grid = build_surface_grid(patch, resolution)
        mark_scan_coverage(grid, scan_points, representative_widths[patch_id])
        result = calculate_patch_coverage(grid)
        zone_profile = scan_profile["zone_profiles"][patch["zone_id"]]
        spacing = float(zone_profile.get("pass_spacing_mm", zone_profile.get("ring_spacing_mm", 0)))
        result.update(
            {
                "target_coverage_percent": float(scan_profile["coverage"]["minimum_zone_coverage_percent"]),
                "pass_spacing_mm": spacing,
                "effective_width_mm": representative_widths[patch_id],
                "minimum_pass_overlap_mm": round(max(0.0, representative_widths[patch_id] - spacing), 3),
                "maximum_pass_gap_mm": round(max(0.0, spacing - representative_widths[patch_id]), 3),
            }
        )
        patch_results.append(result)
    summary = calculate_zone_coverage(patch_results)
    summary["minimum_zone_coverage_percent"] = float(scan_profile["coverage"]["minimum_zone_coverage_percent"])
    summary["minimum_total_coverage_percent"] = float(scan_profile["coverage"]["minimum_total_coverage_percent"])
    return summary


def build_continuous_surface_path_plan(
    vehicle_type_result: dict[str, Any],
    wash_strategy_plan: dict[str, Any],
    wash_flow_run: dict[str, Any],
    nozzle_coverage_plan: dict[str, Any],
    space_model_report: dict[str, Any],
    surface_model: dict[str, Any],
    scan_profile: dict[str, Any],
    motion_model: dict[str, Any] | None = None,
    safety_layout: dict[str, Any] | None = None,
    actuator_system: dict[str, Any] | None = None,
    baseline_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    del wash_strategy_plan
    validate_continuous_path_profile(scan_profile)
    timeline = {str(item["state_id"]): item for item in wash_flow_run.get("timeline", [])}
    states = []
    for state_id in REQUIRED_STATE_ORDER:
        source = timeline.get(state_id, {})
        states.append(
            {
                "state_id": state_id,
                "order": len(states) + 1,
                "duration_seconds": source.get("duration_seconds", 0),
                "target_zone_ids": source.get("target_zone_ids", []),
                "has_motion_path": state_id != "dwell",
            }
        )

    global_profile = scan_profile["global"]
    hard_clearance = float(global_profile["hard_minimum_clearance_mm"])
    safety_context = {
        "workspace": _workspace_from_inputs(space_model_report, motion_model),
        "safe_envelope": {key: float(value) for key, value in space_model_report["vehicle_envelope"]["safe_envelope"].items()},
        "hard_minimum_clearance_mm": hard_clearance,
        "static_obstacles": (safety_layout or {}).get("static_obstacles", []),
        "swept_volume_margin_mm": float((safety_layout or {}).get("swept_volume_margin_mm", 0)),
        "actuators": (actuator_system or {}).get("actuators", []),
    }
    all_passes: list[dict[str, Any]] = []
    all_connections: list[dict[str, Any]] = []
    surface_tasks: list[dict[str, Any]] = []
    representative_scans: dict[str, list[dict[str, Any]]] = {}
    representative_widths: dict[str, float] = {}

    for state in states:
        state_id = state["state_id"]
        if state_id == "dwell":
            continue
        timeline_state = timeline.get(state_id, {})
        for zone_id in timeline_state.get("target_zone_ids", []):
            nozzle = _choose_nozzle(state_id, zone_id, timeline_state, nozzle_coverage_plan)
            patches = get_patches_by_zone(surface_model, zone_id)
            if not nozzle or not patches:
                continue
            patch_paths = []
            task_passes = []
            task_connections = []
            for patch in patches:
                generated = [
                    _enrich_scan_pass(item, state_id, nozzle, hard_clearance, safety_context["workspace"])
                    for item in generate_patch_scan_path(patch, scan_profile)
                ]
                if patch["patch_id"] not in representative_scans:
                    representative_scans[patch["patch_id"]] = copy.deepcopy(generated)
                    representative_widths[patch["patch_id"]] = float(nozzle["effective_width_mm"])
                path, local_connections = stitch_scan_passes(generated, global_profile)
                patch_paths.append((path, local_connections))
                task_passes.extend(generated)
            task_path, patch_connections = stitch_surface_patches(patch_paths, scan_profile, safety_context)
            task_connections.extend(patch_connections)
            segment_id = f"continuous_{state_id}_{zone_id}_{len(surface_tasks) + 1:03d}"
            task_path = _apply_semantics(task_path, state_id, zone_id, nozzle["nozzle_id"], segment_id)
            for connection in task_connections:
                connection["connection_id"] = f"connection_{len(all_connections) + 1:04d}"
                connection["state_id"] = state_id
                connection["zone_id"] = zone_id
                all_connections.append(connection)
            all_passes.extend(task_passes)
            surface_tasks.append(
                {
                    "task_id": f"surface_task_{state_id}_{zone_id}",
                    "segment_id": segment_id,
                    "state_id": state_id,
                    "zone_id": zone_id,
                    "nozzle_id": nozzle["nozzle_id"],
                    "media_type": nozzle.get("media_type"),
                    "effective_width_mm": nozzle["effective_width_mm"],
                    "preferred_actuator_id": task_passes[0]["preferred_actuator_id"],
                    "patch_ids": [item["patch_id"] for item in patches],
                    "scan_pass_ids": [item["scan_pass_id"] for item in task_passes],
                    "points": task_path,
                }
            )

    path_segments: list[dict[str, Any]] = []
    previous_task: dict[str, Any] | None = None
    for task in surface_tasks:
        process_points = list(task["points"])
        if previous_task:
            state_changed = previous_task["state_id"] != task["state_id"]
            connector = build_patch_connection(
                previous_task["points"][-1],
                process_points[0],
                previous_task["points"][-1].get("scan_pass_id", "unknown"),
                process_points[0].get("scan_pass_id", "unknown"),
                scan_profile,
                safety_context,
                required_state_transition=state_changed,
            )
            connector["points"] = _constrain_connector_for_actuator(
                connector["points"], previous_task.get("preferred_actuator_id"), safety_context
            )
            connector["point_count"] = len(connector["points"])
            connector["length_mm"] = round(
                sum(_distance(a, b, "machine_point") for a, b in zip(connector["points"], connector["points"][1:])), 3
            )
            connector["connection_id"] = f"connection_{len(all_connections) + 1:04d}"
            connector["state_id"] = task["state_id"]
            connector["zone_id"] = task["zone_id"]
            all_connections.append(connector)
            connection_segment_id = (
                f"state_transition_{previous_task['state_id']}_to_{task['state_id']}"
                if state_changed
                else f"connector_{previous_task['segment_id']}_to_{task['segment_id']}"
            )
            connection_points = _apply_semantics(
                connector["points"], task["state_id"], previous_task["zone_id"], previous_task["nozzle_id"], connection_segment_id
            )
            path_segments.append(
                {
                    "segment_id": connection_segment_id,
                    "state_id": task["state_id"],
                    "zone_id": previous_task["zone_id"],
                    "nozzle_id": previous_task["nozzle_id"],
                    "segment_type": "transition" if state_changed else "connector",
                    "connection_type": "REQUIRED_STATE_TRANSITION" if state_changed else connector["connection_type"],
                    "points": connection_points,
                }
            )
        process_points = _compact_points(process_points, float(global_profile["maximum_point_spacing_mm"]))
        path_segments.append(
            {
                "segment_id": task["segment_id"],
                "state_id": task["state_id"],
                "zone_id": task["zone_id"],
                "nozzle_id": task["nozzle_id"],
                "segment_type": "process",
                "preferred_actuator_id": task["preferred_actuator_id"],
                "patch_ids": task["patch_ids"],
                "points": process_points,
            }
        )
        previous_task = task

    for segment in path_segments:
        segment["points"] = _compact_points(segment["points"], float(global_profile["maximum_point_spacing_mm"]))

    trajectory: list[dict[str, Any]] = []
    for segment in path_segments:
        for point in segment["points"]:
            if trajectory and _distance(trajectory[-1], point, "machine_point") < 1e-9:
                continue
            item = dict(point)
            item["sequence_index"] = len(trajectory)
            trajectory.append(item)
    coverage = _coverage_summary(surface_model, representative_scans, representative_widths, scan_profile)
    source_length = sum(_distance(a, b) for a, b in zip(trajectory, trajectory[1:]))
    connection_counts = {name: sum(1 for item in all_connections if item["connection_type"] == name) for name in ("LOCAL_U_TURN", "DIRECT_PATCH_CONNECTION", "ADAPTIVE_SAFE_CONNECTION", "REQUIRED_STATE_TRANSITION", "REJECTED_CONNECTION")}
    summary = {
        "state_count": len(states),
        "zone_count": len({item["zone_id"] for item in surface_tasks}),
        "surface_patch_count": len(all_surface_patches(surface_model)),
        "scan_pass_count": len(all_passes),
            "surface_path_segment_count": len(path_segments),
        "connection_count": len(all_connections),
        "trajectory_point_count": len(trajectory),
        "path_length_mm": round(source_length, 3),
        "estimated_surface_coverage_percent": coverage["total_coverage_percent"],
        "local_connection_count": connection_counts["LOCAL_U_TURN"],
        "direct_patch_connection_count": connection_counts["DIRECT_PATCH_CONNECTION"],
        "adaptive_safe_connection_count": connection_counts["ADAPTIVE_SAFE_CONNECTION"],
        "required_state_transition_count": connection_counts["REQUIRED_STATE_TRANSITION"],
        "rejected_connection_count": connection_counts["REJECTED_CONNECTION"],
    }
    plan = {
        "plan_version": "stage4.5",
        "surface_model_id": surface_model["surface_model_id"],
        "scan_profile_id": scan_profile["profile_id"],
        "vehicle_type": vehicle_type_result.get("vehicle_type", space_model_report.get("vehicle", {}).get("vehicle_type", "unknown")),
        "wash_profile": wash_flow_run.get("wash_profile", space_model_report.get("wash_profile", "unknown")),
        "summary": summary,
        "states": states,
        "surface_tasks": [{key: value for key, value in item.items() if key != "points"} for item in surface_tasks],
        "scan_passes": all_passes,
        "connections": [{key: value for key, value in item.items() if key != "points"} for item in all_connections],
        "path_segments": path_segments,
        "trajectory_points": trajectory,
        "coverage_summary": coverage,
        "validation": {},
        "warnings": [],
        "limitations": [
            "Reference analytic surface model only; not CAD or point cloud geometry.",
            "Coverage is a local 2D grid approximation and not real cleaning effectiveness.",
            "No real nozzle orientation, actuator dynamics, PLC, servo, SDK, or hardware control is included.",
        ],
    }
    validation = validate_continuous_surface_path(plan, surface_model, scan_profile, baseline_metrics)
    plan["validation"] = validation
    plan["warnings"] = validation["warnings"]
    return plan


def convert_continuous_plan_to_abstract_path_schema(plan: dict[str, Any]) -> dict[str, Any]:
    segments = []
    for segment in plan.get("path_segments", []):
        points = []
        for index, source in enumerate(segment.get("points", [])):
            nozzle = source["nozzle_point"]
            points.append(
                {
                    "point_id": f"{segment['segment_id']}_p{index + 1:04d}",
                    "x_mm": nozzle["x_mm"],
                    "y_mm": nozzle["y_mm"],
                    "z_mm": nozzle["z_mm"],
                    "speed_mm_s": source.get("target_speed_mm_s", 200.0),
                    "machine_point": source["machine_point"],
                    "surface_point": source["surface_point"],
                    "normal": source["normal"],
                    "standoff_mm": source["standoff_mm"],
                    "critical_point_type": source.get("critical_point_type"),
                }
            )
        segments.append({**{key: segment[key] for key in ("segment_id", "state_id", "zone_id", "nozzle_id", "segment_type")}, "points": points})
    return {
        "plan_version": "stage4.5-compatible",
        "vehicle": {"vehicle_type": plan["vehicle_type"], "wash_profile": plan["wash_profile"]},
        "wash_profile": plan["wash_profile"],
        "summary": {"segment_count": len(segments), "point_count": sum(len(item["points"]) for item in segments)},
        "path_segments": segments,
        "limitations": plan["limitations"],
    }


def build_continuous_machine_path_plan(plan: dict[str, Any], motion_model: dict[str, Any]) -> dict[str, Any]:
    return build_prepositioned_machine_path_plan(
        plan["path_segments"],
        motion_model,
        vehicle_type=plan["vehicle_type"],
        wash_profile=plan["wash_profile"],
        source_summary=plan["summary"],
    )
