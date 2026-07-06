import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aicar_sim.space_model import build_space_model_report  # noqa: E402
from aicar_sim.vehicle_envelope import build_vehicle_envelope  # noqa: E402
from aicar_sim.vehicle_type_input import (  # noqa: E402
    build_vehicle_model_selection,
    load_vehicle_type_result,
)
from aicar_sim.wash_bay import load_wash_bay  # noqa: E402
from aicar_sim.wash_profile import load_wash_profile  # noqa: E402
from aicar_sim.wash_strategy import build_wash_strategy_plan  # noqa: E402


DEFAULT_RESULT_PATH = (
    WORKSPACE_ROOT
    / "vehicle_type_lab"
    / "outputs"
    / "predictions"
    / "vehicle_type_result.json"
)
DEFAULT_STRATEGY_PATH = PROJECT_ROOT / "outputs" / "wash_strategy" / "wash_strategy_plan.json"
DEFAULT_WASH_BAY_PATH = PROJECT_ROOT / "data" / "wash_bays" / "demo_wash_bay.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "space_model" / "space_model_report.json"
VEHICLES_DIR = PROJECT_ROOT / "data" / "vehicles"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Stage2.2 space model report.")
    parser.add_argument(
        "--vehicle-type-result",
        default=str(DEFAULT_RESULT_PATH.relative_to(WORKSPACE_ROOT)),
        help="Path to vehicle_type_result.json.",
    )
    parser.add_argument(
        "--wash-strategy-plan",
        default=str(DEFAULT_STRATEGY_PATH.relative_to(WORKSPACE_ROOT)),
        help="Path to wash_strategy_plan.json.",
    )
    parser.add_argument(
        "--wash-bay",
        default=str(DEFAULT_WASH_BAY_PATH.relative_to(WORKSPACE_ROOT)),
        help="Path to wash bay JSON.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH.relative_to(WORKSPACE_ROOT)),
        help="Output path for space_model_report.json.",
    )
    return parser


def resolve_workspace_path(path_text: str) -> Path:
    path = Path(path_text)
    if not path.is_absolute():
        path = WORKSPACE_ROOT / path
    return path.resolve()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def build_components(vehicle_type_result_path: Path, wash_strategy_plan_path: Path) -> tuple:
    result = load_vehicle_type_result(str(vehicle_type_result_path))
    selection = build_vehicle_model_selection(result, str(VEHICLES_DIR))
    vehicle_model = selection["resolved_vehicle_model"]
    wash_profile = load_wash_profile(vehicle_model.get("wash_profile"))

    if wash_strategy_plan_path.exists():
        wash_strategy_plan = load_json(wash_strategy_plan_path)
    else:
        wash_strategy_plan = build_wash_strategy_plan(result, vehicle_model, wash_profile)
        write_json(wash_strategy_plan_path, wash_strategy_plan)

    vehicle_envelope = build_vehicle_envelope(vehicle_model, wash_profile)
    return result, vehicle_model, wash_profile, wash_strategy_plan, vehicle_envelope


def main() -> None:
    args = build_parser().parse_args()
    result_path = resolve_workspace_path(args.vehicle_type_result)
    strategy_path = resolve_workspace_path(args.wash_strategy_plan)
    wash_bay_path = resolve_workspace_path(args.wash_bay)
    output_path = resolve_workspace_path(args.output)

    if not result_path.exists():
        raise SystemExit(f"missing vehicle type result: {result_path}")

    result, vehicle_model, wash_profile, strategy_plan, vehicle_envelope = build_components(
        result_path,
        strategy_path,
    )
    wash_bay = load_wash_bay(str(wash_bay_path))
    report = build_space_model_report(
        result,
        vehicle_model,
        wash_profile,
        strategy_plan,
        vehicle_envelope,
        wash_bay,
    )
    write_json(output_path, report)

    print(f"vehicle_type: {report['vehicle']['vehicle_type']}")
    print(f"wash_profile: {report['wash_profile']}")
    print(f"bay_id: {report['wash_bay']['wash_bay_id']}")
    print(f"fits_in_bay: {report['clearance_check']['fits_in_bay']}")
    print(f"zone_count: {report['zone_summary']['zone_count']}")
    print(f"output path: {output_path}")


if __name__ == "__main__":
    main()
