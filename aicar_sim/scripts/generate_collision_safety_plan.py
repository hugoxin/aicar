import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.collision_safety_planner import build_collision_safety_plan  # noqa: E402
from aicar_sim.motion_model import load_motion_model  # noqa: E402
from aicar_sim.obstacle_model import load_safety_layout  # noqa: E402
from aicar_sim.task_allocator import load_actuator_system  # noqa: E402


DEFAULTS = {
    "machine_path": PROJECT_ROOT / "outputs/machine_path/machine_path_plan.json",
    "motion_model": PROJECT_ROOT / "data/motion_models/demo_cartesian_gantry.json",
    "space_model": PROJECT_ROOT / "outputs/space_model/space_model_report.json",
    "nozzle_plan": PROJECT_ROOT / "outputs/nozzle_plan/nozzle_coverage_plan.json",
    "safety_layout": PROJECT_ROOT / "data/safety_models/demo_wash_bay_safety_layout.json",
    "actuator_system": PROJECT_ROOT / "data/actuator_systems/demo_multi_actuator_system.json",
    "output": PROJECT_ROOT / "outputs/collision_safety/collision_safety_plan.json",
}


def _relative(path: Path) -> str:
    return str(path.relative_to(WORKSPACE_ROOT))


def resolve(value: str) -> Path:
    path = Path(value)
    return (path if path.is_absolute() else WORKSPACE_ROOT / path).resolve()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_machine_path(path: Path) -> None:
    if path.exists():
        return
    completed = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts/generate_machine_path_plan.py"), "--output", str(path)],
        cwd=WORKSPACE_ROOT,
    )
    if completed.returncode:
        raise SystemExit(completed.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the Stage4.3 collision safety candidate plan.")
    for key, path in DEFAULTS.items():
        parser.add_argument("--" + key.replace("_", "-"), default=_relative(path))
    args = parser.parse_args()
    paths = {key: resolve(getattr(args, key)) for key in DEFAULTS}
    ensure_machine_path(paths["machine_path"])
    missing = [str(path) for key, path in paths.items() if key != "output" and not path.exists()]
    if missing:
        raise SystemExit("missing input: " + ", ".join(missing))
    plan = build_collision_safety_plan(
        load_json(paths["machine_path"]),
        load_motion_model(paths["motion_model"]),
        load_json(paths["space_model"]),
        load_json(paths["nozzle_plan"]),
        load_safety_layout(paths["safety_layout"]),
        load_actuator_system(paths["actuator_system"]),
    )
    paths["output"].parent.mkdir(parents=True, exist_ok=True)
    paths["output"].write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = plan["summary"]
    print(f"validation_status: {plan['validation_status']}")
    print(f"safety_layout_id: {plan['safety_layout_id']}")
    print(f"actuator_system_id: {plan['actuator_system_id']}")
    for key in ("actuator_count", "task_count", "unassigned_task_count", "swept_volume_count", "static_collision_count", "vehicle_collision_count", "warning_count", "violation_count"):
        print(f"{key}: {summary[key]}")
    print(f"output path: {paths['output']}")


if __name__ == "__main__":
    main()
