"""Image input helpers for the vehicle type scaffold."""

from pathlib import Path


def _read_size_with_pillow(path: Path) -> tuple[int, int]:
    from PIL import Image

    with Image.open(path) as image:
        return image.size


def _read_size_with_opencv(path: Path) -> tuple[int, int]:
    import cv2

    image = cv2.imread(str(path))
    if image is None:
        raise ValueError("OpenCV could not read image")
    height, width = image.shape[:2]
    return width, height


def load_image_info(image_path: str) -> dict:
    """Return image existence and size information without running AI models."""
    path = Path(image_path)
    info = {
        "source_image": image_path,
        "image_width": 0,
        "image_height": 0,
        "exists": path.exists(),
        "error": "",
    }

    if not path.exists():
        info["error"] = "image file does not exist"
        return info

    if not path.is_file():
        info["exists"] = False
        info["error"] = "image path is not a file"
        return info

    readers = (_read_size_with_pillow, _read_size_with_opencv)
    errors: list[str] = []
    for reader in readers:
        try:
            width, height = reader(path)
            info["image_width"] = int(width)
            info["image_height"] = int(height)
            return info
        except Exception as exc:
            errors.append(f"{reader.__name__}: {exc}")

    info["error"] = "; ".join(errors)
    return info

