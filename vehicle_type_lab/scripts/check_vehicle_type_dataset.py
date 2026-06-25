from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = PROJECT_ROOT / "data" / "datasets" / "vehicle_type_classification"
SPLIT_MANIFEST_PATH = DATASET_ROOT / "manifests" / "split_manifest.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "vehicle_type_classifier" / "best.pt"
TRAIN_REPORT_PATH = PROJECT_ROOT / "outputs" / "training" / "vehicle_type_classifier" / "reports" / "train_summary.md"
EVAL_REPORT_PATH = PROJECT_ROOT / "outputs" / "training" / "vehicle_type_classifier" / "reports" / "eval_summary.md"
VAL_PREDICTIONS_PATH = PROJECT_ROOT / "outputs" / "training" / "vehicle_type_classifier" / "reports" / "val_predictions.csv"
CLASSES = ("sedan", "suv", "mpv")
SPLITS = ("train", "val")
RAW_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
INCOMING_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
RECOMMENDED_MIN_PER_CLASS = 20
PHASE_16_RAW_COUNT = 20
PHASE_16_TRAIN_COUNT = 16
PHASE_16_VAL_COUNT = 4


def review_sheet_path(split_name: str, class_name: str) -> Path:
    return DATASET_ROOT / "review" / f"split_{split_name}_{class_name}.jpg"


def count_images(directory: Path, suffixes: set[str]) -> int:
    if not directory.exists():
        return 0
    return sum(
        1
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in suffixes
    )


def print_counts(title: str, counts: dict[str, int]) -> None:
    print(title)
    for class_name in CLASSES:
        print(f"  {class_name}: {counts[class_name]}")


def print_minimum_warnings(prefix: str, counts: dict[str, int], standardized: bool) -> None:
    for class_name in CLASSES:
        count = counts[class_name]
        if count < RECOMMENDED_MIN_PER_CLASS:
            if standardized:
                print(
                    f"warning: {prefix}/{class_name} has fewer than "
                    f"{RECOMMENDED_MIN_PER_CLASS} standardized images."
                )
            else:
                print(
                    f"warning: {prefix}/{class_name} has fewer than "
                    f"{RECOMMENDED_MIN_PER_CLASS} images."
                )


def main() -> None:
    if not DATASET_ROOT.exists():
        raise SystemExit(f"missing dataset directory: {DATASET_ROOT}")

    incoming_counts = {
        class_name: count_images(DATASET_ROOT / "incoming" / class_name, INCOMING_IMAGE_SUFFIXES)
        for class_name in CLASSES
    }
    raw_counts = {
        class_name: count_images(DATASET_ROOT / "raw" / class_name, RAW_IMAGE_SUFFIXES)
        for class_name in CLASSES
    }
    train_counts = {
        class_name: count_images(DATASET_ROOT / "split" / "train" / class_name, RAW_IMAGE_SUFFIXES)
        for class_name in CLASSES
    }
    val_counts = {
        class_name: count_images(DATASET_ROOT / "split" / "val" / class_name, RAW_IMAGE_SUFFIXES)
        for class_name in CLASSES
    }
    rejected_counts = {
        class_name: count_images(DATASET_ROOT / "rejected" / class_name, INCOMING_IMAGE_SUFFIXES)
        for class_name in CLASSES
    }

    print(f"vehicle_type_classification dataset: {DATASET_ROOT}")
    print_counts("incoming image counts:", incoming_counts)
    print_counts("raw image counts:", raw_counts)
    print_counts("split/train image counts:", train_counts)
    print_counts("split/val image counts:", val_counts)
    print_counts("rejected image counts:", rejected_counts)
    print(f"split_manifest.csv exists: {SPLIT_MANIFEST_PATH.exists()}")
    print("review contact sheets:")
    for split_name in SPLITS:
        for class_name in CLASSES:
            status = "exists" if review_sheet_path(split_name, class_name).exists() else "missing"
            print(f"  split_{split_name}_{class_name}.jpg: {status}")
    print("vehicle_type_classifier model:")
    print(f"  best.pt exists: {MODEL_PATH.exists()}")
    print("training reports:")
    print(f"  train_summary.md exists: {TRAIN_REPORT_PATH.exists()}")
    print(f"  eval_summary.md exists: {EVAL_REPORT_PATH.exists()}")
    print(f"  val_predictions.csv exists: {VAL_PREDICTIONS_PATH.exists()}")
    print_minimum_warnings("incoming", incoming_counts, standardized=False)
    print_minimum_warnings("raw", raw_counts, standardized=True)

    total_images = (
        sum(incoming_counts.values())
        + sum(raw_counts.values())
        + sum(train_counts.values())
        + sum(val_counts.values())
    )
    if total_images == 0:
        print("dataset is currently empty; this is expected before collecting local images.")

    if sum(incoming_counts.values()) > 0 and sum(raw_counts.values()) == 0:
        print("Run prepare_vehicle_type_images.py to standardize images before training.")

    phase_16_ok = all(
        raw_counts[class_name] == PHASE_16_RAW_COUNT
        and train_counts[class_name] == PHASE_16_TRAIN_COUNT
        and val_counts[class_name] == PHASE_16_VAL_COUNT
        for class_name in CLASSES
    ) and SPLIT_MANIFEST_PATH.exists()
    if phase_16_ok:
        print("split dataset looks OK for phase 1.6.")

    print("suggestion: prepare at least 20 small sample images per class first, then expand later.")


if __name__ == "__main__":
    main()
