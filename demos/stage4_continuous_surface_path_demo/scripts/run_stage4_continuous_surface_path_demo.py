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
    parser = argparse.ArgumentParser(description="Run the Stage4.5 continuous surface candidate path demo.")
    parser.add_argument("--aicar-root", default=str(DEFAULT_AICAR_ROOT))
    parser.add_argument("--open-report", action="store_true")
    args = parser.parse_args()
    root = Path(args.aicar_root).resolve()
    scripts = root / "aicar_sim/scripts"
    for name in (
        "generate_continuous_surface_path.py",
        "generate_continuous_machine_path.py",
        "generate_continuous_surface_validation.py",
        "generate_continuous_surface_report.py",
    ):
        run([sys.executable, str(scripts / name)], root)

    json_dir = DEMO_ROOT / "demo_outputs/json"
    report_dir = DEMO_ROOT / "demo_outputs/reports"
    json_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    sources = {
        root / "aicar_sim/outputs/continuous_surface_path/continuous_surface_path_plan.json": json_dir / "continuous_surface_path_plan.json",
        root / "aicar_sim/outputs/continuous_machine_path/continuous_machine_path_plan.json": json_dir / "continuous_machine_path_plan.json",
        root / "aicar_sim/outputs/continuous_collision_safety/continuous_collision_safety_plan.json": json_dir / "continuous_collision_safety_plan.json",
        root / "aicar_sim/outputs/continuous_schedule/continuous_multi_actuator_schedule.json": json_dir / "continuous_multi_actuator_schedule.json",
        root / "aicar_sim/outputs/continuous_surface_validation/continuous_surface_comparison_report.json": json_dir / "continuous_surface_comparison_report.json",
        root / "aicar_sim/outputs/continuous_surface_validation/stage4_continuous_surface_path_report.html": report_dir / "stage4_continuous_surface_path_report.html",
    }
    for source, destination in sources.items():
        shutil.copy2(source, destination)
    report = json.loads((json_dir / "continuous_surface_comparison_report.json").read_text(encoding="utf-8"))
    improvement = report["improvement_summary"]
    print(f"reconstruction_status: {report['reconstruction_status']}")
    print(f"coverage: {report['continuous_metrics']['coverage_percent']}")
    print(f"path reduction: {improvement['path_length_mm']['improvement_percent']}")
    print(f"transition reduction: {improvement['transition_segment_count']['improvement_percent']}")
    print(f"motion duration reduction: {improvement['motion_duration_s']['improvement_percent']}")
    print(f"schedule duration reduction: {improvement['schedule_duration_s']['improvement_percent']}")
    print(f"safety status: {report['collision_validation_status']}")
    report_path = report_dir / "stage4_continuous_surface_path_report.html"
    print(f"report path: {report_path}")
    if args.open_report:
        if os.name == "nt":
            os.startfile(report_path)  # type: ignore[attr-defined]
        else:
            print(f"Open this report manually: {report_path}")


if __name__ == "__main__":
    main()
