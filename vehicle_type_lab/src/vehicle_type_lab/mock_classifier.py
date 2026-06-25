"""Mock vehicle type classifier for interface testing only."""

from datetime import datetime, timezone


ALLOWED_VEHICLE_TYPES = {"sedan", "suv", "mpv", "unknown"}


def create_mock_result(
    vehicle_type: str,
    source_image: str = "mock_image.jpg",
    image_width: int = 1280,
    image_height: int = 720,
    notes: str | None = None,
) -> dict:
    """Create a vehicle type result without loading any AI model."""
    normalized_type = vehicle_type.lower()
    if normalized_type not in ALLOWED_VEHICLE_TYPES:
        allowed = ", ".join(sorted(ALLOWED_VEHICLE_TYPES))
        raise ValueError(f"vehicle_type must be one of: {allowed}")

    vehicle_detected = normalized_type != "unknown"
    confidence_by_type = {
        "sedan": 0.91,
        "suv": 0.9,
        "mpv": 0.88,
        "unknown": 0.2,
    }
    bbox = [] if normalized_type == "unknown" else [120, 80, 1180, 700]

    return {
        "vehicle_detected": vehicle_detected,
        "vehicle_type": normalized_type,
        "confidence": confidence_by_type[normalized_type],
        "bbox": bbox,
        "source_image": source_image,
        "image_width": int(image_width),
        "image_height": int(image_height),
        "model_name": "mock_vehicle_type_classifier",
        "model_version": "0.1.0-mock",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "notes": notes or "Mock result for interface testing only. No AI model was loaded.",
    }
