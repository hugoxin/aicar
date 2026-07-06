"""Build Stage2.1 wash strategy plans."""


def _stage(
    stage_id: str,
    display_name: str,
    duration_seconds: int,
    target_area: str,
    action: str,
    description: str,
) -> dict:
    return {
        "stage_id": stage_id,
        "display_name": display_name,
        "duration_seconds": int(duration_seconds),
        "target_area": target_area,
        "action": action,
        "description": description,
    }


def build_wash_strategy_plan(
    vehicle_result: dict,
    vehicle_model: dict,
    wash_profile: dict,
) -> dict:
    """Build an abstract wash strategy plan without path planning or hardware control."""
    rinse_seconds = int(wash_profile["rinse_seconds"])
    stages = [
        _stage(
            "pre_rinse",
            "预冲洗",
            20,
            "full_vehicle",
            "water_rinse",
            "Initial rinse to remove loose dust.",
        ),
        _stage(
            "foam",
            "泡沫覆盖",
            int(wash_profile["foam_seconds"]),
            "full_vehicle",
            "foam_apply",
            "Apply foam based on vehicle size and wash profile.",
        ),
        _stage(
            "dwell",
            "泡沫停留",
            int(wash_profile["dwell_seconds"]),
            "full_vehicle",
            "wait",
            "Allow foam to dwell before high pressure rinse.",
        ),
        _stage(
            "top_clean",
            "车顶清洗",
            max(15, int(rinse_seconds * 0.4)),
            "roof",
            "high_pressure_water",
            "Clean roof area using top clearance setting.",
        ),
        _stage(
            "side_clean",
            "侧面清洗",
            max(20, int(rinse_seconds * 0.5)),
            "left_right_sides",
            "high_pressure_water",
            "Clean side surfaces using side clearance setting.",
        ),
        _stage(
            "wheel_clean",
            "轮毂重点清洗",
            int(wash_profile["wheel_focus_seconds"]),
            "wheels",
            "focused_water",
            "Focus on wheel areas.",
        ),
        _stage(
            "air_dry",
            "风干",
            int(wash_profile["dry_seconds"]),
            "full_vehicle",
            "air_dry",
            "Dry vehicle surface.",
        ),
    ]
    estimated_total_seconds = sum(stage["duration_seconds"] for stage in stages)

    return {
        "plan_version": "stage2.1",
        "vehicle": {
            "vehicle_type": vehicle_model.get(
                "vehicle_type", vehicle_result.get("vehicle_type", "unknown")
            ),
            "input_vehicle_type": vehicle_result.get("vehicle_type", "unknown"),
            "vehicle_detected": bool(vehicle_result.get("vehicle_detected", False)),
            "length_mm": int(vehicle_model["length_mm"]),
            "width_mm": int(vehicle_model["width_mm"]),
            "height_mm": int(vehicle_model["height_mm"]),
            "wash_profile": vehicle_model["wash_profile"],
        },
        "profile": {
            "wash_profile": wash_profile["wash_profile"],
            "safe_distance_mm": int(wash_profile["safe_distance_mm"]),
            "top_clearance_mm": int(wash_profile["top_clearance_mm"]),
            "side_clearance_mm": int(wash_profile["side_clearance_mm"]),
            "front_rear_clearance_mm": int(wash_profile["front_rear_clearance_mm"]),
            "gantry_speed_mm_s": int(wash_profile["gantry_speed_mm_s"]),
            "nozzle_travel_speed_mm_s": int(wash_profile["nozzle_travel_speed_mm_s"]),
            "fallback_used": bool(wash_profile.get("fallback_used", False)),
            "fallback_reason": wash_profile.get("fallback_reason", ""),
        },
        "strategy_summary": {
            "estimated_total_seconds": estimated_total_seconds,
            "stage_count": len(stages),
            "notes": "Stage2.1 abstract wash strategy plan. No real nozzle path yet.",
        },
        "stages": stages,
        "limitations": [
            "This is a Stage2.1 strategy-level plan.",
            "No real nozzle path is generated yet.",
            "No PLC or hardware control is included.",
        ],
    }
