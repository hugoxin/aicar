import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.path_optimization_report import build_path_optimization_report  # noqa: E402


DEFAULTS = {
    "baseline_path": PROJECT_ROOT / "outputs/machine_path/machine_path_plan.json",
    "optimized_path": PROJECT_ROOT / "outputs/path_optimization/optimized_machine_path_plan.json",
    "baseline_schedule": PROJECT_ROOT / "outputs/multi_actuator_schedule/multi_actuator_schedule.json",
    "safety_layout": PROJECT_ROOT / "data/safety_models/demo_wash_bay_safety_layout.json",
    "space_model": PROJECT_ROOT / "outputs/space_model/space_model_report.json",
    "json_output": PROJECT_ROOT / "outputs/path_optimization/path_optimization_report.json",
    "html_output": PROJECT_ROOT / "outputs/path_optimization/stage4_path_optimization_report.html",
}


def resolve(value: str) -> Path:
    path = Path(value)
    return (path if path.is_absolute() else WORKSPACE_ROOT / path).resolve()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Stage4.4 optimization comparison JSON and HTML.")
    for key, path in DEFAULTS.items():
        parser.add_argument("--" + key.replace("_", "-"), default=str(path.relative_to(WORKSPACE_ROOT)))
    args = parser.parse_args()
    paths = {key: resolve(getattr(args, key)) for key in DEFAULTS}
    if not paths["optimized_path"].exists():
        completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_optimized_machine_path.py")], cwd=WORKSPACE_ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    report, html_text = build_path_optimization_report(
        load_json(paths["baseline_path"]), load_json(paths["optimized_path"]),
        load_json(paths["baseline_schedule"]), load_json(paths["safety_layout"]),
        load_json(paths["space_model"]),
    )
    paths["json_output"].parent.mkdir(parents=True, exist_ok=True)
    paths["html_output"].parent.mkdir(parents=True, exist_ok=True)
    paths["json_output"].write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    paths["html_output"].write_text(html_text, encoding="utf-8")
    improvements = report["improvement_summary"]
    print(f"optimization_status: {report['optimization_status']}")
    print(f"safety_validation_status: {report['safety_validation_status']}")
    print(f"path improvement: {improvements['path_length_mm']['improvement_percent']}")
    print(f"duration improvement: {improvements['estimated_motion_duration_s']['improvement_percent']}")
    print(f"schedule improvement: {improvements['total_schedule_duration_s']['improvement_percent']}")
    print(f"transition improvement: {improvements['transition_segment_count']['improvement_percent']}")
    print(f"violation_count: {report['violation_count']}")
    print(f"warning_count: {report['warning_count']}")
    print(f"JSON output: {paths['json_output']}")
    print(f"HTML output: {paths['html_output']}")


if __name__ == "__main__":
    main()
