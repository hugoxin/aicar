"""Vehicle detection placeholders."""


def detect_vehicle_placeholder(image_path: str) -> dict[str, object]:
    """Return a placeholder detection result for future YOLO integration."""
    return {
        "vehicle_detected": False,
        "source_image": image_path,
    }

