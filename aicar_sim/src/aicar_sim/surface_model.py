from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


SUPPORTED_SURFACE_TYPES = {"vertical_rectangle", "arched_rectangle", "circular_disk"}
REQUIRED_ZONES = {"roof", "left_side", "right_side", "front", "rear", "wheels"}


def load_surface_model(path: str | Path) -> dict[str, Any]:
    model_path = Path(path)
    if not model_path.exists():
        raise FileNotFoundError(f"surface model not found: {model_path}")
    model = json.loads(model_path.read_text(encoding="utf-8"))
    validate_surface_model(model)
    return model


def all_surface_patches(model: dict[str, Any]) -> list[dict[str, Any]]:
    return [*model.get("surface_patches", []), *model.get("wheel_patches", [])]


def validate_surface_model(model: dict[str, Any]) -> None:
    if not model.get("surface_model_id"):
        raise ValueError("surface model requires surface_model_id")
    patches = all_surface_patches(model)
    if not patches:
        raise ValueError("surface model requires patches")
    patch_ids = [str(item.get("patch_id", "")) for item in patches]
    if any(not item for item in patch_ids):
        raise ValueError("every surface patch requires patch_id")
    if len(set(patch_ids)) != len(patch_ids):
        raise ValueError("surface patch IDs must be unique")
    zones = {str(item.get("zone_id", "")) for item in patches}
    missing_zones = REQUIRED_ZONES - zones
    if missing_zones:
        raise ValueError(f"surface model missing zones: {', '.join(sorted(missing_zones))}")
    wheels = model.get("wheel_patches", [])
    if len(wheels) != 4:
        raise ValueError("surface model requires exactly four wheel patches")

    for patch in patches:
        surface_type = patch.get("surface_type")
        if surface_type not in SUPPORTED_SURFACE_TYPES:
            raise ValueError(f"unsupported surface_type: {surface_type}")
        if patch.get("zone_id") not in REQUIRED_ZONES:
            raise ValueError(f"unsupported zone_id: {patch.get('zone_id')}")
        if surface_type == "circular_disk":
            if float(patch.get("radius_mm", 0)) <= 0:
                raise ValueError(f"patch {patch['patch_id']} requires positive radius_mm")
            if not patch.get("center"):
                raise ValueError(f"patch {patch['patch_id']} requires center")
        else:
            dimensions = patch.get("dimensions", {})
            required = (
                ("width_mm", "length_mm", "arch_height_mm")
                if surface_type == "arched_rectangle"
                else (("length_mm", "height_mm") if patch["zone_id"] in {"left_side", "right_side"} else ("width_mm", "height_mm"))
            )
            if any(float(dimensions.get(key, 0)) <= 0 for key in required):
                raise ValueError(f"patch {patch['patch_id']} has invalid dimensions")
            if not patch.get("local_origin"):
                raise ValueError(f"patch {patch['patch_id']} requires local_origin")


def get_surface_patch(model: dict[str, Any], patch_id: str) -> dict[str, Any]:
    for patch in all_surface_patches(model):
        if patch.get("patch_id") == patch_id:
            return patch
    raise KeyError(f"surface patch not found: {patch_id}")


def get_patches_by_zone(model: dict[str, Any], zone_id: str) -> list[dict[str, Any]]:
    return [item for item in all_surface_patches(model) if item.get("zone_id") == zone_id]


def patch_local_bounds(patch: dict[str, Any]) -> dict[str, float]:
    surface_type = patch["surface_type"]
    if surface_type == "circular_disk":
        radius = float(patch["radius_mm"])
        return {"u_min_mm": -radius, "u_max_mm": radius, "v_min_mm": -radius, "v_max_mm": radius}
    dimensions = patch["dimensions"]
    if surface_type == "arched_rectangle":
        half_width = float(dimensions["width_mm"]) / 2.0
        return {"u_min_mm": -half_width, "u_max_mm": half_width, "v_min_mm": 0.0, "v_max_mm": float(dimensions["length_mm"])}
    primary = float(dimensions["length_mm"] if patch["zone_id"] in {"left_side", "right_side"} else dimensions["width_mm"])
    return {"u_min_mm": 0.0, "u_max_mm": primary, "v_min_mm": 0.0, "v_max_mm": float(dimensions["height_mm"])}


def get_reference_surface_point(patch: dict[str, Any], u_mm: float, v_mm: float) -> dict[str, float]:
    surface_type = patch["surface_type"]
    if surface_type == "circular_disk":
        center = patch["center"]
        return {
            "x_mm": float(center["x_mm"]),
            "y_mm": float(center["y_mm"]) + float(u_mm),
            "z_mm": float(center["z_mm"]) + float(v_mm),
        }

    origin = patch["local_origin"]
    if surface_type == "arched_rectangle":
        width = float(patch["dimensions"]["width_mm"])
        arch = float(patch["dimensions"]["arch_height_mm"])
        ratio = max(-1.0, min(1.0, 2.0 * float(u_mm) / width))
        return {
            "x_mm": float(origin["x_mm"]) + float(u_mm),
            "y_mm": float(origin["y_mm"]) + float(v_mm),
            "z_mm": float(origin["z_mm"]) + arch * (1.0 - ratio * ratio),
        }

    zone_id = patch["zone_id"]
    if zone_id in {"left_side", "right_side"}:
        return {
            "x_mm": float(origin["x_mm"]),
            "y_mm": float(origin["y_mm"]) + float(u_mm),
            "z_mm": float(origin["z_mm"]) + float(v_mm),
        }
    return {
        "x_mm": float(origin["x_mm"]) + float(u_mm),
        "y_mm": float(origin["y_mm"]),
        "z_mm": float(origin["z_mm"]) + float(v_mm),
    }


def get_reference_normal(patch: dict[str, Any], u_mm: float, v_mm: float) -> dict[str, float]:
    del v_mm
    direction = patch["normal_direction"]
    fixed = {
        "outward_left": (-1.0, 0.0, 0.0),
        "outward_right": (1.0, 0.0, 0.0),
        "outward_front": (0.0, 1.0, 0.0),
        "outward_rear": (0.0, -1.0, 0.0),
        "outward_up": (0.0, 0.0, 1.0),
    }
    if patch["surface_type"] == "arched_rectangle":
        width = float(patch["dimensions"]["width_mm"])
        arch = float(patch["dimensions"]["arch_height_mm"])
        dz_dx = -8.0 * arch * float(u_mm) / (width * width)
        vector = (-dz_dx, 0.0, 1.0)
    elif direction in fixed:
        vector = fixed[direction]
    else:
        raise ValueError(f"unsupported normal direction: {direction}")
    length = math.sqrt(sum(value * value for value in vector))
    return {"x": vector[0] / length, "y": vector[1] / length, "z": vector[2] / length}


def surface_local_to_world(patch: dict[str, Any], u_mm: float, v_mm: float) -> dict[str, float]:
    return get_reference_surface_point(patch, u_mm, v_mm)
