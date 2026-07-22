import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
OUTPUT = PROJECT_ROOT / "outputs/continuous_surface_path_r/continuous_surface_path_plan_r.json"
STATES = {"pre_rinse", "foam", "dwell", "top_clean", "side_clean", "wheel_clean", "air_dry"}
ZONES = {"roof", "left_side", "right_side", "front", "rear", "wheels"}
PATCHES = {"roof_main", "left_side_main", "right_side_main", "front_main", "rear_main", "left_front_wheel", "left_rear_wheel", "right_front_wheel", "right_rear_wheel"}


def main() -> None:
    if not OUTPUT.exists():
        completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_continuous_surface_path_r.py")], cwd=WORKSPACE_ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    plan = json.loads(OUTPUT.read_text(encoding="utf-8"))
    summary = plan["summary"]
    validation = plan["validation"]
    safety_rejected = summary["safety_rejected_direct_candidate_count"]
    distance_rejected = summary["distance_policy_rejected_direct_candidate_count"]
    total_rejected = summary["direct_candidate_rejected_count"]
    seen_states = {item["state_id"] for item in plan["states"]}
    seen_zones = {zone for task in plan["surface_tasks"] for zone in task["zone_ids"]}
    seen_patches = {patch for task in plan["surface_tasks"] for patch in task["patch_ids"]}
    checks = [
        STATES <= seen_states,
        ZONES <= seen_zones,
        PATCHES <= seen_patches,
        len({patch for patch in seen_patches if patch.endswith("wheel")}) == 4,
        bool(plan["scan_passes"]),
        bool(plan["surface_tasks"]),
        summary["trajectory_point_count"] <= 5000,
        plan["coverage_summary"]["unique_geometric_coverage_percent"] >= 92,
        min(item["standoff_mm"] for item in plan["trajectory_points"]) >= 250,
        validation["violation_count"] == 0,
        safety_rejected + distance_rejected == total_rejected,
        summary["direct_patch_connection_count"] >= 0,
    ]
    if not all(checks):
        raise SystemExit("repaired continuous surface path semantic or safety check failed")
    if subprocess.run(["git", "check-ignore", "-q", str(OUTPUT.relative_to(WORKSPACE_ROOT))], cwd=WORKSPACE_ROOT).returncode:
        raise SystemExit("repaired continuous surface JSON is not ignored")
    print("PASS stage4 repaired continuous surface path")
    print("AI car repaired continuous surface path check OK")


if __name__ == "__main__":
    main()
