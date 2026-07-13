import subprocess
import sys
from pathlib import Path


DEMO_ROOT = Path(__file__).resolve().parents[1]
AICAR_ROOT = DEMO_ROOT.parents[1]
REQUIRED_PATHS = [
    DEMO_ROOT / "scripts" / "run_stage4_motion_constraint_demo.py",
    DEMO_ROOT / "templates" / "stage4_motion_constraint_report_template.html",
    DEMO_ROOT / "docs" / "STAGE4_MOTION_CONSTRAINT_DEMO_EXPLANATION.md",
    DEMO_ROOT / "demo_outputs" / "reports",
    DEMO_ROOT / "demo_outputs" / "json",
    AICAR_ROOT / "aicar_sim" / "data" / "motion_models" / "demo_cartesian_gantry.json",
    AICAR_ROOT / "aicar_sim" / "scripts" / "generate_machine_path_plan.py",
    AICAR_ROOT / "aicar_sim" / "scripts" / "generate_motion_validation_report.py",
    AICAR_ROOT / "aicar_sim" / "scripts" / "generate_abstract_nozzle_path_plan.py",
]


def main() -> None:
    missing = [path for path in REQUIRED_PATHS if not path.exists()]
    if missing:
        print("Missing Stage4 motion constraint demo paths:")
        for path in missing:
            print(f"- {path}")
        raise SystemExit(1)

    completed = subprocess.run(
        [sys.executable, str(AICAR_ROOT / "aicar_sim" / "scripts" / "generate_machine_path_plan.py")],
        cwd=str(AICAR_ROOT),
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        print(completed.stdout)
        print(completed.stderr, file=sys.stderr)
        raise SystemExit(completed.returncode)

    print("AI car stage4 motion constraint demo check OK")


if __name__ == "__main__":
    main()
