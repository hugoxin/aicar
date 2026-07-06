import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aicar_sim.vehicle_type_input import (  # noqa: E402
    build_vehicle_model_selection,
    load_vehicle_type_result,
)
from aicar_sim.wash_profile import load_wash_profile  # noqa: E402
from aicar_sim.wash_strategy import build_wash_strategy_plan  # noqa: E402


FIXTURE_DIR = PROJECT_ROOT / "tests" / "fixtures"
VEHICLES_DIR = PROJECT_ROOT / "data" / "vehicles"
CASES = [
    ("sedan", "vehicle_type_result_sedan.json", "standard_sedan", False),
    ("suv", "vehicle_type_result_suv.json", "standard_suv", False),
    ("mpv", "vehicle_type_result_mpv.json", "standard_mpv", False),
    ("unknown", "vehicle_type_result_unknown.json", "standard_suv", True),
]


def _validate_plan(label: str, plan: dict, expected_profile: str) -> None:
    if plan.get("plan_version") != "stage2.1":
        raise AssertionError(f"{label}: wrong plan_version: {plan.get('plan_version')}")

    stages = plan.get("stages", [])
    if not stages:
        raise AssertionError(f"{label}: stages are empty")

    stage_count = plan.get("strategy_summary", {}).get("stage_count")
    if stage_count != len(stages):
        raise AssertionError(f"{label}: wrong stage_count: {stage_count}")

    expected_total = sum(int(stage["duration_seconds"]) for stage in stages)
    actual_total = plan.get("strategy_summary", {}).get("estimated_total_seconds")
    if actual_total != expected_total:
        raise AssertionError(
            f"{label}: expected total {expected_total}, got {actual_total}"
        )

    actual_profile = plan.get("profile", {}).get("wash_profile")
    if actual_profile != expected_profile:
        raise AssertionError(
            f"{label}: expected profile {expected_profile}, got {actual_profile}"
        )


def main() -> None:
    for label, fixture_name, expected_profile, expect_fallback in CASES:
        result = load_vehicle_type_result(str(FIXTURE_DIR / fixture_name))
        selection = build_vehicle_model_selection(result, str(VEHICLES_DIR))
        vehicle_model = selection["resolved_vehicle_model"]
        wash_profile = load_wash_profile(vehicle_model.get("wash_profile"))
        plan = build_wash_strategy_plan(result, vehicle_model, wash_profile)

        _validate_plan(label, plan, expected_profile)
        if selection["fallback_used"] != expect_fallback:
            raise AssertionError(
                f"{label}: expected vehicle fallback={expect_fallback}, got {selection['fallback_used']}"
            )
        if label == "unknown" and plan["vehicle"]["vehicle_type"] != "suv":
            raise AssertionError("unknown: expected fallback vehicle_type suv")

        suffix = " fallback" if expect_fallback else ""
        print(f"PASS {label} -> {expected_profile}{suffix}")

    print("AI car wash strategy plan check OK")


if __name__ == "__main__":
    main()
