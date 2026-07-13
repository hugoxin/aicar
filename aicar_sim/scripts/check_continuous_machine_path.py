import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
OUTPUT = PROJECT_ROOT / "outputs/continuous_machine_path/continuous_machine_path_plan.json"


def main() -> None:
    if not OUTPUT.exists():
        completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_continuous_machine_path.py")], cwd=WORKSPACE_ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    plan = json.loads(OUTPUT.read_text(encoding="utf-8"))
    points = plan["trajectory_points"]
    validation = plan["motion_validation"]
    if validation["validation_status"] not in {"PASS", "PASS_WITH_WARNINGS"} or validation["violation_count"]:
        raise SystemExit("continuous machine motion validation failed")
    if any(float(point["delta_time_s"]) <= 0 for point in points):
        raise SystemExit("continuous machine path has non-positive delta time")
    if any(float(current["timestamp_s"]) <= float(previous["timestamp_s"]) for previous, current in zip(points, points[1:])):
        raise SystemExit("continuous machine timestamps are not strictly increasing")
    if abs(float(points[-1]["velocity_mm_s"])) > 1e-6:
        raise SystemExit("continuous machine final velocity is not zero")
    completed = subprocess.run(["git", "check-ignore", "-q", str(OUTPUT.relative_to(WORKSPACE_ROOT))], cwd=WORKSPACE_ROOT)
    if completed.returncode:
        raise SystemExit("continuous machine output JSON is not ignored")
    print("PASS stage4 continuous machine path")
    print("AI car continuous machine path check OK")


if __name__ == "__main__":
    main()
