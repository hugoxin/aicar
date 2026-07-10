import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "machine_path" / "machine_path_plan.json"


def run_generator() -> None:
    completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "generate_machine_path_plan.py")], cwd=str(WORKSPACE_ROOT), text=True, capture_output=True)
    if completed.returncode != 0:
        print(completed.stdout)
        print(completed.stderr, file=sys.stderr)
        raise SystemExit(completed.returncode)


def assert_git_ignored(path: Path) -> None:
    relative = path.relative_to(WORKSPACE_ROOT)
    completed = subprocess.run(["git", "check-ignore", "-v", str(relative)], cwd=str(WORKSPACE_ROOT), capture_output=True, text=True)
    if completed.returncode != 0:
        raise SystemExit(f"generated output is not ignored: {relative}")


def main() -> None:
    run_generator()
    plan = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    points = plan.get("trajectory_points", [])
    if not points:
        raise SystemExit("machine path has no trajectory points")
    if len(points) > 5000:
        raise SystemExit(f"trajectory point count exceeds 5000: {len(points)}")
    required = {"x_mm", "y_mm", "z_mm", "state_id", "zone_id", "nozzle_id", "segment_id", "timestamp_s", "delta_time_s"}
    previous_timestamp = None
    for index, point in enumerate(points):
        missing = required - set(point)
        if missing:
            raise SystemExit(f"trajectory point {index} missing fields: {', '.join(sorted(missing))}")
        if float(point["delta_time_s"]) <= 0:
            raise SystemExit(f"trajectory point {index} has non-positive delta_time_s")
        timestamp = float(point["timestamp_s"])
        if previous_timestamp is not None and timestamp <= previous_timestamp:
            raise SystemExit(f"trajectory timestamp is not strictly increasing at point {index}")
        previous_timestamp = timestamp
    if abs(float(points[-1].get("velocity_mm_s", 0))) > 1e-6:
        raise SystemExit("last trajectory point velocity is not close to zero")
    assert_git_ignored(OUTPUT_PATH)
    print("PASS stage4 machine path plan")
    print("AI car machine path plan check OK")


if __name__ == "__main__":
    main()
