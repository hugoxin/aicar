import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aicar_sim.nozzle_coverage import build_nozzle_coverage_plan  # noqa: E402
from aicar_sim.nozzle_model import (  # noqa: E402
    load_nozzle_catalog,
    load_nozzle_zone_mapping,
)
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


def build_demo_run() -> tuple[dict, dict]:
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
    return flow_run, strategy_plan


def main() -> None:
    flow_run, strategy_plan = build_demo_run()
    timeline = flow_run["timeline"]

    if flow_run["run_version"] != "stage2.4":
        raise AssertionError("wrong run_version")
    if flow_run["flow_id"] != "demo_wash_flow":
        raise AssertionError("wrong flow_id")
    if not timeline:
        raise AssertionError("timeline is empty")
    if timeline[-1]["state_id"] != "completed":
        raise AssertionError("last mainline state must be completed")
    if flow_run["summary"]["state_count"] != 12:
        raise AssertionError("expected 12 configured states")
    if flow_run["summary"]["timeline_state_count"] != 10:
        raise AssertionError("expected 10 mainline timeline states")
    if flow_run["summary"]["wash_state_count"] != 7:
        raise AssertionError("expected 7 wash states")

    expected_total = strategy_plan["strategy_summary"]["estimated_total_seconds"]
    if flow_run["summary"]["estimated_total_seconds"] != expected_total:
        raise AssertionError(
            f"expected total {expected_total}, got {flow_run['summary']['estimated_total_seconds']}"
        )

    for previous, current in zip(timeline, timeline[1:]):
        if previous["end_time_s"] != current["start_time_s"]:
            raise AssertionError(
                f"timeline is not continuous between {previous['state_id']} and {current['state_id']}"
            )

    limitations = " ".join(flow_run["limitations"]).lower()
    for keyword in ("no real nozzle path", "no animation", "no plc", "hardware"):
        if keyword not in limitations:
            raise AssertionError(f"limitations missing {keyword}")

    print("PASS wash flow run")
    print("AI car wash flow run check OK")


if __name__ == "__main__":
    main()
