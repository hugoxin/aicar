from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


EPSILON = 1e-6
BOUND_KEYS = (
    "x_min_mm", "x_max_mm", "y_min_mm", "y_max_mm", "z_min_mm", "z_max_mm"
)


def validate_aabb(bounds: dict[str, Any], context: str = "aabb") -> None:
    missing = [key for key in BOUND_KEYS if key not in bounds]
    if missing:
        raise ValueError(f"{context} missing bounds: {', '.join(missing)}")
    for axis in ("x", "y", "z"):
        minimum = bounds[f"{axis}_min_mm"]
        maximum = bounds[f"{axis}_max_mm"]
        if not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)):
            raise ValueError(f"{context} {axis} bounds must be numeric")
        if float(minimum) >= float(maximum):
            raise ValueError(f"{context} {axis}_min_mm must be less than {axis}_max_mm")


def validate_obstacle(obstacle: dict[str, Any]) -> None:
    if not obstacle.get("obstacle_id"):
        raise ValueError("obstacle_id is required")
    if obstacle.get("shape") != "aabb":
        raise ValueError(f"unsupported obstacle shape: {obstacle.get('shape')}")
    validate_aabb(obstacle.get("bounds", {}), f"obstacle {obstacle['obstacle_id']}")


def load_safety_layout(path: str | Path) -> dict[str, Any]:
    layout_path = Path(path)
    if not layout_path.exists():
        raise FileNotFoundError(f"safety layout not found: {layout_path}")
    layout = json.loads(layout_path.read_text(encoding="utf-8"))
    if not layout.get("layout_id"):
        raise ValueError("safety layout requires layout_id")
    obstacle_ids: set[str] = set()
    for obstacle in layout.get("static_obstacles", []):
        validate_obstacle(obstacle)
        obstacle_id = obstacle["obstacle_id"]
        if obstacle_id in obstacle_ids:
            raise ValueError(f"duplicate obstacle_id: {obstacle_id}")
        obstacle_ids.add(obstacle_id)
    zone_ids: set[str] = set()
    for zone in layout.get("safety_zones", []):
        zone_id = zone.get("zone_id")
        if not zone_id:
            raise ValueError("safety zone requires zone_id")
        if zone_id in zone_ids:
            raise ValueError(f"duplicate zone_id: {zone_id}")
        zone_ids.add(zone_id)
        if zone.get("shape") == "aabb":
            validate_aabb(zone.get("bounds", {}), f"safety zone {zone_id}")
        elif not zone.get("source"):
            raise ValueError(f"safety zone {zone_id} requires aabb bounds or source")
    policy = layout.get("vehicle_clearance_policy", {})
    hard = float(policy.get("hard_minimum_mm", 0))
    warning = float(policy.get("warning_threshold_mm", 0))
    recommended = float(policy.get("recommended_mm", 0))
    if not 0 < hard < warning < recommended:
        raise ValueError("vehicle clearance policy must satisfy 0 < hard < warning < recommended")
    return layout


def point_inside_aabb(point: dict[str, Any], bounds: dict[str, Any]) -> bool:
    validate_aabb(bounds)
    return all(
        float(bounds[f"{axis}_min_mm"]) - EPSILON
        <= float(point[f"{axis}_mm"])
        <= float(bounds[f"{axis}_max_mm"]) + EPSILON
        for axis in ("x", "y", "z")
    )


def aabb_intersects(aabb_a: dict[str, Any], aabb_b: dict[str, Any]) -> bool:
    validate_aabb(aabb_a, "aabb_a")
    validate_aabb(aabb_b, "aabb_b")
    return all(
        float(aabb_a[f"{axis}_max_mm"]) + EPSILON >= float(aabb_b[f"{axis}_min_mm"])
        and float(aabb_b[f"{axis}_max_mm"]) + EPSILON >= float(aabb_a[f"{axis}_min_mm"])
        for axis in ("x", "y", "z")
    )


def distance_point_to_aabb(point: dict[str, Any], bounds: dict[str, Any]) -> float:
    validate_aabb(bounds)
    distances = []
    for axis in ("x", "y", "z"):
        value = float(point[f"{axis}_mm"])
        minimum = float(bounds[f"{axis}_min_mm"])
        maximum = float(bounds[f"{axis}_max_mm"])
        distances.append(max(minimum - value, 0.0, value - maximum))
    return math.sqrt(sum(value * value for value in distances))


def expand_aabb(bounds: dict[str, Any], margin_mm: float) -> dict[str, float]:
    validate_aabb(bounds)
    margin = float(margin_mm)
    return {
        f"{axis}_min_mm": float(bounds[f"{axis}_min_mm"]) - margin
        for axis in ("x", "y", "z")
    } | {
        f"{axis}_max_mm": float(bounds[f"{axis}_max_mm"]) + margin
        for axis in ("x", "y", "z")
    }
