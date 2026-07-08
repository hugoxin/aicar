from pathlib import Path


DEMO_ROOT = Path(__file__).resolve().parents[1]
AICAR_ROOT = DEMO_ROOT.parents[1]
REQUIRED_PATHS = [
    DEMO_ROOT,
    DEMO_ROOT / "demo_outputs" / "reports",
    DEMO_ROOT / "demo_outputs" / "json",
    DEMO_ROOT / "scripts" / "run_stage3_timeline_animation_demo.py",
    DEMO_ROOT / "templates" / "stage3_timeline_animation_report_template.html",
    AICAR_ROOT / "aicar_sim" / "scripts" / "generate_timeline_animation_report.py",
]
VEHICLE_TYPE_RESULT = (
    AICAR_ROOT / "vehicle_type_lab" / "outputs" / "predictions" / "vehicle_type_result.json"
)


def main() -> None:
    missing = [path for path in REQUIRED_PATHS if not path.exists()]
    if missing:
        print("Missing Stage3 timeline animation demo paths:")
        for path in missing:
            print(f"- {path}")
        raise SystemExit(1)

    if not VEHICLE_TYPE_RESULT.exists():
        print(f"Missing vehicle type result: {VEHICLE_TYPE_RESULT}")
        print("Run stage1 classify or Stage1 Demo first.")
        raise SystemExit(1)

    print("AI car stage3 timeline animation demo check OK")


if __name__ == "__main__":
    main()
