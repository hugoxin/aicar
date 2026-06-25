import argparse
import shutil
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
DEFAULT_DATA_ROOT = PROJECT_ROOT / "data" / "datasets" / "vehicle_type_classification" / "split"
DEFAULT_RUNS_ROOT = PROJECT_ROOT / "outputs" / "training" / "vehicle_type_classifier" / "runs"
REPORTS_ROOT = PROJECT_ROOT / "outputs" / "training" / "vehicle_type_classifier" / "reports"
MODEL_OUTPUT_ROOT = PROJECT_ROOT / "models" / "vehicle_type_classifier"
TRAIN_SUMMARY_PATH = REPORTS_ROOT / "train_summary.md"
COPIED_BEST_PATH = MODEL_OUTPUT_ROOT / "best.pt"
CLASSES = ("sedan", "suv", "mpv")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train a small sedan/suv/mpv classifier.")
    parser.add_argument("--data", default=str(DEFAULT_DATA_ROOT), help="Dataset split root.")
    parser.add_argument("--model", default="yolo11n-cls.pt", help="Ultralytics classification model.")
    parser.add_argument("--epochs", type=int, default=20, help="Training epochs.")
    parser.add_argument("--imgsz", type=int, default=224, help="Training image size.")
    parser.add_argument("--batch", type=int, default=8, help="Batch size.")
    parser.add_argument("--device", default="cpu", help="Training device.")
    parser.add_argument("--dry-run", action="store_true", help="Print configuration without training.")
    parser.add_argument("--copy-best", action="store_true", help="Copy best.pt to models/vehicle_type_classifier.")
    return parser


def count_images(directory: Path) -> int:
    if not directory.exists():
        return 0
    return sum(
        1
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def check_dataset(data_root: Path) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {"train": {}, "val": {}}
    missing: list[Path] = []
    for split_name in ("train", "val"):
        for class_name in CLASSES:
            class_dir = data_root / split_name / class_name
            if not class_dir.exists():
                missing.append(class_dir)
            counts[split_name][class_name] = count_images(class_dir)

    if missing:
        missing_text = "\n".join(f"- {path}" for path in missing)
        raise SystemExit(f"missing required dataset directories:\n{missing_text}")

    for class_name in CLASSES:
        if counts["train"][class_name] < 5:
            print(f"warning: train/{class_name} has fewer than 5 images.")
        if counts["val"][class_name] < 1:
            print(f"warning: val/{class_name} has fewer than 1 image.")

    return counts


def print_counts(counts: dict[str, dict[str, int]]) -> None:
    print("dataset counts:")
    for split_name in ("train", "val"):
        for class_name in CLASSES:
            print(f"{split_name}/{class_name}: {counts[split_name][class_name]}")


def find_weight(run_dir: Path, name: str) -> Path | None:
    direct = run_dir / "weights" / name
    if direct.exists():
        return direct
    matches = sorted(run_dir.rglob(name))
    return matches[0] if matches else None


def write_train_summary(
    *,
    data_root: Path,
    counts: dict[str, dict[str, int]],
    model_name: str,
    epochs: int,
    imgsz: int,
    batch: int,
    device: str,
    best_path: Path | None,
    copied_best_path: Path | None,
    last_path: Path | None,
    run_dir: Path,
) -> None:
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Vehicle Type Classifier Training Summary",
        "",
        "- Stage: 1.7",
        f"- Training time: {datetime.now().isoformat(timespec='seconds')}",
        f"- Data path: `{data_root}`",
        "- Classes: sedan, suv, mpv",
        "",
        "## Counts",
        "",
    ]
    for split_name in ("train", "val"):
        for class_name in CLASSES:
            lines.append(f"- {split_name}/{class_name}: {counts[split_name][class_name]}")

    lines.extend(
        [
            "",
            "## Parameters",
            "",
            f"- Model: `{model_name}`",
            f"- Epochs: {epochs}",
            f"- Image size: {imgsz}",
            f"- Batch: {batch}",
            f"- Device: `{device}`",
            "",
            "## Outputs",
            "",
            f"- Training output directory: `{run_dir}`",
            f"- best.pt original path: `{best_path if best_path else 'not found'}`",
            f"- last.pt original path: `{last_path if last_path else 'not found'}`",
            f"- best.pt copied path: `{copied_best_path if copied_best_path else 'not copied'}`",
            "",
            "## Notes",
            "",
            "Current data has only 20 images per class. This result is for pipeline validation only and does not represent commercial accuracy.",
        ]
    )
    TRAIN_SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    data_root = Path(args.data)
    project_root = DEFAULT_RUNS_ROOT
    run_name = "yolo11n_cls_sedan_suv_mpv"
    run_dir = project_root / run_name

    counts = check_dataset(data_root)
    print_counts(counts)
    print("training parameters:")
    print(f"model: {args.model}")
    print(f"imgsz: {args.imgsz}")
    print(f"epochs: {args.epochs}")
    print(f"batch: {args.batch}")
    print(f"seed: 42")
    print(f"device: {args.device}")
    print(f"project: {project_root}")
    print(f"name: {run_name}")
    print("exist_ok: true")

    if args.dry_run:
        print("dry-run only; training will not start.")
        return

    from ultralytics import YOLO

    project_root.mkdir(parents=True, exist_ok=True)
    model = YOLO(args.model)
    model.train(
        data=str(data_root),
        imgsz=args.imgsz,
        epochs=args.epochs,
        batch=args.batch,
        seed=42,
        device=args.device,
        project=str(project_root),
        name=run_name,
        exist_ok=True,
    )

    best_path = find_weight(run_dir, "best.pt")
    last_path = find_weight(run_dir, "last.pt")
    copied_best_path = None
    if args.copy_best:
        if best_path is None:
            raise SystemExit(f"best.pt was not found under {run_dir}")
        MODEL_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        shutil.copy2(best_path, COPIED_BEST_PATH)
        copied_best_path = COPIED_BEST_PATH
        print(f"best.pt copied: {copied_best_path}")

    write_train_summary(
        data_root=data_root,
        counts=counts,
        model_name=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        best_path=best_path,
        copied_best_path=copied_best_path,
        last_path=last_path,
        run_dir=run_dir,
    )
    print(f"train_summary saved: {TRAIN_SUMMARY_PATH}")
    print(f"training output directory: {run_dir}")
    print(f"best.pt original path: {best_path}")
    print(f"last.pt original path: {last_path}")


if __name__ == "__main__":
    main()

