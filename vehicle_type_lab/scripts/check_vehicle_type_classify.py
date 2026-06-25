import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
TEST_IMAGE_PATH = PROJECT_ROOT / "data" / "input_images" / "test_car.jpg"
RESULT_PATH = PROJECT_ROOT / "outputs" / "predictions" / "vehicle_type_result.json"
CLASSIFIER_MODEL_PATH = PROJECT_ROOT / "models" / "vehicle_type_classifier" / "best.pt"
CLASSIFIED_IMAGE_PATH = (
    PROJECT_ROOT / "outputs" / "predictions" / "visualized" / "test_car_classified.jpg"
)
MAIN_PATH = PROJECT_ROOT / "src" / "vehicle_type_lab" / "main.py"

ALLOWED_TYPES = {"sedan", "suv", "mpv", "unknown"}
REQUIRED_FIELDS = {
    "vehicle_detected",
    "vehicle_type",
    "confidence",
    "bbox",
    "source_image",
    "image_width",
    "image_height",
    "model_name",
    "model_version",
    "timestamp",
    "notes",
    "detection_confidence",
    "classification_confidence",
    "detector_model_name",
    "classifier_model_name",
    "classifier_model_path",
    "crop_path",
    "pipeline_mode",
}


def main() -> None:
    if not TEST_IMAGE_PATH.exists():
        print(
            "No local test image found. Put a small image at "
            "vehicle_type_lab\\data\\input_images\\test_car.jpg "
            "to test classify mode."
        )
        return

    if not CLASSIFIER_MODEL_PATH.exists():
        print("classifier model missing, run stage 1.7 first.")
        return

    subprocess.run(
        [
            sys.executable,
            str(MAIN_PATH),
            "--mode",
            "classify",
            "--image",
            str(TEST_IMAGE_PATH),
            "--save-history",
        ],
        cwd=str(WORKSPACE_ROOT),
        check=True,
    )

    if not RESULT_PATH.exists():
        raise SystemExit(f"missing result JSON: {RESULT_PATH}")

    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED_FIELDS - set(result))
    if missing:
        raise AssertionError(f"missing classify result fields: {missing}")

    if result["pipeline_mode"] != "classify":
        raise AssertionError("pipeline_mode must be classify")

    if result["vehicle_type"] not in ALLOWED_TYPES:
        raise AssertionError(f"unsupported vehicle_type: {result['vehicle_type']}")

    if not result["vehicle_detected"]:
        raise AssertionError("test_car.jpg should produce vehicle_detected=true")

    if not result["bbox"]:
        raise AssertionError("bbox is required for classify mode test image")

    if "detection_confidence" not in result:
        raise AssertionError("missing detection_confidence")

    if "classification_confidence" not in result:
        raise AssertionError("missing classification_confidence")

    crop_path = Path(result["crop_path"])
    if not crop_path.exists():
        raise AssertionError(f"missing crop image: {crop_path}")

    if not CLASSIFIED_IMAGE_PATH.exists():
        raise AssertionError(f"missing classified visualization: {CLASSIFIED_IMAGE_PATH}")

    print("vehicle_type_lab classify check OK")
    print(f"vehicle_detected: {result['vehicle_detected']}")
    print(f"vehicle_type: {result['vehicle_type']}")
    print(f"detection_confidence: {result['detection_confidence']}")
    print(f"classification_confidence: {result['classification_confidence']}")
    print(f"bbox: {result['bbox']}")
    print(f"crop_path: {result['crop_path']}")
    print(f"classified_visualization: {CLASSIFIED_IMAGE_PATH}")


if __name__ == "__main__":
    main()
