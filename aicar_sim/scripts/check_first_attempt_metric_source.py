import ast
import inspect
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.continuous_surface_repair_report import (  # noqa: E402
    _first_attempt_metrics,
    extract_first_attempt_clearance_metrics,
)

VALIDATION_OUTPUT = (
    PROJECT_ROOT
    / "outputs/continuous_surface_validation/continuous_collision_safety_validation_report.json"
)
VALIDATION_SOURCE = str(VALIDATION_OUTPUT.relative_to(WORKSPACE_ROOT)).replace("\\", "/")


def check_real_metric_source() -> None:
    if not VALIDATION_OUTPUT.exists():
        raise SystemExit(f"first-attempt validation report is missing: {VALIDATION_OUTPUT}")
    validation = json.loads(VALIDATION_OUTPUT.read_text(encoding="utf-8"))
    minimum_clearance, warning_count = extract_first_attempt_clearance_metrics(
        validation, VALIDATION_SOURCE
    )
    if minimum_clearance != 300.0 or warning_count != 45:
        raise SystemExit(
            "unexpected first-attempt clearance metrics: "
            f"minimum_clearance_mm={minimum_clearance}, clearance_warning_count={warning_count}"
        )

    metrics = _first_attempt_metrics(
        {"summary": {"scan_pass_count": 1, "path_length_mm": 1.0}, "surface_tasks": []},
        {
            "summary": {
                "trajectory_point_count": 1,
                "transition_segment_count": 0,
                "path_length_mm": 1.0,
                "estimated_motion_duration_s": 1.0,
            }
        },
        {
            "summary": {
                "task_count": 1,
                "total_schedule_duration_s": 1.0,
                "total_delay_s": 0.0,
                "parallel_group_count": 0,
                "synchronized_group_count": 0,
                "conflict_count_before_resolution": 0,
                "conflict_count_after_resolution": 0,
                "unresolved_conflict_count": 0,
            },
            "sync_groups": [],
            "resource_locks": [],
        },
        {"path_length_breakdown": {}},
        validation,
        VALIDATION_SOURCE,
    )
    if metrics.get("clearance_metric_source") != VALIDATION_SOURCE:
        raise SystemExit("first-attempt metrics did not record clearance_metric_source")


def check_missing_data_errors() -> None:
    for payload, expected in (
        ({}, "no summary object"),
        ({"summary": {"clearance_warning_count": 45}}, "minimum_clearance_mm"),
        ({"summary": {"minimum_clearance_mm": 300.0}}, "clearance_warning_count"),
    ):
        try:
            extract_first_attempt_clearance_metrics(payload, "synthetic-validation.json")
        except ValueError as error:
            if expected not in str(error):
                raise SystemExit(f"missing metric data raised an unclear error: {error}")
        else:
            raise SystemExit(f"missing metric data was accepted: {payload}")


def check_no_numeric_fallback() -> None:
    source = inspect.getsource(extract_first_attempt_clearance_metrics)
    constants = {
        node.value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float))
    }
    forbidden = constants & {45, 300, 300.0}
    if forbidden:
        raise SystemExit(f"first-attempt metric reader contains hard-coded numeric fallback values: {forbidden}")


def main() -> None:
    check_real_metric_source()
    check_missing_data_errors()
    check_no_numeric_fallback()
    print("PASS stage4 first attempt metric source")
    print("AI car first attempt metric source check OK")


if __name__ == "__main__":
    main()
