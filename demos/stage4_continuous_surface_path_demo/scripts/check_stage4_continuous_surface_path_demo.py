import subprocess
import sys
from pathlib import Path


DEMO_ROOT = Path(__file__).resolve().parents[1]
AICAR_ROOT = Path(__file__).resolve().parents[3]
REQUIRED = [
    DEMO_ROOT / "README.md",
    DEMO_ROOT / "templates/stage4_continuous_surface_path_report_template.html",
    DEMO_ROOT / "docs/STAGE4_CONTINUOUS_SURFACE_PATH_DEMO_EXPLANATION.md",
    DEMO_ROOT / "demo_outputs/json/.gitkeep",
    DEMO_ROOT / "demo_outputs/reports/.gitkeep",
    AICAR_ROOT / "aicar_sim/data/surface_models/demo_sedan_surface_model.json",
    AICAR_ROOT / "aicar_sim/data/continuous_path_profiles/demo_continuous_surface_scan_profile.json",
    AICAR_ROOT / "aicar_sim/scripts/generate_continuous_surface_path.py",
    AICAR_ROOT / "aicar_sim/scripts/generate_continuous_machine_path.py",
    AICAR_ROOT / "aicar_sim/scripts/generate_continuous_surface_validation.py",
    AICAR_ROOT / "aicar_sim/scripts/generate_continuous_surface_report.py",
]


def main() -> None:
    missing = [str(path) for path in REQUIRED if not path.exists()]
    if missing:
        raise SystemExit("missing Stage4.5 demo path: " + ", ".join(missing))
    for script in ("check_surface_model.py", "check_continuous_path_profile.py", "generate_machine_path_plan.py"):
        completed = subprocess.run([sys.executable, str(AICAR_ROOT / "aicar_sim/scripts" / script)], cwd=AICAR_ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    print("AI car stage4 continuous surface path demo check OK")


if __name__ == "__main__":
    main()
