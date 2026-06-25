from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "README.md",
    "requirements.txt",
    "pyproject.toml",
    "config/vehicle_type_config.yaml",
    "data/input_images/.gitkeep",
    "data/input_images/README.md",
    "data/sample_images/README.md",
    "data/datasets/README.md",
    "data/datasets/vehicle_type_classification/README.md",
    "data/datasets/vehicle_type_classification/CLASS_DEFINITION.md",
    "data/datasets/vehicle_type_classification/NAMING_RULES.md",
    "data/datasets/vehicle_type_classification/incoming/sedan/.gitkeep",
    "data/datasets/vehicle_type_classification/incoming/suv/.gitkeep",
    "data/datasets/vehicle_type_classification/incoming/mpv/.gitkeep",
    "data/datasets/vehicle_type_classification/raw/sedan/.gitkeep",
    "data/datasets/vehicle_type_classification/raw/suv/.gitkeep",
    "data/datasets/vehicle_type_classification/raw/mpv/.gitkeep",
    "data/datasets/vehicle_type_classification/split/train/sedan/.gitkeep",
    "data/datasets/vehicle_type_classification/split/train/suv/.gitkeep",
    "data/datasets/vehicle_type_classification/split/train/mpv/.gitkeep",
    "data/datasets/vehicle_type_classification/split/val/sedan/.gitkeep",
    "data/datasets/vehicle_type_classification/split/val/suv/.gitkeep",
    "data/datasets/vehicle_type_classification/split/val/mpv/.gitkeep",
    "data/datasets/vehicle_type_classification/review/.gitkeep",
    "data/datasets/vehicle_type_classification/manifests/README.md",
    "data/datasets/vehicle_type_classification/manifests/dataset_manifest_template.csv",
    "data/datasets/vehicle_type_classification/manifests/split_manifest.csv",
    "data/annotations/README.md",
    "schemas/vehicle_type_result.schema.json",
    "examples/result_sedan.json",
    "examples/result_suv.json",
    "examples/result_mpv.json",
    "examples/result_unknown.json",
    "scripts/check_image_input.py",
    "scripts/check_yolo_detect.py",
    "scripts/check_vehicle_type_classify.py",
    "scripts/check_vehicle_type_dataset.py",
    "scripts/prepare_vehicle_type_images.py",
    "scripts/split_vehicle_type_dataset.py",
    "scripts/make_vehicle_type_split_contact_sheets.py",
    "scripts/train_vehicle_type_classifier.py",
    "scripts/eval_vehicle_type_classifier.py",
    "models/vehicle_type_classifier/.gitkeep",
    "outputs/training/vehicle_type_classifier/.gitkeep",
    "outputs/training/vehicle_type_classifier/runs/.gitkeep",
    "outputs/training/vehicle_type_classifier/reports/.gitkeep",
    "outputs/predictions/visualized/.gitkeep",
    "outputs/predictions/crops/.gitkeep",
    "src/vehicle_type_lab/__init__.py",
    "src/vehicle_type_lab/main.py",
    "src/vehicle_type_lab/mock_classifier.py",
    "src/vehicle_type_lab/image_io.py",
    "src/vehicle_type_lab/yolo_detector.py",
    "src/vehicle_type_lab/crop_utils.py",
    "src/vehicle_type_lab/vehicle_type_classifier.py",
]


def main() -> None:
    missing = [path for path in REQUIRED_PATHS if not (PROJECT_ROOT / path).exists()]
    if missing:
        print("Missing vehicle_type_lab scaffold paths:")
        for path in missing:
            print(f"- {path}")
        raise SystemExit(1)

    print("vehicle_type_lab scaffold OK")


if __name__ == "__main__":
    main()
