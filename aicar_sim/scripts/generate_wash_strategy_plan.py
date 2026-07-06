import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aicar_sim.vehicle_type_input import (  # noqa: E402
    build_vehicle_model_selection,
    load_vehicle_type_result,
)
from aicar_sim.wash_profile import load_wash_profile  # noqa: E402
from aicar_sim.wash_strategy import build_wash_strategy_plan  # noqa: E402


DEFAULT_RESULT_PATH = (
    WORKSPACE_ROOT
    / "vehicle_type_lab"
    / "outputs"
    / "predictions"
    / "vehicle_type_result.json"
)
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "wash_strategy" / "wash_strategy_plan.json"
VEHICLES_DIR = PROJECT_ROOT / "data" / "vehicles"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Stage2.1 wash strategy plan.")
    parser.add_argument(
        "--vehicle-type-result",
        default=str(DEFAULT_RESULT_PATH.relative_to(WORKSPACE_ROOT)),
        help="Path to vehicle_type_result.json.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH.relative_to(WORKSPACE_ROOT)),
        help="Output path for wash_strategy_plan.json.",
    )
    return parser


def resolve_workspace_path(path_text: str) -> Path:
    path = Path(path_text)
    if not path.is_absolute():
        path = WORKSPACE_ROOT / path
    return path.resolve()


def generate_plan(vehicle_type_result_path: Path) -> tuple[dict, dict]:
    result = load_vehicle_type_result(str(vehicle_type_result_path))
    selection = build_vehicle_model_selection(result, str(VEHICLES_DIR))
    vehicle_model = selection["resolved_vehicle_model"]
    profile = load_wash_profile(vehicle_model.get("wash_profile"))
    plan = build_wash_strategy_plan(result, vehicle_model, profile)
    return plan, selection


def main() -> None:
    args = build_parser().parse_args()
    result_path = resolve_workspace_path(args.vehicle_type_result)
    output_path = resolve_workspace_path(args.output)

    if not result_path.exists():
        raise SystemExit(f"missing vehicle type result: {result_path}")

    plan, selection = generate_plan(result_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(plan, file, ensure_ascii=False, indent=2)
        file.write("\n")

    print(f"vehicle_type: {selection['vehicle_type']}")
    print(f"resolved vehicle model: {selection['resolved_vehicle_model_path']}")
    print(f"wash_profile: {plan['profile']['wash_profile']}")
    print(f"estimated_total_seconds: {plan['strategy_summary']['estimated_total_seconds']}")
    print(f"stage_count: {plan['strategy_summary']['stage_count']}")
    print(f"output path: {output_path}")


if __name__ == "__main__":
    main()
