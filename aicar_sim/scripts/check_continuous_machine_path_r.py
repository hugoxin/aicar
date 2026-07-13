import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
OUTPUT = PROJECT_ROOT / "outputs/continuous_machine_path_r/continuous_machine_path_plan_r.json"


def main() -> None:
    if not OUTPUT.exists():
        completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_continuous_machine_path_r.py")], cwd=WORKSPACE_ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    plan = json.loads(OUTPUT.read_text(encoding="utf-8"))
    points = plan["trajectory_points"]
    timestamps = [float(item["timestamp_s"]) for item in points]
    if not points or any(current <= previous for previous, current in zip(timestamps, timestamps[1:])):
        raise SystemExit("machine path timestamps are not strictly increasing")
    if any(float(item["delta_time_s"]) <= 0 for item in points):
        raise SystemExit("machine path contains a non-positive delta_time_s")
    if abs(float(points[-1]["velocity_mm_s"])) > 1e-6:
        raise SystemExit("machine path terminal velocity is not zero")
    validation = plan["motion_validation"]
    required_checks = ("workspace", "velocity", "acceleration", "continuity", "timestamp")
    metric_summary = validation["metric_summary"]
    if validation["violation_count"] or any(not metric_summary[name]["passed"] for name in required_checks):
        raise SystemExit(f"machine motion validation failed: {validation['violations']}")
    if subprocess.run(["git", "check-ignore", "-q", str(OUTPUT.relative_to(WORKSPACE_ROOT))], cwd=WORKSPACE_ROOT).returncode:
        raise SystemExit("repaired machine path JSON is not ignored")
    print("PASS stage4 repaired continuous machine path")
    print("AI car repaired continuous machine path check OK")


if __name__ == "__main__":
    main()
