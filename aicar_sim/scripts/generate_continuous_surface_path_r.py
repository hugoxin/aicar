import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.continuous_surface_path_repair import (  # noqa: E402
    build_continuous_surface_path_repair,
    diagnose_first_attempt,
    load_repair_scan_profile,
)
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
    "scan_profile": PROJECT_ROOT / "data/continuous_path_profiles/demo_continuous_surface_scan_profile_r.json",
    "motion_model": PROJECT_ROOT / "data/motion_models/demo_cartesian_gantry.json",
    "safety_layout": PROJECT_ROOT / "data/safety_models/demo_wash_bay_safety_layout.json",
    "actuator_system": PROJECT_ROOT / "data/actuator_systems/demo_multi_actuator_system.json",
    "first_plan": PROJECT_ROOT / "outputs/continuous_surface_path/continuous_surface_path_plan.json",
    "first_machine": PROJECT_ROOT / "outputs/continuous_machine_path/continuous_machine_path_plan.json",
    "first_schedule": PROJECT_ROOT / "outputs/continuous_schedule/continuous_multi_actuator_schedule.json",
    "output": PROJECT_ROOT / "outputs/continuous_surface_path_r/continuous_surface_path_plan_r.json",
}


def resolve(value: str) -> Path:
    path = Path(value)
    return (path if path.is_absolute() else WORKSPACE_ROOT / path).resolve()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_inputs(paths: dict[str, Path]) -> None:
    if not all(paths[key].exists() for key in ("wash_strategy", "wash_flow", "nozzle_plan", "space_model")):
        completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_abstract_nozzle_path_plan.py")], cwd=WORKSPACE_ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    if not all(paths[key].exists() for key in ("first_plan", "first_machine", "first_schedule")):
        for script in (
            "generate_continuous_surface_path.py",
            "generate_continuous_machine_path.py",
            "generate_continuous_surface_validation.py",
        ):
            completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / script)], cwd=WORKSPACE_ROOT)
            if completed.returncode:
                raise SystemExit(completed.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the Stage4.5-R state-aware continuous surface source path.")
    for key, path in DEFAULTS.items():
        parser.add_argument("--" + key.replace("_", "-"), default=str(path.relative_to(WORKSPACE_ROOT)))
    args = parser.parse_args()
    paths = {key: resolve(getattr(args, key)) for key in DEFAULTS}
    ensure_inputs(paths)
    diagnosis = diagnose_first_attempt(
        load_json(paths["first_plan"]), load_json(paths["first_machine"]), load_json(paths["first_schedule"])
    )
    plan = build_continuous_surface_path_repair(
        load_json(paths["vehicle_type_result"]),
        load_json(paths["wash_strategy"]),
        load_json(paths["wash_flow"]),
        load_json(paths["nozzle_plan"]),
        load_json(paths["space_model"]),
        load_surface_model(paths["surface_model"]),
        load_repair_scan_profile(paths["scan_profile"]),
        load_motion_model(paths["motion_model"]),
        load_safety_layout(paths["safety_layout"]),
        load_actuator_system(paths["actuator_system"]),
        diagnosis,
    )
    paths["output"].parent.mkdir(parents=True, exist_ok=True)
    paths["output"].write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"repair_profile_id: {plan['repair_profile_id']}")
    for key in ("state_count", "surface_patch_count", "scan_pass_count", "surface_task_count", "direct_patch_connection_count", "adaptive_safe_connection_count", "trajectory_point_count", "source_path_length_mm", "unique_geometric_coverage_percent", "mean_surface_visit_count"):
        print(f"{key}: {plan['summary'][key]}")
    print(f"output path: {paths['output']}")


if __name__ == "__main__":
    main()
