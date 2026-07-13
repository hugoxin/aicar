from __future__ import annotations

import math
from typing import Any

from aicar_sim.surface_model import patch_local_bounds
from aicar_sim.surface_patch import make_surface_sample


def _distance(point_a: dict[str, Any], point_b: dict[str, Any]) -> float:
    a = point_a["nozzle_point"]
    b = point_b["nozzle_point"]
    return math.sqrt(sum((float(b[f"{axis}_mm"]) - float(a[f"{axis}_mm"])) ** 2 for axis in ("x", "y", "z")))


def _line_values(start: float, end: float, maximum_spacing: float) -> list[float]:
    distance = abs(end - start)
    steps = max(1, int(math.ceil(distance / maximum_spacing)))
    return [start + (end - start) * index / steps for index in range(steps + 1)]


def _cross_positions(start: float, end: float, spacing: float) -> list[float]:
    span = end - start
    count = max(1, int(math.ceil(span / spacing)))
    return [start + span * (index + 0.5) / count for index in range(count)]


def _mark_pass_points(points: list[dict[str, Any]], pass_id: str) -> list[dict[str, Any]]:
    result = []
    for index, source in enumerate(points):
        point = dict(source)
        point["scan_pass_id"] = pass_id
        point["critical_point_type"] = "PASS_START" if index == 0 else ("PASS_END" if index == len(points) - 1 else "SCAN_POINT")
        point["interpolated"] = index not in {0, len(points) - 1}
        result.append(point)
    return result


def generate_boustrophedon_scan(
    patch: dict[str, Any],
    zone_profile: dict[str, Any],
    global_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    bounds = patch_local_bounds(patch)
    direction = str(zone_profile["scan_direction"])
    spacing = float(zone_profile["pass_spacing_mm"])
    overscan = float(zone_profile.get("overscan_margin_mm", 0))
    maximum_spacing = float(global_profile["maximum_point_spacing_mm"])
    standoff = float(global_profile["preferred_standoff_mm"])

    if direction == "longitudinal" and patch["zone_id"] == "roof":
        primary_axis, cross_axis = "v", "u"
    elif direction == "longitudinal":
        primary_axis, cross_axis = "u", "v"
    elif direction in {"lateral", "horizontal"}:
        primary_axis, cross_axis = "u", "v"
    elif direction == "vertical":
        primary_axis, cross_axis = "v", "u"
    else:
        raise ValueError(f"unsupported scan direction: {direction}")

    primary_min = bounds[f"{primary_axis}_min_mm"] - overscan
    primary_max = bounds[f"{primary_axis}_max_mm"] + overscan
    cross_min = bounds[f"{cross_axis}_min_mm"]
    cross_max = bounds[f"{cross_axis}_max_mm"]
    cross_values = _cross_positions(cross_min, cross_max, spacing)
    passes = []
    for pass_index, cross_value in enumerate(cross_values):
        start, end = (primary_min, primary_max) if pass_index % 2 == 0 else (primary_max, primary_min)
        samples = []
        for primary_value in _line_values(start, end, maximum_spacing):
            u_value = primary_value if primary_axis == "u" else cross_value
            v_value = primary_value if primary_axis == "v" else cross_value
            samples.append(make_surface_sample(patch, u_value, v_value, standoff))
        pass_id = f"{patch['patch_id']}_pass_{pass_index + 1:03d}"
        points = _mark_pass_points(samples, pass_id)
        passes.append(
            {
                "scan_pass_id": pass_id,
                "patch_id": patch["patch_id"],
                "zone_id": patch["zone_id"],
                "pass_index": pass_index,
                "scan_direction": direction,
                "points": points,
                "entry_point": points[0],
                "exit_point": points[-1],
                "estimated_length_mm": round(sum(_distance(a, b) for a, b in zip(points, points[1:])), 3),
                "preferred_actuator_id": zone_profile["preferred_actuator_id"],
            }
        )
    return passes


def generate_wheel_scan(
    patch: dict[str, Any],
    zone_profile: dict[str, Any],
    global_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    radius = float(patch["radius_mm"])
    ring_spacing = float(zone_profile["ring_spacing_mm"])
    angular_step = float(zone_profile["angular_step_deg"])
    standoff = float(global_profile["preferred_standoff_mm"])
    ring_count = max(1, int(math.ceil(radius / ring_spacing)))
    angular_count = max(8, int(math.ceil(360.0 / angular_step)))
    preferred = "left_side_actuator" if float(patch["center"]["x_mm"]) < 0 else "right_side_actuator"
    passes = []
    for pass_index in range(ring_count):
        ring_radius = radius * (pass_index + 0.5) / ring_count
        angles = [360.0 * index / angular_count for index in range(angular_count + 1)]
        if pass_index % 2:
            angles.reverse()
        samples = [
            make_surface_sample(
                patch,
                ring_radius * math.cos(math.radians(angle)),
                ring_radius * math.sin(math.radians(angle)),
                standoff,
            )
            for angle in angles
        ]
        pass_id = f"{patch['patch_id']}_ring_{pass_index + 1:03d}"
        points = _mark_pass_points(samples, pass_id)
        for point in points:
            point["critical_point_type"] = "WHEEL_RING"
        passes.append(
            {
                "scan_pass_id": pass_id,
                "patch_id": patch["patch_id"],
                "zone_id": patch["zone_id"],
                "pass_index": pass_index,
                "scan_direction": "concentric_ring",
                "points": points,
                "entry_point": points[0],
                "exit_point": points[-1],
                "estimated_length_mm": round(sum(_distance(a, b) for a, b in zip(points, points[1:])), 3),
                "preferred_actuator_id": preferred,
            }
        )
    return passes


def generate_patch_scan_path(patch: dict[str, Any], scan_profile: dict[str, Any]) -> list[dict[str, Any]]:
    zone_profile = scan_profile["zone_profiles"][patch["zone_id"]]
    if zone_profile["scan_pattern"] == "boustrophedon":
        return generate_boustrophedon_scan(patch, zone_profile, scan_profile["global"])
    if zone_profile["scan_pattern"] == "concentric_rings":
        return generate_wheel_scan(patch, zone_profile, scan_profile["global"])
    raise ValueError(f"unsupported scan pattern: {zone_profile['scan_pattern']}")
