import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

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
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "path_plan" / "abstract_nozzle_path_plan.json"


def build_demo_path_plan() -> tuple[dict, dict]:
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
    return path_plan, flow_run


def main() -> None:
    path_plan, flow_run = build_demo_path_plan()
    segments = path_plan["path_segments"]
    point_count = sum(len(segment["points"]) for segment in segments)

    if path_plan["plan_version"] != "stage2.5":
        raise AssertionError("wrong plan_version")
    if not segments:
        raise AssertionError("path_segments must not be empty")
    if path_plan["summary"]["segment_count"] != len(segments):
        raise AssertionError("segment_count mismatch")
    if path_plan["summary"]["point_count"] != point_count:
        raise AssertionError("point_count mismatch")
    if (
        path_plan["summary"]["estimated_total_seconds"]
        != flow_run["summary"]["estimated_total_seconds"]
    ):
        raise AssertionError("estimated_total_seconds mismatch")

    limitations = " ".join(path_plan["limitations"]).lower()
    for keyword in ("no real actuator trajectory", "no plc", "hardware control"):
        if keyword not in limitations:
            raise AssertionError(f"limitations missing {keyword}")

    gitignore_text = (WORKSPACE_ROOT / ".gitignore").read_text(encoding="utf-8")
    if "aicar_sim/outputs/path_plan/*.json" not in gitignore_text:
        raise AssertionError("path plan JSON output is not ignored")

    print("PASS abstract nozzle path plan")
    print("AI car path plan check OK")


if __name__ == "__main__":
    main()
