from __future__ import annotations

from typing import Any


MOTION_STATES = ("pre_rinse", "foam", "top_clean", "side_clean", "wheel_clean", "air_dry")


def _assigned_nozzles(nozzle_coverage_plan: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {**item, "zone_id": zone["zone_id"]}
        for zone in nozzle_coverage_plan.get("zone_coverage", [])
        for item in zone.get("assigned_nozzles", [])
    ]


def resolve_nozzle_effective_width(
    state_id: str,
    nozzle_id: str,
    nozzle_coverage_plan: dict[str, Any],
    scan_profile: dict[str, Any],
    zone_id: str | None = None,
) -> tuple[float, str, list[dict[str, Any]]]:
    matches = [
        item
        for item in _assigned_nozzles(nozzle_coverage_plan)
        if item.get("nozzle_id") == nozzle_id and (zone_id is None or item.get("zone_id") == zone_id)
    ]
    if matches and float(matches[0].get("effective_width_mm", 0)) > 0:
        return float(matches[0]["effective_width_mm"]), "nozzle_coverage_plan", []
    fallback = float(scan_profile["pass_spacing_policy"]["fallback_effective_width_mm"].get(state_id, 0))
    if fallback <= 0:
        raise ValueError(f"no effective width for state={state_id}, nozzle={nozzle_id}, zone={zone_id}")
    warning = {
        "check_id": "effective_width_fallback",
        "severity": "WARNING",
        "message": "Nozzle effective width was missing; configured state fallback was used.",
        "state_id": state_id,
        "zone_id": zone_id,
        "nozzle_id": nozzle_id,
        "fallback_effective_width_mm": fallback,
    }
    return fallback, "repair_profile_fallback", [warning]


def calculate_initial_pass_spacing(
    effective_width_mm: float,
    spacing_factor: float,
    minimum_spacing_mm: float = 1.0,
    maximum_spacing_mm: float | None = None,
) -> float:
    if effective_width_mm <= 0 or spacing_factor <= 0:
        raise ValueError("effective width and spacing factor must be positive")
    spacing = max(float(minimum_spacing_mm), float(effective_width_mm) * float(spacing_factor))
    if maximum_spacing_mm is not None:
        spacing = min(spacing, float(maximum_spacing_mm))
    return round(spacing, 3)


def build_state_scan_policy(
    state_id: str,
    zone_id: str,
    patch: dict[str, Any],
    nozzle_id: str,
    nozzle_coverage_plan: dict[str, Any],
    scan_profile: dict[str, Any],
) -> dict[str, Any]:
    state_policy = scan_profile["state_scan_policies"].get(state_id)
    if not state_policy:
        raise ValueError(f"repair scan policy missing state: {state_id}")
    motion_required = bool(state_policy.get("motion_required", state_id != "dwell"))
    if not motion_required:
        return {
            "state_id": state_id,
            "zone_id": zone_id,
            "patch_id": patch["patch_id"],
            "nozzle_id": nozzle_id,
            "effective_width_mm": 0.0,
            "effective_width_source": "not_applicable",
            "spacing_factor": 0.0,
            "initial_pass_spacing_mm": 0.0,
            "minimum_coverage_percent": 0.0,
            "preferred_maximum_coverage_percent": 0.0,
            "motion_required": False,
            "warnings": [],
        }
    width, source, warnings = resolve_nozzle_effective_width(
        state_id, nozzle_id, nozzle_coverage_plan, scan_profile, zone_id
    )
    spacing_factor = float(state_policy["spacing_factor"])
    spacing_rules = scan_profile["pass_spacing_policy"]
    maximum_spacing = width * float(spacing_rules.get("maximum_spacing_to_width_ratio", 1.0))
    spacing = calculate_initial_pass_spacing(
        width,
        spacing_factor,
        float(spacing_rules.get("minimum_spacing_mm", 1.0)),
        maximum_spacing,
    )
    return {
        "state_id": state_id,
        "zone_id": zone_id,
        "patch_id": patch["patch_id"],
        "nozzle_id": nozzle_id,
        "effective_width_mm": width,
        "effective_width_source": source,
        "spacing_factor": spacing_factor,
        "initial_pass_spacing_mm": spacing,
        "minimum_coverage_percent": float(state_policy["minimum_state_zone_coverage_percent"]),
        "preferred_maximum_coverage_percent": float(state_policy["maximum_preferred_coverage_percent"]),
        "motion_required": True,
        "allow_sparse_scan": bool(state_policy.get("allow_sparse_scan", False)),
        "warnings": warnings,
    }
