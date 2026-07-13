import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
OUTPUT = PROJECT_ROOT / "outputs/continuous_surface_path_r/continuous_surface_path_plan_r.json"


def main() -> None:
    if not OUTPUT.exists():
        completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_continuous_surface_path_r.py")], cwd=WORKSPACE_ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    plan = json.loads(OUTPUT.read_text(encoding="utf-8"))
    aggregation = plan["aggregation_summary"]
    if aggregation["validation_status"] != "PASS" or not all(aggregation["checks"].values()):
        raise SystemExit(f"surface task aggregation failed: {aggregation}")
    tasks = plan["surface_tasks"]
    source_passes = {item["scan_pass_id"] for item in plan["scan_passes"]}
    task_passes = [pass_id for task in tasks for pass_id in task["scan_pass_ids"]]
    if set(task_passes) != source_passes or len(task_passes) != len(source_passes):
        raise SystemExit("scan pass IDs were lost or duplicated during aggregation")
    if any(not task["scan_pass_ids"] or float(task["estimated_duration_s"]) < 0 for task in tasks):
        raise SystemExit("empty or negative-duration surface task found")
    semantic_keys = {"state_id", "zone_ids", "patch_ids", "nozzle_id", "actuator_id"}
    if any(not semantic_keys <= set(task["task_semantics"]) for task in tasks):
        raise SystemExit("surface task semantics are incomplete")
    state_order = [item["state_id"] for item in plan["states"] if item["state_id"] != "dwell"]
    task_state_order = list(dict.fromkeys(task["state_id"] for task in tasks))
    if task_state_order != state_order:
        raise SystemExit("surface task state order changed")
    if len(tasks) >= len(plan["scan_passes"]):
        raise SystemExit("aggregation did not reduce downstream task granularity")
    print("PASS stage4 surface task aggregation")
    print("AI car surface task aggregation check OK")


if __name__ == "__main__":
    main()
