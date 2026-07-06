"""Build Stage2.4 wash flow state-machine run plans."""

from aicar_sim.wash_flow import get_linear_flow_sequence, validate_wash_flow_config


FULL_VEHICLE_ZONES = ("roof", "left_side", "right_side", "front", "rear", "wheels")


def _strategy_stage_index(wash_strategy_plan: dict) -> dict:
    return {stage["stage_id"]: stage for stage in wash_strategy_plan.get("stages", [])}


def _coverage_index(nozzle_coverage_plan: dict) -> dict:
    return {
        zone["zone_id"]: zone for zone in nozzle_coverage_plan.get("zone_coverage", [])
    }


def _resolve_target_zones(state: dict, strategy_stage: dict | None) -> list[str]:
    if state.get("target_zone_ids"):
        return list(state["target_zone_ids"])

    if strategy_stage is None:
        return []

    target_area = strategy_stage.get("target_area", "")
    if target_area == "full_vehicle":
        return list(FULL_VEHICLE_ZONES)
    if target_area == "left_right_sides":
        return ["left_side", "right_side", "front", "rear"]
    if target_area == "roof":
        return ["roof"]
    if target_area == "wheels":
        return ["wheels"]
    return [target_area] if target_area else []


def _unique_nozzles(nozzle_ids: list[str]) -> list[str]:
    seen = set()
    unique = []
    for nozzle_id in nozzle_ids:
        if nozzle_id not in seen:
            seen.add(nozzle_id)
            unique.append(nozzle_id)
    return unique


def _assigned_nozzles(
    state: dict,
    target_zone_ids: list[str],
    nozzle_coverage_plan: dict,
) -> list[str]:
    coverage_by_zone = _coverage_index(nozzle_coverage_plan)
    assigned = []
    state_id = state["state_id"]

    for zone_id in target_zone_ids:
        zone_coverage = coverage_by_zone.get(zone_id)
        if not zone_coverage:
            continue
        for nozzle in zone_coverage.get("assigned_nozzles", []):
            nozzle_id = nozzle["nozzle_id"]
            media_type = nozzle.get("media_type", "")
            if state_id == "pre_rinse" and media_type == "water":
                assigned.append(nozzle_id)
            elif state_id == "foam" and nozzle_id == "foam_nozzle":
                assigned.append(nozzle_id)
            elif state_id == "air_dry" and nozzle_id == "air_dry_nozzle":
                assigned.append(nozzle_id)
            elif state_id not in {"pre_rinse", "foam", "air_dry"}:
                assigned.append(nozzle_id)

    return _unique_nozzles(assigned)


def build_wash_flow_run(
    config: dict,
    wash_strategy_plan: dict,
    space_model_report: dict,
    nozzle_coverage_plan: dict,
) -> dict:
    """Build a Stage2.4 state-machine-level wash flow run plan."""
    validate_wash_flow_config(config, wash_strategy_plan)
    sequence = get_linear_flow_sequence(config)
    strategy_by_id = _strategy_stage_index(wash_strategy_plan)

    timeline = []
    current_time = 0
    for index, state in enumerate(sequence, start=1):
        strategy_stage_id = state.get("strategy_stage_id")
        strategy_stage = strategy_by_id.get(strategy_stage_id) if strategy_stage_id else None
        duration = int(strategy_stage["duration_seconds"]) if strategy_stage else 0
        start_time = current_time
        end_time = current_time + duration
        target_zone_ids = _resolve_target_zones(state, strategy_stage)

        timeline.append(
            {
                "order": index,
                "state_id": state["state_id"],
                "display_name": state["display_name"],
                "state_type": state["state_type"],
                "duration_seconds": duration,
                "start_time_s": start_time,
                "end_time_s": end_time,
                "strategy_stage_id": strategy_stage_id,
                "target_zone_ids": target_zone_ids,
                "assigned_nozzles": _assigned_nozzles(
                    state,
                    target_zone_ids,
                    nozzle_coverage_plan,
                ),
            }
        )
        current_time = end_time

    wash_states = [item for item in timeline if item["strategy_stage_id"]]
    return {
        "run_version": "stage2.4",
        "flow_id": config["flow_id"],
        "vehicle": wash_strategy_plan["vehicle"],
        "wash_profile": wash_strategy_plan["vehicle"]["wash_profile"],
        "wash_bay_id": space_model_report["wash_bay"]["wash_bay_id"],
        "summary": {
            "state_count": len(config["states"]),
            "timeline_state_count": len(timeline),
            "wash_state_count": len(wash_states),
            "estimated_total_seconds": current_time,
            "terminal_states": config["terminal_states"],
            "notes": "Stage2.4 state-machine-level wash flow. No path planning or PLC control.",
        },
        "timeline": timeline,
        "limitations": [
            "This is a Stage2.4 wash flow state machine.",
            "No real nozzle path is generated.",
            "No animation is generated.",
            "No PLC or hardware control is included.",
        ],
    }
