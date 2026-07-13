import subprocess
import sys
from pathlib import Path


DEMO_ROOT = Path(__file__).resolve().parents[1]
AICAR_ROOT = Path(__file__).resolve().parents[3]
REQUIRED = [
    DEMO_ROOT / "README.md",
    DEMO_ROOT / "templates/stage4_collision_safety_report_template.html",
    DEMO_ROOT / "docs/STAGE4_COLLISION_SAFETY_DEMO_EXPLANATION.md",
    DEMO_ROOT / "demo_outputs/json/.gitkeep",
    DEMO_ROOT / "demo_outputs/reports/.gitkeep",
    AICAR_ROOT / "aicar_sim/data/safety_models/demo_wash_bay_safety_layout.json",
    AICAR_ROOT / "aicar_sim/data/actuator_systems/demo_multi_actuator_system.json",
]


def main() -> None:
    missing = [str(path) for path in REQUIRED if not path.exists()]
    if missing:
        raise SystemExit("missing Stage4.3 demo path: " + ", ".join(missing))
    completed = subprocess.run([sys.executable, str(AICAR_ROOT / "aicar_sim/scripts/generate_collision_safety_plan.py")], cwd=AICAR_ROOT)
    if completed.returncode:
        raise SystemExit(completed.returncode)
    print("AI car stage4 collision safety demo check OK")


if __name__ == "__main__":
    main()
