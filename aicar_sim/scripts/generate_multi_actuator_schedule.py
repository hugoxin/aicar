import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
PLAN = PROJECT_ROOT / "outputs/collision_safety/collision_safety_plan.json"
OUTPUT = PROJECT_ROOT / "outputs/multi_actuator_schedule/multi_actuator_schedule.json"


def resolve(value: str) -> Path:
    path = Path(value)
    return (path if path.is_absolute() else WORKSPACE_ROOT / path).resolve()


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the Stage4.3 multi-actuator schedule.")
    parser.add_argument("--plan", default=str(PLAN.relative_to(WORKSPACE_ROOT)))
    parser.add_argument("--output", default=str(OUTPUT.relative_to(WORKSPACE_ROOT)))
    args = parser.parse_args()
    plan_path = resolve(args.plan)
    output = resolve(args.output)
    if not plan_path.exists():
        completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_collision_safety_plan.py"), "--output", str(plan_path)], cwd=WORKSPACE_ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    schedule = json.loads(plan_path.read_text(encoding="utf-8"))["multi_actuator_schedule"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(schedule, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for key, value in schedule["summary"].items():
        print(f"{key}: {value}")
    print(f"output path: {output}")


if __name__ == "__main__":
    main()
