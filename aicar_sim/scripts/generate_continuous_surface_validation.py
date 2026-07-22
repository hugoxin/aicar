import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.continuous_surface_validation import build_continuous_surface_validation  # noqa: E402
from aicar_sim.motion_model import load_motion_model  # noqa: E402
from aicar_sim.obstacle_model import load_safety_layout  # noqa: E402
from aicar_sim.task_allocator import load_actuator_system  # noqa: E402


DEFAULTS = {
    "surface_path": PROJECT_ROOT / "outputs/continuous_surface_path/continuous_surface_path_plan.json",
    "machine_path": PROJECT_ROOT / "outputs/continuous_machine_path/continuous_machine_path_plan.json",
    "motion_model": PROJECT_ROOT / "data/motion_models/demo_cartesian_gantry.json",
    "space_model": PROJECT_ROOT / "outputs/space_model/space_model_report.json",
    "nozzle_plan": PROJECT_ROOT / "outputs/nozzle_plan/nozzle_coverage_plan.json",
    "safety_layout": PROJECT_ROOT / "data/safety_models/demo_wash_bay_safety_layout.json",
    "actuator_system": PROJECT_ROOT / "data/actuator_systems/demo_multi_actuator_system.json",
    "baseline_report": PROJECT_ROOT / "outputs/path_optimization/path_optimization_report.json",
    "collision_output": PROJECT_ROOT / "outputs/continuous_collision_safety/continuous_collision_safety_plan.json",
    "schedule_output": PROJECT_ROOT / "outputs/continuous_schedule/continuous_multi_actuator_schedule.json",
    "validation_output": PROJECT_ROOT / "outputs/continuous_surface_validation/continuous_collision_safety_validation_report.json",
}


def resolve(value: str) -> Path:
    path = Path(value)
    return (path if path.is_absolute() else WORKSPACE_ROOT / path).resolve()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Stage4.5 motion, collision, interlock, schedule, and safe-stop validation.")
    for key, path in DEFAULTS.items():
        parser.add_argument("--" + key.replace("_", "-"), default=str(path.relative_to(WORKSPACE_ROOT)))
    args = parser.parse_args()
    paths = {key: resolve(getattr(args, key)) for key in DEFAULTS}
    if not paths["machine_path"].exists():
        completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_continuous_machine_path.py")], cwd=WORKSPACE_ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    if not paths["baseline_report"].exists():
        completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_path_optimization_report.py")], cwd=WORKSPACE_ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    baseline = load_json(paths["baseline_report"])["optimized_metrics"]
    report, collision_plan, schedule = build_continuous_surface_validation(
        load_json(paths["surface_path"]), load_json(paths["machine_path"]),
        load_motion_model(paths["motion_model"]), load_json(paths["space_model"]),
        load_json(paths["nozzle_plan"]), load_safety_layout(paths["safety_layout"]),
        load_actuator_system(paths["actuator_system"]), baseline,
    )
    write_json(paths["collision_output"], collision_plan)
    write_json(paths["schedule_output"], schedule)
    write_json(paths["validation_output"], report)
    summary = report["summary"]
    print(f"motion_validation_status: {report['motion_validation_status']}")
    print(f"collision_validation_status: {report['collision_validation_status']}")
    for key in ("violation_count", "warning_count", "static_collision_count", "vehicle_collision_count", "forbidden_zone_entry_count", "unresolved_conflict_count", "safe_stop_point_count"):
        print(f"{key}: {summary[key]}")
    print(f"collision output: {paths['collision_output']}")
    print(f"schedule output: {paths['schedule_output']}")
    print(f"validation output: {paths['validation_output']}")


if __name__ == "__main__":
    main()
