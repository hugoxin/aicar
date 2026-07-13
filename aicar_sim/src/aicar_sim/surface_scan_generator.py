from __future__ import annotations

import math
from typing import Any

from aicar_sim.surface_model import patch_local_bounds
from aicar_sim.surface_patch import make_surface_sample
from aicar_sim.surface_coverage import build_surface_grid, calculate_patch_visit_metrics, mark_scan_pass_visits


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


def generate_adaptive_patch_scan(
    patch: dict[str, Any],
    state_policy: dict[str, Any],
    scan_profile: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Find the sparsest configured scan that still meets state coverage."""
    if not state_policy.get("motion_required", True):
        return [], {
            "initial_pass_spacing_mm": 0.0,
            "final_pass_spacing_mm": 0.0,
            "initial_pass_count": 0,
            "final_pass_count": 0,
            "coverage_percent": 0.0,
            "adaptation_iteration_count": 0,
            "adaptation_status": "NO_MOTION_REQUIRED",
            "effective_width_mm": 0.0,
            "estimated_overlap_mm": 0.0,
            "overcoverage_warning": False,
        }
    spacing = float(state_policy["initial_pass_spacing_mm"])
    initial_spacing = spacing
    width = float(state_policy["effective_width_mm"])
    minimum_coverage = float(state_policy["minimum_coverage_percent"])
    preferred_maximum = float(state_policy["preferred_maximum_coverage_percent"])
    maximum_iterations = int(scan_profile["global"].get("maximum_adaptation_iterations", 20))
    resolution = float(scan_profile["coverage_targets"]["grid_resolution_mm"])
    minimum_spacing = float(scan_profile["pass_spacing_policy"].get("minimum_spacing_mm", 1.0))
    maximum_spacing = width * float(scan_profile["pass_spacing_policy"].get("maximum_spacing_to_width_ratio", 1.0))

    def generate(candidate_spacing: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        profile = {**scan_profile, "zone_profiles": {key: dict(value) for key, value in scan_profile["zone_profiles"].items()}}
        zone_profile = profile["zone_profiles"][patch["zone_id"]]
        if zone_profile["scan_pattern"] == "concentric_rings":
            zone_profile["ring_spacing_mm"] = candidate_spacing
        else:
            zone_profile["pass_spacing_mm"] = candidate_spacing
        passes = generate_patch_scan_path(patch, profile)
        grid = build_surface_grid(patch, resolution)
        mark_scan_pass_visits(grid, passes, width)
        return passes, calculate_patch_visit_metrics(grid)

    passes, metrics = generate(spacing)
    initial_count = len(passes)
    status = "ACCEPTED_INITIAL"
    iterations = 0
    if float(metrics["patch_coverage_percent"]) < minimum_coverage:
        status = "SPACING_DECREASED"
        while float(metrics["patch_coverage_percent"]) < minimum_coverage and iterations < maximum_iterations:
            candidate = max(minimum_spacing, spacing * 0.95)
            if abs(candidate - spacing) < 1e-6:
                break
            spacing = candidate
            passes, metrics = generate(spacing)
            iterations += 1
    else:
        while float(metrics["patch_coverage_percent"]) > preferred_maximum and iterations < maximum_iterations:
            candidate = min(maximum_spacing, spacing * 1.05)
            if abs(candidate - spacing) < 1e-6:
                break
            candidate_passes, candidate_metrics = generate(candidate)
            if float(candidate_metrics["patch_coverage_percent"]) < minimum_coverage:
                break
            spacing, passes, metrics = candidate, candidate_passes, candidate_metrics
            status = "SPACING_INCREASED"
            iterations += 1
    if float(metrics["patch_coverage_percent"]) < minimum_coverage or iterations >= maximum_iterations:
        status = "MAX_ITERATIONS_REACHED"
    elif float(metrics["patch_coverage_percent"]) > preferred_maximum and abs(spacing - maximum_spacing) < 1e-6:
        status = "COVERAGE_EXACT_LIMIT"
    result = {
        "initial_pass_spacing_mm": round(initial_spacing, 3),
        "final_pass_spacing_mm": round(spacing, 3),
        "initial_pass_count": initial_count,
        "final_pass_count": len(passes),
        "coverage_percent": float(metrics["patch_coverage_percent"]),
        "adaptation_iteration_count": iterations,
        "adaptation_status": status,
        "effective_width_mm": width,
        "estimated_overlap_mm": round(max(0.0, width - spacing), 3),
        "overcoverage_warning": float(metrics["patch_coverage_percent"]) > preferred_maximum,
        "visit_metrics": metrics,
    }
    return passes, result
