"""Crop helpers for YOLO bbox based vehicle type classification."""

from pathlib import Path
from typing import Sequence

from PIL import Image, ImageOps


def expand_bbox(
    bbox: Sequence[int | float],
    image_width: int,
    image_height: int,
    margin_ratio: float = 0.12,
) -> list[int]:
    """Expand a bbox by a margin and clamp it to image boundaries."""
    if len(bbox) != 4:
        raise ValueError("bbox must contain four values")

    x1, y1, x2, y2 = [float(value) for value in bbox]
    box_width = max(1.0, x2 - x1)
    box_height = max(1.0, y2 - y1)
    margin_x = box_width * margin_ratio
    margin_y = box_height * margin_ratio

    expanded = [
        int(max(0, round(x1 - margin_x))),
        int(max(0, round(y1 - margin_y))),
        int(min(image_width, round(x2 + margin_x))),
        int(min(image_height, round(y2 + margin_y))),
    ]

    if expanded[2] <= expanded[0] or expanded[3] <= expanded[1]:
        raise ValueError(f"expanded bbox is invalid: {expanded}")
    return expanded


def crop_vehicle_region(
    image_path: str,
    bbox: Sequence[int | float],
    margin_ratio: float = 0.12,
    output_path: str | Path | None = None,
) -> Image.Image:
    """Crop a vehicle region from an image and optionally save the crop."""
    with Image.open(image_path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        expanded_bbox = expand_bbox(bbox, image.width, image.height, margin_ratio)
        crop = image.crop(tuple(expanded_bbox))

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        crop.save(path, quality=92)

    return crop
