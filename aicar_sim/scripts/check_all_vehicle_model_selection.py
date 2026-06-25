import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aicar_sim.vehicle_type_input import (  # noqa: E402
    build_vehicle_model_selection,
    load_vehicle_type_result,
)


FIXTURE_DIR = PROJECT_ROOT / "tests" / "fixtures"
VEHICLES_DIR = PROJECT_ROOT / "data" / "vehicles"
CASES = [
    ("sedan", "vehicle_type_result_sedan.json", "sedan.json", False),
    ("suv", "vehicle_type_result_suv.json", "suv.json", False),
    ("mpv", "vehicle_type_result_mpv.json", "mpv.json", False),
    ("unknown", "vehicle_type_result_unknown.json", "suv.json", True),
]


def main() -> None:
    for label, fixture_name, expected_model_name, expect_fallback in CASES:
        fixture_path = FIXTURE_DIR / fixture_name
        if not fixture_path.exists():
            raise SystemExit(f"missing fixture: {fixture_path}")

        result = load_vehicle_type_result(str(fixture_path))
        selection = build_vehicle_model_selection(result, str(VEHICLES_DIR))
        model_path = Path(selection["resolved_vehicle_model_path"])
        if model_path.name != expected_model_name:
            raise AssertionError(
                f"{label}: expected {expected_model_name}, got {model_path.name}"
            )
        if selection["fallback_used"] != expect_fallback:
            raise AssertionError(
                f"{label}: expected fallback={expect_fallback}, got {selection['fallback_used']}"
            )
        if not model_path.exists():
            raise AssertionError(f"{label}: resolved model missing: {model_path}")

        suffix = " fallback" if expect_fallback else ""
        print(f"PASS {label} -> {model_path.name}{suffix}")


if __name__ == "__main__":
    main()
