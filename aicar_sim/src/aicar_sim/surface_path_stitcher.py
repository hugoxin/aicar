from __future__ import annotations

import math
from typing import Any

from aicar_sim.surface_patch import normalize_vector


def _cartesian_distance(a: dict[str, float], b: dict[str, float]) -> float:
    return math.sqrt(sum((float(b[f"{axis}_mm"]) - float(a[f"{axis}_mm"])) ** 2 for axis in ("x", "y", "z")))


def _lerp_dict(a: dict[str, float], b: dict[str, float], ratio: float, suffix: str = "") -> dict[str, float]:
    return {
        f"{axis}{suffix}": float(a[f"{axis}{suffix}"]) + (float(b[f"{axis}{suffix}"]) - float(a[f"{axis}{suffix}"])) * ratio
        for axis in ("x", "y", "z")
    }


def _interpolate_sample(a: dict[str, Any], b: dict[str, Any], ratio: float) -> dict[str, Any]:
    raw_normal = {
        axis: float(a["normal"][axis]) + (float(b["normal"][axis]) - float(a["normal"][axis])) * ratio
        for axis in ("x", "y", "z")
    }
    if math.sqrt(sum(value * value for value in raw_normal.values())) <= 1e-9:
        raw_normal = dict(a["normal"] if ratio < 0.5 else b["normal"])
    normal = normalize_vector(raw_normal)
    return {
        "patch_id": b.get("patch_id", a.get("patch_id")),
        "zone_id": b.get("zone_id", a.get("zone_id")),
        "u_mm": float(a.get("u_mm", 0)) + (float(b.get("u_mm", 0)) - float(a.get("u_mm", 0))) * ratio,
        "v_mm": float(a.get("v_mm", 0)) + (float(b.get("v_mm", 0)) - float(a.get("v_mm", 0))) * ratio,
        "surface_point": _lerp_dict(a["surface_point"], b["surface_point"], ratio, "_mm"),
        "normal": normal,
        "nozzle_point": _lerp_dict(a["nozzle_point"], b["nozzle_point"], ratio, "_mm"),
        "machine_point": _lerp_dict(a["machine_point"], b["machine_point"], ratio, "_mm"),
        "standoff_mm": float(a["standoff_mm"]) + (float(b["standoff_mm"]) - float(a["standoff_mm"])) * ratio,
        "interpolated": True,
    }


def _polyline_samples(waypoints: list[dict[str, Any]], maximum_spacing_mm: float) -> list[dict[str, Any]]:
    result = [dict(waypoints[0])]
    for start, end in zip(waypoints, waypoints[1:]):
        distance = _cartesian_distance(start["machine_point"], end["machine_point"])
        steps = max(1, int(math.ceil(distance / maximum_spacing_mm)))
        result.extend(_interpolate_sample(start, end, index / steps) for index in range(1, steps + 1))
    return result


def _distance_to_box(point: dict[str, float], bounds: dict[str, float]) -> float:
    values = {axis: float(point[f"{axis}_mm"]) for axis in ("x", "y", "z")}
    distances = {
        axis: max(float(bounds[f"{axis}_min_mm"]) - values[axis], 0.0, values[axis] - float(bounds[f"{axis}_max_mm"]))
        for axis in ("x", "y", "z")
    }
    return math.sqrt(sum(value * value for value in distances.values()))


def _inside(point: dict[str, float], bounds: dict[str, float]) -> bool:
    return all(float(bounds[f"{axis}_min_mm"]) <= float(point[f"{axis}_mm"]) <= float(bounds[f"{axis}_max_mm"]) for axis in ("x", "y", "z"))


def validate_surface_connection(points: list[dict[str, Any]], safety_context: dict[str, Any]) -> tuple[bool, str | None]:
    workspace = safety_context["workspace"]
    safe = safety_context["safe_envelope"]
    minimum = float(safety_context["hard_minimum_clearance_mm"])
    obstacles = safety_context.get("static_obstacles", [])
    for point in points:
        machine = point["machine_point"]
        if not _inside(machine, workspace):
            return False, "connection leaves motion workspace"
        if _distance_to_box(machine, safe) + 1e-6 < minimum:
            return False, "connection violates vehicle hard clearance"
        if any(_inside(machine, item["bounds"]) for item in obstacles):
            return False, "connection enters a static obstacle"
    return True, None


def build_local_pass_connection(
    source_pass: dict[str, Any],
    target_pass: dict[str, Any],
    global_profile: dict[str, Any],
) -> dict[str, Any]:
    start = source_pass["points"][-1]
    end = target_pass["points"][0]
    middle = _interpolate_sample(start, end, 0.5)
    outward = 0.0
    for axis in ("x", "y", "z"):
        middle["nozzle_point"][f"{axis}_mm"] += middle["normal"][axis] * outward
        middle["machine_point"][f"{axis}_mm"] += middle["normal"][axis] * outward
    middle["standoff_mm"] = float(start["standoff_mm"]) + outward
    points = _polyline_samples([start, middle, end], float(global_profile["maximum_point_spacing_mm"]))
    for point in points:
        point["critical_point_type"] = "U_TURN"
        point["scan_pass_id"] = target_pass["scan_pass_id"]
    return {
        "connection_type": "LOCAL_U_TURN",
        "source_patch_id": source_pass["patch_id"],
        "target_patch_id": target_pass["patch_id"],
        "source_scan_pass_id": source_pass["scan_pass_id"],
        "target_scan_pass_id": target_pass["scan_pass_id"],
        "points": points,
        "point_count": len(points),
        "length_mm": round(sum(_cartesian_distance(a["machine_point"], b["machine_point"]) for a, b in zip(points, points[1:])), 3),
        "safety_status": "SAFE_BY_LOCAL_SURFACE_OFFSET",
        "rejection_reason": None,
    }


def _sample_with_machine_point(template: dict[str, Any], machine_point: dict[str, float]) -> dict[str, Any]:
    result = dict(template)
    result["machine_point"] = {key: float(value) for key, value in machine_point.items()}
    hard = 250.0
    normal = result["normal"]
    result["nozzle_point"] = {
        f"{axis}_mm": float(machine_point[f"{axis}_mm"]) - float(normal[axis]) * hard
        for axis in ("x", "y", "z")
    }
    result["surface_point"] = {
        f"{axis}_mm": float(result["nozzle_point"][f"{axis}_mm"]) - float(normal[axis]) * float(result.get("standoff_mm", 350.0))
        for axis in ("x", "y", "z")
    }
    result["interpolated"] = True
    return result


def build_patch_connection(
    start: dict[str, Any],
    end: dict[str, Any],
    source_scan_pass_id: str,
    target_scan_pass_id: str,
    scan_profile: dict[str, Any],
    safety_context: dict[str, Any],
    required_state_transition: bool = False,
) -> dict[str, Any]:
    global_profile = scan_profile["global"]
    policy = scan_profile["connection_policy"]
    maximum_spacing = float(global_profile["maximum_point_spacing_mm"])
    direct_points = _polyline_samples([start, end], maximum_spacing)
    direct_safe, direct_reason = validate_surface_connection(direct_points, safety_context)
    direct_distance = _cartesian_distance(start["machine_point"], end["machine_point"])
    use_direct = direct_safe and direct_distance <= float(policy["maximum_direct_patch_distance_mm"])
    repair_direct_points: list[dict[str, Any]] | None = None
    repair_direct_type: str | None = None
    if (
        not use_direct
        and scan_profile.get("profile_version") == "stage4.5-r"
        and direct_distance <= float(policy["maximum_direct_patch_distance_mm"])
    ):
        safe = safety_context["safe_envelope"]
        safe_z = min(
            float(safety_context["workspace"]["z_max_mm"]),
            float(safe["z_max_mm"])
            + float(global_profile["hard_minimum_clearance_mm"])
            + float(global_profile["connector_clearance_margin_mm"]),
        )
        middle = _interpolate_sample(start, end, 0.5)
        candidates = [
            (
                "TWO_SEGMENT_SAFE_HEIGHT",
                _sample_with_machine_point(
                    middle,
                    {
                        "x_mm": middle["machine_point"]["x_mm"],
                        "y_mm": middle["machine_point"]["y_mm"],
                        "z_mm": max(middle["machine_point"]["z_mm"], safe_z),
                    },
                ),
            ),
            (
                "TWO_SEGMENT_SOURCE_HEIGHT",
                _sample_with_machine_point(
                    middle,
                    {
                        "x_mm": start["machine_point"]["x_mm"],
                        "y_mm": start["machine_point"]["y_mm"],
                        "z_mm": max(start["machine_point"]["z_mm"], safe_z),
                    },
                ),
            ),
            (
                "TWO_SEGMENT_TARGET_HEIGHT",
                _sample_with_machine_point(
                    middle,
                    {
                        "x_mm": end["machine_point"]["x_mm"],
                        "y_mm": end["machine_point"]["y_mm"],
                        "z_mm": max(end["machine_point"]["z_mm"], safe_z),
                    },
                ),
            ),
        ]
        for candidate_type, waypoint in candidates:
            candidate_points = _polyline_samples([start, waypoint, end], maximum_spacing)
            candidate_safe, candidate_reason = validate_surface_connection(candidate_points, safety_context)
            if candidate_safe:
                repair_direct_points = candidate_points
                repair_direct_type = candidate_type
                break
            direct_reason = candidate_reason or direct_reason
        if repair_direct_points is None:
            start_high = _sample_with_machine_point(
                start,
                {
                    "x_mm": start["machine_point"]["x_mm"],
                    "y_mm": start["machine_point"]["y_mm"],
                    "z_mm": max(start["machine_point"]["z_mm"], safe_z),
                },
            )
            end_high = _sample_with_machine_point(
                end,
                {
                    "x_mm": end["machine_point"]["x_mm"],
                    "y_mm": end["machine_point"]["y_mm"],
                    "z_mm": max(end["machine_point"]["z_mm"], safe_z),
                },
            )
            candidate_points = _polyline_samples([start, start_high, end_high, end], maximum_spacing)
            candidate_safe, candidate_reason = validate_surface_connection(candidate_points, safety_context)
            if candidate_safe:
                repair_direct_points = candidate_points
                repair_direct_type = "LOCAL_SAFE_HEIGHT"
            else:
                direct_reason = candidate_reason or direct_reason

    if use_direct:
        points = direct_points
        route_type = "DIRECT_PATCH_CONNECTION"
        chosen_candidate_type = "DIRECT_LINE"
        rejection_reason = None
    elif repair_direct_points is not None:
        points = repair_direct_points
        route_type = "DIRECT_PATCH_CONNECTION"
        chosen_candidate_type = repair_direct_type
        rejection_reason = None
    elif policy.get("fallback_to_safe_transition", True):
        safe = safety_context["safe_envelope"]
        safe_z = min(
            float(safety_context["workspace"]["z_max_mm"]),
            float(safe["z_max_mm"]) + float(global_profile["hard_minimum_clearance_mm"]) + float(global_profile["connector_clearance_margin_mm"]),
        )
        start_high = _sample_with_machine_point(start, {"x_mm": start["machine_point"]["x_mm"], "y_mm": start["machine_point"]["y_mm"], "z_mm": max(start["machine_point"]["z_mm"], safe_z)})
        end_high = _sample_with_machine_point(end, {"x_mm": end["machine_point"]["x_mm"], "y_mm": end["machine_point"]["y_mm"], "z_mm": max(end["machine_point"]["z_mm"], safe_z)})
        points = _polyline_samples([start, start_high, end_high, end], maximum_spacing)
        route_type = "ADAPTIVE_SAFE_CONNECTION"
        chosen_candidate_type = "ADAPTIVE_SAFE_HEIGHT"
        valid, rejection_reason = validate_surface_connection(points, safety_context)
        if not valid:
            route_type = "REJECTED_CONNECTION"
    else:
        points = direct_points
        route_type = "REJECTED_CONNECTION"
        chosen_candidate_type = "REJECTED_DIRECT_LINE"
        rejection_reason = direct_reason or "direct connection rejected and fallback disabled"

    connection_type = "REQUIRED_STATE_TRANSITION" if required_state_transition and route_type != "REJECTED_CONNECTION" else route_type
    if route_type in {"ADAPTIVE_SAFE_CONNECTION", "REJECTED_CONNECTION"}:
        direct_rejection_category = "safety" if not direct_safe else "distance_policy"
    else:
        direct_rejection_category = None
    for point in points:
        point["critical_point_type"] = "STATE_BOUNDARY" if required_state_transition else "PATCH_CONNECTION"
        point["scan_pass_id"] = target_scan_pass_id
    return {
        "connection_type": connection_type,
        "route_type": route_type,
        "direct_rejection_category": direct_rejection_category,
        "chosen_candidate_type": chosen_candidate_type,
        "source_patch_id": start.get("patch_id"),
        "target_patch_id": end.get("patch_id"),
        "source_scan_pass_id": source_scan_pass_id,
        "target_scan_pass_id": target_scan_pass_id,
        "points": points,
        "point_count": len(points),
        "length_mm": round(sum(_cartesian_distance(a["machine_point"], b["machine_point"]) for a, b in zip(points, points[1:])), 3),
        "safety_status": "SAFE" if route_type != "REJECTED_CONNECTION" else "REJECTED",
        "rejection_reason": rejection_reason or (direct_reason if route_type == "ADAPTIVE_SAFE_CONNECTION" else None),
    }


def stitch_scan_passes(scan_passes: list[dict[str, Any]], global_profile: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    path: list[dict[str, Any]] = []
    connections: list[dict[str, Any]] = []
    for index, scan_pass in enumerate(scan_passes):
        if index:
            connection = build_local_pass_connection(scan_passes[index - 1], scan_pass, global_profile)
            connections.append(connection)
            path.extend(connection["points"][1:])
        if not path:
            path.extend(scan_pass["points"])
        else:
            path.extend(scan_pass["points"][1:])
    return path, connections


def stitch_surface_patches(
    patch_paths: list[tuple[list[dict[str, Any]], list[dict[str, Any]]]],
    scan_profile: dict[str, Any],
    safety_context: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    combined: list[dict[str, Any]] = []
    connections: list[dict[str, Any]] = []
    for index, (path, local_connections) in enumerate(patch_paths):
        connections.extend(local_connections)
        if index and path:
            patch_connection = build_patch_connection(
                combined[-1], path[0], combined[-1].get("scan_pass_id", "unknown"), path[0].get("scan_pass_id", "unknown"), scan_profile, safety_context
            )
            connections.append(patch_connection)
            combined.extend(patch_connection["points"][1:])
        combined.extend(path if not combined else path[1:])
    return combined, connections
