from pathlib import Path


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".jfif"}
DEMO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AICAR_ROOT = Path(__file__).resolve().parents[3]


def main() -> None:
    checks = [
        ("aicar root", DEFAULT_AICAR_ROOT),
        (
            "vehicle_type_lab main.py",
            DEFAULT_AICAR_ROOT / "vehicle_type_lab" / "src" / "vehicle_type_lab" / "main.py",
        ),
        (
            "best.pt",
            DEFAULT_AICAR_ROOT
            / "vehicle_type_lab"
            / "models"
            / "vehicle_type_classifier"
            / "best.pt",
        ),
        ("sedan vehicle model", DEFAULT_AICAR_ROOT / "aicar_sim" / "data" / "vehicles" / "sedan.json"),
        ("suv vehicle model", DEFAULT_AICAR_ROOT / "aicar_sim" / "data" / "vehicles" / "suv.json"),
        ("mpv vehicle model", DEFAULT_AICAR_ROOT / "aicar_sim" / "data" / "vehicles" / "mpv.json"),
        ("demo_inputs", DEMO_ROOT / "demo_inputs"),
        ("demo_outputs/reports", DEMO_ROOT / "demo_outputs" / "reports"),
        ("demo_outputs/visualized", DEMO_ROOT / "demo_outputs" / "visualized"),
        ("demo_outputs/crops", DEMO_ROOT / "demo_outputs" / "crops"),
        ("demo_outputs/json", DEMO_ROOT / "demo_outputs" / "json"),
        ("run_stage1_demo.py", DEMO_ROOT / "scripts" / "run_stage1_demo.py"),
    ]

    missing = [(label, path) for label, path in checks if not path.exists()]
    if missing:
        print("Missing stage1 visual demo paths:")
        for label, path in missing:
            print(f"- {label}: {path}")
        raise SystemExit(1)

    demo_images = [
        path
        for path in (DEMO_ROOT / "demo_inputs").iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    ]
    if not demo_images:
        print("No demo image found. Put a vehicle image into demo_inputs, for example car_demo.jpg.")

    print("AI car stage1 visual demo check OK")


if __name__ == "__main__":
    main()

