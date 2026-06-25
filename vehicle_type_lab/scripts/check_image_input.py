import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from vehicle_type_lab.image_io import load_image_info


TEST_IMAGE_PATH = PROJECT_ROOT / "data" / "input_images" / "test_car.jpg"


def main() -> None:
    if not TEST_IMAGE_PATH.exists():
        print(
            "No local test image found. Put a small image at "
            "vehicle_type_lab\\data\\input_images\\test_car.jpg "
            "to test real image size reading."
        )
        return

    info = load_image_info(str(TEST_IMAGE_PATH))
    if info["error"]:
        raise SystemExit(f"Failed to read local test image: {info['error']}")

    print("Local test image found")
    print(f"image_path: {TEST_IMAGE_PATH}")
    print(f"image_width: {info['image_width']}")
    print(f"image_height: {info['image_height']}")


if __name__ == "__main__":
    main()

