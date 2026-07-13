from __future__ import annotations

from typing import Any

from aicar_sim.obstacle_model import expand_aabb, point_inside_aabb


ZONE_SPEED_SCALES = {
    "normal": 1.0,
    "slow": 0.5,
    "shared_interlock": 0.4,
    "safe_stop": 0.3,
    "forbidden": 0.0,
}


def get_zone_speed_scale(zone_type: str) -> float:
    return ZONE_SPEED_SCALES.get(zone_type, 1.0)


def resolve_dynamic_safety_zones(
    safety_layout: dict[str, Any],
    vehicle_safe_envelope: dict[str, Any],
) -> dict[str, Any]:
    layout = {**safety_layout, "safety_zones": []}
    for zone in safety_layout.get("safety_zones", []):
        item = dict(zone)
        if zone.get("source") == "vehicle_safe_envelope":
            if zone.get("zone_type") == "forbidden":
                item["bounds"] = dict(vehicle_safe_envelope)
            elif zone.get("zone_type") == "slow":
                item["bounds"] = expand_aabb(
                    vehicle_safe_envelope,
                    float(zone.get("outer_margin_mm", 0)),
                )
                item["exclude_bounds"] = dict(vehicle_safe_envelope)
            item["shape"] = "aabb"
        layout["safety_zones"].append(item)
    return layout


def classify_point_safety_zones(
    point: dict[str, Any],
    safety_layout: dict[str, Any],
) -> list[dict[str, Any]]:
    matches = []
    for zone in safety_layout.get("safety_zones", []):
        bounds = zone.get("bounds")
        if not bounds or not point_inside_aabb(point, bounds):
            continue
        exclude = zone.get("exclude_bounds")
        if exclude and point_inside_aabb(point, exclude):
            continue
        matches.append(zone)
    return matches


def apply_safety_zone_annotations(
    points: list[dict[str, Any]],
    safety_layout: dict[str, Any],
) -> list[dict[str, Any]]:
    annotated = []
    for point in points:
        matches = classify_point_safety_zones(point, safety_layout)
        zone_types = [str(zone.get("zone_type", "normal")) for zone in matches]
        speed_scale = min([get_zone_speed_scale(item) for item in zone_types] or [1.0])
        item = dict(point)
        item.update(
            {
                "safety_zone_ids": [zone["zone_id"] for zone in matches],
                "zone_policy": zone_types or ["normal"],
                "speed_scale": speed_scale,
                "requires_interlock": "shared_interlock" in zone_types,
                "forbidden": "forbidden" in zone_types,
                "adjusted_velocity_mm_s": round(float(point.get("velocity_mm_s", 0)) * speed_scale, 6),
            }
        )
        annotated.append(item)
    return annotated
