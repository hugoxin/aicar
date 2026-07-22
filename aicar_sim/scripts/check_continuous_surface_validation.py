import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
OUTPUT = PROJECT_ROOT / "outputs/continuous_surface_validation/continuous_collision_safety_validation_report.json"


def main() -> None:
    if not OUTPUT.exists():
        completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_continuous_surface_validation.py")], cwd=WORKSPACE_ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    report = json.loads(OUTPUT.read_text(encoding="utf-8"))
    summary = report["summary"]
    required_zero = ("violation_count", "static_collision_count", "vehicle_collision_count", "forbidden_zone_entry_count", "unassigned_task_count", "conflict_count_after_resolution", "unresolved_conflict_count", "deadlock_warning_count")
    failures = [key for key in required_zero if int(summary[key]) != 0]
    if failures:
        raise SystemExit("continuous surface safety failures: " + ", ".join(failures))
    if float(summary["minimum_clearance_mm"]) < 250:
        raise SystemExit("continuous surface minimum clearance below 250 mm")
    if int(summary["safe_stop_point_count"]) < 3:
        raise SystemExit("continuous surface safe-stop count below actuator count")
    for relative in (
        "aicar_sim/outputs/continuous_collision_safety/continuous_collision_safety_plan.json",
        "aicar_sim/outputs/continuous_schedule/continuous_multi_actuator_schedule.json",
        "aicar_sim/outputs/continuous_surface_validation/continuous_collision_safety_validation_report.json",
    ):
        if subprocess.run(["git", "check-ignore", "-q", relative], cwd=WORKSPACE_ROOT).returncode:
            raise SystemExit(f"generated output is not ignored: {relative}")
    print("PASS stage4 continuous surface validation")
    print("AI car continuous surface validation check OK")


if __name__ == "__main__":
    main()
