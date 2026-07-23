import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aicar_sim.geometry_demo_runner import run_source  # noqa: E402

for name in ("analytic", "obj", "stl", "ply"):
    result = run_source(name)
    summary = result["validation"]["summary"]
    assert summary["static_collision_count"] == 0
    assert summary["vehicle_collision_count"] == 0
    assert summary["forbidden_zone_entry_count"] == 0
    assert summary["unassigned_task_count"] == 0
    assert summary["unresolved_conflict_count"] == 0
    assert summary["deadlock_warning_count"] == 0
    assert summary["safe_stop_point_count"] >= 3
    assert summary["minimum_clearance_mm"] >= 250
    assert summary["violation_count"] == 0
    assert result["validation"]["status"] == "ACCEPTED_WITH_WARNINGS"
print("geometry safety validation check: PASS")
