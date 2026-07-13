import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.continuous_surface_path_planner import load_continuous_path_profile  # noqa: E402
from aicar_sim.continuous_surface_report import build_continuous_surface_report  # noqa: E402
from aicar_sim.obstacle_model import load_safety_layout  # noqa: E402
from aicar_sim.surface_model import load_surface_model  # noqa: E402


DEFAULTS = {
    "surface_path": PROJECT_ROOT / "outputs/continuous_surface_path/continuous_surface_path_plan.json",
    "continuous_machine_path": PROJECT_ROOT / "outputs/continuous_machine_path/continuous_machine_path_plan.json",
    "validation": PROJECT_ROOT / "outputs/continuous_surface_validation/continuous_collision_safety_validation_report.json",
    "baseline_path": PROJECT_ROOT / "outputs/machine_path/machine_path_plan.json",
    "baseline_report": PROJECT_ROOT / "outputs/path_optimization/path_optimization_report.json",
    "surface_model": PROJECT_ROOT / "data/surface_models/demo_sedan_surface_model.json",
    "scan_profile": PROJECT_ROOT / "data/continuous_path_profiles/demo_continuous_surface_scan_profile.json",
    "space_model": PROJECT_ROOT / "outputs/space_model/space_model_report.json",
    "safety_layout": PROJECT_ROOT / "data/safety_models/demo_wash_bay_safety_layout.json",
    "json_output": PROJECT_ROOT / "outputs/continuous_surface_validation/continuous_surface_comparison_report.json",
    "html_output": PROJECT_ROOT / "outputs/continuous_surface_validation/stage4_continuous_surface_path_report.html",
}


def resolve(value: str) -> Path:
    path = Path(value)
    return (path if path.is_absolute() else WORKSPACE_ROOT / path).resolve()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Stage4.5 continuous-surface comparison JSON and HTML.")
    for key, path in DEFAULTS.items():
        parser.add_argument("--" + key.replace("_", "-"), default=str(path.relative_to(WORKSPACE_ROOT)))
    args = parser.parse_args()
    paths = {key: resolve(getattr(args, key)) for key in DEFAULTS}
    if not paths["validation"].exists():
        completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_continuous_surface_validation.py")], cwd=WORKSPACE_ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    report, html_text = build_continuous_surface_report(
        load_json(paths["surface_path"]), load_json(paths["continuous_machine_path"]), load_json(paths["validation"]),
        load_json(paths["baseline_path"]), load_json(paths["baseline_report"]), load_surface_model(paths["surface_model"]),
        load_continuous_path_profile(paths["scan_profile"]), load_json(paths["space_model"]), load_safety_layout(paths["safety_layout"]),
    )
    paths["json_output"].parent.mkdir(parents=True, exist_ok=True)
    paths["html_output"].parent.mkdir(parents=True, exist_ok=True)
    paths["json_output"].write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["html_output"].write_text(html_text, encoding="utf-8")
    improvement = report["improvement_summary"]
    print(f"reconstruction_status: {report['reconstruction_status']}")
    print(f"baseline path length: {report['baseline_metrics']['path_length_mm']}")
    print(f"continuous path length: {report['continuous_metrics']['path_length_mm']}")
    print(f"path reduction percent: {improvement['path_length_mm']['improvement_percent']}")
    print(f"baseline transition count: {report['baseline_metrics']['transition_segment_count']}")
    print(f"continuous transition count: {report['continuous_metrics']['transition_segment_count']}")
    print(f"transition reduction percent: {improvement['transition_segment_count']['improvement_percent']}")
    print(f"baseline motion duration: {report['baseline_metrics']['motion_duration_s']}")
    print(f"continuous motion duration: {report['continuous_metrics']['motion_duration_s']}")
    print(f"baseline schedule duration: {report['baseline_metrics']['schedule_duration_s']}")
    print(f"continuous schedule duration: {report['continuous_metrics']['schedule_duration_s']}")
    print(f"coverage percent: {report['continuous_metrics']['coverage_percent']}")
    print(f"violation_count: {report['violation_count']}")
    print(f"warning_count: {report['warning_count']}")
    print(f"JSON path: {paths['json_output']}")
    print(f"HTML path: {paths['html_output']}")


if __name__ == "__main__":
    main()
