"""Build Stage2.3 nozzle coverage plans."""

from aicar_sim.nozzle_model import get_nozzles_for_zone, validate_nozzle_zone_mapping


def _mapping_index(mapping: dict) -> dict:
    return {item["zone_id"]: item for item in mapping.get("zone_mappings", [])}


def _assigned_nozzle_summary(nozzle: dict) -> dict:
    return {
        "nozzle_id": nozzle["nozzle_id"],
        "display_name": nozzle["display_name"],
        "media_type": nozzle["media_type"],
        "pressure_level": nozzle["pressure_level"],
        "spray_angle_deg": int(nozzle["spray_angle_deg"]),
        "recommended_distance_mm": int(nozzle["recommended_distance_mm"]),
        "effective_width_mm": int(nozzle["effective_width_mm"]),
        "flow_l_min": float(nozzle["flow_l_min"]),
        "pass_count_hint": int(nozzle["pass_count_hint"]),
    }


def build_nozzle_coverage_plan(
    space_model_report: dict,
    nozzle_catalog: dict,
    nozzle_zone_mapping: dict,
) -> dict:
    """Build a nozzle coverage parameter plan without motion path generation."""
    validate_nozzle_zone_mapping(nozzle_zone_mapping, nozzle_catalog)
    mapping_by_zone = _mapping_index(nozzle_zone_mapping)
    surface_zones = space_model_report["vehicle_envelope"]["surface_zones"]

    zone_coverage = []
    target_percent_values = []
    used_nozzle_ids = set()
    for zone in surface_zones:
        zone_id = zone["zone_id"]
        mapping = mapping_by_zone.get(zone_id)
        if mapping is None:
            raise ValueError(f"missing nozzle zone mapping for surface zone: {zone_id}")

        assigned_nozzles = get_nozzles_for_zone(
            zone_id,
            nozzle_catalog,
            nozzle_zone_mapping,
        )
        used_nozzle_ids.update(nozzle["nozzle_id"] for nozzle in assigned_nozzles)
        target_percent = int(mapping["coverage_target_percent"])
        target_percent_values.append(target_percent)

        zone_coverage.append(
            {
                "zone_id": zone_id,
                "display_name": zone.get("display_name", zone_id),
                "target_area": zone.get("target_area", zone_id),
                "priority": int(mapping["priority"]),
                "target_coverage_percent": target_percent,
                "zone_pass_count_hint": int(mapping["pass_count_hint"]),
                "assigned_nozzles": [
                    _assigned_nozzle_summary(nozzle) for nozzle in assigned_nozzles
                ],
            }
        )

    estimated_coverage = int(round(sum(target_percent_values) / len(target_percent_values)))

    return {
        "plan_version": "stage2.3",
        "source_space_model_version": space_model_report["report_version"],
        "vehicle": space_model_report["vehicle"],
        "wash_profile": space_model_report["wash_profile"],
        "wash_bay_id": space_model_report["wash_bay"]["wash_bay_id"],
        "coverage_summary": {
            "zone_count": len(zone_coverage),
            "nozzle_count": len(used_nozzle_ids),
            "estimated_coverage_percent": estimated_coverage,
            "notes": "Stage2.3 nozzle coverage parameter plan. No motion path yet.",
        },
        "zone_coverage": zone_coverage,
        "limitations": [
            "This is a Stage2.3 nozzle coverage parameter plan.",
            "No real nozzle path is generated.",
            "No animation is generated.",
            "No PLC or hardware control is included.",
        ],
    }
