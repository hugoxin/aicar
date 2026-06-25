import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aicar_sim.vehicle_type_input import (  # noqa: E402
    ALLOWED_VEHICLE_TYPES,
    build_vehicle_model_selection,
    load_vehicle_type_result,
)


RESULT_PATH = (
    WORKSPACE_ROOT
    / "vehicle_type_lab"
    / "outputs"
    / "predictions"
    / "vehicle_type_result.json"
)
VEHICLES_DIR = PROJECT_ROOT / "data" / "vehicles"


def main() -> None:
    if not RESULT_PATH.exists():
        raise SystemExit(f"missing vehicle type result: {RESULT_PATH}")

    result = load_vehicle_type_result(str(RESULT_PATH))
    vehicle_type = str(result.get("vehicle_type", "unknown")).lower()
    if vehicle_type not in ALLOWED_VEHICLE_TYPES:
        raise AssertionError(f"unsupported vehicle_type: {vehicle_type}")

    selection = build_vehicle_model_selection(result, str(VEHICLES_DIR))
    model_path = Path(selection["resolved_vehicle_model_path"])
    if not model_path.exists():
        raise AssertionError(f"resolved vehicle model does not exist: {model_path}")

    model = selection["resolved_vehicle_model"]
    required_model_fields = {
        "vehicle_type",
        "length_mm",
        "width_mm",
        "height_mm",
        "wash_profile",
    }
    missing = sorted(required_model_fields - set(model))
    if missing:
        raise AssertionError(f"vehicle model missing fields: {missing}")

    expected_name = "suv.json" if vehicle_type == "unknown" else f"{vehicle_type}.json"
    if model_path.name != expected_name:
        raise AssertionError(
            f"expected {expected_name} for vehicle_type={vehicle_type}, got {model_path.name}"
        )

    print("aicar_sim vehicle model selection check OK")
    print(f"vehicle_detected: {selection['vehicle_detected']}")
    print(f"vehicle_type: {selection['vehicle_type']}")
    print(f"pipeline_mode: {selection['pipeline_mode']}")
    print(f"resolved vehicle model: {selection['resolved_vehicle_model_path']}")
    print(f"wash_profile: {model.get('wash_profile')}")
    print("vehicle dimensions:")
    print(f"length_mm: {model.get('length_mm')}")
    print(f"width_mm: {model.get('width_mm')}")
    print(f"height_mm: {model.get('height_mm')}")


if __name__ == "__main__":
    main()
