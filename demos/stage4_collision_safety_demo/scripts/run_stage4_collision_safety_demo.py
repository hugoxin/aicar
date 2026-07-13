import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


DEMO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AICAR_ROOT = Path(__file__).resolve().parents[3]


def run(command: list[str], root: Path) -> None:
    completed = subprocess.run(command, cwd=root, text=True, capture_output=True)
    if completed.stdout.strip():
        print(completed.stdout.strip())
    if completed.stderr.strip():
        print(completed.stderr.strip(), file=sys.stderr)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Stage4.3 collision safety demo.")
    parser.add_argument("--aicar-root", default=str(DEFAULT_AICAR_ROOT))
    parser.add_argument("--open-report", action="store_true")
    args = parser.parse_args()
    root = Path(args.aicar_root).resolve()
    scripts = root / "aicar_sim/scripts"
    for name in ("generate_collision_safety_plan.py", "generate_multi_actuator_schedule.py", "generate_collision_safety_report.py"):
        run([sys.executable, str(scripts / name)], root)
    json_dir = DEMO_ROOT / "demo_outputs/json"
    report_dir = DEMO_ROOT / "demo_outputs/reports"
    json_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    sources = {
        root / "aicar_sim/outputs/collision_safety/collision_safety_plan.json": json_dir / "collision_safety_plan.json",
        root / "aicar_sim/outputs/multi_actuator_schedule/multi_actuator_schedule.json": json_dir / "multi_actuator_schedule.json",
        root / "aicar_sim/outputs/collision_safety/collision_safety_validation_report.json": json_dir / "collision_safety_validation_report.json",
        root / "aicar_sim/outputs/collision_safety/stage4_collision_safety_report.html": report_dir / "stage4_collision_safety_report.html",
    }
    for source, destination in sources.items():
        shutil.copy2(source, destination)
    report = json.loads((json_dir / "collision_safety_validation_report.json").read_text(encoding="utf-8"))
    summary = report["summary"]
    print(f"validation_status: {report['validation_status']}")
    print(f"actuator_count: {summary['actuator_count']}")
    print(f"task_count: {summary['task_count']}")
    print(f"unresolved_conflict_count: {report['unresolved_conflict_count']}")
    print(f"violation_count: {summary['violation_count']}")
    print(f"warning_count: {summary['warning_count']}")
    print(f"report path: {sources[root / 'aicar_sim/outputs/collision_safety/stage4_collision_safety_report.html']}")
    if args.open_report:
        report_path = report_dir / "stage4_collision_safety_report.html"
        if os.name == "nt":
            os.startfile(report_path)  # type: ignore[attr-defined]
        else:
            print(f"Open this report manually: {report_path}")


if __name__ == "__main__":
    main()
