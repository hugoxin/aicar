import argparse
import json
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
from aicar_sim.space_model import build_space_model_report  # noqa: E402
from aicar_sim.vehicle_envelope import build_vehicle_envelope  # noqa: E402
from aicar_sim.vehicle_type_input import (  # noqa: E402
    build_vehicle_model_selection,
    load_vehicle_type_result,
)
from aicar_sim.wash_bay import load_wash_bay  # noqa: E402
from aicar_sim.wash_profile import load_wash_profile  # noqa: E402
from aicar_sim.wash_strategy import build_wash_strategy_plan  # noqa: E402


DEFAULT_SPACE_MODEL_PATH = PROJECT_ROOT / "outputs" / "space_model" / "space_model_report.json"
DEFAULT_RESULT_PATH = (
    WORKSPACE_ROOT
    / "vehicle_type_lab"
    / "outputs"
    / "predictions"
    / "vehicle_type_result.json"
)
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "nozzle_plan" / "nozzle_coverage_plan.json"
VEHICLES_DIR = PROJECT_ROOT / "data" / "vehicles"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Stage2.3 nozzle coverage plan.")
    parser.add_argument(
        "--space-model-report",
        default=str(DEFAULT_SPACE_MODEL_PATH.relative_to(WORKSPACE_ROOT)),
        help="Path to space_model_report.json.",
    )
    parser.add_argument(
        "--vehicle-type-result",
        default=str(DEFAULT_RESULT_PATH.relative_to(WORKSPACE_ROOT)),
        help="Path to vehicle_type_result.json used if the space model must be generated.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH.relative_to(WORKSPACE_ROOT)),
        help="Output path for nozzle_coverage_plan.json.",
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


def build_space_model_from_result(vehicle_type_result_path: Path) -> dict:
    result = load_vehicle_type_result(str(vehicle_type_result_path))
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
    args = build_parser().parse_args()
    space_model_path = resolve_workspace_path(args.space_model_report)
    vehicle_type_result_path = resolve_workspace_path(args.vehicle_type_result)
    output_path = resolve_workspace_path(args.output)

    if space_model_path.exists():
        space_model_report = load_json(space_model_path)
    else:
        if not vehicle_type_result_path.exists():
            raise SystemExit(f"missing vehicle type result: {vehicle_type_result_path}")
        space_model_report = build_space_model_from_result(vehicle_type_result_path)
        write_json(space_model_path, space_model_report)

    catalog = load_nozzle_catalog()
    mapping = load_nozzle_zone_mapping()
    plan = build_nozzle_coverage_plan(space_model_report, catalog, mapping)
    write_json(output_path, plan)

    print(f"vehicle_type: {plan['vehicle']['vehicle_type']}")
    print(f"wash_profile: {plan['wash_profile']}")
    print(f"wash_bay_id: {plan['wash_bay_id']}")
    print(f"zone_count: {plan['coverage_summary']['zone_count']}")
    print(f"nozzle_count: {plan['coverage_summary']['nozzle_count']}")
    print(
        f"estimated_coverage_percent: {plan['coverage_summary']['estimated_coverage_percent']}"
    )
    print(f"output path: {output_path}")


if __name__ == "__main__":
    main()
