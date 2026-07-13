import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
OUTPUT = PROJECT_ROOT / "outputs/path_optimization/optimized_machine_path_plan.json"


def assert_ignored(path: Path) -> None:
    completed = subprocess.run(["git", "check-ignore", "-v", str(path.relative_to(WORKSPACE_ROOT))], cwd=WORKSPACE_ROOT, capture_output=True, text=True)
    if completed.returncode:
        raise SystemExit(f"generated output is not ignored: {path}")


def main() -> None:
    completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_optimized_machine_path.py")], cwd=WORKSPACE_ROOT)
    if completed.returncode:
        raise SystemExit(completed.returncode)
    plan = json.loads(OUTPUT.read_text(encoding="utf-8"))
    points = plan["trajectory_points"]
    if not points or len(points) > 5000:
        raise SystemExit("optimized trajectory point count is invalid")
    if any(float(point.get("delta_time_s", 0)) <= 0 for point in points):
        raise SystemExit("optimized trajectory contains non-positive delta_time_s")
    if any(float(right["timestamp_s"]) <= float(left["timestamp_s"]) for left, right in zip(points, points[1:])):
        raise SystemExit("optimized trajectory timestamps are not strictly increasing")
    if abs(float(points[-1]["velocity_mm_s"])) > 1e-6:
        raise SystemExit("optimized trajectory does not stop at the last point")
    conditions = plan["safety_validation"]["conditions"]
    required = ("task_set_unchanged", "task_count_unchanged", "wash_state_order_unchanged", "minimum_clearance_not_reduced", "clearance_warnings_not_increased", "motion_validation_passed")
    failed = [key for key in required if not conditions.get(key)]
    if failed:
        raise SystemExit("optimized path acceptance conditions failed: " + ", ".join(failed))
    if plan["safety_validation"]["motion_validation"]["violation_count"] != 0 or plan["violations"]:
        raise SystemExit("optimized path contains safety violations")
    if not plan["accepted_optimization"]:
        raise SystemExit(f"optimization was rejected: {plan['rejection_reasons']}")
    assert_ignored(OUTPUT)
    print(f"optimization_status: {plan['optimization_status']}")
    print("PASS stage4 optimized machine path")
    print("AI car optimized machine path check OK")


if __name__ == "__main__":
    main()
