import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
PLAN = PROJECT_ROOT / "outputs/path_optimization/optimized_machine_path_plan.json"
OUTPUT = PROJECT_ROOT / "outputs/optimized_schedule/optimized_multi_actuator_schedule.json"


def resolve(value: str) -> Path:
    path = Path(value)
    return (path if path.is_absolute() else WORKSPACE_ROOT / path).resolve()


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the selected Stage4.4 optimized schedule.")
    parser.add_argument("--optimized-path", default=str(PLAN.relative_to(WORKSPACE_ROOT)))
    parser.add_argument("--output", default=str(OUTPUT.relative_to(WORKSPACE_ROOT)))
    args = parser.parse_args()
    plan_path, output = resolve(args.optimized_path), resolve(args.output)
    if not plan_path.exists():
        completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_optimized_machine_path.py")], cwd=WORKSPACE_ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    schedule = plan["optimized_schedule"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(schedule, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    comparison = plan["improvement_summary"]
    print(f"optimization_status: {schedule['optimization_status']}")
    for metric, label in (("total_schedule_duration_s", "schedule"), ("total_delay_s", "total_delay")):
        print(f"baseline_{label}: {comparison[metric]['baseline']}")
        print(f"optimized_{label}: {comparison[metric]['optimized']}")
        print(f"{label}_reduction_percent: {comparison[metric]['improvement_percent']}")
    print(f"baseline_sync_count: {comparison['synchronized_group_count']['baseline']}")
    print(f"optimized_sync_count: {comparison['synchronized_group_count']['optimized']}")
    print(f"conflict_count_after_resolution: {schedule['summary']['conflict_count_after_resolution']}")
    print(f"unresolved_conflict_count: {schedule['summary']['unresolved_conflict_count']}")
    print(f"output path: {output}")


if __name__ == "__main__":
    main()
