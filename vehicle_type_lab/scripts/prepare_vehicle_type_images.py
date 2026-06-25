import argparse
import csv
import stat
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageOps


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = PROJECT_ROOT / "data" / "datasets" / "vehicle_type_classification"
DEFAULT_SOURCE_ROOT = DATASET_ROOT / "incoming"
DEFAULT_OUTPUT_ROOT = DATASET_ROOT / "raw"
REPORT_PATH = DATASET_ROOT / "manifests" / "preprocess_report.csv"
CLASSES = ("sedan", "suv", "mpv")
SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
RAW_OUTPUT_SUFFIXES = {".jpg", ".jpeg", ".png"}
TARGET_YOLO_CLASSES = {"car", "truck", "bus"}
RECOMMENDED_MIN_PER_CLASS = 20


@dataclass
class ProcessRecord:
    class_name: str
    source_path: str
    output_path: str
    status: str
    method: str
    width: int
    height: int
    notes: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Standardize incoming sedan/suv/mpv images into raw training-ready JPG files."
    )
    parser.add_argument("--size", type=int, default=640, help="Output square image size.")
    parser.add_argument(
        "--source-root",
        default=str(DEFAULT_SOURCE_ROOT),
        help="Root directory containing incoming/sedan, incoming/suv, incoming/mpv.",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="Root directory for standardized raw/sedan, raw/suv, raw/mpv outputs.",
    )
    parser.add_argument(
        "--use-yolo-crop",
        action="store_true",
        help="Use YOLO vehicle bbox as an optional crop before letterbox resize.",
    )
    parser.add_argument(
        "--margin-ratio",
        type=float,
        default=0.12,
        help="Margin around YOLO bbox before cropping.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting existing standardized images.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned processing without writing files or running YOLO.",
    )
    parser.add_argument(
        "--clean-output",
        action="store_true",
        help="Remove old raw images and preprocess report before regenerating outputs.",
    )
    return parser


def iter_images(class_dir: Path) -> Iterable[Path]:
    if not class_dir.exists():
        return []
    return sorted(
        path
        for path in class_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    )


def count_images(directory: Path, suffixes: set[str]) -> int:
    if not directory.exists():
        return 0
    return sum(
        1
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in suffixes
    )


def clean_output(output_root: Path) -> None:
    removed_images = 0
    failed_paths: list[str] = []
    for class_name in CLASSES:
        class_output_dir = output_root / class_name
        if not class_output_dir.exists():
            continue
        for path in class_output_dir.iterdir():
            if path.is_file() and path.suffix.lower() in RAW_OUTPUT_SUFFIXES:
                try:
                    path.chmod(stat.S_IWRITE)
                    path.unlink()
                    removed_images += 1
                except PermissionError:
                    failed_paths.append(str(path))

    if REPORT_PATH.exists():
        try:
            REPORT_PATH.chmod(stat.S_IWRITE)
            REPORT_PATH.unlink()
            print(f"removed old preprocess report: {REPORT_PATH}")
        except PermissionError:
            failed_paths.append(str(REPORT_PATH))

    print(f"removed raw image files: {removed_images}")
    if failed_paths:
        failed_text = "\n".join(f"- {path}" for path in failed_paths)
        raise PermissionError(f"failed to remove generated raw files:\n{failed_text}")


def print_raw_minimum_status(output_root: Path) -> None:
    raw_counts = {
        class_name: count_images(output_root / class_name, RAW_OUTPUT_SUFFIXES)
        for class_name in CLASSES
    }
    all_ok = True
    for class_name, count in raw_counts.items():
        print(f"raw/{class_name}: {count}")
        if count < RECOMMENDED_MIN_PER_CLASS:
            all_ok = False
            print(
                f"warning: raw/{class_name} has {count} images, "
                f"less than recommended minimum {RECOMMENDED_MIN_PER_CLASS}."
            )

    if all_ok:
        print("raw dataset minimum count OK: each class >= 20")


def next_index(output_dir: Path, class_name: str, overwrite: bool) -> int:
    if overwrite:
        return 1
    pattern = re.compile(rf"^{re.escape(class_name)}_local_(\d{{4}})\.jpg$", re.IGNORECASE)
    max_index = 0
    if output_dir.exists():
        for path in output_dir.iterdir():
            match = pattern.match(path.name)
            if match:
                max_index = max(max_index, int(match.group(1)))
    return max_index + 1


def output_path_for(output_dir: Path, class_name: str, index: int) -> Path:
    return output_dir / f"{class_name}_local_{index:04d}.jpg"


def load_image(path: Path) -> Image.Image:
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image)
        return image.convert("RGB")


def best_yolo_bbox(image_path: Path, model) -> list[int] | None:
    results = model(str(image_path), verbose=False)
    best_box: list[int] | None = None
    best_confidence = -1.0
    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue
        names = result.names
        for box in boxes:
            class_id = int(box.cls[0].item())
            class_name = str(names.get(class_id, class_id)).lower()
            if class_name not in TARGET_YOLO_CLASSES:
                continue
            confidence = float(box.conf[0].item())
            if confidence > best_confidence:
                best_confidence = confidence
                best_box = [int(round(value)) for value in box.xyxy[0].tolist()]
    return best_box


def crop_with_margin(image: Image.Image, bbox: list[int], margin_ratio: float) -> Image.Image:
    width, height = image.size
    x1, y1, x2, y2 = bbox
    box_width = max(1, x2 - x1)
    box_height = max(1, y2 - y1)
    margin_x = int(round(box_width * margin_ratio))
    margin_y = int(round(box_height * margin_ratio))
    crop_box = (
        max(0, x1 - margin_x),
        max(0, y1 - margin_y),
        min(width, x2 + margin_x),
        min(height, y2 + margin_y),
    )
    return image.crop(crop_box)


def letterbox_resize(image: Image.Image, size: int) -> Image.Image:
    width, height = image.size
    scale = min(size / width, size / height)
    new_width = max(1, int(round(width * scale)))
    new_height = max(1, int(round(height * scale)))
    resample_filter = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
    resized = image.resize((new_width, new_height), resample_filter)
    canvas = Image.new("RGB", (size, size), (114, 114, 114))
    left = (size - new_width) // 2
    top = (size - new_height) // 2
    canvas.paste(resized, (left, top))
    return canvas


def write_report(records: list[ProcessRecord]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "class_name",
                "source_path",
                "output_path",
                "status",
                "method",
                "width",
                "height",
                "notes",
            ],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(record.__dict__)


def load_yolo_model():
    from ultralytics import YOLO

    return YOLO("yolo11n.pt")


def main() -> None:
    args = build_parser().parse_args()
    source_root = Path(args.source_root)
    output_root = Path(args.output_root)

    if args.clean_output:
        print("clean-output enabled")
        print("raw images will be removed and regenerated")
        print("incoming images will NOT be removed")
        if args.dry_run:
            print("dry-run only; no raw images or reports will be removed.")
        else:
            clean_output(output_root)

    planned: list[tuple[str, Path, Path, int]] = []
    indices = {
        class_name: next_index(output_root / class_name, class_name, args.overwrite)
        for class_name in CLASSES
    }

    for class_name in CLASSES:
        class_source_dir = source_root / class_name
        class_output_dir = output_root / class_name
        for source_path in iter_images(class_source_dir):
            output_path = output_path_for(class_output_dir, class_name, indices[class_name])
            planned.append((class_name, source_path, output_path, indices[class_name]))
            indices[class_name] += 1

    if not planned:
        print(f"No incoming images found under {source_root}.")
        print("Put images into incoming\\sedan, incoming\\suv, or incoming\\mpv, then run again.")
        return

    print(f"found incoming images: {len(planned)}")
    for class_name in CLASSES:
        class_count = sum(1 for planned_item in planned if planned_item[0] == class_name)
        print(f"  {class_name}: {class_count}")

    if args.dry_run:
        print("dry-run only; no files will be written and YOLO will not be loaded.")
        for class_name, source_path, output_path, _ in planned:
            print(f"would process [{class_name}] {source_path} -> {output_path}")
        print_raw_minimum_status(output_root)
        return

    yolo_model = None
    if args.use_yolo_crop:
        try:
            yolo_model = load_yolo_model()
        except Exception as exc:
            print(f"warning: YOLO is unavailable; fallback to letterbox. Reason: {exc}")

    records: list[ProcessRecord] = []
    for class_name, source_path, output_path, _ in planned:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.exists() and not args.overwrite:
            records.append(
                ProcessRecord(
                    class_name=class_name,
                    source_path=str(source_path),
                    output_path=str(output_path),
                    status="skipped",
                    method="letterbox",
                    width=0,
                    height=0,
                    notes="output already exists and overwrite is false",
                )
            )
            continue

        try:
            image = load_image(source_path)
            original_width, original_height = image.size
            method = "letterbox"
            notes = "standardized with whole-image letterbox"

            if args.use_yolo_crop and yolo_model is not None:
                bbox = best_yolo_bbox(source_path, yolo_model)
                if bbox:
                    image = crop_with_margin(image, bbox, args.margin_ratio)
                    method = "yolo_crop"
                    notes = f"cropped by YOLO vehicle bbox with margin_ratio={args.margin_ratio}"
                else:
                    method = "fallback_letterbox"
                    notes = "YOLO did not detect car/truck/bus; fallback to whole-image letterbox"
            elif args.use_yolo_crop:
                method = "fallback_letterbox"
                notes = "YOLO unavailable; fallback to whole-image letterbox"

            standardized = letterbox_resize(image, args.size)
            standardized.save(output_path, format="JPEG", quality=92)
            records.append(
                ProcessRecord(
                    class_name=class_name,
                    source_path=str(source_path),
                    output_path=str(output_path),
                    status="ok",
                    method=method,
                    width=original_width,
                    height=original_height,
                    notes=notes,
                )
            )
        except Exception as exc:
            records.append(
                ProcessRecord(
                    class_name=class_name,
                    source_path=str(source_path),
                    output_path=str(output_path),
                    status="error",
                    method="letterbox",
                    width=0,
                    height=0,
                    notes=str(exc),
                )
            )

    write_report(records)
    ok_count = sum(1 for record in records if record.status == "ok")
    skipped_count = sum(1 for record in records if record.status == "skipped")
    error_count = sum(1 for record in records if record.status == "error")
    print(f"preprocess complete: ok={ok_count}, skipped={skipped_count}, error={error_count}")
    print(f"report saved: {REPORT_PATH}")
    print_raw_minimum_status(output_root)


if __name__ == "__main__":
    main()
