import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aicar_sim.space_model import build_space_model_report  # noqa: E402
from aicar_sim.vehicle_envelope import build_vehicle_envelope  # noqa: E402
from aicar_sim.vehicle_type_input import (  # noqa: E402
    build_vehicle_model_selection,
    load_vehicle_type_result,
)
from aicar_sim.wash_bay import load_wash_bay  # noqa: E402
from aicar_sim.wash_profile import load_wash_profile  # noqa: E402
from aicar_sim.wash_strategy import build_wash_strategy_plan  # noqa: E402


FIXTURE_DIR = PROJECT_ROOT / "tests" / "fixtures"
VEHICLES_DIR = PROJECT_ROOT / "data" / "vehicles"
CASES = [
    ("sedan", "vehicle_type_result_sedan.json", "sedan"),
    ("suv", "vehicle_type_result_suv.json", "suv"),
    ("mpv", "vehicle_type_result_mpv.json", "mpv"),
    ("unknown", "vehicle_type_result_unknown.json", "suv"),
]


def _build_report(fixture_name: str) -> dict:
    result = load_vehicle_type_result(str(FIXTURE_DIR / fixture_name))
    selection = build_vehicle_model_selection(result, str(VEHICLES_DIR))
    vehicle_model = selection["resolved_vehicle_model"]
    wash_profile = load_wash_profile(vehicle_model["wash_profile"])
    strategy_plan = build_wash_strategy_plan(result, vehicle_model, wash_profile)
    envelope = build_vehicle_envelope(vehicle_model, wash_profile)
    wash_bay = load_wash_bay("demo_wash_bay")
    return build_space_model_report(
        result,
        vehicle_model,
        wash_profile,
        strategy_plan,
        envelope,
        wash_bay,
    )


def _validate_report(label: str, report: dict, expected_vehicle_type: str) -> None:
    if report["report_version"] != "stage2.2":
        raise AssertionError(f"{label}: wrong report_version")
    if report["vehicle"]["vehicle_type"] != expected_vehicle_type:
        raise AssertionError(
            f"{label}: expected vehicle_type {expected_vehicle_type}, got {report['vehicle']['vehicle_type']}"
        )
    if not report["clearance_check"]["fits_in_bay"]:
        raise AssertionError(f"{label}: expected fits_in_bay true")
    if report["zone_summary"]["zone_count"] != 6:
        raise AssertionError(f"{label}: expected 6 zones")

    limitations = " ".join(report["limitations"]).lower()
    for keyword in ("no nozzle path", "no animation", "no plc", "hardware"):
        if keyword not in limitations:
            raise AssertionError(f"{label}: limitations missing {keyword}")


def main() -> None:
    for label, fixture_name, expected_vehicle_type in CASES:
        report = _build_report(fixture_name)
        _validate_report(label, report, expected_vehicle_type)
        suffix = " fallback" if label == "unknown" else ""
        print(f"PASS {label}{suffix} space model")

    print("AI car space model check OK")


if __name__ == "__main__":
    main()
