import subprocess
import sys
from pathlib import Path


DEMO_ROOT = Path(__file__).resolve().parents[1]
AICAR_ROOT = Path(__file__).resolve().parents[3]
REQUIRED = [
    DEMO_ROOT / "README.md",
    DEMO_ROOT / "templates/stage4_path_optimization_report_template.html",
    DEMO_ROOT / "docs/STAGE4_PATH_OPTIMIZATION_DEMO_EXPLANATION.md",
    DEMO_ROOT / "demo_outputs/json/.gitkeep",
    DEMO_ROOT / "demo_outputs/reports/.gitkeep",
    AICAR_ROOT / "aicar_sim/data/optimization_profiles/demo_path_optimization_profile.json",
    AICAR_ROOT / "aicar_sim/scripts/generate_optimized_machine_path.py",
    AICAR_ROOT / "aicar_sim/scripts/generate_optimized_schedule.py",
    AICAR_ROOT / "aicar_sim/scripts/generate_path_optimization_report.py",
]


def main() -> None:
    missing = [str(path) for path in REQUIRED if not path.exists()]
    if missing:
        raise SystemExit("missing Stage4.4 demo path: " + ", ".join(missing))
    for script in ("generate_machine_path_plan.py", "generate_collision_safety_plan.py"):
        completed = subprocess.run([sys.executable, str(AICAR_ROOT / "aicar_sim/scripts" / script)], cwd=AICAR_ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    print("AI car stage4 path optimization demo check OK")


if __name__ == "__main__":
    main()
