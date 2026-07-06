"""Build Stage2.5 abstract nozzle path segments."""


DEFAULT_SPEED_MM_S = 200


def _num(value: int | float) -> int:
    return int(round(float(value)))


def _bounds(zone: dict) -> dict:
    if "bounds" not in zone:
        raise ValueError(f"zone missing bounds: {zone.get('zone_id', '<unknown>')}")
    return zone["bounds"]


def _safe_envelope(zone: dict) -> dict:
    return zone.get("safe_envelope", _bounds(zone))


def _mid(min_value: int | float, max_value: int | float) -> int:
    return _num((float(min_value) + float(max_value)) / 2)


def _point(point_id: str, x_mm: int, y_mm: int, z_mm: int, speed_mm_s: int) -> dict:
    return {
        "point_id": point_id,
        "x_mm": _num(x_mm),
        "y_mm": _num(y_mm),
        "z_mm": _num(z_mm),
        "speed_mm_s": int(speed_mm_s),
    }


def _segment(
    state_id: str,
    zone: dict,
    nozzle: dict,
    duration_seconds: int,
    segment_index: int,
    path_type: str,
    points: list[dict],
) -> dict:
    zone_id = zone["zone_id"]
    nozzle_id = nozzle["nozzle_id"]
    return {
        "segment_id": f"{state_id}_{zone_id}_{nozzle_id}_{segment_index:03d}",
        "state_id": state_id,
        "zone_id": zone_id,
        "nozzle_id": nozzle_id,
        "media_type": nozzle.get("media_type", "unknown"),
        "path_type": path_type,
        "duration_seconds": int(duration_seconds),
        "recommended_distance_mm": int(nozzle.get("recommended_distance_mm", 0)),
        "points": points,
        "notes": "Stage2.5 abstract path only. Not real actuator command.",
    }


def _roof_segment(
    state_id: str,
    zone: dict,
    nozzle: dict,
    duration_seconds: int,
    segment_index: int,
) -> dict:
    bounds = _bounds(zone)
    safe = _safe_envelope(zone)
    x_min = _num(bounds["x_min_mm"])
    x_max = _num(bounds["x_max_mm"])
    y_min = _num(bounds["y_min_mm"])
    y_max = _num(bounds["y_max_mm"])
    z = _num(safe.get("z_max_mm", bounds["z_max_mm"]))
    y_mid = _mid(y_min, y_max)
    points = [
        _point("p1", x_min, y_min, z, DEFAULT_SPEED_MM_S),
        _point("p2", x_max, y_min, z, DEFAULT_SPEED_MM_S),
        _point("p3", x_max, y_mid, z, DEFAULT_SPEED_MM_S),
        _point("p4", x_min, y_mid, z, DEFAULT_SPEED_MM_S),
        _point("p5", x_min, y_max, z, DEFAULT_SPEED_MM_S),
        _point("p6", x_max, y_max, z, DEFAULT_SPEED_MM_S),
    ]
    return _segment(
        state_id,
        zone,
        nozzle,
        duration_seconds,
        segment_index,
        "linear_sweep",
        points,
    )


def _side_segment(
    state_id: str,
    zone: dict,
    nozzle: dict,
    duration_seconds: int,
    segment_index: int,
    side: str,
) -> dict:
    bounds = _bounds(zone)
    safe = _safe_envelope(zone)
    x = safe.get("x_min_mm") if side == "left_side" else safe.get("x_max_mm")
    if x is None:
        x = bounds["x_min_mm"] if side == "left_side" else bounds["x_max_mm"]
    y_min = _num(bounds["y_min_mm"])
    y_max = _num(bounds["y_max_mm"])
    z_min = _num(bounds["z_min_mm"])
    z_max = _num(bounds["z_max_mm"])
    z_mid = _mid(z_min, z_max)
    points = [
        _point("p1", _num(x), y_min, z_max, DEFAULT_SPEED_MM_S),
        _point("p2", _num(x), y_max, z_max, DEFAULT_SPEED_MM_S),
        _point("p3", _num(x), y_max, z_mid, DEFAULT_SPEED_MM_S),
        _point("p4", _num(x), y_min, z_mid, DEFAULT_SPEED_MM_S),
        _point("p5", _num(x), y_min, z_min, DEFAULT_SPEED_MM_S),
        _point("p6", _num(x), y_max, z_min, DEFAULT_SPEED_MM_S),
    ]
    return _segment(
        state_id,
        zone,
        nozzle,
        duration_seconds,
        segment_index,
        "vertical_side_sweep",
        points,
    )


def _front_rear_segment(
    state_id: str,
    zone: dict,
    nozzle: dict,
    duration_seconds: int,
    segment_index: int,
    path_type: str,
) -> dict:
    bounds = _bounds(zone)
    safe = _safe_envelope(zone)
    y = safe.get("y_max_mm") if path_type == "front_sweep" else safe.get("y_min_mm")
    if y is None:
        y = bounds["y_max_mm"] if path_type == "front_sweep" else bounds["y_min_mm"]
    x_min = _num(bounds["x_min_mm"])
    x_max = _num(bounds["x_max_mm"])
    z_min = _num(bounds["z_min_mm"])
    z_max = _num(bounds["z_max_mm"])
    z_mid = _mid(z_min, z_max)
    points = [
        _point("p1", x_min, _num(y), z_max, DEFAULT_SPEED_MM_S),
        _point("p2", x_max, _num(y), z_max, DEFAULT_SPEED_MM_S),
        _point("p3", x_max, _num(y), z_mid, DEFAULT_SPEED_MM_S),
        _point("p4", x_min, _num(y), z_mid, DEFAULT_SPEED_MM_S),
    ]
    return _segment(
        state_id,
        zone,
        nozzle,
        duration_seconds,
        segment_index,
        path_type,
        points,
    )


def _wheel_segment(
    state_id: str,
    zone: dict,
    nozzle: dict,
    duration_seconds: int,
    segment_index: int,
) -> dict:
    sub_zones = zone.get("sub_zones", [])
    points = []
    if sub_zones:
        for index, sub_zone in enumerate(sub_zones, start=1):
            bounds = _bounds(sub_zone)
            points.append(
                _point(
                    f"p{index}",
                    _mid(bounds["x_min_mm"], bounds["x_max_mm"]),
                    _mid(bounds["y_min_mm"], bounds["y_max_mm"]),
                    _mid(bounds["z_min_mm"], bounds["z_max_mm"]),
                    DEFAULT_SPEED_MM_S // 2,
                )
            )
    else:
        bounds = _bounds(zone)
        x_min = _num(bounds["x_min_mm"])
        x_max = _num(bounds["x_max_mm"])
        y_min = _num(bounds["y_min_mm"])
        y_max = _num(bounds["y_max_mm"])
        z = _mid(bounds["z_min_mm"], bounds["z_max_mm"])
        points = [
            _point("p1", x_min, y_min, z, DEFAULT_SPEED_MM_S // 2),
            _point("p2", x_max, y_min, z, DEFAULT_SPEED_MM_S // 2),
            _point("p3", x_min, y_max, z, DEFAULT_SPEED_MM_S // 2),
            _point("p4", x_max, y_max, z, DEFAULT_SPEED_MM_S // 2),
        ]

    return _segment(
        state_id,
        zone,
        nozzle,
        duration_seconds,
        segment_index,
        "focused_points",
        points,
    )


def build_zone_path_segment(
    state_id: str,
    zone: dict,
    nozzle: dict,
    duration_seconds: int,
    segment_index: int,
) -> dict:
    """Build an abstract path segment for one state, zone, and nozzle."""
    zone_id = zone["zone_id"]
    if zone_id == "roof":
        return _roof_segment(state_id, zone, nozzle, duration_seconds, segment_index)
    if zone_id == "left_side":
        return _side_segment(
            state_id,
            zone,
            nozzle,
            duration_seconds,
            segment_index,
            "left_side",
        )
    if zone_id == "right_side":
        return _side_segment(
            state_id,
            zone,
            nozzle,
            duration_seconds,
            segment_index,
            "right_side",
        )
    if zone_id == "front":
        return _front_rear_segment(
            state_id,
            zone,
            nozzle,
            duration_seconds,
            segment_index,
            "front_sweep",
        )
    if zone_id == "rear":
        return _front_rear_segment(
            state_id,
            zone,
            nozzle,
            duration_seconds,
            segment_index,
            "rear_sweep",
        )
    if zone_id == "wheels":
        return _wheel_segment(state_id, zone, nozzle, duration_seconds, segment_index)
    raise ValueError(f"unsupported abstract path zone: {zone_id}")
