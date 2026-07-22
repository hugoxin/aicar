import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROFILE = PROJECT_ROOT / "data/continuous_path_profiles/demo_continuous_surface_scan_profile_r.json"
MOTION_STATES = {"pre_rinse", "foam", "top_clean", "side_clean", "wheel_clean", "air_dry"}


def main() -> None:
    if not PROFILE.exists():
        raise SystemExit(f"repair profile missing: {PROFILE}")
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    global_rules = profile["global"]
    coverage = profile["coverage_targets"]
    policies = profile["state_scan_policies"]
    aggregation = profile["task_aggregation"]
    connection = profile["connection_policy"]
    checks = {
        "hard minimum is 250 mm": global_rules["hard_minimum_clearance_mm"] == 250,
        "total coverage threshold is at least 92 percent": coverage["minimum_total_unique_coverage_percent"] >= 92,
        "zone coverage threshold is at least 90 percent": coverage["minimum_zone_coverage_percent"] >= 90,
        "motion policies are complete": MOTION_STATES <= set(policies),
        "dwell produces no motion": policies["dwell"].get("motion_required") is False,
        "cross-state reordering is disabled": connection["allow_cross_state_reordering"] is False,
        "aggregation is enabled": aggregation["enabled"] is True,
        "scan passes stay inside tasks": aggregation["keep_scan_passes_inside_task"] is True,
        "scan passes are not schedule tasks": aggregation["emit_scan_pass_as_independent_task"] is False,
        "output point limit does not exceed 5000": global_rules["maximum_output_points"] <= 5000,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise SystemExit("repair profile checks failed: " + ", ".join(failed))
    print("PASS stage4 continuous surface repair profile")
    print("AI car continuous surface repair profile check OK")


if __name__ == "__main__":
    main()
