from __future__ import annotations

import copy
from typing import Any

from aicar_sim.vehicle_dimension_profile import compare_geometry_to_dimensions


def calculate_bounding_box(items: list[dict[str, Any]]) -> dict[str, float]:
    if not items:
        raise ValueError("cannot calculate bounding box for empty geometry")
    return {
        "x_min_mm": min(float(item["x_mm"]) for item in items),
        "x_max_mm": max(float(item["x_mm"]) for item in items),
        "y_min_mm": min(float(item["y_mm"]) for item in items),
        "y_max_mm": max(float(item["y_mm"]) for item in items),
        "z_min_mm": min(float(item["z_mm"]) for item in items),
        "z_max_mm": max(float(item["z_mm"]) for item in items),
    }


def normalize_geometry(geometry: dict[str, Any], import_profile: dict[str, Any], dimension_profile: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(geometry)
    points = result["vertices"] or result["points"]
    original = calculate_bounding_box(points)
    unit = str(result.get("unit", "mm")).lower()
    unit_scale = {"mm": 1.0, "cm": 10.0, "m": 1000.0}.get(unit)
    if unit_scale is None or unit not in import_profile["normalization"]["allowed_input_units"]:
        raise ValueError(f"unsupported geometry unit: {unit}")
    center_x = (original["x_min_mm"] + original["x_max_mm"]) / 2
    center_y = (original["y_min_mm"] + original["y_max_mm"]) / 2
    ground = original["z_min_mm"]
    for collection in (result["vertices"], result["points"]):
        for item in collection:
            item["x_mm"] = (float(item["x_mm"]) - center_x) * unit_scale
            item["y_mm"] = (float(item["y_mm"]) - center_y) * unit_scale
            item["z_mm"] = (float(item["z_mm"]) - ground) * unit_scale
    target = dimension_profile["dimensions"]
    centered = calculate_bounding_box(result["vertices"] or result["points"])
    source_dims = {
        "x": centered["x_max_mm"] - centered["x_min_mm"],
        "y": centered["y_max_mm"] - centered["y_min_mm"],
        "z": centered["z_max_mm"] - centered["z_min_mm"],
    }
    desired = {"x": float(target["width_mm"]), "y": float(target["length_mm"]), "z": float(target["height_mm"])}
    raw_scales = {axis: desired[axis] / source_dims[axis] for axis in ("x", "y", "z")}
    if result["geometry_source_type"] == "ANALYTIC_REFERENCE":
        scales = raw_scales
        mode = "NON_UNIFORM_ANALYTIC"
    else:
        uniform = sum(raw_scales.values()) / 3
        scales = {axis: uniform for axis in ("x", "y", "z")}
        mode = "UNIFORM"
    for collection in (result["vertices"], result["points"]):
        for item in collection:
            item["x_mm"] *= scales["x"]
            item["y_mm"] *= scales["y"]
            item["z_mm"] *= scales["z"]
    result["unit"] = "mm"
    result["bounding_box"] = calculate_bounding_box(result["vertices"] or result["points"])
    comparison = compare_geometry_to_dimensions(result, dimension_profile)
    if comparison["reject"]:
        raise ValueError(f"geometry dimension mismatch exceeds reject ratio: {comparison['maximum_mismatch_ratio']:.6f}")
    result["dimension_summary"] = comparison
    result["normalization"] = {
        "input_unit": unit,
        "unit_scale": unit_scale,
        "axis_mapping": {"x": "x", "y": "y", "z": "z", "handedness": "right"},
        "translation": {"x_mm": -center_x, "y_mm": -center_y, "z_mm": -ground},
        "scale": scales,
        "scale_mode": mode,
        "original_bbox": original,
        "normalized_bbox": result["bounding_box"],
        "dimension_mismatch_ratio": comparison["mismatch_ratio"],
        "normalization_status": "PASS_WITH_WARNINGS" if comparison["warning"] else "PASS",
    }
    return result
