import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aicar_sim.vehicle_type_input import (
    load_vehicle_type_result,
    resolve_vehicle_model_path,
)


def main() -> None:
    result_path = (
        WORKSPACE_ROOT
        / "vehicle_type_lab"
        / "outputs"
        / "predictions"
        / "vehicle_type_result.json"
    )
    if not result_path.exists():
        raise SystemExit(f"missing vehicle type result: {result_path}")

    result = load_vehicle_type_result(str(result_path))
    model_path = resolve_vehicle_model_path(result, str(PROJECT_ROOT / "data" / "vehicles"))

    if not Path(model_path).exists():
        raise SystemExit(f"resolved vehicle model does not exist: {model_path}")

    print("aicar_sim vehicle type input check OK")
    print(f"vehicle_type: {result.get('vehicle_type', 'unknown')}")
    print(f"resolved vehicle model: {model_path}")


if __name__ == "__main__":
    main()

