from __future__ import annotations

import copy
import itertools
import math
from typing import Any

from aicar_sim.obstacle_model import aabb_intersects
from aicar_sim.surface_path_stitcher import build_patch_connection, stitch_scan_passes
from aicar_sim.swept_volume import build_swept_aabb


def _distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    return math.sqrt(
        sum(
            (float(b["machine_point"][f"{axis}_mm"]) - float(a["machine_point"][f"{axis}_mm"])) ** 2
            for axis in ("x", "y", "z")
        )
    )


def _reverse_scan_pass(scan_pass: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(scan_pass)
    result["points"] = list(reversed(result["points"]))
    for index, point in enumerate(result["points"]):
        point["sequence_index"] = index
        point["critical_point_type"] = (
            "PASS_START" if index == 0 else "PASS_END" if index == len(result["points"]) - 1 else point.get("critical_point_type", "SCAN_POINT")
        )
    result["entry_point"] = result["points"][0]
    result["exit_point"] = result["points"][-1]
    return result


def build_patch_orientation_candidates(
    patch_id: str,
    scan_passes: list[dict[str, Any]],
    global_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    candidates = []
    for direction, passes in (
        ("forward", copy.deepcopy(scan_passes)),
        ("reverse", [_reverse_scan_pass(item) for item in reversed(scan_passes)]),
    ):
        path, local_connections = stitch_scan_passes(passes, global_profile)
        candidates.append(
            {
                "patch_id": patch_id,
                "path_direction": direction,
                "scan_passes": passes,
                "path": path,
                "local_connections": local_connections,
                "scan_length_mm": round(sum(float(item["estimated_length_mm"]) for item in passes), 3),
                "local_connection_length_mm": round(sum(float(item["length_mm"]) for item in local_connections), 3),
            }
        )
    return candidates


def calculate_patch_connection_cost(connection: dict[str, Any]) -> float:
    safety_penalty = 1_000_000_000.0 if connection.get("safety_status") == "REJECTED" else 0.0
    adaptive_penalty = 5000.0 if connection.get("route_type") == "ADAPTIVE_SAFE_CONNECTION" else 0.0
    return safety_penalty + adaptive_penalty + float(connection.get("length_mm", 0))


def validate_route_candidate(
    candidate: dict[str, Any],
    actuator_id: str,
    safety_context: dict[str, Any],
) -> tuple[bool, list[str]]:
    reasons = [
        str(item.get("rejection_reason") or "connection rejected")
        for item in candidate.get("connections", [])
        if item.get("safety_status") == "REJECTED"
    ]
    if not candidate.get("path"):
        reasons.append("route has no path points")
    actuator = next(
        (item for item in safety_context.get("actuators", []) if item.get("actuator_id") == actuator_id),
        None,
    )
    if not actuator:
        reasons.append(f"route actuator definition missing: {actuator_id}")
    else:
        margin = float(safety_context.get("swept_volume_margin_mm", 0))
        safe_envelope = safety_context["safe_envelope"]
        obstacles = safety_context.get("static_obstacles", [])
        for connection in candidate.get("connections", []):
            for left, right in zip(connection.get("points", []), connection.get("points", [])[1:]):
                swept = build_swept_aabb(
                    left["machine_point"], right["machine_point"], actuator["end_effector"], margin
                )
                if aabb_intersects(swept, safe_envelope):
                    reasons.append("connection swept AABB intersects vehicle safe envelope")
                    break
                obstacle = next(
                    (item for item in obstacles if aabb_intersects(swept, item["bounds"])),
                    None,
                )
                if obstacle:
                    reasons.append(
                        f"connection swept AABB intersects static obstacle {obstacle['obstacle_id']}"
                    )
                    break
    return not reasons, reasons


def optimize_surface_route_order(
    patch_candidates: dict[str, list[dict[str, Any]]],
    route_profile: dict[str, Any],
    scan_profile: dict[str, Any],
    safety_context: dict[str, Any],
) -> list[dict[str, Any]]:
    configured = [item for item in route_profile["patch_ids"] if item in patch_candidates]
    orders = list(itertools.permutations(configured)) if len(configured) > 1 else [tuple(configured)]
    maximum = int(scan_profile["connection_policy"].get("maximum_direct_connection_candidates", 30))
    candidates = []
    for order in orders:
        option_sets = [patch_candidates[patch_id] for patch_id in order]
        for orientations in itertools.product(*option_sets):
            path = []
            connections = []
            for index, patch_choice in enumerate(orientations):
                if index:
                    previous = orientations[index - 1]
                    connection = build_patch_connection(
                        previous["path"][-1],
                        patch_choice["path"][0],
                        previous["scan_passes"][-1]["scan_pass_id"],
                        patch_choice["scan_passes"][0]["scan_pass_id"],
                        scan_profile,
                        safety_context,
                    )
                    connection.update(
                        {
                            "candidate_count": 1,
                            "chosen_candidate_type": connection.get("chosen_candidate_type", connection.get("route_type")),
                            "source_path_direction": previous["path_direction"],
                            "target_path_direction": patch_choice["path_direction"],
                            "direct_distance_mm": round(_distance(previous["path"][-1], patch_choice["path"][0]), 3),
                            "selected_connection_length_mm": float(connection["length_mm"]),
                            "minimum_clearance_mm": float(scan_profile["global"]["hard_minimum_clearance_mm"]),
                            "rejection_reasons": [connection["rejection_reason"]] if connection.get("rejection_reason") else [],
                        }
                    )
                    connections.append(connection)
                    path.extend(connection["points"][1:])
                path.extend(patch_choice["path"] if not path else patch_choice["path"][1:])
            candidate = {
                "patch_order": list(order),
                "patch_directions": {item["patch_id"]: item["path_direction"] for item in orientations},
                "patch_choices": list(orientations),
                "path": path,
                "connections": connections,
                "scan_length_mm": round(sum(item["scan_length_mm"] for item in orientations), 3),
                "local_connection_length_mm": round(sum(item["local_connection_length_mm"] for item in orientations), 3),
                "patch_connection_length_mm": round(sum(float(item["length_mm"]) for item in connections), 3),
            }
            safe, reasons = validate_route_candidate(
                candidate, route_profile["actuator_id"], safety_context
            )
            candidate["safe"] = safe
            candidate["rejection_reasons"] = reasons
            candidate["total_route_cost"] = round(
                candidate["scan_length_mm"]
                + candidate["local_connection_length_mm"]
                + sum(calculate_patch_connection_cost(item) for item in connections),
                3,
            )
            candidates.append(candidate)
            if len(candidates) >= maximum:
                return candidates
    return candidates


def select_best_safe_surface_route(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    safe = [item for item in candidates if item.get("safe")]
    if not safe:
        reasons = sorted({reason for item in candidates for reason in item.get("rejection_reasons", [])})
        raise ValueError("no safe surface route candidate: " + "; ".join(reasons))
    selected = min(safe, key=lambda item: (float(item["total_route_cost"]), item["patch_order"]))
    selected = copy.deepcopy(selected)
    selected["candidate_count"] = len(candidates)
    selected["rejected_candidate_count"] = len(candidates) - len(safe)
    return selected
