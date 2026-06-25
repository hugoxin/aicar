from math import ceil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = PROJECT_ROOT / "data" / "datasets" / "vehicle_type_classification"
SPLIT_ROOT = DATASET_ROOT / "split"
REVIEW_ROOT = DATASET_ROOT / "review"
CLASSES = ("sedan", "suv", "mpv")
SPLITS = ("train", "val")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
THUMB_SIZE = 160
LABEL_HEIGHT = 34
GAP = 12
BACKGROUND = (245, 245, 245)
TILE_BACKGROUND = (255, 255, 255)
TEXT_COLOR = (30, 30, 30)


def list_images(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def load_font() -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", 12)
    except OSError:
        return ImageFont.load_default()


def truncate_label(label: str, max_chars: int = 24) -> str:
    if len(label) <= max_chars:
        return label
    return f"{label[: max_chars - 3]}..."


def make_contact_sheet(split_name: str, class_name: str, image_paths: list[Path]) -> Path | None:
    if not image_paths:
        print(f"No images found for split/{split_name}/{class_name}; skipping contact sheet.")
        return None

    REVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    output_path = REVIEW_ROOT / f"split_{split_name}_{class_name}.jpg"
    font = load_font()
    columns = min(4, max(1, len(image_paths)))
    rows = ceil(len(image_paths) / columns)
    tile_width = THUMB_SIZE
    tile_height = THUMB_SIZE + LABEL_HEIGHT
    canvas_width = columns * tile_width + (columns + 1) * GAP
    canvas_height = rows * tile_height + (rows + 1) * GAP
    canvas = Image.new("RGB", (canvas_width, canvas_height), BACKGROUND)
    draw = ImageDraw.Draw(canvas)

    for index, image_path in enumerate(image_paths):
        row = index // columns
        column = index % columns
        x = GAP + column * (tile_width + GAP)
        y = GAP + row * (tile_height + GAP)
        tile = Image.new("RGB", (tile_width, tile_height), TILE_BACKGROUND)

        with Image.open(image_path) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            image.thumbnail((THUMB_SIZE, THUMB_SIZE), Image.Resampling.LANCZOS)
            left = (THUMB_SIZE - image.width) // 2
            top = (THUMB_SIZE - image.height) // 2
            tile.paste(image, (left, top))

        label = truncate_label(image_path.name)
        tile_draw = ImageDraw.Draw(tile)
        tile_draw.text((4, THUMB_SIZE + 8), label, fill=TEXT_COLOR, font=font)
        canvas.paste(tile, (x, y))
        draw.rectangle((x, y, x + tile_width - 1, y + tile_height - 1), outline=(210, 210, 210))

    canvas.save(output_path, quality=92)
    print(f"contact sheet saved: {output_path}")
    return output_path


def main() -> None:
    generated = 0
    for split_name in SPLITS:
        for class_name in CLASSES:
            image_dir = SPLIT_ROOT / split_name / class_name
            output_path = make_contact_sheet(split_name, class_name, list_images(image_dir))
            if output_path is not None:
                generated += 1

    print(f"contact sheets generated: {generated}")


if __name__ == "__main__":
    main()

