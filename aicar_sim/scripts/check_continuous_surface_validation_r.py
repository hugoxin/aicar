import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
OUTPUT = PROJECT_ROOT / "outputs/continuous_surface_validation_r/continuous_surface_validation_r.json"


def main() -> None:
    if not OUTPUT.exists():
        completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_continuous_surface_validation_r.py")], cwd=WORKSPACE_ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    report = json.loads(OUTPUT.read_text(encoding="utf-8"))
    summary = report["summary"]
    zero_keys = (
        "static_collision_count",
        "vehicle_collision_count",
        "forbidden_zone_entry_count",
        "unassigned_task_count",
        "conflict_count_after_resolution",
        "unresolved_conflict_count",
        "deadlock_warning_count",
        "violation_count",
    )
    if any(summary[key] != 0 for key in zero_keys):
        raise SystemExit("repaired path contains a collision, assignment, interlock, deadlock, or validation failure")
    if summary["safe_stop_point_count"] < 3 or summary["minimum_clearance_mm"] < 250:
        raise SystemExit("safe-stop or minimum-clearance requirement failed")
    if not all(report["safety_conditions"].values()):
        raise SystemExit("one or more Stage4.5-R safety conditions failed")
    if subprocess.run(["git", "check-ignore", "-q", str(OUTPUT.relative_to(WORKSPACE_ROOT))], cwd=WORKSPACE_ROOT).returncode:
        raise SystemExit("repaired validation JSON is not ignored")
    print("PASS stage4 repaired continuous surface validation")
    print("AI car repaired continuous surface validation check OK")


if __name__ == "__main__":
    main()
