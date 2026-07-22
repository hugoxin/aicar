import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.continuous_surface_path_repair import build_continuous_machine_path_repair  # noqa: E402
from aicar_sim.motion_model import load_motion_model  # noqa: E402
from aicar_sim.motion_validator import validate_machine_path  # noqa: E402


DEFAULTS = {
    "surface_path": PROJECT_ROOT / "outputs/continuous_surface_path_r/continuous_surface_path_plan_r.json",
    "motion_model": PROJECT_ROOT / "data/motion_models/demo_cartesian_gantry.json",
    "space_model": PROJECT_ROOT / "outputs/space_model/space_model_report.json",
    "nozzle_plan": PROJECT_ROOT / "outputs/nozzle_plan/nozzle_coverage_plan.json",
    "output": PROJECT_ROOT / "outputs/continuous_machine_path_r/continuous_machine_path_plan_r.json",
}


def resolve(value: str) -> Path:
    path = Path(value)
    return (path if path.is_absolute() else WORKSPACE_ROOT / path).resolve()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the Stage4.5-R machine candidate path.")
    for key, path in DEFAULTS.items():
        parser.add_argument("--" + key.replace("_", "-"), default=str(path.relative_to(WORKSPACE_ROOT)))
    args = parser.parse_args()
    paths = {key: resolve(getattr(args, key)) for key in DEFAULTS}
    if not paths["surface_path"].exists():
        completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_continuous_surface_path_r.py")], cwd=WORKSPACE_ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    motion_model = load_motion_model(paths["motion_model"])
    plan = build_continuous_machine_path_repair(load_json(paths["surface_path"]), motion_model)
    validation = validate_machine_path(plan, motion_model, load_json(paths["space_model"]), load_json(paths["nozzle_plan"]))
    plan["motion_validation"] = validation
    paths["output"].parent.mkdir(parents=True, exist_ok=True)
    paths["output"].write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = plan["summary"]
    print(f"trajectory_point_count: {summary['trajectory_point_count']}")
    print(f"transition_count: {summary['transition_segment_count']}")
    print(f"machine_path_length_mm: {summary['path_length_mm']}")
    print(f"motion_duration_s: {summary['estimated_motion_duration_s']}")
    print(f"minimum_clearance_mm: {validation['metric_summary']['clearance']['minimum_measured_mm']}")
    print(f"motion_violation_count: {validation['violation_count']}")
    print(f"output path: {paths['output']}")


if __name__ == "__main__":
    main()
