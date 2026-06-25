import argparse
from datetime import datetime, timezone
from pathlib import Path

try:
    from vehicle_type_lab.crop_utils import crop_vehicle_region
    from vehicle_type_lab.export_result import export_result
    from vehicle_type_lab.image_io import load_image_info
    from vehicle_type_lab.mock_classifier import create_mock_result
    from vehicle_type_lab.vehicle_type_classifier import classify_vehicle_type
    from vehicle_type_lab.yolo_detector import detect_vehicle_bbox, detect_vehicle_with_yolo
except ModuleNotFoundError:
    from crop_utils import crop_vehicle_region
    from export_result import export_result
    from image_io import load_image_info
    from mock_classifier import create_mock_result
    from vehicle_type_classifier import classify_vehicle_type
    from yolo_detector import detect_vehicle_bbox, detect_vehicle_with_yolo


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "predictions" / "vehicle_type_result.json"
HISTORY_DIR = PROJECT_ROOT / "outputs" / "predictions" / "history"
DEFAULT_INPUT_IMAGE_PATH = PROJECT_ROOT / "data" / "input_images" / "test_car.jpg"
DEFAULT_CLASSIFIER_MODEL_PATH = PROJECT_ROOT / "models" / "vehicle_type_classifier" / "best.pt"
CROPS_DIR = PROJECT_ROOT / "outputs" / "predictions" / "crops"
VISUALIZED_DIR = PROJECT_ROOT / "outputs" / "predictions" / "visualized"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="vehicle_type_lab scaffold entrypoint")
    parser.add_argument(
        "--mode",
        choices=["mock", "detect", "classify"],
        default="mock",
        help="Run mock, YOLO detection only, or detection plus vehicle type classification.",
    )
    parser.add_argument(
        "--mock-type",
        choices=["sedan", "suv", "mpv", "unknown"],
        help="Generate a mock vehicle type result without loading any AI model.",
    )
    parser.add_argument(
        "--image",
        help="Optional image path. The scaffold reads image dimensions only.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Output JSON path.",
    )
    parser.add_argument(
        "--save-history",
        action="store_true",
        help="Also save a timestamped result under outputs/predictions/history.",
    )
    parser.add_argument(
        "--source-image",
        default="mock_image.jpg",
        help="Source image name or path recorded when --image is not provided.",
    )
    parser.add_argument(
        "--model-name",
        dest="detector_model",
        default=argparse.SUPPRESS,
        help="Deprecated alias for --detector-model.",
    )
    parser.add_argument(
        "--detector-model",
        dest="detector_model",
        default="yolo11n.pt",
        help="YOLO detector model used in detect/classify mode.",
    )
    parser.add_argument(
        "--classifier-model",
        default=str(DEFAULT_CLASSIFIER_MODEL_PATH),
        help="Vehicle type classifier model path used in classify mode.",
    )
    return parser


def build_result(args: argparse.Namespace) -> dict:
    image_info = None
    source_image = args.source_image
    image_width = 1280
    image_height = 720
    mock_type = args.mock_type or "unknown"
    notes = "Mock result for interface testing only. No AI model was loaded."

    if args.image:
        image_info = load_image_info(args.image)
        source_image = image_info["source_image"]
        image_width = image_info["image_width"] or image_width
        image_height = image_info["image_height"] or image_height

        if image_info["exists"] and not image_info["error"]:
            notes = (
                "Image dimensions were read successfully. "
                "Vehicle type is still a mock result; no AI model was loaded."
            )
        else:
            mock_type = "unknown"
            notes = (
                "Input image could not be used; generated unknown mock result. "
                f"Reason: {image_info['error']}"
            )

    return create_mock_result(
        mock_type,
        source_image=source_image,
        image_width=image_width,
        image_height=image_height,
        notes=notes,
    )


def save_history_result(result: dict) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    history_path = HISTORY_DIR / f"vehicle_type_result_{timestamp}_{result['vehicle_type']}.json"
    export_result(result, history_path)
    return history_path


def save_classified_visualization(
    image_path: str,
    bbox: list[int],
    vehicle_type: str,
    classification_confidence: float,
) -> Path:
    from PIL import Image, ImageDraw, ImageFont

    VISUALIZED_DIR.mkdir(parents=True, exist_ok=True)
    source_path = Path(image_path)
    output_path = VISUALIZED_DIR / f"{source_path.stem}_classified.jpg"

    with Image.open(source_path) as image:
        visualized = image.convert("RGB")
        draw = ImageDraw.Draw(visualized)
        x1, y1, x2, y2 = bbox
        draw.rectangle((x1, y1, x2, y2), outline="lime", width=4)
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
        label_lines = [
            "detected vehicle",
            f"type: {vehicle_type}",
            f"cls_conf: {classification_confidence:.2f}",
        ]
        label_y = max(0, y1 - 42)
        for index, label in enumerate(label_lines):
            draw.text((x1, label_y + index * 14), label, fill="lime", font=font)
        visualized.save(output_path, quality=90)

    return output_path


def build_classify_result(args: argparse.Namespace) -> dict:
    image_path = args.image or str(DEFAULT_INPUT_IMAGE_PATH)
    detection = detect_vehicle_bbox(image_path, args.detector_model)

    classifier_path = Path(args.classifier_model)
    if not classifier_path.is_absolute():
        classifier_path = Path.cwd() / classifier_path

    classification = {
        "vehicle_type": "unknown",
        "classification_confidence": 0.0,
        "classifier_model_name": classifier_path.name,
        "classifier_model_path": str(classifier_path),
        "classifier_notes": "Classification was not run because no vehicle was detected.",
    }
    crop_path = ""
    classified_visualization_path = ""

    if detection["vehicle_detected"]:
        source_path = Path(detection["source_image"])
        crop_output_path = CROPS_DIR / f"{source_path.stem}_crop.jpg"
        try:
            crop_image = crop_vehicle_region(
                detection["source_image"],
                detection["bbox"],
                margin_ratio=0.12,
                output_path=crop_output_path,
            )
            crop_path = str(crop_output_path)
            classification = classify_vehicle_type(crop_image, str(classifier_path))
            classified_visualization_path = str(
                save_classified_visualization(
                    detection["source_image"],
                    detection["bbox"],
                    classification["vehicle_type"],
                    classification["classification_confidence"],
                )
            )
        except Exception as exc:
            classification["classifier_notes"] = (
                f"Vehicle crop/classification step failed: {exc}"
            )
            print(f"warning: {classification['classifier_notes']}")

    classification_confidence = float(classification["classification_confidence"])
    detection_confidence = float(detection["detection_confidence"])
    confidence = classification_confidence if classification_confidence > 0 else detection_confidence
    vehicle_type = classification["vehicle_type"]
    notes = (
        f"{detection['notes']} {classification['classifier_notes']} "
        "This classify pipeline is a small-sample demo and may confuse MPV/SUV boundary cases."
    )
    if classified_visualization_path:
        notes += f" Classified visualization saved to {classified_visualization_path}."

    return {
        "vehicle_detected": bool(detection["vehicle_detected"]),
        "vehicle_type": vehicle_type,
        "confidence": confidence,
        "bbox": detection["bbox"],
        "source_image": detection["source_image"],
        "image_width": int(detection["image_width"]),
        "image_height": int(detection["image_height"]),
        "model_name": (
            f"{detection['detector_model_name']} + "
            f"{classification['classifier_model_name']}"
        ),
        "model_version": "yolo-detect-plus-vehicle-type-classifier",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "notes": notes,
        "detection_confidence": detection_confidence,
        "classification_confidence": classification_confidence,
        "detector_model_name": detection["detector_model_name"],
        "classifier_model_name": classification["classifier_model_name"],
        "classifier_model_path": classification["classifier_model_path"],
        "crop_path": crop_path,
        "pipeline_mode": "classify",
    }


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.mode == "detect":
        if not args.image:
            parser.error("--image is required when --mode detect")
        result = detect_vehicle_with_yolo(args.image, args.detector_model)
        output_path = Path(args.output)
        export_result(result, output_path)
        print(f"vehicle_type_lab detect result saved: {output_path.resolve()}")
        print(f"vehicle_detected: {result['vehicle_detected']}")
        print(f"vehicle_type: {result['vehicle_type']}")
        if args.save_history:
            history_path = save_history_result(result)
            print(f"vehicle_type_lab history result saved: {history_path.resolve()}")
        return

    if args.mode == "classify":
        result = build_classify_result(args)
        output_path = Path(args.output)
        export_result(result, output_path)
        print(f"vehicle_type_lab classify result saved: {output_path.resolve()}")
        print(f"vehicle_detected: {result['vehicle_detected']}")
        print(f"vehicle_type: {result['vehicle_type']}")
        print(f"detection_confidence: {result['detection_confidence']}")
        print(f"classification_confidence: {result['classification_confidence']}")
        print(f"bbox: {result['bbox']}")
        print(f"crop_path: {result['crop_path']}")
        if args.save_history:
            history_path = save_history_result(result)
            print(f"vehicle_type_lab history result saved: {history_path.resolve()}")
        return

    if args.mock_type or args.image:
        result = build_result(args)
        output_path = Path(args.output)
        export_result(result, output_path)
        print(f"vehicle_type_lab mock result saved: {output_path.resolve()}")
        print(f"vehicle_type: {result['vehicle_type']}")
        if args.save_history:
            history_path = save_history_result(result)
            print(f"vehicle_type_lab history result saved: {history_path.resolve()}")
        return

    print("vehicle_type_lab scaffold")
    print("Target classes: sedan, SUV, MPV")
    print("Current phase: structure only; no training and no dataset download.")


if __name__ == "__main__":
    main()
