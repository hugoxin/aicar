from pathlib import Path


DEMO_ROOT = Path(__file__).resolve().parents[1]
AICAR_ROOT = Path(__file__).resolve().parents[3]


def main() -> None:
    checks = [
        ("aicar root", AICAR_ROOT),
        (
            "vehicle_type_result.json",
            AICAR_ROOT
            / "vehicle_type_lab"
            / "outputs"
            / "predictions"
            / "vehicle_type_result.json",
        ),
        (
            "generate_wash_strategy_plan.py",
            AICAR_ROOT / "aicar_sim" / "scripts" / "generate_wash_strategy_plan.py",
        ),
        (
            "generate_space_model.py",
            AICAR_ROOT / "aicar_sim" / "scripts" / "generate_space_model.py",
        ),
        (
            "generate_nozzle_coverage_plan.py",
            AICAR_ROOT / "aicar_sim" / "scripts" / "generate_nozzle_coverage_plan.py",
        ),
        (
            "generate_wash_flow_run.py",
            AICAR_ROOT / "aicar_sim" / "scripts" / "generate_wash_flow_run.py",
        ),
        (
            "generate_abstract_nozzle_path_plan.py",
            AICAR_ROOT
            / "aicar_sim"
            / "scripts"
            / "generate_abstract_nozzle_path_plan.py",
        ),
        (
            "generate_coverage_report.py",
            AICAR_ROOT / "aicar_sim" / "scripts" / "generate_coverage_report.py",
        ),
        (
            "check_coverage_report.py",
            AICAR_ROOT / "aicar_sim" / "scripts" / "check_coverage_report.py",
        ),
        ("demo_outputs/reports", DEMO_ROOT / "demo_outputs" / "reports"),
        ("demo_outputs/json", DEMO_ROOT / "demo_outputs" / "json"),
        (
            "run_stage2_pipeline_demo.py",
            DEMO_ROOT / "scripts" / "run_stage2_pipeline_demo.py",
        ),
        (
            "stage2_pipeline_report_template.html",
            DEMO_ROOT / "templates" / "stage2_pipeline_report_template.html",
        ),
    ]

    missing = [(label, path) for label, path in checks if not path.exists()]
    if missing:
        print("Missing stage2 pipeline demo paths:")
        for label, path in missing:
            print(f"- {label}: {path}")
        if any(label == "vehicle_type_result.json" for label, _ in missing):
            print("Run stage1 classify or stage1 visual demo first.")
        raise SystemExit(1)

    print("AI car stage2 pipeline demo check OK")


if __name__ == "__main__":
    main()
