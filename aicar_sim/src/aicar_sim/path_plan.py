"""Build Stage2.5 abstract nozzle path plans."""

from aicar_sim.abstract_path import build_zone_path_segment


PATH_ZONE_IDS = ("roof", "left_side", "right_side", "front", "rear", "wheels")


def _zone_index(space_model_report: dict) -> dict:
    safe_envelope = space_model_report["vehicle_envelope"]["safe_envelope"]
    zones = {}
    for zone in space_model_report["vehicle_envelope"].get("surface_zones", []):
        enriched_zone = dict(zone)
        enriched_zone["safe_envelope"] = safe_envelope
        zones[zone["zone_id"]] = enriched_zone
    return zones


def _coverage_index(nozzle_coverage_plan: dict) -> dict:
    return {
        zone["zone_id"]: zone for zone in nozzle_coverage_plan.get("zone_coverage", [])
    }


def _state_zone_ids(state: dict) -> list[str]:
    zone_ids = list(state.get("target_zone_ids", []))
    if "full_vehicle" in zone_ids:
        return list(PATH_ZONE_IDS)
    if state["state_id"] == "foam":
        return [zone_id for zone_id in zone_ids if zone_id != "wheels"]
    return zone_ids


def _state_nozzles(state_id: str, zone_id: str, nozzles: list[dict]) -> list[dict]:
    if state_id == "pre_rinse":
        return [nozzle for nozzle in nozzles if nozzle.get("media_type") == "water"]
    if state_id == "foam":
        if zone_id == "wheels":
            return []
        return [
            nozzle
            for nozzle in nozzles
            if nozzle.get("nozzle_id") == "foam_nozzle"
            or nozzle.get("media_type") == "foam"
        ]
    if state_id == "dwell":
        return []
    if state_id == "air_dry":
        return [
            nozzle
            for nozzle in nozzles
            if nozzle.get("nozzle_id") == "air_dry_nozzle"
            or nozzle.get("media_type") == "air"
        ]
    if state_id == "wheel_clean":
        return [
            nozzle
            for nozzle in nozzles
            if nozzle.get("nozzle_id") == "wheel_focused_nozzle"
            or nozzle.get("media_type") == "water"
        ]
    if state_id in {"top_clean", "side_clean"}:
        return [nozzle for nozzle in nozzles if nozzle.get("media_type") == "water"]
    return nozzles


def _segment_tasks(state: dict, zones: dict, coverage_by_zone: dict) -> list[tuple[dict, dict]]:
    tasks = []
    for zone_id in _state_zone_ids(state):
        zone = zones.get(zone_id)
        coverage = coverage_by_zone.get(zone_id)
        if not zone or not coverage:
            continue
        for nozzle in _state_nozzles(
            state["state_id"],
            zone_id,
            coverage.get("assigned_nozzles", []),
        ):
            tasks.append((zone, nozzle))
    return tasks


def _durations(total_seconds: int, count: int) -> list[int]:
    if count <= 0:
        return []
    base = int(total_seconds) // count
    remainder = int(total_seconds) % count
    return [base + (1 if index < remainder else 0) for index in range(count)]


def build_abstract_nozzle_path_plan(
    wash_flow_run: dict,
    space_model_report: dict,
    nozzle_coverage_plan: dict,
) -> dict:
    """Build a Stage2.5 abstract nozzle path plan."""
    zones = _zone_index(space_model_report)
    coverage_by_zone = _coverage_index(nozzle_coverage_plan)

    path_segments = []
    state_path_summary = []
    segment_index = 1
    for state in wash_flow_run.get("timeline", []):
        if state.get("state_type") not in {"wash", "dry"}:
            continue

        tasks = _segment_tasks(state, zones, coverage_by_zone)
        durations = _durations(int(state.get("duration_seconds", 0)), len(tasks))
        state_segment_count = 0
        for duration, (zone, nozzle) in zip(durations, tasks):
            path_segments.append(
                build_zone_path_segment(
                    state["state_id"],
                    zone,
                    nozzle,
                    duration,
                    segment_index,
                )
            )
            segment_index += 1
            state_segment_count += 1

        state_path_summary.append(
            {
                "state_id": state["state_id"],
                "target_zone_ids": _state_zone_ids(state),
                "segment_count": state_segment_count,
            }
        )

    point_count = sum(len(segment["points"]) for segment in path_segments)
    return {
        "plan_version": "stage2.5",
        "source_versions": {
            "wash_flow_run": wash_flow_run.get("run_version"),
            "space_model_report": space_model_report.get("report_version"),
            "nozzle_coverage_plan": nozzle_coverage_plan.get("plan_version"),
        },
        "vehicle": wash_flow_run["vehicle"],
        "wash_profile": wash_flow_run["wash_profile"],
        "wash_bay_id": wash_flow_run["wash_bay_id"],
        "summary": {
            "state_count": len(wash_flow_run.get("timeline", [])),
            "state_with_path_count": len(
                [item for item in state_path_summary if item["segment_count"] > 0]
            ),
            "segment_count": len(path_segments),
            "point_count": point_count,
            "estimated_total_seconds": wash_flow_run["summary"][
                "estimated_total_seconds"
            ],
            "notes": "Stage2.5 abstract nozzle path plan. No real motion control.",
        },
        "state_path_summary": state_path_summary,
        "path_segments": path_segments,
        "limitations": [
            "This is a Stage2.5 abstract path plan.",
            "Coordinates are simulation-level reference points only.",
            "No real actuator trajectory is generated.",
            "No PLC or hardware control is included.",
        ],
    }
