import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aicar_sim.vehicle_type_input import (  # noqa: E402
    build_vehicle_model_selection,
    load_vehicle_type_result,
)
from aicar_sim.wash_flow import (  # noqa: E402
    get_linear_flow_sequence,
    load_wash_flow_config,
    validate_wash_flow_config,
)
from aicar_sim.wash_profile import load_wash_profile  # noqa: E402
from aicar_sim.wash_strategy import build_wash_strategy_plan  # noqa: E402


FIXTURE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "vehicle_type_result_sedan.json"
VEHICLES_DIR = PROJECT_ROOT / "data" / "vehicles"


def build_demo_strategy_plan() -> dict:
    result = load_vehicle_type_result(str(FIXTURE_PATH))
    selection = build_vehicle_model_selection(result, str(VEHICLES_DIR))
    vehicle_model = selection["resolved_vehicle_model"]
    wash_profile = load_wash_profile(vehicle_model["wash_profile"])
    return build_wash_strategy_plan(result, vehicle_model, wash_profile)


def main() -> None:
    config = load_wash_flow_config()
    strategy_plan = build_demo_strategy_plan()
    validate_wash_flow_config(config, strategy_plan)

    if config["initial_state"] != "idle":
        raise AssertionError("expected initial_state idle")
    for terminal in ("completed", "aborted", "error"):
        if terminal not in config["terminal_states"]:
            raise AssertionError(f"missing terminal state: {terminal}")

    sequence = get_linear_flow_sequence(config)
    if sequence[-1]["state_id"] != "completed":
        raise AssertionError("main flow does not reach completed")

    print("PASS demo_wash_flow config")
    print("AI car wash flow config check OK")


if __name__ == "__main__":
    main()
