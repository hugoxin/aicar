import argparse
from pathlib import Path

try:
    from aicar_sim.vehicle_type_input import (
        build_vehicle_model_selection,
        load_vehicle_type_result,
    )
except ModuleNotFoundError:
    from vehicle_type_input import build_vehicle_model_selection, load_vehicle_type_result


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VEHICLES_DIR = PROJECT_ROOT / "data" / "vehicles"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="aicar_sim scaffold entrypoint")
    parser.add_argument(
        "--vehicle-type-result",
        help="Path to vehicle_type_lab output JSON.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.vehicle_type_result:
        result = load_vehicle_type_result(args.vehicle_type_result)
        selection = build_vehicle_model_selection(result, str(VEHICLES_DIR))
        vehicle_model = selection["resolved_vehicle_model"]

        print("Loaded vehicle type result")
        print(f"vehicle_detected: {str(selection['vehicle_detected']).lower()}")
        print(f"vehicle_type: {selection['vehicle_type']}")
        print(f"pipeline_mode: {selection['pipeline_mode']}")
        print(f"detection_confidence: {selection['detection_confidence']}")
        print(f"classification_confidence: {selection['classification_confidence']}")
        print(f"bbox: {selection['bbox']}")
        print(f"resolved vehicle model: {selection['resolved_vehicle_model_path']}")
        print("vehicle dimensions:")
        print(f"length_mm: {vehicle_model.get('length_mm')}")
        print(f"width_mm: {vehicle_model.get('width_mm')}")
        print(f"height_mm: {vehicle_model.get('height_mm')}")
        print(f"wash_profile: {vehicle_model.get('wash_profile')}")
        return

    print("aicar_sim scaffold")
    print("Current phase: workspace and simulation framework only.")
    print("No model training, no dataset download, no real hardware connection.")


if __name__ == "__main__":
    main()
