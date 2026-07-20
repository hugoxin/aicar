import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.continuous_surface_repair_report import build_continuous_surface_repair_report  # noqa: E402


DEFAULTS = {
    "repair_plan": PROJECT_ROOT / "outputs/continuous_surface_path_r/continuous_surface_path_plan_r.json",
    "repair_machine": PROJECT_ROOT / "outputs/continuous_machine_path_r/continuous_machine_path_plan_r.json",
    "repair_validation": PROJECT_ROOT / "outputs/continuous_surface_validation_r/continuous_surface_validation_r.json",
    "first_plan": PROJECT_ROOT / "outputs/continuous_surface_path/continuous_surface_path_plan.json",
    "first_machine": PROJECT_ROOT / "outputs/continuous_machine_path/continuous_machine_path_plan.json",
    "first_schedule": PROJECT_ROOT / "outputs/continuous_schedule/continuous_multi_actuator_schedule.json",
    "first_validation": PROJECT_ROOT / "outputs/continuous_surface_validation/continuous_collision_safety_validation_report.json",
    "baseline_report": PROJECT_ROOT / "outputs/path_optimization/path_optimization_report.json",
    "baseline_schedule": PROJECT_ROOT / "outputs/optimized_schedule/optimized_multi_actuator_schedule.json",
    "json_output": PROJECT_ROOT / "outputs/continuous_surface_validation_r/continuous_surface_repair_report.json",
    "html_output": PROJECT_ROOT / "outputs/continuous_surface_validation_r/stage4_continuous_surface_path_repair_report.html",
}


def resolve(value: str) -> Path:
    path = Path(value)
    return (path if path.is_absolute() else WORKSPACE_ROOT / path).resolve()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the Stage4.5-R three-way comparison JSON and HTML report.")
    for key, path in DEFAULTS.items():
        parser.add_argument("--" + key.replace("_", "-"), default=str(path.relative_to(WORKSPACE_ROOT)))
    args = parser.parse_args()
    paths = {key: resolve(getattr(args, key)) for key in DEFAULTS}
    if not paths["repair_validation"].exists():
        completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_continuous_surface_validation_r.py")], cwd=WORKSPACE_ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    if not paths["first_validation"].exists():
        completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_continuous_surface_validation.py")], cwd=WORKSPACE_ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    if not paths["first_validation"].exists():
        raise SystemExit(f"first-attempt validation report is missing and could not be generated: {paths['first_validation']}")
    report, html_text = build_continuous_surface_repair_report(
        load_json(paths["repair_plan"]),
        load_json(paths["repair_machine"]),
        load_json(paths["repair_validation"]),
        load_json(paths["first_plan"]),
        load_json(paths["first_machine"]),
        load_json(paths["first_schedule"]),
        load_json(paths["first_validation"]),
        load_json(paths["baseline_report"]),
        load_json(paths["baseline_schedule"]),
        first_validation_source=str(paths["first_validation"].relative_to(WORKSPACE_ROOT)).replace("\\", "/"),
    )
    paths["json_output"].parent.mkdir(parents=True, exist_ok=True)
    paths["html_output"].parent.mkdir(parents=True, exist_ok=True)
    paths["json_output"].write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["html_output"].write_text(html_text, encoding="utf-8")
    first = report["stage4_5_first_attempt_metrics"]
    baseline = report["stage4_baseline_metrics"]
    repair = report["stage4_5_r_metrics"]
    improvement = report["improvement_summary"]
    print(f"repair_status: {report['repair_status']}")
    print(f"Stage4 baseline path/motion/schedule/delay: {baseline['machine_path_length_mm']} / {baseline['motion_duration_s']} / {baseline['schedule_duration_s']} / {baseline['total_delay_s']}")
    print(f"Stage4.5 first path/motion/schedule/delay: {first['machine_path_length_mm']} / {first['motion_duration_s']} / {first['schedule_duration_s']} / {first['total_delay_s']}")
    print(f"Stage4.5-R path/motion/schedule/delay: {repair['machine_path_length_mm']} / {repair['motion_duration_s']} / {repair['schedule_duration_s']} / {repair['total_delay_s']}")
    for key in ("machine_path_length_mm", "motion_duration_s", "schedule_duration_s", "total_delay_s"):
        print(f"{key} reduction vs first: {improvement[key]['versus_first_attempt_percent']}")
    print(f"transition_count: {repair['transition_count']}")
    print(f"coverage: {repair['unique_geometric_coverage_percent']}")
    print(f"violation_count: {report['violation_count']}")
    print(f"warning_count: {report['warning_count']}")
    print(f"JSON path: {paths['json_output']}")
    print(f"HTML path: {paths['html_output']}")


if __name__ == "__main__":
    main()
