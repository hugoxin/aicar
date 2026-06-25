"""Read vehicle type results produced by vehicle_type_lab."""

import json
from pathlib import Path


KNOWN_VEHICLE_TYPES = {"sedan", "suv", "mpv"}
ALLOWED_VEHICLE_TYPES = KNOWN_VEHICLE_TYPES | {"unknown"}
DEFAULT_VEHICLE_TYPE = "suv"


def load_vehicle_type_result(json_path: str) -> dict:
    """Load a vehicle type JSON result."""
    path = Path(json_path)
    with path.open("r", encoding="utf-8") as file:
        result = json.load(file)
    return result


def _normalized_vehicle_type(result: dict) -> str:
    vehicle_type = str(result.get("vehicle_type", "unknown")).lower()
    if vehicle_type not in ALLOWED_VEHICLE_TYPES:
        return "unknown"
    return vehicle_type


def _select_vehicle_type(result: dict) -> tuple[str, bool, str]:
    """Return selected vehicle type, fallback flag, and warning text."""
    vehicle_detected = bool(result.get("vehicle_detected"))
    raw_vehicle_type = str(result.get("vehicle_type", "unknown")).lower()
    vehicle_type = _normalized_vehicle_type(result)

    if not vehicle_detected:
        warning = (
            "warning: vehicle was not detected; "
            f"defaulting to {DEFAULT_VEHICLE_TYPE}.json"
        )
        print(warning)
        return DEFAULT_VEHICLE_TYPE, True, warning

    if vehicle_type == "unknown":
        warning = (
            "warning: vehicle type is unknown or not detected; "
            f"defaulting to {DEFAULT_VEHICLE_TYPE}.json"
        )
        print(warning)
        return DEFAULT_VEHICLE_TYPE, True, warning

    if raw_vehicle_type not in KNOWN_VEHICLE_TYPES:
        warning = (
            f"warning: unsupported vehicle_type '{raw_vehicle_type}'; "
            f"defaulting to {DEFAULT_VEHICLE_TYPE}.json"
        )
        print(warning)
        return DEFAULT_VEHICLE_TYPE, True, warning

    return vehicle_type, False, ""


def resolve_vehicle_model_path(result: dict, vehicles_dir: str) -> str:
    """Resolve vehicle model JSON path from a vehicle type result."""
    vehicle_type, _, _ = _select_vehicle_type(result)
    model_path = Path(vehicles_dir) / f"{vehicle_type}.json"
    return str(model_path.resolve())


def load_vehicle_model(model_path: str) -> dict:
    """Load a selected vehicle model JSON."""
    path = Path(model_path)
    with path.open("r", encoding="utf-8") as file:
        model = json.load(file)

    # Backward-compatible shape for early scaffold vehicle JSON files.
    if "length_mm" not in model and "length" in model:
        model["length_mm"] = model["length"]
    if "width_mm" not in model and "width" in model:
        model["width_mm"] = model["width"]
    if "height_mm" not in model and "height" in model:
        model["height_mm"] = model["height"]
    if "vehicle_type" not in model and "name" in model:
        model["vehicle_type"] = model["name"]
    if "wash_profile" not in model:
        vehicle_type = str(model.get("vehicle_type", DEFAULT_VEHICLE_TYPE)).lower()
        model["wash_profile"] = f"standard_{vehicle_type}"

    return model


def build_vehicle_model_selection(result: dict, vehicles_dir: str) -> dict:
    """Build the aicar_sim vehicle model selection summary."""
    selected_type, fallback_used, warning = _select_vehicle_type(result)
    model_path = Path(vehicles_dir) / f"{selected_type}.json"
    model = load_vehicle_model(str(model_path))

    return {
        "vehicle_detected": bool(result.get("vehicle_detected")),
        "vehicle_type": _normalized_vehicle_type(result),
        "detection_confidence": float(result.get("detection_confidence", 0.0) or 0.0),
        "classification_confidence": float(
            result.get("classification_confidence", 0.0) or 0.0
        ),
        "bbox": result.get("bbox", []),
        "source_image": str(result.get("source_image", "")),
        "pipeline_mode": str(result.get("pipeline_mode", "")),
        "resolved_vehicle_model_path": str(model_path.resolve()),
        "resolved_vehicle_model": model,
        "fallback_used": fallback_used,
        "fallback_reason": warning,
    }
