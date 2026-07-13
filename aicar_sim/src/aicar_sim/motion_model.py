from __future__ import annotations

import json
from pathlib import Path
from typing import Any


AXES = ("x", "y", "z")


def load_motion_model(path: str | Path) -> dict[str, Any]:
    """Load and validate a Stage4 motion model JSON file."""
    model_path = Path(path)
    if not model_path.exists():
        raise FileNotFoundError(f"motion model not found: {model_path}")
    with model_path.open("r", encoding="utf-8") as file:
        model = json.load(file)
    validate_motion_model(model)
    return model


def _require_dict(data: dict[str, Any], key: str, context: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{context}.{key} must be an object")
    return value


def _require_positive(data: dict[str, Any], key: str, context: str) -> float:
    value = data.get(key)
    if not isinstance(value, (int, float)) or float(value) <= 0:
        raise ValueError(f"{context}.{key} must be greater than 0")
    return float(value)


def validate_motion_model(model: dict[str, Any]) -> None:
    """Validate required fields and numeric ranges for a reference model."""
    for key in ("model_version", "motion_model_id", "display_name"):
        if not isinstance(model.get(key), str) or not model[key].strip():
            raise ValueError(f"motion_model.{key} must be a non-empty string")

    coordinate_system = _require_dict(model, "coordinate_system", "motion_model")
    if coordinate_system.get("unit") != "mm":
        raise ValueError("motion_model.coordinate_system.unit must be 'mm'")
    axes = _require_dict(coordinate_system, "axes", "motion_model.coordinate_system")
    for axis in AXES:
        if not isinstance(axes.get(axis), str) or not axes[axis].strip():
            raise ValueError(f"motion_model.coordinate_system.axes.{axis} is required")

    workspace = _require_dict(model, "workspace", "motion_model")
    for axis in AXES:
        min_key = f"{axis}_min_mm"
        max_key = f"{axis}_max_mm"
        minimum = workspace.get(min_key)
        maximum = workspace.get(max_key)
        if not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)):
            raise ValueError(f"motion_model.workspace.{axis} bounds must be numeric")
        if float(minimum) >= float(maximum):
            raise ValueError(f"motion_model.workspace.{min_key} must be less than {max_key}")

    axis_limits = _require_dict(model, "axis_limits", "motion_model")
    for axis in AXES:
        limits = _require_dict(axis_limits, axis, "motion_model.axis_limits")
        _require_positive(limits, "max_velocity_mm_s", f"motion_model.axis_limits.{axis}")
        _require_positive(limits, "max_acceleration_mm_s2", f"motion_model.axis_limits.{axis}")

    constraints = _require_dict(model, "path_constraints", "motion_model")
    for key in (
        "minimum_vehicle_clearance_mm",
        "preferred_nozzle_standoff_mm",
        "maximum_nozzle_standoff_mm",
        "maximum_segment_gap_mm",
        "minimum_segment_duration_s",
        "sampling_interval_s",
        "transition_velocity_scale",
    ):
        _require_positive(constraints, key, "motion_model.path_constraints")
    if constraints["preferred_nozzle_standoff_mm"] > constraints["maximum_nozzle_standoff_mm"]:
        raise ValueError("preferred nozzle standoff cannot exceed maximum standoff")
    if float(constraints["transition_velocity_scale"]) > 1:
        raise ValueError("transition_velocity_scale must be in the range (0, 1]")


def get_workspace_bounds(model: dict[str, Any]) -> dict[str, float]:
    validate_motion_model(model)
    return {key: float(value) for key, value in model["workspace"].items()}


def get_axis_velocity_limits(model: dict[str, Any]) -> dict[str, float]:
    validate_motion_model(model)
    return {
        axis: float(model["axis_limits"][axis]["max_velocity_mm_s"])
        for axis in AXES
    }


def get_axis_acceleration_limits(model: dict[str, Any]) -> dict[str, float]:
    validate_motion_model(model)
    return {
        axis: float(model["axis_limits"][axis]["max_acceleration_mm_s2"])
        for axis in AXES
    }


def is_point_inside_workspace(point: dict[str, Any], model: dict[str, Any]) -> bool:
    bounds = get_workspace_bounds(model)
    try:
        x = float(point["x_mm"])
        y = float(point["y_mm"])
        z = float(point["z_mm"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("point must contain numeric x_mm, y_mm, and z_mm") from exc
    return (
        bounds["x_min_mm"] <= x <= bounds["x_max_mm"]
        and bounds["y_min_mm"] <= y <= bounds["y_max_mm"]
        and bounds["z_min_mm"] <= z <= bounds["z_max_mm"]
    )
