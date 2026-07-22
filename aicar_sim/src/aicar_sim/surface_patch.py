from __future__ import annotations

import math
from typing import Any

from aicar_sim.surface_model import get_reference_normal, get_reference_surface_point


def normalize_vector(vector: dict[str, float]) -> dict[str, float]:
    length = math.sqrt(sum(float(vector[key]) ** 2 for key in ("x", "y", "z")))
    if length <= 0:
        raise ValueError("surface normal must have non-zero length")
    return {key: float(vector[key]) / length for key in ("x", "y", "z")}


def make_surface_sample(
    patch: dict[str, Any],
    u_mm: float,
    v_mm: float,
    standoff_mm: float,
) -> dict[str, Any]:
    if standoff_mm < 250:
        raise ValueError("surface sample standoff must be at least 250 mm")
    surface = get_reference_surface_point(patch, u_mm, v_mm)
    normal = normalize_vector(get_reference_normal(patch, u_mm, v_mm))
    nozzle = {
        f"{axis}_mm": float(surface[f"{axis}_mm"]) + normal[axis] * float(standoff_mm)
        for axis in ("x", "y", "z")
    }
    return {
        "patch_id": patch["patch_id"],
        "zone_id": patch["zone_id"],
        "u_mm": round(float(u_mm), 6),
        "v_mm": round(float(v_mm), 6),
        "surface_point": {key: round(float(value), 6) for key, value in surface.items()},
        "normal": {key: round(float(value), 9) for key, value in normal.items()},
        "nozzle_point": {key: round(float(value), 6) for key, value in nozzle.items()},
        "standoff_mm": round(float(standoff_mm), 6),
    }


def add_machine_clearance(sample: dict[str, Any], clearance_mm: float) -> dict[str, Any]:
    result = dict(sample)
    normal = sample["normal"]
    nozzle = sample["nozzle_point"]
    result["machine_point"] = {
        f"{axis}_mm": round(float(nozzle[f"{axis}_mm"]) + float(normal[axis]) * clearance_mm, 6)
        for axis in ("x", "y", "z")
    }
    return result
