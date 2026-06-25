"""Vehicle type classification inference using a trained YOLO cls model."""

from pathlib import Path
from typing import Any


ALLOWED_VEHICLE_TYPES = {"sedan", "suv", "mpv"}


def _unknown_result(model_path: str, notes: str) -> dict[str, Any]:
    path = Path(model_path)
    return {
        "vehicle_type": "unknown",
        "classification_confidence": 0.0,
        "classifier_model_name": path.name,
        "classifier_model_path": str(path),
        "classifier_notes": notes,
    }


def _as_float(value: Any) -> float:
    if hasattr(value, "item"):
        return float(value.item())
    return float(value)


def classify_vehicle_type(
    image: Any,
    classifier_model_path: str,
) -> dict[str, Any]:
    """Classify a cropped vehicle image as sedan/suv/mpv."""
    model_path = Path(classifier_model_path)
    if not model_path.exists():
        notes = "classifier model missing, run stage 1.7 first."
        print(f"warning: {notes}")
        return _unknown_result(str(model_path), notes)

    try:
        from ultralytics import YOLO

        model = YOLO(str(model_path))
        results = model(image, verbose=False)
        if not results:
            return _unknown_result(str(model_path), "Classifier returned no results.")

        result = results[0]
        if result.probs is None:
            return _unknown_result(
                str(model_path),
                "Classifier result did not include probabilities.",
            )

        class_id = int(result.probs.top1)
        confidence = _as_float(result.probs.top1conf)
        raw_name = str(result.names.get(class_id, "unknown")).lower()
        vehicle_type = raw_name if raw_name in ALLOWED_VEHICLE_TYPES else "unknown"
        notes = "Vehicle type classifier produced a top-1 prediction."
        if vehicle_type == "unknown":
            notes = f"Classifier produced unsupported class: {raw_name}"

        return {
            "vehicle_type": vehicle_type,
            "classification_confidence": confidence,
            "classifier_model_name": model_path.name,
            "classifier_model_path": str(model_path),
            "classifier_notes": notes,
        }
    except Exception as exc:
        notes = f"Vehicle type classification failed: {exc}"
        print(f"warning: {notes}")
        return _unknown_result(str(model_path), notes)
