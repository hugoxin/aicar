import argparse
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "vehicle_type_classifier" / "best.pt"
DEFAULT_VAL_ROOT = PROJECT_ROOT / "data" / "datasets" / "vehicle_type_classification" / "split" / "val"
REPORTS_ROOT = PROJECT_ROOT / "outputs" / "training" / "vehicle_type_classifier" / "reports"
VAL_PREDICTIONS_PATH = REPORTS_ROOT / "val_predictions.csv"
EVAL_SUMMARY_PATH = REPORTS_ROOT / "eval_summary.md"
CLASSES = ("sedan", "suv", "mpv")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate the trained vehicle type classifier on split/val.")
    parser.add_argument("--model", default=str(DEFAULT_MODEL_PATH), help="Path to trained classifier best.pt.")
    parser.add_argument("--data", default=str(DEFAULT_VAL_ROOT), help="Validation data root.")
    parser.add_argument("--save-report", action="store_true", help="Save CSV and markdown evaluation reports.")
    return parser


def list_images(val_root: Path) -> list[tuple[str, Path]]:
    items: list[tuple[str, Path]] = []
    missing: list[Path] = []
    for class_name in CLASSES:
        class_dir = val_root / class_name
        if not class_dir.exists():
            missing.append(class_dir)
            continue
        for path in sorted(class_dir.iterdir()):
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
                items.append((class_name, path))

    if missing:
        missing_text = "\n".join(f"- {path}" for path in missing)
        raise SystemExit(f"missing validation directories:\n{missing_text}")
    return items


def save_predictions(rows: list[dict[str, object]]) -> None:
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    with VAL_PREDICTIONS_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["file_name", "image_path", "true_class", "pred_class", "confidence", "correct"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def save_eval_summary(
    rows: list[dict[str, object]],
    overall_accuracy: float,
    class_accuracy: dict[str, float],
    model_path: Path,
) -> None:
    lines = [
        "# Vehicle Type Classifier Evaluation Summary",
        "",
        "- Stage: 1.7",
        f"- Evaluation time: {datetime.now().isoformat(timespec='seconds')}",
        f"- Model: `{model_path}`",
        f"- Validation samples: {len(rows)}",
        f"- Overall accuracy: {overall_accuracy:.4f}",
        "",
        "## Per-class Accuracy",
        "",
    ]
    for class_name in CLASSES:
        lines.append(f"- {class_name}: {class_accuracy[class_name]:.4f}")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "This is a small-sample validation result for pipeline verification only.",
        ]
    )
    EVAL_SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    model_path = Path(args.model)
    val_root = Path(args.data)
    if not model_path.exists():
        raise SystemExit(
            f"trained model not found: {model_path}\n"
            "Run python vehicle_type_lab\\scripts\\train_vehicle_type_classifier.py --copy-best first."
        )

    items = list_images(val_root)
    if not items:
        raise SystemExit(f"no validation images found under {val_root}")

    from ultralytics import YOLO

    model = YOLO(str(model_path))
    rows: list[dict[str, object]] = []
    class_total: dict[str, int] = defaultdict(int)
    class_correct: dict[str, int] = defaultdict(int)

    for true_class, image_path in items:
        result = model(str(image_path), verbose=False)[0]
        if result.probs is None:
            pred_class = "unknown"
            confidence = 0.0
        else:
            top1 = int(result.probs.top1)
            confidence = float(result.probs.top1conf)
            pred_class = str(result.names.get(top1, top1))
        correct = pred_class == true_class
        class_total[true_class] += 1
        class_correct[true_class] += int(correct)
        row = {
            "file_name": image_path.name,
            "image_path": str(image_path),
            "true_class": true_class,
            "pred_class": pred_class,
            "confidence": f"{confidence:.6f}",
            "correct": correct,
        }
        rows.append(row)
        print(
            f"{image_path.name} true_class={true_class} "
            f"pred_class={pred_class} confidence={confidence:.4f} correct={correct}"
        )

    total_correct = sum(int(row["correct"]) for row in rows)
    overall_accuracy = total_correct / len(rows)
    class_accuracy = {
        class_name: (class_correct[class_name] / class_total[class_name] if class_total[class_name] else 0.0)
        for class_name in CLASSES
    }

    print(f"overall accuracy: {overall_accuracy:.4f}")
    for class_name in CLASSES:
        print(f"{class_name} accuracy: {class_accuracy[class_name]:.4f}")

    if args.save_report:
        save_predictions(rows)
        save_eval_summary(rows, overall_accuracy, class_accuracy, model_path)
        print(f"val_predictions saved: {VAL_PREDICTIONS_PATH}")
        print(f"eval_summary saved: {EVAL_SUMMARY_PATH}")


if __name__ == "__main__":
    main()
