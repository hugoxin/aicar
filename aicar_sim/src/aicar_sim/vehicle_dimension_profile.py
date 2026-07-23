from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


DIMENSION_KEYS = ("length_mm", "width_mm", "height_mm")


def load_vehicle_dimension_profile(path: str | Path) -> dict[str, Any]:
    profile = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_vehicle_dimension_profile(profile)
    return profile


def validate_vehicle_dimension_profile(profile: dict[str, Any]) -> dict[str, Any]:
    dimensions = profile.get("dimensions", {})
    required = (*DIMENSION_KEYS, "wheelbase_mm", "front_track_mm", "rear_track_mm", "wheel_radius_mm", "wheel_width_mm", "ground_clearance_mm")
    missing = [key for key in required if key not in dimensions]
    errors = []
    if missing:
        errors.append("missing dimensions: " + ", ".join(missing))
    for key in required:
        if key in dimensions and float(dimensions[key]) <= 0:
            errors.append(f"{key} must be positive")
    if dimensions.get("wheelbase_mm", 0) >= dimensions.get("length_mm", float("inf")):
        errors.append("wheelbase_mm must be smaller than length_mm")
    if max(dimensions.get("front_track_mm", 0), dimensions.get("rear_track_mm", 0)) >= dimensions.get("width_mm", float("inf")):
        errors.append("track width must be smaller than width_mm")
    if dimensions.get("wheel_radius_mm", 0) * 2 >= dimensions.get("height_mm", float("inf")):
        errors.append("wheel diameter must be smaller than height_mm")
    if errors:
        raise ValueError("; ".join(errors))
    return {"valid": True, "errors": []}


def compare_geometry_to_dimensions(geometry: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    bbox = geometry["bounding_box"]
    measured = {
        "width_mm": float(bbox["x_max_mm"]) - float(bbox["x_min_mm"]),
        "length_mm": float(bbox["y_max_mm"]) - float(bbox["y_min_mm"]),
        "height_mm": float(bbox["z_max_mm"]) - float(bbox["z_min_mm"]),
    }
    target = profile["dimensions"]
    ratios = {key: abs(measured[key] - float(target[key])) / float(target[key]) for key in DIMENSION_KEYS}
    tolerance = profile["geometry_tolerance"]
    return {
        "measured_dimensions": measured,
        "target_dimensions": {key: float(target[key]) for key in DIMENSION_KEYS},
        "mismatch_ratio": ratios,
        "maximum_mismatch_ratio": max(ratios.values()),
        "warning": max(ratios.values()) > float(tolerance["dimension_warning_ratio"]),
        "reject": max(ratios.values()) > float(tolerance["dimension_reject_ratio"]),
    }


def scale_analytic_surface_model(surface_model: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(surface_model)
    source = surface_model.get("vehicle_dimensions", surface_model.get("dimensions", {}))
    target = profile["dimensions"]
    scales = {
        "x": float(target["width_mm"]) / float(source["width_mm"]),
        "y": float(target["length_mm"]) / float(source["length_mm"]),
        "z": float(target["height_mm"]) / float(source["height_mm"]),
    }
    result["dimension_profile_id"] = profile["dimension_profile_id"]
    result["applied_scale"] = scales
    result["vehicle_dimensions"] = {key: target[key] for key in DIMENSION_KEYS}
    return result


def get_wheel_centers(profile: dict[str, Any]) -> dict[str, dict[str, float]]:
    d = profile["dimensions"]
    half_wheelbase = float(d["wheelbase_mm"]) / 2
    front_half_track = float(d["front_track_mm"]) / 2
    rear_half_track = float(d["rear_track_mm"]) / 2
    z = float(d["wheel_radius_mm"])
    return {
        "left_front_wheel": {"x_mm": -front_half_track, "y_mm": half_wheelbase, "z_mm": z},
        "right_front_wheel": {"x_mm": front_half_track, "y_mm": half_wheelbase, "z_mm": z},
        "left_rear_wheel": {"x_mm": -rear_half_track, "y_mm": -half_wheelbase, "z_mm": z},
        "right_rear_wheel": {"x_mm": rear_half_track, "y_mm": -half_wheelbase, "z_mm": z},
    }


def get_vehicle_reference_center(profile: dict[str, Any]) -> dict[str, float]:
    return {"x_mm": 0.0, "y_mm": 0.0, "z_mm": float(profile["dimensions"]["height_mm"]) / 2}
