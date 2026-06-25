import argparse
import csv
import random
import shutil
import stat
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = PROJECT_ROOT / "data" / "datasets" / "vehicle_type_classification"
DEFAULT_RAW_ROOT = DATASET_ROOT / "raw"
DEFAULT_SPLIT_ROOT = DATASET_ROOT / "split"
SPLIT_MANIFEST_PATH = DATASET_ROOT / "manifests" / "split_manifest.csv"
CLASSES = ("sedan", "suv", "mpv")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
MIN_WARNING_COUNT = 5


@dataclass(frozen=True)
class SplitRecord:
    class_name: str
    split: str
    image_path: str
    source_raw_path: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Copy standardized raw vehicle type images into train/val splits."
    )
    parser.add_argument("--train-ratio", type=float, default=0.8, help="Train split ratio.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible split.")
    parser.add_argument(
        "--clean-split",
        action="store_true",
        help="Remove old split images before copying. Only split/train and split/val images are removed.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print split plan without copying files.")
    return parser


def list_images(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def count_images(directory: Path) -> int:
    return len(list_images(directory))


def clean_split(split_root: Path) -> int:
    removed = 0
    for split_name in ("train", "val"):
        for class_name in CLASSES:
            split_dir = split_root / split_name / class_name
            if not split_dir.exists():
                continue
            for path in split_dir.iterdir():
                if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
                    path.chmod(stat.S_IWRITE)
                    path.unlink()
                    removed += 1
    return removed


def relative_to_dataset(path: Path) -> str:
    return path.relative_to(DATASET_ROOT).as_posix()


def write_manifest(records: list[SplitRecord]) -> None:
    SPLIT_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SPLIT_MANIFEST_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["class_name", "split", "image_path", "source_raw_path"],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(record.__dict__)


def split_class_images(class_name: str, images: list[Path], train_ratio: float, seed: int) -> tuple[list[Path], list[Path]]:
    shuffled = list(images)
    rng = random.Random(f"{seed}:{class_name}")
    rng.shuffle(shuffled)
    train_count = int(len(shuffled) * train_ratio)
    return shuffled[:train_count], shuffled[train_count:]


def print_counts(title: str, counts: dict[str, int]) -> None:
    print(title)
    for class_name in CLASSES:
        print(f"{class_name}: {counts[class_name]}")


def main() -> None:
    args = build_parser().parse_args()
    if not 0.0 < args.train_ratio < 1.0:
        raise SystemExit("--train-ratio must be between 0.0 and 1.0")

    raw_counts = {
        class_name: count_images(DEFAULT_RAW_ROOT / class_name)
        for class_name in CLASSES
    }
    print_counts("raw counts:", raw_counts)

    plan: dict[str, tuple[list[Path], list[Path]]] = {}
    for class_name in CLASSES:
        images = list_images(DEFAULT_RAW_ROOT / class_name)
        if len(images) < MIN_WARNING_COUNT:
            print(f"warning: raw/{class_name} has fewer than {MIN_WARNING_COUNT} images.")
        plan[class_name] = split_class_images(class_name, images, args.train_ratio, args.seed)

    print("split result:")
    for class_name in CLASSES:
        train_images, val_images = plan[class_name]
        print(f"train/{class_name}: {len(train_images)}")
        print(f"val/{class_name}: {len(val_images)}")

    records: list[SplitRecord] = []
    for class_name in CLASSES:
        for split_name, images in (("train", plan[class_name][0]), ("val", plan[class_name][1])):
            for raw_path in images:
                target_path = DEFAULT_SPLIT_ROOT / split_name / class_name / raw_path.name
                records.append(
                    SplitRecord(
                        class_name=class_name,
                        split=split_name,
                        image_path=relative_to_dataset(target_path),
                        source_raw_path=relative_to_dataset(raw_path),
                    )
                )

    if args.dry_run:
        print("dry-run only; no split images will be copied.")
        print(f"split_manifest would be saved: {SPLIT_MANIFEST_PATH}")
        return

    if args.clean_split:
        print("clean-split enabled")
        print("split/train and split/val images will be removed and regenerated")
        print("raw and incoming images will NOT be removed")
        removed = clean_split(DEFAULT_SPLIT_ROOT)
        print(f"removed split image files: {removed}")

    for record in records:
        source_path = DATASET_ROOT / record.source_raw_path
        target_path = DATASET_ROOT / record.image_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)

    write_manifest(records)
    print(f"split_manifest saved: {SPLIT_MANIFEST_PATH}")


if __name__ == "__main__":
    main()

