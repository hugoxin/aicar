import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
TEST_IMAGE_PATH = PROJECT_ROOT / "data" / "input_images" / "test_car.jpg"
RESULT_PATH = PROJECT_ROOT / "outputs" / "predictions" / "vehicle_type_result.json"
MAIN_PATH = PROJECT_ROOT / "src" / "vehicle_type_lab" / "main.py"


def main() -> None:
    if not TEST_IMAGE_PATH.exists():
        print(
            "No local test image found. Put a small image at "
            "vehicle_type_lab\\data\\input_images\\test_car.jpg "
            "to test YOLO vehicle detection."
        )
        return

    subprocess.run(
        [
            sys.executable,
            str(MAIN_PATH),
            "--mode",
            "detect",
            "--image",
            str(TEST_IMAGE_PATH),
        ],
        cwd=str(WORKSPACE_ROOT),
        check=True,
    )

    if not RESULT_PATH.exists():
        raise SystemExit(f"missing result JSON: {RESULT_PATH}")

    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    print(f"vehicle_detected: {result.get('vehicle_detected')}")
    print(f"confidence: {result.get('confidence')}")
    print(f"bbox: {result.get('bbox')}")
    print(f"model_name: {result.get('model_name')}")


if __name__ == "__main__":
    main()

