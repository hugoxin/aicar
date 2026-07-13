import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.collision_checker import check_static_obstacle_collisions, check_swept_volume_collisions  # noqa: E402


OUTPUT = PROJECT_ROOT / "outputs/collision_safety/collision_safety_plan.json"


def run_generator() -> None:
    completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_collision_safety_plan.py")], cwd=WORKSPACE_ROOT)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def assert_ignored(path: Path) -> None:
    completed = subprocess.run(["git", "check-ignore", "-v", str(path.relative_to(WORKSPACE_ROOT))], cwd=WORKSPACE_ROOT, capture_output=True, text=True)
    if completed.returncode:
        raise SystemExit(f"generated output is not ignored: {path}")


def main() -> None:
    run_generator()
    plan = json.loads(OUTPUT.read_text(encoding="utf-8"))
    summary = plan["summary"]
    if summary["task_count"] <= 0 or summary["actuator_count"] < 2 or summary["swept_volume_count"] <= 0:
        raise SystemExit("collision plan has no meaningful tasks, actuators, or swept volumes")
    if summary["assigned_task_count"] != summary["task_count"] or plan["unassigned_tasks"]:
        raise SystemExit("not every task has an actuator assignment")
    if any(not task.get("assigned_actuator_id") for task in plan["actuator_tasks"]):
        raise SystemExit("task without assigned actuator")
    if any(item.get("severity") == "CRITICAL" for item in plan["warnings"]):
        raise SystemExit("critical issue was incorrectly stored as warning")
    bounds = {"x_min_mm": -1, "x_max_mm": 1, "y_min_mm": -1, "y_max_mm": 1, "z_min_mm": -1, "z_max_mm": 1}
    obstacle = {"obstacle_id": "synthetic", "bounds": bounds}
    point = {"x_mm": 0, "y_mm": 0, "z_mm": 0, "sequence_index": 1}
    volume = {"bounds": bounds, "actuator_id": "test", "end_point_index": 1, "segment_id": "test", "state_id": "test", "zone_id": "test", "end_time_s": 1}
    if not check_static_obstacle_collisions([point], [obstacle], "test"):
        raise SystemExit("synthetic point collision was not detected")
    if not check_swept_volume_collisions([volume], [obstacle]):
        raise SystemExit("synthetic swept collision was not detected")
    assert_ignored(OUTPUT)
    print(f"validation_status: {plan['validation_status']}")
    print("PASS stage4 collision safety plan")
    print("AI car collision safety plan check OK")


if __name__ == "__main__":
    main()
