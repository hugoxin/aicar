import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROFILE = PROJECT_ROOT / "data/optimization_profiles/demo_path_optimization_profile.json"


def main() -> None:
    if not PROFILE.exists():
        raise SystemExit(f"optimization profile missing: {PROFILE}")
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    geometry, clearance, schedule, weights = (profile[key] for key in ("geometry", "clearance", "schedule", "objective_weights"))
    positive = ("duplicate_point_tolerance_mm", "collinear_distance_tolerance_mm", "collinear_angle_tolerance_deg", "maximum_output_point_spacing_mm")
    if any(float(geometry[key]) <= 0 for key in positive):
        raise SystemExit("all geometry tolerances must be positive")
    if int(geometry["maximum_trajectory_points"]) > 5000:
        raise SystemExit("maximum_trajectory_points must not exceed 5000")
    if not 0 < float(clearance["hard_minimum_mm"]) < float(clearance["warning_threshold_mm"]) < float(clearance["recommended_mm"]):
        raise SystemExit("clearance policy ordering is invalid")
    if int(schedule["maximum_iterations"]) <= 0:
        raise SystemExit("maximum_iterations must be positive")
    if profile["transition"].get("allow_reorder_across_states"):
        raise SystemExit("cross-state reordering must remain disabled")
    if not schedule.get("preserve_wash_state_order"):
        raise SystemExit("wash state order must be preserved")
    if float(weights["safety_violation"]) <= max(float(value) for key, value in weights.items() if key != "safety_violation"):
        raise SystemExit("safety_violation must have the highest objective weight")
    print("PASS stage4 path optimization profile")
    print("AI car path optimization profile check OK")


if __name__ == "__main__":
    main()
