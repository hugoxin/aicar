"""Build Stage2.2 vehicle envelope models."""


SURFACE_ZONE_IDS = ("roof", "left_side", "right_side", "front", "rear", "wheels")


def _bounds(
    x_min: int,
    x_max: int,
    y_min: int,
    y_max: int,
    z_min: int,
    z_max: int,
) -> dict:
    return {
        "x_min_mm": int(x_min),
        "x_max_mm": int(x_max),
        "y_min_mm": int(y_min),
        "y_max_mm": int(y_max),
        "z_min_mm": int(z_min),
        "z_max_mm": int(z_max),
    }


def _zone(
    zone_id: str,
    display_name: str,
    target_area: str,
    bounds: dict,
    sub_zones: list[dict] | None = None,
) -> dict:
    zone = {
        "zone_id": zone_id,
        "display_name": display_name,
        "target_area": target_area,
        "bounds": bounds,
    }
    if sub_zones:
        zone["sub_zones"] = sub_zones
    return zone


def _wheel_sub_zones(bounding_box: dict, length_mm: int, width_mm: int) -> list[dict]:
    wheel_patch_y = max(180, int(length_mm * 0.08))
    wheel_patch_x = max(120, int(width_mm * 0.08))
    wheel_z_max = max(350, min(700, int(bounding_box["z_max_mm"] * 0.45)))
    x_left = bounding_box["x_min_mm"]
    x_right = bounding_box["x_max_mm"]
    y_front = bounding_box["y_max_mm"] - int(length_mm * 0.18)
    y_rear = bounding_box["y_min_mm"] + int(length_mm * 0.18)

    wheel_specs = [
        ("front_left_wheel", x_left, y_front),
        ("front_right_wheel", x_right, y_front),
        ("rear_left_wheel", x_left, y_rear),
        ("rear_right_wheel", x_right, y_rear),
    ]
    sub_zones = []
    for zone_id, center_x, center_y in wheel_specs:
        sub_zones.append(
            {
                "zone_id": zone_id,
                "bounds": _bounds(
                    center_x - wheel_patch_x,
                    center_x + wheel_patch_x,
                    center_y - wheel_patch_y,
                    center_y + wheel_patch_y,
                    0,
                    wheel_z_max,
                ),
            }
        )
    return sub_zones


def build_vehicle_envelope(vehicle_model: dict, wash_profile: dict) -> dict:
    """Build a static vehicle envelope from vehicle dimensions and profile clearances."""
    vehicle_type = str(vehicle_model.get("vehicle_type", "unknown")).lower()
    length_mm = int(vehicle_model["length_mm"])
    width_mm = int(vehicle_model["width_mm"])
    height_mm = int(vehicle_model["height_mm"])

    half_width = width_mm // 2
    half_length = length_mm // 2
    bounding_box = _bounds(
        -half_width,
        width_mm - half_width,
        -half_length,
        length_mm - half_length,
        0,
        height_mm,
    )

    side_clearance = int(wash_profile["side_clearance_mm"])
    front_rear_clearance = int(wash_profile["front_rear_clearance_mm"])
    top_clearance = int(wash_profile["top_clearance_mm"])
    safe_envelope = _bounds(
        bounding_box["x_min_mm"] - side_clearance,
        bounding_box["x_max_mm"] + side_clearance,
        bounding_box["y_min_mm"] - front_rear_clearance,
        bounding_box["y_max_mm"] + front_rear_clearance,
        0,
        bounding_box["z_max_mm"] + top_clearance,
    )

    roof_band = min(160, max(80, height_mm // 10))
    side_z_min = max(0, int(height_mm * 0.18))
    surface_zones = [
        _zone(
            "roof",
            "车顶区域",
            "roof",
            _bounds(
                bounding_box["x_min_mm"],
                bounding_box["x_max_mm"],
                bounding_box["y_min_mm"],
                bounding_box["y_max_mm"],
                max(0, height_mm - roof_band),
                height_mm,
            ),
        ),
        _zone(
            "left_side",
            "左侧区域",
            "left_side",
            _bounds(
                bounding_box["x_min_mm"],
                bounding_box["x_min_mm"],
                bounding_box["y_min_mm"],
                bounding_box["y_max_mm"],
                side_z_min,
                height_mm,
            ),
        ),
        _zone(
            "right_side",
            "右侧区域",
            "right_side",
            _bounds(
                bounding_box["x_max_mm"],
                bounding_box["x_max_mm"],
                bounding_box["y_min_mm"],
                bounding_box["y_max_mm"],
                side_z_min,
                height_mm,
            ),
        ),
        _zone(
            "front",
            "车头区域",
            "front",
            _bounds(
                bounding_box["x_min_mm"],
                bounding_box["x_max_mm"],
                bounding_box["y_max_mm"],
                bounding_box["y_max_mm"],
                0,
                height_mm,
            ),
        ),
        _zone(
            "rear",
            "车尾区域",
            "rear",
            _bounds(
                bounding_box["x_min_mm"],
                bounding_box["x_max_mm"],
                bounding_box["y_min_mm"],
                bounding_box["y_min_mm"],
                0,
                height_mm,
            ),
        ),
        _zone(
            "wheels",
            "轮毂区域",
            "wheels",
            _bounds(
                bounding_box["x_min_mm"],
                bounding_box["x_max_mm"],
                bounding_box["y_min_mm"],
                bounding_box["y_max_mm"],
                0,
                max(350, min(700, int(height_mm * 0.45))),
            ),
            _wheel_sub_zones(bounding_box, length_mm, width_mm),
        ),
    ]

    return {
        "vehicle_type": vehicle_type,
        "base_dimensions": {
            "length_mm": length_mm,
            "width_mm": width_mm,
            "height_mm": height_mm,
        },
        "coordinate_system": {
            "origin": "vehicle_center_floor",
            "x_axis": "left_right",
            "y_axis": "front_rear",
            "z_axis": "up",
        },
        "bounding_box": bounding_box,
        "safe_envelope": safe_envelope,
        "surface_zones": surface_zones,
        "notes": "Stage2.2 geometric envelope only. Not a real CAD model.",
    }
