"""YOLO vehicle presence detection for phase 1.4."""

from datetime import datetime, timezone
from pathlib import Path

try:
    from vehicle_type_lab.image_io import load_image_info
except ModuleNotFoundError:
    from image_io import load_image_info


TARGET_CLASSES = {"car", "truck", "bus"}
DEFAULT_OUTPUT_DIR = (
    Path(__file__).resolve().parents[2] / "outputs" / "predictions" / "visualized"
)


def _base_result(
    image_path: str,
    image_width: int,
    image_height: int,
    model_name: str,
    notes: str,
) -> dict:
    return {
        "vehicle_detected": False,
        "vehicle_type": "unknown",
        "confidence": 0.0,
        "bbox": [],
        "source_image": image_path,
        "image_width": int(image_width),
        "image_height": int(image_height),
        "model_name": model_name,
        "model_version": "ultralytics-yolo-detect",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "notes": notes,
    }


def _save_visualized_image(image_path: str, bbox: list[int], confidence: float) -> str:
    from PIL import Image, ImageDraw, ImageFont

    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source_path = Path(image_path)
    output_path = DEFAULT_OUTPUT_DIR / f"{source_path.stem}_detected.jpg"

    with Image.open(source_path) as image:
        visualized = image.convert("RGB")
        draw = ImageDraw.Draw(visualized)
        x1, y1, x2, y2 = bbox
        draw.rectangle((x1, y1, x2, y2), outline="red", width=4)
        label = f"vehicle {confidence:.2f}"
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
        draw.text((x1, max(0, y1 - 14)), label, fill="red", font=font)
        visualized.save(output_path, quality=90)

    return str(output_path)


def detect_vehicle_bbox(image_path: str, model_name: str = "yolo11n.pt") -> dict:
    """Return the highest-confidence car/truck/bus bbox from a YOLO model."""
    image_info = load_image_info(image_path)
    if not image_info["exists"]:
        return {
            "vehicle_detected": False,
            "detection_confidence": 0.0,
            "bbox": [],
            "source_image": image_info["source_image"],
            "image_width": 0,
            "image_height": 0,
            "selected_class_name": "",
            "detector_model_name": model_name,
            "notes": "Input image does not exist; YOLO detection was not run.",
        }

    if image_info["error"]:
        return {
            "vehicle_detected": False,
            "detection_confidence": 0.0,
            "bbox": [],
            "source_image": image_info["source_image"],
            "image_width": image_info["image_width"],
            "image_height": image_info["image_height"],
            "selected_class_name": "",
            "detector_model_name": model_name,
            "notes": (
                "Input image could not be read; YOLO detection was not run. "
                f"Reason: {image_info['error']}"
            ),
        }

    from ultralytics import YOLO

    model = YOLO(model_name)
    results = model(image_path, verbose=False)

    best_detection: dict | None = None
    for result in results:
        names = result.names
        boxes = result.boxes
        if boxes is None:
            continue

        for box in boxes:
            class_id = int(box.cls[0].item())
            class_name = str(names.get(class_id, class_id)).lower()
            if class_name not in TARGET_CLASSES:
                continue

            confidence = float(box.conf[0].item())
            xyxy = [int(round(value)) for value in box.xyxy[0].tolist()]
            candidate = {
                "vehicle_detected": True,
                "detection_confidence": confidence,
                "bbox": xyxy,
                "source_image": image_info["source_image"],
                "image_width": image_info["image_width"],
                "image_height": image_info["image_height"],
                "selected_class_name": class_name,
                "detector_model_name": model_name,
                "notes": "YOLO detected a vehicle target.",
            }
            if (
                best_detection is None
                or confidence > best_detection["detection_confidence"]
            ):
                best_detection = candidate

    if best_detection is None:
        return {
            "vehicle_detected": False,
            "detection_confidence": 0.0,
            "bbox": [],
            "source_image": image_info["source_image"],
            "image_width": image_info["image_width"],
            "image_height": image_info["image_height"],
            "selected_class_name": "",
            "detector_model_name": model_name,
            "notes": (
                "YOLO only detects vehicle presence; no car, truck, or bus was found. "
                "Vehicle type classification is not enabled yet."
            ),
        }

    return best_detection


def detect_vehicle_with_yolo(image_path: str, model_name: str = "yolo11n.pt") -> dict:
    """Detect vehicle presence using an existing Ultralytics YOLO model."""
    detection = detect_vehicle_bbox(image_path, model_name)
    if not detection["vehicle_detected"]:
        return _base_result(
            image_path=detection["source_image"],
            image_width=detection["image_width"],
            image_height=detection["image_height"],
            model_name=model_name,
            notes=detection["notes"],
        )

    best_detection = {
        "vehicle_detected": True,
        "vehicle_type": "unknown",
        "confidence": detection["detection_confidence"],
        "bbox": detection["bbox"],
        "source_image": detection["source_image"],
        "image_width": detection["image_width"],
        "image_height": detection["image_height"],
        "model_name": model_name,
        "model_version": "ultralytics-yolo-detect",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "notes": (
            "YOLO only detects vehicle presence; vehicle type classification "
            "is not enabled yet."
        ),
        "detection_confidence": detection["detection_confidence"],
        "detector_model_name": detection["detector_model_name"],
        "selected_class_name": detection["selected_class_name"],
    }

    visualized_path = _save_visualized_image(
        detection["source_image"],
        best_detection["bbox"],
        best_detection["confidence"],
    )
    best_detection["notes"] = (
        best_detection["notes"] + f" Visualized result saved to {visualized_path}."
    )
    return best_detection
