import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aicar_sim.coverage_report import build_coverage_report  # noqa: E402
from aicar_sim.nozzle_coverage import build_nozzle_coverage_plan  # noqa: E402
from aicar_sim.nozzle_model import (  # noqa: E402
    load_nozzle_catalog,
    load_nozzle_zone_mapping,
)
from aicar_sim.path_plan import build_abstract_nozzle_path_plan  # noqa: E402
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
DEFAULT_FLOW_RUN_PATH = PROJECT_ROOT / "outputs" / "wash_flow" / "wash_flow_run.json"
DEFAULT_PATH_PLAN_PATH = PROJECT_ROOT / "outputs" / "path_plan" / "abstract_nozzle_path_plan.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "coverage_report" / "coverage_report.json"
VEHICLES_DIR = PROJECT_ROOT / "data" / "vehicles"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Stage2.6 coverage report.")
    parser.add_argument(
        "--vehicle-type-result",
        default=str(DEFAULT_RESULT_PATH.relative_to(WORKSPACE_ROOT)),
        help="Path to vehicle_type_result.json.",
    )
    parser.add_argument(
        "--path-plan",
        default=str(DEFAULT_PATH_PLAN_PATH.relative_to(WORKSPACE_ROOT)),
        help="Path to abstract_nozzle_path_plan.json.",
    )
    parser.add_argument(
        "--nozzle-coverage-plan",
        default=str(DEFAULT_NOZZLE_PLAN_PATH.relative_to(WORKSPACE_ROOT)),
        help="Path to nozzle_coverage_plan.json.",
    )
    parser.add_argument(
        "--space-model-report",
        default=str(DEFAULT_SPACE_MODEL_PATH.relative_to(WORKSPACE_ROOT)),
        help="Path to space_model_report.json.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH.relative_to(WORKSPACE_ROOT)),
        help="Output path for coverage_report.json.",
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


def ensure_strategy(path: Path, result: dict, vehicle_model: dict, wash_profile: dict) -> dict:
    if path.exists():
        return load_json(path)
    plan = build_wash_strategy_plan(result, vehicle_model, wash_profile)
    write_json(path, plan)
    return plan


def ensure_space_model(
    path: Path,
    result: dict,
    vehicle_model: dict,
    wash_profile: dict,
    strategy_plan: dict,
) -> dict:
    if path.exists():
        return load_json(path)
    envelope = build_vehicle_envelope(vehicle_model, wash_profile)
    report = build_space_model_report(
        result,
        vehicle_model,
        wash_profile,
        strategy_plan,
        envelope,
        load_wash_bay("demo_wash_bay"),
    )
    write_json(path, report)
    return report


def ensure_nozzle_plan(path: Path, space_model_report: dict) -> dict:
    if path.exists():
        return load_json(path)
    plan = build_nozzle_coverage_plan(
        space_model_report,
        load_nozzle_catalog(),
        load_nozzle_zone_mapping(),
    )
    write_json(path, plan)
    return plan


def ensure_flow_run(
    path: Path,
    strategy_plan: dict,
    space_model_report: dict,
    nozzle_coverage_plan: dict,
) -> dict:
    if path.exists():
        return load_json(path)
    flow_run = build_wash_flow_run(
        load_wash_flow_config(),
        strategy_plan,
        space_model_report,
        nozzle_coverage_plan,
    )
    write_json(path, flow_run)
    return flow_run


def ensure_path_plan(
    path: Path,
    flow_run: dict,
    space_model_report: dict,
    nozzle_coverage_plan: dict,
) -> dict:
    if path.exists():
        return load_json(path)
    path_plan = build_abstract_nozzle_path_plan(
        flow_run,
        space_model_report,
        nozzle_coverage_plan,
    )
    write_json(path, path_plan)
    return path_plan


def main() -> None:
    args = build_parser().parse_args()
    result_path = resolve_workspace_path(args.vehicle_type_result)
    path_plan_path = resolve_workspace_path(args.path_plan)
    nozzle_plan_path = resolve_workspace_path(args.nozzle_coverage_plan)
    space_model_path = resolve_workspace_path(args.space_model_report)
    output_path = resolve_workspace_path(args.output)

    if not result_path.exists():
        raise SystemExit(f"missing vehicle type result: {result_path}")

    result, vehicle_model, wash_profile = build_base_components(result_path)
    strategy_plan = ensure_strategy(
        DEFAULT_STRATEGY_PATH,
        result,
        vehicle_model,
        wash_profile,
    )
    space_model_report = ensure_space_model(
        space_model_path,
        result,
        vehicle_model,
        wash_profile,
        strategy_plan,
    )
    nozzle_coverage_plan = ensure_nozzle_plan(nozzle_plan_path, space_model_report)
    flow_run = ensure_flow_run(
        DEFAULT_FLOW_RUN_PATH,
        strategy_plan,
        space_model_report,
        nozzle_coverage_plan,
    )
    path_plan = ensure_path_plan(
        path_plan_path,
        flow_run,
        space_model_report,
        nozzle_coverage_plan,
    )
    report = build_coverage_report(path_plan, nozzle_coverage_plan, space_model_report)
    write_json(output_path, report)

    summary = report["coverage_summary"]
    print(f"vehicle_type: {report['vehicle']['vehicle_type']}")
    print(f"wash_profile: {report['wash_profile']}")
    print(f"zone_count: {summary['zone_count']}")
    print(f"covered_zone_count: {summary['covered_zone_count']}")
    print(
        f"estimated_actual_coverage_percent: "
        f"{summary['estimated_actual_coverage_percent']}"
    )
    print(f"coverage_pass: {summary['coverage_pass']}")
    print(f"output path: {output_path}")


if __name__ == "__main__":
    main()
