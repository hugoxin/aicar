import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from vehicle_type_lab.export_result import export_result
from vehicle_type_lab.image_io import load_image_info
from vehicle_type_lab.mock_classifier import create_mock_result


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
}
ALLOWED_TYPES = {"sedan", "suv", "mpv", "unknown"}


def validate_result(result: dict) -> None:
    missing = sorted(REQUIRED_FIELDS - set(result))
    if missing:
        raise AssertionError(f"missing fields: {missing}")

    if result["vehicle_type"] not in ALLOWED_TYPES:
        raise AssertionError(f"unsupported vehicle_type: {result['vehicle_type']}")

    if not 0.0 <= float(result["confidence"]) <= 1.0:
        raise AssertionError("confidence must be between 0.0 and 1.0")

    bbox = result["bbox"]
    if bbox and len(bbox) != 4:
        raise AssertionError("bbox must be empty or contain four values")


def main() -> None:
    schema_path = PROJECT_ROOT / "schemas" / "vehicle_type_result.schema.json"
    if not schema_path.exists():
        raise SystemExit(f"missing schema: {schema_path}")

    image_io_path = PROJECT_ROOT / "src" / "vehicle_type_lab" / "image_io.py"
    if not image_io_path.exists():
        raise SystemExit(f"missing image_io module: {image_io_path}")

    yolo_detector_path = PROJECT_ROOT / "src" / "vehicle_type_lab" / "yolo_detector.py"
    if not yolo_detector_path.exists():
        raise SystemExit(f"missing yolo_detector module: {yolo_detector_path}")

    crop_utils_path = PROJECT_ROOT / "src" / "vehicle_type_lab" / "crop_utils.py"
    if not crop_utils_path.exists():
        raise SystemExit(f"missing crop_utils module: {crop_utils_path}")

    classifier_path = PROJECT_ROOT / "src" / "vehicle_type_lab" / "vehicle_type_classifier.py"
    if not classifier_path.exists():
        raise SystemExit(f"missing vehicle_type_classifier module: {classifier_path}")

    history_dir = PROJECT_ROOT / "outputs" / "predictions" / "history"
    if not history_dir.exists():
        raise SystemExit(f"missing history directory: {history_dir}")

    visualized_dir = PROJECT_ROOT / "outputs" / "predictions" / "visualized"
    if not visualized_dir.exists():
        raise SystemExit(f"missing visualized directory: {visualized_dir}")

    crops_dir = PROJECT_ROOT / "outputs" / "predictions" / "crops"
    if not crops_dir.exists():
        raise SystemExit(f"missing crops directory: {crops_dir}")

    example_paths = [
        PROJECT_ROOT / "examples" / "result_sedan.json",
        PROJECT_ROOT / "examples" / "result_suv.json",
        PROJECT_ROOT / "examples" / "result_mpv.json",
        PROJECT_ROOT / "examples" / "result_unknown.json",
    ]
    for path in example_paths:
        if not path.exists():
            raise SystemExit(f"missing example: {path}")
        validate_result(json.loads(path.read_text(encoding="utf-8")))

    result = create_mock_result("suv")
    validate_result(result)

    output_path = PROJECT_ROOT / "outputs" / "predictions" / "vehicle_type_result.json"
    export_result(result, output_path)
    validate_result(json.loads(output_path.read_text(encoding="utf-8")))

    main_path = PROJECT_ROOT / "src" / "vehicle_type_lab" / "main.py"
    subprocess.run(
        [sys.executable, str(main_path), "--mock-type", "suv"],
        cwd=str(WORKSPACE_ROOT),
        check=True,
    )
    validate_result(json.loads(output_path.read_text(encoding="utf-8")))

    missing_image = PROJECT_ROOT / "data" / "input_images" / "not_exist.jpg"
    subprocess.run(
        [
            sys.executable,
            str(main_path),
            "--image",
            str(missing_image),
            "--mock-type",
            "suv",
        ],
        cwd=str(WORKSPACE_ROOT),
        check=True,
    )
    missing_image_result = json.loads(output_path.read_text(encoding="utf-8"))
    validate_result(missing_image_result)
    if missing_image_result["vehicle_type"] != "unknown":
        raise AssertionError("missing image should produce unknown vehicle_type")

    image_info = load_image_info(str(missing_image))
    if image_info["exists"]:
        raise AssertionError("missing image check unexpectedly found an image")

    print("vehicle_type_lab interface check OK")


if __name__ == "__main__":
    main()
