import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.continuous_surface_path_planner import build_continuous_surface_path_plan, load_continuous_path_profile  # noqa: E402
from aicar_sim.motion_model import load_motion_model  # noqa: E402
from aicar_sim.obstacle_model import load_safety_layout  # noqa: E402
from aicar_sim.surface_model import load_surface_model  # noqa: E402
from aicar_sim.task_allocator import load_actuator_system  # noqa: E402


DEFAULTS = {
    "vehicle_type_result": WORKSPACE_ROOT / "vehicle_type_lab/outputs/predictions/vehicle_type_result.json",
    "wash_strategy": PROJECT_ROOT / "outputs/wash_strategy/wash_strategy_plan.json",
    "wash_flow": PROJECT_ROOT / "outputs/wash_flow/wash_flow_run.json",
    "nozzle_plan": PROJECT_ROOT / "outputs/nozzle_plan/nozzle_coverage_plan.json",
    "space_model": PROJECT_ROOT / "outputs/space_model/space_model_report.json",
    "surface_model": PROJECT_ROOT / "data/surface_models/demo_sedan_surface_model.json",
    "scan_profile": PROJECT_ROOT / "data/continuous_path_profiles/demo_continuous_surface_scan_profile.json",
    "motion_model": PROJECT_ROOT / "data/motion_models/demo_cartesian_gantry.json",
    "safety_layout": PROJECT_ROOT / "data/safety_models/demo_wash_bay_safety_layout.json",
    "actuator_system": PROJECT_ROOT / "data/actuator_systems/demo_multi_actuator_system.json",
    "baseline_report": PROJECT_ROOT / "outputs/path_optimization/path_optimization_report.json",
    "output": PROJECT_ROOT / "outputs/continuous_surface_path/continuous_surface_path_plan.json",
}


def resolve(value: str) -> Path:
    path = Path(value)
    return (path if path.is_absolute() else WORKSPACE_ROOT / path).resolve()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_stage2_inputs(paths: list[Path]) -> None:
    if all(path.exists() for path in paths):
        return
    completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_abstract_nozzle_path_plan.py")], cwd=WORKSPACE_ROOT)
    if completed.returncode:
        raise SystemExit(completed.returncode)
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise SystemExit("missing Stage2 input after generation: " + ", ".join(missing))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Stage4.5 continuous-surface candidate source path.")
    for key, path in DEFAULTS.items():
        parser.add_argument("--" + key.replace("_", "-"), default=str(path.relative_to(WORKSPACE_ROOT)))
    args = parser.parse_args()
    paths = {key: resolve(getattr(args, key)) for key in DEFAULTS}
    stage2 = [paths[key] for key in ("wash_strategy", "wash_flow", "nozzle_plan", "space_model")]
    ensure_stage2_inputs(stage2)
    if not paths["vehicle_type_result"].exists():
        raise SystemExit(f"vehicle type result not found: {paths['vehicle_type_result']}")
    baseline_metrics = None
    if paths["baseline_report"].exists():
        baseline_metrics = load_json(paths["baseline_report"]).get("optimized_metrics")
    plan = build_continuous_surface_path_plan(
        load_json(paths["vehicle_type_result"]),
        load_json(paths["wash_strategy"]),
        load_json(paths["wash_flow"]),
        load_json(paths["nozzle_plan"]),
        load_json(paths["space_model"]),
        load_surface_model(paths["surface_model"]),
        load_continuous_path_profile(paths["scan_profile"]),
        load_motion_model(paths["motion_model"]),
        load_safety_layout(paths["safety_layout"]),
        load_actuator_system(paths["actuator_system"]),
        baseline_metrics,
    )
    paths["output"].parent.mkdir(parents=True, exist_ok=True)
    paths["output"].write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"surface_model_id: {plan['surface_model_id']}")
    print(f"scan_profile_id: {plan['scan_profile_id']}")
    for key in ("surface_patch_count", "scan_pass_count", "connection_count", "trajectory_point_count", "path_length_mm", "estimated_surface_coverage_percent"):
        print(f"{key}: {plan['summary'][key]}")
    print(f"validation_status: {plan['validation']['validation_status']}")
    print(f"output path: {paths['output']}")


if __name__ == "__main__":
    main()
