"""Build Stage2.6 abstract coverage reports."""


REQUIRED_ZONES = ("roof", "left_side", "right_side", "front", "rear", "wheels")


def _coverage_index(nozzle_coverage_plan: dict) -> dict:
    return {
        zone["zone_id"]: zone for zone in nozzle_coverage_plan.get("zone_coverage", [])
    }


def _segments_by_zone(path_plan: dict) -> dict:
    grouped: dict[str, list[dict]] = {}
    for segment in path_plan.get("path_segments", []):
        grouped.setdefault(segment["zone_id"], []).append(segment)
    return grouped


def _point_count(segments: list[dict]) -> int:
    return sum(len(segment.get("points", [])) for segment in segments)


def _zone_suggestion(zone_id: str) -> str:
    if zone_id == "wheels":
        return "Increase wheel_focused_nozzle pass count or add wheel-focused points."
    if zone_id == "roof":
        return "Increase roof sweep count or add an additional roof pass."
    if zone_id in {"left_side", "right_side", "front", "rear"}:
        return "Increase side_high_pressure sweep count for side/front/rear zones."
    return f"Review abstract path coverage for zone {zone_id}."


def _build_zone_report(zone_id: str, coverage: dict | None, segments: list[dict]) -> dict:
    assigned_nozzles = coverage.get("assigned_nozzles", []) if coverage else []
    target = int(coverage.get("target_coverage_percent", 0)) if coverage else 0
    warnings = []

    if not assigned_nozzles:
        estimated = 0
        warnings.append("no assigned nozzle for zone")
    elif not segments:
        estimated = max(0, target - 30)
        warnings.append("no path segment for zone")
    else:
        estimated = target

    return {
        "zone_id": zone_id,
        "target_coverage_percent": target,
        "estimated_coverage_percent": estimated,
        "coverage_pass": bool(assigned_nozzles and segments and estimated >= target),
        "segment_count": len(segments),
        "point_count": _point_count(segments),
        "assigned_nozzles": [
            nozzle["nozzle_id"] for nozzle in assigned_nozzles
        ],
        "warnings": warnings,
    }


def build_coverage_report(
    path_plan: dict,
    nozzle_coverage_plan: dict,
    space_model_report: dict,
) -> dict:
    """Build a Stage2.6 abstract coverage report."""
    zones = list(space_model_report.get("zone_summary", {}).get("zones", []))
    if not zones:
        zones = list(REQUIRED_ZONES)

    missing_required = [zone_id for zone_id in REQUIRED_ZONES if zone_id not in zones]
    if missing_required:
        raise ValueError(f"space model missing required zones: {missing_required}")

    coverage_by_zone = _coverage_index(nozzle_coverage_plan)
    segments_by_zone = _segments_by_zone(path_plan)

    zone_reports = [
        _build_zone_report(
            zone_id,
            coverage_by_zone.get(zone_id),
            segments_by_zone.get(zone_id, []),
        )
        for zone_id in zones
    ]

    target_values = [report["target_coverage_percent"] for report in zone_reports]
    estimated_values = [
        report["estimated_coverage_percent"] for report in zone_reports
    ]
    covered_zone_count = sum(1 for report in zone_reports if report["segment_count"] > 0)
    uncovered_zone_count = len(zone_reports) - covered_zone_count
    overall_target = int(round(sum(target_values) / len(target_values)))
    estimated_actual = int(round(sum(estimated_values) / len(estimated_values)))
    coverage_pass = estimated_actual >= 90 and uncovered_zone_count == 0

    warnings = []
    improvement_suggestions = []
    for report in zone_reports:
        for warning in report["warnings"]:
            warnings.append(f"{report['zone_id']}: {warning}")
        if not report["coverage_pass"]:
            improvement_suggestions.append(_zone_suggestion(report["zone_id"]))

    if not improvement_suggestions:
        improvement_suggestions.append(
            "Current abstract coverage passes Stage2.6 demo threshold."
        )

    return {
        "report_version": "stage2.6",
        "source_versions": {
            "abstract_nozzle_path_plan": path_plan.get("plan_version"),
            "nozzle_coverage_plan": nozzle_coverage_plan.get("plan_version"),
            "space_model_report": space_model_report.get("report_version"),
        },
        "vehicle": path_plan["vehicle"],
        "wash_profile": path_plan["wash_profile"],
        "wash_bay_id": path_plan["wash_bay_id"],
        "coverage_summary": {
            "zone_count": len(zone_reports),
            "covered_zone_count": covered_zone_count,
            "uncovered_zone_count": uncovered_zone_count,
            "overall_target_coverage_percent": overall_target,
            "estimated_actual_coverage_percent": estimated_actual,
            "coverage_pass": coverage_pass,
            "total_segment_count": int(path_plan["summary"]["segment_count"]),
            "total_point_count": int(path_plan["summary"]["point_count"]),
            "notes": "Stage2.6 abstract coverage report. Not real fluid simulation.",
        },
        "zone_reports": zone_reports,
        "warnings": warnings,
        "improvement_suggestions": improvement_suggestions,
        "limitations": [
            "This is a Stage2.6 abstract coverage report.",
            "Coverage is estimated from path segments and configured target coverage.",
            "No real water flow, pressure, collision, or sensor feedback is simulated.",
            "No PLC or hardware control is included.",
        ],
    }
