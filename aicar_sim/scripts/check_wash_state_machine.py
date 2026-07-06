import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aicar_sim.wash_flow import get_linear_flow_sequence, load_wash_flow_config  # noqa: E402


EXPECTED_SEQUENCE = [
    "idle",
    "load_vehicle_context",
    "pre_rinse",
    "foam",
    "dwell",
    "top_clean",
    "side_clean",
    "wheel_clean",
    "air_dry",
    "completed",
]


def main() -> None:
    config = load_wash_flow_config()
    sequence = [state["state_id"] for state in get_linear_flow_sequence(config)]
    if sequence != EXPECTED_SEQUENCE:
        raise AssertionError(f"unexpected sequence: {sequence}")
    if "aborted" in sequence or "error" in sequence:
        raise AssertionError("main sequence should not enter aborted/error")

    print("PASS wash state machine sequence")
    print("AI car wash state machine check OK")


if __name__ == "__main__":
    main()
