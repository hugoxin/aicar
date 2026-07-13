import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.shared_space_interlock import detect_time_interval_conflicts  # noqa: E402


OUTPUT = PROJECT_ROOT / "outputs/multi_actuator_schedule/multi_actuator_schedule.json"


def main() -> None:
    completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_multi_actuator_schedule.py")], cwd=WORKSPACE_ROOT)
    if completed.returncode:
        raise SystemExit(completed.returncode)
    schedule = json.loads(OUTPUT.read_text(encoding="utf-8"))
    by_actuator = defaultdict(list)
    for item in schedule["schedule_items"]:
        if float(item["adjusted_end_s"]) <= float(item["adjusted_start_s"]):
            raise SystemExit(f"non-positive schedule interval: {item['task_id']}")
        by_actuator[item["actuator_id"]].append(item)
    for actuator_id, items in by_actuator.items():
        ordered = sorted(items, key=lambda item: float(item["adjusted_start_s"]))
        for left, right in zip(ordered, ordered[1:]):
            if float(left["adjusted_end_s"]) > float(right["adjusted_start_s"]) + 1e-6:
                raise SystemExit(f"same-actuator overlap: {actuator_id}")
    for lock in schedule["resource_locks"]:
        if float(lock["end_s"]) <= float(lock["start_s"]):
            raise SystemExit("invalid resource lock interval")
    valid_sync = {"SYNCHRONIZED", "DEGRADED", "BLOCKED_BY_INTERLOCK", "NOT_APPLICABLE"}
    if any(item.get("sync_status") not in valid_sync for item in schedule["sync_groups"]):
        raise SystemExit("invalid sync group status")
    synthetic = [
        {"resource_id": "shared", "actuator_id": "a", "task_id": "a1", "start_s": 0, "end_s": 2},
        {"resource_id": "shared", "actuator_id": "b", "task_id": "b1", "start_s": 2, "end_s": 3},
    ]
    if not detect_time_interval_conflicts(synthetic):
        raise SystemExit("boundary-overlap interlock conflict was not detected")
    if schedule["summary"]["conflict_count_after_resolution"] != len(schedule["conflicts_after_resolution"]):
        raise SystemExit("resolved conflict summary is inconsistent")
    ignored = subprocess.run(["git", "check-ignore", "-v", str(OUTPUT.relative_to(WORKSPACE_ROOT))], cwd=WORKSPACE_ROOT)
    if ignored.returncode:
        raise SystemExit("generated multi-actuator schedule is not ignored")
    print("PASS stage4 multi actuator schedule")
    print("AI car multi actuator schedule check OK")


if __name__ == "__main__":
    main()
