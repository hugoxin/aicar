import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
OUTPUT = PROJECT_ROOT / "outputs/optimized_schedule/optimized_multi_actuator_schedule.json"
PLAN = PROJECT_ROOT / "outputs/path_optimization/optimized_machine_path_plan.json"


def main() -> None:
    completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_optimized_schedule.py")], cwd=WORKSPACE_ROOT)
    if completed.returncode:
        raise SystemExit(completed.returncode)
    schedule = json.loads(OUTPUT.read_text(encoding="utf-8"))
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    summary, baseline = schedule["summary"], schedule["baseline_summary"]
    if summary["task_count"] != baseline["task_count"] or summary["assigned_task_count"] != summary["task_count"] or summary["unassigned_task_count"] != 0:
        raise SystemExit("optimized schedule changed or failed to assign the task set")
    by_actuator = defaultdict(list)
    for item in schedule["schedule_items"]:
        if float(item["duration_s"]) <= 0 or float(item["adjusted_end_s"]) <= float(item["adjusted_start_s"]):
            raise SystemExit(f"invalid optimized interval: {item['task_id']}")
        by_actuator[item["actuator_id"]].append(item)
    for actuator_id, items in by_actuator.items():
        ordered = sorted(items, key=lambda item: float(item["adjusted_start_s"]))
        if any(float(left["adjusted_end_s"]) > float(right["adjusted_start_s"]) + 1e-6 for left, right in zip(ordered, ordered[1:])):
            raise SystemExit(f"same actuator overlap: {actuator_id}")
    if summary["conflict_count_after_resolution"] != 0 or summary["unresolved_conflict_count"] != 0 or summary["deadlock_warning_count"] != 0:
        raise SystemExit("optimized schedule retains conflict or deadlock")
    if not plan["safety_validation"]["conditions"]["safe_stop_points_valid"]:
        raise SystemExit("safe-stop validation regressed")
    ignored = subprocess.run(["git", "check-ignore", "-v", str(OUTPUT.relative_to(WORKSPACE_ROOT))], cwd=WORKSPACE_ROOT)
    if ignored.returncode:
        raise SystemExit("optimized schedule JSON is not ignored")
    print("PASS stage4 optimized schedule")
    print("AI car optimized schedule check OK")


if __name__ == "__main__":
    main()
