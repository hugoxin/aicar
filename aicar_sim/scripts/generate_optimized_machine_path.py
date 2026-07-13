import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.motion_model import load_motion_model  # noqa: E402
from aicar_sim.obstacle_model import load_safety_layout  # noqa: E402
from aicar_sim.path_optimization import build_optimized_machine_path  # noqa: E402
from aicar_sim.task_allocator import load_actuator_system  # noqa: E402


DEFAULTS = {
    "machine_path": PROJECT_ROOT / "outputs/machine_path/machine_path_plan.json",
    "collision_safety_plan": PROJECT_ROOT / "outputs/collision_safety/collision_safety_plan.json",
    "schedule": PROJECT_ROOT / "outputs/multi_actuator_schedule/multi_actuator_schedule.json",
    "motion_model": PROJECT_ROOT / "data/motion_models/demo_cartesian_gantry.json",
    "space_model": PROJECT_ROOT / "outputs/space_model/space_model_report.json",
    "nozzle_plan": PROJECT_ROOT / "outputs/nozzle_plan/nozzle_coverage_plan.json",
    "safety_layout": PROJECT_ROOT / "data/safety_models/demo_wash_bay_safety_layout.json",
    "actuator_system": PROJECT_ROOT / "data/actuator_systems/demo_multi_actuator_system.json",
    "optimization_profile": PROJECT_ROOT / "data/optimization_profiles/demo_path_optimization_profile.json",
    "output": PROJECT_ROOT / "outputs/path_optimization/optimized_machine_path_plan.json",
}


def resolve(value: str) -> Path:
    path = Path(value)
    return (path if path.is_absolute() else WORKSPACE_ROOT / path).resolve()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_input(path: Path, generator: str) -> None:
    if path.exists():
        return
    completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / generator)], cwd=WORKSPACE_ROOT)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the Stage4.4 safety-first optimized machine path.")
    for key, path in DEFAULTS.items():
        parser.add_argument("--" + key.replace("_", "-"), default=str(path.relative_to(WORKSPACE_ROOT)))
    args = parser.parse_args()
    paths = {key: resolve(getattr(args, key)) for key in DEFAULTS}
    ensure_input(paths["machine_path"], "generate_machine_path_plan.py")
    ensure_input(paths["collision_safety_plan"], "generate_collision_safety_plan.py")
    ensure_input(paths["schedule"], "generate_multi_actuator_schedule.py")
    result = build_optimized_machine_path(
        load_json(paths["machine_path"]), load_json(paths["collision_safety_plan"]),
        load_json(paths["schedule"]), load_motion_model(paths["motion_model"]),
        load_json(paths["space_model"]), load_json(paths["nozzle_plan"]),
        load_safety_layout(paths["safety_layout"]), load_actuator_system(paths["actuator_system"]),
        load_json(paths["optimization_profile"]),
    )
    paths["output"].parent.mkdir(parents=True, exist_ok=True)
    paths["output"].write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    changes = result["improvement_summary"]
    print(f"optimization_status: {result['optimization_status']}")
    for metric, label in (
        ("path_length_mm", "path_length"), ("transition_segment_count", "transition"),
        ("estimated_motion_duration_s", "motion_duration"),
    ):
        print(f"baseline_{label}: {changes[metric]['baseline']}")
        print(f"optimized_{label}: {changes[metric]['optimized']}")
        print(f"{label}_reduction_percent: {changes[metric]['improvement_percent']}")
    print(f"minimum_vehicle_clearance_mm: {result['optimized_summary']['minimum_vehicle_clearance_mm']}")
    print(f"clearance_warning_count: {result['optimized_summary']['clearance_warning_count']}")
    print(f"violation_count: {len(result['violations'])}")
    print(f"output path: {paths['output']}")


if __name__ == "__main__":
    main()
