import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aicar_sim.geometry_demo_runner import run_source  # noqa: E402

for name in ("analytic", "obj", "ply"):
    result = run_source(name)
    machine = result["machine_plan"]
    points = machine["trajectory_points"]
    assert all(float(b["timestamp_s"]) > float(a["timestamp_s"]) for a, b in zip(points, points[1:]))
    assert abs(float(points[-1]["velocity_mm_s"])) < 1e-9
    assert machine["motion_validation"]["violation_count"] == 0
    summary = result["validation"]["summary"]
    assert (summary["state_count"], summary["zone_count"], summary["patch_count"], summary["wheel_patch_count"]) == (7, 6, 9, 4)
print("geometry machine path check: PASS")
