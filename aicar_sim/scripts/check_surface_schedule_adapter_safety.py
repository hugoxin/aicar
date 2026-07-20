import json
import math
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.shared_space_interlock import detect_time_interval_conflicts  # noqa: E402
from aicar_sim.surface_schedule_adapter import (  # noqa: E402
    calculate_actual_shared_zone_intervals,
    map_relative_interval_to_window,
    validate_resource_lock_intervals,
)

SCHEDULE_OUTPUT = PROJECT_ROOT / "outputs/continuous_schedule_r/continuous_multi_actuator_schedule_r.json"
ALLOWED_MAPPING_MODES = {
    "PROPORTIONAL_SOURCE_TO_SCHEDULE",
    "FULL_WINDOW_FALLBACK",
    "FULL_TASK_RESOURCE",
}
ZONE_BOUNDS = {
    "x_min_mm": -500.0,
    "x_max_mm": 500.0,
    "y_min_mm": -500.0,
    "y_max_mm": 500.0,
    "z_min_mm": 0.0,
    "z_max_mm": 1000.0,
}


def _output_has_current_mapping_fields(schedule: dict) -> bool:
    locks = schedule.get("resource_locks")
    checks = schedule.get("adapter_validation", {}).get("checks", {})
    return (
        isinstance(schedule.get("interval_mapping_warnings"), list)
        and isinstance(locks, list)
        and bool(locks)
        and all("interval_mapping_mode" in lock for lock in locks)
        and "lock_durations_positive" in checks
        and "locks_within_task_windows" in checks
    )


def _load_current_schedule() -> dict:
    schedule = None
    if SCHEDULE_OUTPUT.exists():
        schedule = json.loads(SCHEDULE_OUTPUT.read_text(encoding="utf-8"))
    if schedule is None or not _output_has_current_mapping_fields(schedule):
        completed = subprocess.run(
            [sys.executable, "-B", str(PROJECT_ROOT / "scripts/generate_continuous_surface_validation_r.py")],
            cwd=WORKSPACE_ROOT,
        )
        if completed.returncode:
            raise SystemExit(completed.returncode)
        schedule = json.loads(SCHEDULE_OUTPUT.read_text(encoding="utf-8"))
    if not _output_has_current_mapping_fields(schedule):
        raise SystemExit("Stage4.5-R schedule is missing current interval mapping fields after regeneration")
    return schedule


def check_real_schedule_locks() -> None:
    schedule = _load_current_schedule()
    items = {item["task_id"]: item for item in schedule["schedule_items"]}
    locks = schedule["resource_locks"]
    reversed_count = 0
    outside_count = 0
    for lock in locks:
        start = float(lock["start_s"])
        end = float(lock["end_s"])
        if not math.isfinite(start) or not math.isfinite(end) or end <= start:
            reversed_count += 1
        item = items.get(lock["task_id"])
        if item is None:
            raise SystemExit(f"resource lock references unknown task: {lock['task_id']}")
        if start < float(item["adjusted_start_s"]) - 1e-6 or end > float(item["adjusted_end_s"]) + 1e-6:
            outside_count += 1
        if lock.get("interval_mapping_mode") not in ALLOWED_MAPPING_MODES:
            raise SystemExit(f"resource lock has invalid mapping mode: {lock}")
    if reversed_count or outside_count:
        raise SystemExit(
            f"real schedule has invalid locks: reversed={reversed_count}, outside_window={outside_count}"
        )
    validate_resource_lock_intervals(schedule["schedule_items"], locks)
    conflicts = detect_time_interval_conflicts(locks)
    if conflicts:
        raise SystemExit(f"real schedule has {len(conflicts)} same-resource final conflicts")
    checks = schedule["adapter_validation"]["checks"]
    for name in ("lock_durations_positive", "locks_within_task_windows"):
        if not checks.get(name):
            raise SystemExit(f"adapter validation check failed: {name}")


def _assert_mapping(
    relative_start: float,
    relative_end: float,
    source_span: float,
    window_start: float,
    window_end: float,
    expected_start: float,
    expected_end: float,
    expected_mode: str = "PROPORTIONAL_SOURCE_TO_SCHEDULE",
    expected_clamped: bool = False,
) -> dict:
    result = map_relative_interval_to_window(
        relative_start, relative_end, source_span, window_start, window_end
    )
    if abs(float(result["start_s"]) - expected_start) > 1e-6 or abs(float(result["end_s"]) - expected_end) > 1e-6:
        raise SystemExit(f"unexpected proportional mapping result: {result}")
    if result["interval_mapping_mode"] != expected_mode:
        raise SystemExit(f"unexpected interval mapping mode: {result}")
    if bool(result["interval_clamped_to_window"]) != expected_clamped:
        raise SystemExit(f"unexpected interval clamp status: {result}")
    return result


def check_mapping_examples() -> None:
    _assert_mapping(20.0, 40.0, 100.0, 0.0, 10.0, 2.0, 4.0)
    _assert_mapping(80.0, 90.0, 100.0, 0.0, 10.0, 8.0, 9.0)
    _assert_mapping(50.0, 100.0, 200.0, 30.0, 50.0, 35.0, 40.0)
    clamped = _assert_mapping(90.0, 120.0, 100.0, 0.0, 10.0, 9.0, 10.0, expected_clamped=True)
    if not clamped["interval_clamped_to_window"]:
        raise SystemExit("source interval outside its span did not produce a clamp marker")
    fallback = _assert_mapping(
        2.0,
        3.0,
        0.0,
        5.0,
        15.0,
        5.0,
        15.0,
        expected_mode="FULL_WINDOW_FALLBACK",
    )
    if not fallback["fallback_reason"]:
        raise SystemExit("invalid source span fallback did not record a reason")
    nonfinite = map_relative_interval_to_window(float("nan"), 3.0, 10.0, 5.0, 15.0)
    if (
        nonfinite["interval_mapping_mode"] != "FULL_WINDOW_FALLBACK"
        or (float(nonfinite["start_s"]), float(nonfinite["end_s"])) != (5.0, 15.0)
        or nonfinite["source_relative_start_s"] is not None
    ):
        raise SystemExit(f"non-finite source data did not use a serializable full-window fallback: {nonfinite}")
    try:
        map_relative_interval_to_window(1.0, 2.0, 10.0, 5.0, 5.0)
    except ValueError as error:
        if "invalid schedule window" not in str(error):
            raise SystemExit(f"invalid schedule window raised an unclear error: {error}")
    else:
        raise SystemExit("invalid schedule window did not raise ValueError")


def check_mapping_warning_generation() -> None:
    schedule = [
        {
            "task_id": "task_long_span",
            "actuator_id": "top_actuator",
            "shared_resources": [],
            "adjusted_start_s": 0.0,
            "adjusted_end_s": 10.0,
            "source_start_s": 0.0,
            "source_end_s": 100.0,
        }
    ]
    swept_volumes = [
        {
            "task_id": "task_long_span",
            "bounds": dict(ZONE_BOUNDS),
            "start_point_index": 90,
            "end_point_index": 120,
        }
    ]
    safety_layout = {
        "safety_zones": [
            {"zone_id": "center_shared_space", "zone_type": "shared_interlock", "bounds": dict(ZONE_BOUNDS)}
        ]
    }
    trajectory_points = [
        {"sequence_index": index, "timestamp_s": float(index)} for index in range(121)
    ]
    locks, warnings = calculate_actual_shared_zone_intervals(
        schedule, swept_volumes, safety_layout, trajectory_points
    )
    lock = next(item for item in locks if item["interval_source"] == "actual_shared_zone_swept_interval")
    if (float(lock["start_s"]), float(lock["end_s"])) != (9.0, 10.0):
        raise SystemExit(f"clamped shared-zone lock has unexpected times: {lock}")
    if not any(item.get("check_id") == "shared_interval_clamped_to_source_span" for item in warnings):
        raise SystemExit("clamped shared-zone mapping did not emit a warning")


def check_lock_validation_rejects_bad_intervals() -> None:
    schedule = [{"task_id": "task_a", "adjusted_start_s": 0.0, "adjusted_end_s": 10.0}]
    for bad_lock, expected in (
        ({"resource_id": "r", "task_id": "task_a", "start_s": 5.0, "end_s": 4.0}, "non-positive duration"),
        ({"resource_id": "r", "task_id": "task_a", "start_s": 5.0, "end_s": 11.0}, "leaves its schedule window"),
        ({"resource_id": "r", "task_id": "task_missing", "start_s": 1.0, "end_s": 2.0}, "unknown schedule task"),
    ):
        try:
            validate_resource_lock_intervals(schedule, [bad_lock])
        except ValueError as error:
            if expected not in str(error):
                raise SystemExit(f"lock validation raised an unclear error for {bad_lock}: {error}")
        else:
            raise SystemExit(f"lock validation accepted an invalid lock: {bad_lock}")


def main() -> None:
    check_mapping_examples()
    check_mapping_warning_generation()
    check_lock_validation_rejects_bad_intervals()
    check_real_schedule_locks()
    print("PASS stage4 shared interval mapping")
    print("AI car shared interval mapping check OK")


if __name__ == "__main__":
    main()
