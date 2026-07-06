import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aicar_sim.coverage_report import build_coverage_report  # noqa: E402
from aicar_sim.nozzle_coverage import build_nozzle_coverage_plan  # noqa: E402
from aicar_sim.nozzle_model import (  # noqa: E402
    load_nozzle_catalog,
    load_nozzle_zone_mapping,
)
from aicar_sim.path_plan import build_abstract_nozzle_path_plan  # noqa: E402
from aicar_sim.space_model import build_space_model_report  # noqa: E402
from aicar_sim.vehicle_envelope import build_vehicle_envelope  # noqa: E402
from aicar_sim.vehicle_type_input import (  # noqa: E402
    build_vehicle_model_selection,
    load_vehicle_type_result,
)
from aicar_sim.wash_bay import load_wash_bay  # noqa: E402
from aicar_sim.wash_flow import load_wash_flow_config  # noqa: E402
from aicar_sim.wash_profile import load_wash_profile  # noqa: E402
from aicar_sim.wash_state_machine import build_wash_flow_run  # noqa: E402
from aicar_sim.wash_strategy import build_wash_strategy_plan  # noqa: E402


FIXTURE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "vehicle_type_result_sedan.json"
VEHICLES_DIR = PROJECT_ROOT / "data" / "vehicles"
EXPECTED_ZONES = {"roof", "left_side", "right_side", "front", "rear", "wheels"}


def build_demo_coverage_report() -> dict:
    result = load_vehicle_type_result(str(FIXTURE_PATH))
    selection = build_vehicle_model_selection(result, str(VEHICLES_DIR))
    vehicle_model = selection["resolved_vehicle_model"]
    wash_profile = load_wash_profile(vehicle_model["wash_profile"])
    strategy_plan = build_wash_strategy_plan(result, vehicle_model, wash_profile)
    envelope = build_vehicle_envelope(vehicle_model, wash_profile)
    space_model = build_space_model_report(
        result,
        vehicle_model,
        wash_profile,
        strategy_plan,
        envelope,
        load_wash_bay("demo_wash_bay"),
    )
    nozzle_plan = build_nozzle_coverage_plan(
        space_model,
        load_nozzle_catalog(),
        load_nozzle_zone_mapping(),
    )
    flow_run = build_wash_flow_run(
        load_wash_flow_config(),
        strategy_plan,
        space_model,
        nozzle_plan,
    )
    path_plan = build_abstract_nozzle_path_plan(flow_run, space_model, nozzle_plan)
    return build_coverage_report(path_plan, nozzle_plan, space_model)


def main() -> None:
    report = build_demo_coverage_report()
    summary = report["coverage_summary"]
    zone_ids = {zone_report["zone_id"] for zone_report in report["zone_reports"]}

    if report["report_version"] != "stage2.6":
        raise AssertionError("wrong report_version")
    if summary["zone_count"] != 6:
        raise AssertionError("expected 6 zones")
    if summary["covered_zone_count"] != 6:
        raise AssertionError("expected 6 covered zones")
    if summary["uncovered_zone_count"] != 0:
        raise AssertionError("expected 0 uncovered zones")
    if summary["estimated_actual_coverage_percent"] <= 0:
        raise AssertionError("estimated coverage must be positive")
    if summary["coverage_pass"] is not True:
        raise AssertionError("coverage_pass must be true")
    if zone_ids != EXPECTED_ZONES:
        raise AssertionError(f"unexpected zones: {sorted(zone_ids)}")

    for zone_report in report["zone_reports"]:
        for field in (
            "segment_count",
            "point_count",
            "target_coverage_percent",
            "estimated_coverage_percent",
        ):
            if field not in zone_report:
                raise AssertionError(f"zone report missing field: {field}")

    limitations = " ".join(report["limitations"]).lower()
    for keyword in ("no real water flow", "no plc", "hardware control"):
        if keyword not in limitations:
            raise AssertionError(f"limitations missing {keyword}")

    print("PASS coverage report")
    print("AI car coverage report check OK")


if __name__ == "__main__":
    main()
