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
from aicar_sim.wash_flow import load_wash_flow_config  # noqa: E402
from aicar_sim.wash_profile import load_wash_profile  # noqa: E402
from aicar_sim.wash_state_machine import build_wash_flow_run  # noqa: E402
from aicar_sim.wash_strategy import build_wash_strategy_plan  # noqa: E402


DEFAULT_RESULT_PATH = (
    WORKSPACE_ROOT
    / "vehicle_type_lab"
    / "outputs"
    / "predictions"
    / "vehicle_type_result.json"
)
DEFAULT_STRATEGY_PATH = PROJECT_ROOT / "outputs" / "wash_strategy" / "wash_strategy_plan.json"
DEFAULT_SPACE_MODEL_PATH = PROJECT_ROOT / "outputs" / "space_model" / "space_model_report.json"
DEFAULT_NOZZLE_PLAN_PATH = PROJECT_ROOT / "outputs" / "nozzle_plan" / "nozzle_coverage_plan.json"
DEFAULT_FLOW_CONFIG_PATH = PROJECT_ROOT / "data" / "wash_flows" / "demo_wash_flow.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "wash_flow" / "wash_flow_run.json"
VEHICLES_DIR = PROJECT_ROOT / "data" / "vehicles"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Stage2.4 wash flow run.")
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
        "--space-model-report",
        default=str(DEFAULT_SPACE_MODEL_PATH.relative_to(WORKSPACE_ROOT)),
        help="Path to space_model_report.json.",
    )
    parser.add_argument(
        "--nozzle-coverage-plan",
        default=str(DEFAULT_NOZZLE_PLAN_PATH.relative_to(WORKSPACE_ROOT)),
        help="Path to nozzle_coverage_plan.json.",
    )
    parser.add_argument(
        "--flow-config",
        default=str(DEFAULT_FLOW_CONFIG_PATH.relative_to(WORKSPACE_ROOT)),
        help="Path to wash flow config JSON.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH.relative_to(WORKSPACE_ROOT)),
        help="Output path for wash_flow_run.json.",
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


def build_base_components(vehicle_type_result_path: Path) -> tuple[dict, dict, dict]:
    result = load_vehicle_type_result(str(vehicle_type_result_path))
    selection = build_vehicle_model_selection(result, str(VEHICLES_DIR))
    vehicle_model = selection["resolved_vehicle_model"]
    wash_profile = load_wash_profile(vehicle_model["wash_profile"])
    return result, vehicle_model, wash_profile


def ensure_wash_strategy_plan(path: Path, result: dict, vehicle_model: dict, wash_profile: dict) -> dict:
    if path.exists():
        return load_json(path)
    plan = build_wash_strategy_plan(result, vehicle_model, wash_profile)
    write_json(path, plan)
    return plan


def ensure_space_model_report(
    path: Path,
    result: dict,
    vehicle_model: dict,
    wash_profile: dict,
    wash_strategy_plan: dict,
) -> dict:
    if path.exists():
        return load_json(path)
    envelope = build_vehicle_envelope(vehicle_model, wash_profile)
    wash_bay = load_wash_bay("demo_wash_bay")
    report = build_space_model_report(
        result,
        vehicle_model,
        wash_profile,
        wash_strategy_plan,
        envelope,
        wash_bay,
    )
    write_json(path, report)
    return report


def ensure_nozzle_coverage_plan(path: Path, space_model_report: dict) -> dict:
    if path.exists():
        return load_json(path)
    plan = build_nozzle_coverage_plan(
        space_model_report,
        load_nozzle_catalog(),
        load_nozzle_zone_mapping(),
    )
    write_json(path, plan)
    return plan


def main() -> None:
    args = build_parser().parse_args()
    result_path = resolve_workspace_path(args.vehicle_type_result)
    strategy_path = resolve_workspace_path(args.wash_strategy_plan)
    space_model_path = resolve_workspace_path(args.space_model_report)
    nozzle_plan_path = resolve_workspace_path(args.nozzle_coverage_plan)
    flow_config_path = resolve_workspace_path(args.flow_config)
    output_path = resolve_workspace_path(args.output)

    if not result_path.exists():
        raise SystemExit(f"missing vehicle type result: {result_path}")

    result, vehicle_model, wash_profile = build_base_components(result_path)
    strategy_plan = ensure_wash_strategy_plan(
        strategy_path,
        result,
        vehicle_model,
        wash_profile,
    )
    space_model_report = ensure_space_model_report(
        space_model_path,
        result,
        vehicle_model,
        wash_profile,
        strategy_plan,
    )
    nozzle_coverage_plan = ensure_nozzle_coverage_plan(
        nozzle_plan_path,
        space_model_report,
    )
    flow_config = load_wash_flow_config(flow_config_path)
    flow_run = build_wash_flow_run(
        flow_config,
        strategy_plan,
        space_model_report,
        nozzle_coverage_plan,
    )
    write_json(output_path, flow_run)

    print(f"vehicle_type: {flow_run['vehicle']['vehicle_type']}")
    print(f"wash_profile: {flow_run['wash_profile']}")
    print(f"flow_id: {flow_run['flow_id']}")
    print(f"state_count: {flow_run['summary']['state_count']}")
    print(f"wash_state_count: {flow_run['summary']['wash_state_count']}")
    print(f"estimated_total_seconds: {flow_run['summary']['estimated_total_seconds']}")
    print(f"output path: {output_path}")


if __name__ == "__main__":
    main()
