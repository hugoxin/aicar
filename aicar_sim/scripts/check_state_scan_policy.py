import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.state_scan_policy import MOTION_STATES, calculate_initial_pass_spacing, resolve_nozzle_effective_width  # noqa: E402


def main() -> None:
    profile = json.loads((PROJECT_ROOT / "data/continuous_path_profiles/demo_continuous_surface_scan_profile_r.json").read_text(encoding="utf-8"))
    nozzle_plan = json.loads((PROJECT_ROOT / "outputs/nozzle_plan/nozzle_coverage_plan.json").read_text(encoding="utf-8"))
    if not set(MOTION_STATES) <= set(profile["state_scan_policies"]):
        raise SystemExit("one or more motion-state scan policies are missing")
    for state_id in MOTION_STATES:
        policy = profile["state_scan_policies"][state_id]
        width, source, warnings = resolve_nozzle_effective_width(state_id, "missing_check_nozzle", nozzle_plan, profile)
        spacing = calculate_initial_pass_spacing(width, float(policy["spacing_factor"]))
        if width <= 0 or spacing <= 0 or source != "repair_profile_fallback" or not warnings:
            raise SystemExit(f"effective-width fallback check failed for {state_id}")
        minimum = float(policy["minimum_state_zone_coverage_percent"])
        preferred = float(policy["maximum_preferred_coverage_percent"])
        if minimum < 90 or preferred < minimum or preferred > 100:
            raise SystemExit(f"invalid coverage target for {state_id}")
    print("PASS stage4 state scan policy")
    print("AI car state scan policy check OK")


if __name__ == "__main__":
    main()
