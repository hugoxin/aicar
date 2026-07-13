import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


DEMO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = DEMO_ROOT.parents[1]
SIM_ROOT = WORKSPACE_ROOT / "aicar_sim"

SCRIPTS = (
    "generate_continuous_surface_path_r.py",
    "generate_continuous_machine_path_r.py",
    "generate_continuous_surface_validation_r.py",
    "generate_continuous_surface_report_r.py",
)

JSON_SOURCES = {
    "continuous_surface_path_plan_r.json": SIM_ROOT / "outputs/continuous_surface_path_r/continuous_surface_path_plan_r.json",
    "continuous_machine_path_plan_r.json": SIM_ROOT / "outputs/continuous_machine_path_r/continuous_machine_path_plan_r.json",
    "continuous_collision_safety_plan_r.json": SIM_ROOT / "outputs/continuous_collision_safety_r/continuous_collision_safety_plan_r.json",
    "continuous_multi_actuator_schedule_r.json": SIM_ROOT / "outputs/continuous_schedule_r/continuous_multi_actuator_schedule_r.json",
    "continuous_surface_repair_report.json": SIM_ROOT / "outputs/continuous_surface_validation_r/continuous_surface_repair_report.json",
}
HTML_SOURCE = SIM_ROOT / "outputs/continuous_surface_validation_r/stage4_continuous_surface_path_repair_report.html"


def run_script(name: str) -> None:
    completed = subprocess.run([sys.executable, str(SIM_ROOT / "scripts" / name)], cwd=WORKSPACE_ROOT)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Stage4.5-R continuous surface path repair demo.")
    parser.add_argument("--open-report", action="store_true", help="Open the generated local HTML report.")
    args = parser.parse_args()

    for script in SCRIPTS:
        run_script(script)

    json_output = DEMO_ROOT / "demo_outputs/json"
    report_output = DEMO_ROOT / "demo_outputs/reports"
    json_output.mkdir(parents=True, exist_ok=True)
    report_output.mkdir(parents=True, exist_ok=True)
    for name, source in JSON_SOURCES.items():
        shutil.copy2(source, json_output / name)
    report_path = report_output / HTML_SOURCE.name
    shutil.copy2(HTML_SOURCE, report_path)

    report = json.loads(JSON_SOURCES["continuous_surface_repair_report.json"].read_text(encoding="utf-8"))
    repair = report["stage4_5_r_metrics"]
    improvement = report["improvement_summary"]
    print(f"repair_status: {report['repair_status']}")
    print(f"scan_pass_count: {repair['scan_pass_count']}")
    print(f"surface_task_count: {repair['surface_task_count']}")
    print(f"path_reduction_vs_first_attempt_percent: {improvement['machine_path_length_mm']['versus_first_attempt_percent']}")
    print(f"path_reduction_vs_stage4_baseline_percent: {improvement['machine_path_length_mm']['versus_stage4_baseline_percent']}")
    print(f"motion_reduction_vs_first_attempt_percent: {improvement['motion_duration_s']['versus_first_attempt_percent']}")
    print(f"schedule_reduction_vs_first_attempt_percent: {improvement['schedule_duration_s']['versus_first_attempt_percent']}")
    print(f"delay_reduction_vs_first_attempt_percent: {improvement['total_delay_s']['versus_first_attempt_percent']}")
    print(f"coverage_percent: {repair['unique_geometric_coverage_percent']}")
    print(f"safety_status: {report['collision_validation_status']}")
    print(f"report path: {report_path}")
    if args.open_report:
        os.startfile(report_path)


if __name__ == "__main__":
    main()
