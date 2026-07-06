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
from aicar_sim.wash_profile import load_wash_profile  # noqa: E402
from aicar_sim.wash_strategy import build_wash_strategy_plan  # noqa: E402


FIXTURE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "vehicle_type_result_sedan.json"
VEHICLES_DIR = PROJECT_ROOT / "data" / "vehicles"


def build_demo_space_model() -> dict:
    result = load_vehicle_type_result(str(FIXTURE_PATH))
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


def main() -> None:
    plan = build_nozzle_coverage_plan(
        build_demo_space_model(),
        load_nozzle_catalog(),
        load_nozzle_zone_mapping(),
    )

    if plan["plan_version"] != "stage2.3":
        raise AssertionError("wrong plan_version")
    if plan["coverage_summary"]["zone_count"] != 6:
        raise AssertionError("expected zone_count 6")
    if plan["coverage_summary"]["nozzle_count"] < 5:
        raise AssertionError("expected at least 5 nozzles")
    if plan["coverage_summary"]["estimated_coverage_percent"] <= 0:
        raise AssertionError("expected positive estimated coverage percent")

    limitations = " ".join(plan["limitations"]).lower()
    for keyword in ("no real nozzle path", "no animation", "no plc", "hardware"):
        if keyword not in limitations:
            raise AssertionError(f"limitations missing {keyword}")

    print("PASS nozzle coverage plan")
    print("AI car nozzle coverage plan check OK")


if __name__ == "__main__":
    main()
