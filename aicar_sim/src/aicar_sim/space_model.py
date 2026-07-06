"""Build Stage2.2 static space model reports."""


def _half_extent(bounds: dict, min_key: str, max_key: str) -> int:
    return max(abs(int(bounds[min_key])), abs(int(bounds[max_key])))


def _build_clearance_check(vehicle_envelope: dict, wash_bay: dict) -> dict:
    safe = vehicle_envelope["safe_envelope"]
    bay_dimensions = wash_bay["bay_dimensions"]
    bay_half_width = int(bay_dimensions["width_mm"]) // 2
    bay_half_length = int(bay_dimensions["length_mm"]) // 2

    x_required = _half_extent(safe, "x_min_mm", "x_max_mm")
    y_required = _half_extent(safe, "y_min_mm", "y_max_mm")
    z_required = int(safe["z_max_mm"])

    x_clearance = bay_half_width - x_required
    y_clearance = bay_half_length - y_required
    z_clearance = int(bay_dimensions["height_mm"]) - z_required

    warnings = []
    if x_clearance < 0:
        warnings.append("safe envelope is wider than the wash bay width")
    if y_clearance < 0:
        warnings.append("safe envelope is longer than the wash bay length")
    if z_clearance < 0:
        warnings.append("safe envelope is taller than the wash bay height")

    return {
        "fits_in_bay": not warnings,
        "x_clearance_each_side_mm": x_clearance,
        "y_clearance_front_rear_mm": y_clearance,
        "z_clearance_top_mm": z_clearance,
        "warnings": warnings,
    }


def build_space_model_report(
    vehicle_result: dict,
    vehicle_model: dict,
    wash_profile: dict,
    wash_strategy_plan: dict,
    vehicle_envelope: dict,
    wash_bay: dict,
) -> dict:
    """Build a Stage2.2 static space model report."""
    zones = [zone["zone_id"] for zone in vehicle_envelope["surface_zones"]]
    return {
        "report_version": "stage2.2",
        "vehicle": {
            "vehicle_type": vehicle_model.get("vehicle_type", "unknown"),
            "input_vehicle_type": vehicle_result.get("vehicle_type", "unknown"),
            "length_mm": int(vehicle_model["length_mm"]),
            "width_mm": int(vehicle_model["width_mm"]),
            "height_mm": int(vehicle_model["height_mm"]),
            "wash_profile": vehicle_model["wash_profile"],
        },
        "wash_profile": wash_profile["wash_profile"],
        "wash_strategy": {
            "plan_version": wash_strategy_plan.get("plan_version"),
            "estimated_total_seconds": wash_strategy_plan.get(
                "strategy_summary", {}
            ).get("estimated_total_seconds"),
            "stage_count": wash_strategy_plan.get("strategy_summary", {}).get(
                "stage_count"
            ),
        },
        "wash_bay": {
            "wash_bay_id": wash_bay["wash_bay_id"],
            "description": wash_bay.get("description", ""),
            "coordinate_system": wash_bay["coordinate_system"],
            "bay_dimensions": wash_bay["bay_dimensions"],
            "gantry": wash_bay["gantry"],
            "safety_margin": wash_bay["safety_margin"],
        },
        "vehicle_envelope": vehicle_envelope,
        "clearance_check": _build_clearance_check(vehicle_envelope, wash_bay),
        "zone_summary": {
            "zone_count": len(zones),
            "zones": zones,
        },
        "next_stage_hint": (
            "Stage2.3 can add nozzle models based on these zones. "
            "Stage2.5 can add path planning later."
        ),
        "limitations": [
            "This is a Stage2.2 static space model.",
            "No nozzle path is generated.",
            "No animation is generated.",
            "No PLC or hardware control is included.",
        ],
    }
