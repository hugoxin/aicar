from __future__ import annotations

import math
from typing import Any

from aicar_sim.surface_model import REQUIRED_ZONES, all_surface_patches


REQUIRED_STATE_ORDER = ["pre_rinse", "foam", "dwell", "top_clean", "side_clean", "wheel_clean", "air_dry"]


def _issue(check_id: str, severity: str, message: str, **details: Any) -> dict[str, Any]:
    return {"check_id": check_id, "severity": severity, "message": message, **details}


def _distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    point_a = a.get("machine_point", a.get("nozzle_point", {}))
    point_b = b.get("machine_point", b.get("nozzle_point", {}))
    return math.sqrt(sum((float(point_b[f"{axis}_mm"]) - float(point_a[f"{axis}_mm"])) ** 2 for axis in ("x", "y", "z")))


def validate_continuous_surface_path(
    plan: dict[str, Any],
    surface_model: dict[str, Any],
    scan_profile: dict[str, Any],
    baseline_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    violations: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    states = [str(item.get("state_id")) for item in plan.get("states", [])]
    state_positions = [states.index(item) for item in REQUIRED_STATE_ORDER if item in states]
    if any(item not in states for item in REQUIRED_STATE_ORDER):
        violations.append(_issue("required_states", "violation", "Continuous path is missing a required wash state."))
    elif state_positions != sorted(state_positions):
        violations.append(_issue("state_order", "violation", "Required wash-state order was changed."))

    tasks = plan.get("surface_tasks", [])
    task_zones = {str(item.get("zone_id")) for item in tasks}
    missing_zones = REQUIRED_ZONES - task_zones
    if missing_zones:
        violations.append(_issue("required_zones", "violation", "Continuous path is missing required zones.", missing=sorted(missing_zones)))
    if any(not item.get("state_id") or not item.get("zone_id") or not item.get("nozzle_id") for item in tasks):
        violations.append(_issue("task_semantics", "violation", "Every surface task requires state, zone, and nozzle semantics."))

    scan_passes = plan.get("scan_passes", [])
    scanned_patch_ids = {str(item.get("patch_id")) for item in scan_passes}
    required_patch_ids = {str(item["patch_id"]) for item in all_surface_patches(surface_model)}
    missing_patches = required_patch_ids - scanned_patch_ids
    if missing_patches:
        violations.append(_issue("patch_paths", "violation", "Surface patches are missing scan paths.", missing=sorted(missing_patches)))
    wheel_ids = {str(item["patch_id"]) for item in surface_model.get("wheel_patches", [])}
    if len(wheel_ids & scanned_patch_ids) != 4:
        violations.append(_issue("wheel_paths", "violation", "All four wheel patches require independent scan paths."))
    if not scan_passes:
        violations.append(_issue("scan_passes", "violation", "No scan passes were generated."))

    connections = plan.get("connections", [])
    if not connections:
        violations.append(_issue("connections", "violation", "No local or patch connections were generated."))
    rejected = [item for item in connections if item.get("connection_type") == "REJECTED_CONNECTION" or item.get("safety_status") == "REJECTED"]
    if rejected:
        violations.append(_issue("connection_safety", "violation", "One or more surface connections could not be made safe.", count=len(rejected)))

    points = plan.get("trajectory_points", [])
    maximum_points = int(scan_profile["global"]["maximum_output_points"])
    if not points:
        violations.append(_issue("trajectory", "violation", "Continuous surface trajectory is empty."))
    if len(points) > maximum_points:
        violations.append(_issue("point_limit", "violation", "Continuous surface trajectory exceeds maximum_output_points.", measured=len(points), limit=maximum_points))
    minimum_standoff = float(scan_profile["global"]["hard_minimum_clearance_mm"])
    maximum_standoff = float(scan_profile["global"]["maximum_standoff_mm"])
    for index, point in enumerate(points):
        standoff = float(point.get("standoff_mm", 0))
        if standoff < minimum_standoff:
            violations.append(_issue("standoff_minimum", "violation", "Surface standoff is below the hard minimum.", point_index=index, measured=standoff, limit=minimum_standoff))
            break
        if standoff > maximum_standoff:
            violations.append(_issue("standoff_maximum", "violation", "Surface standoff exceeds the configured maximum.", point_index=index, measured=standoff, limit=maximum_standoff))
            break

    maximum_spacing = float(scan_profile["global"]["maximum_point_spacing_mm"])
    maximum_gap = max((_distance(a, b) for a, b in zip(points, points[1:])), default=0.0)
    if maximum_gap > maximum_spacing + 1e-3:
        violations.append(_issue("path_continuity", "violation", "Adjacent continuous path points exceed maximum spacing.", measured=round(maximum_gap, 3), limit=maximum_spacing))

    coverage = plan.get("coverage_summary", {})
    total_coverage = float(coverage.get("total_coverage_percent", 0))
    minimum_total = float(scan_profile["coverage"]["minimum_total_coverage_percent"])
    if total_coverage < minimum_total:
        violations.append(_issue("total_coverage", "violation", "Estimated total surface coverage is below the configured threshold.", measured=total_coverage, limit=minimum_total))
    minimum_zone = float(scan_profile["coverage"]["minimum_zone_coverage_percent"])
    low_zones = [item for item in coverage.get("zone_coverage", []) if float(item.get("zone_coverage_percent", 0)) < minimum_zone]
    if low_zones:
        violations.append(_issue("zone_coverage", "violation", "One or more zones are below the configured coverage threshold.", zones=[item["zone_id"] for item in low_zones], limit=minimum_zone))

    if baseline_metrics:
        baseline_path = float(baseline_metrics.get("path_length_mm", 0))
        baseline_transitions = int(baseline_metrics.get("transition_segment_count", 0))
        if float(plan.get("summary", {}).get("path_length_mm", 0)) >= baseline_path:
            warnings.append(_issue("path_improvement", "warning", "Continuous source path did not reduce baseline path length."))
        if int(plan.get("summary", {}).get("required_state_transition_count", 0)) >= baseline_transitions:
            warnings.append(_issue("transition_improvement", "warning", "Continuous source path did not reduce baseline transitions."))

    warnings.extend(
        [
            _issue("analytic_surface", "warning", "Coverage and normals use an analytic reference surface, not CAD or point cloud data."),
            _issue("coverage_approximation", "warning", "Coverage is a local 2D grid estimate and is not real cleaning effectiveness."),
        ]
    )
    status = "FAIL" if violations else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    return {
        "validation_status": status,
        "violation_count": len(violations),
        "warning_count": len(warnings),
        "required_state_order": REQUIRED_STATE_ORDER,
        "required_zones": sorted(REQUIRED_ZONES),
        "maximum_adjacent_gap_mm": round(maximum_gap, 3),
        "minimum_standoff_mm": min((float(item.get("standoff_mm", 0)) for item in points), default=0.0),
        "maximum_standoff_mm": max((float(item.get("standoff_mm", 0)) for item in points), default=0.0),
        "violations": violations,
        "warnings": warnings,
    }
