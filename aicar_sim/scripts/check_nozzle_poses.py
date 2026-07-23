import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aicar_sim.geometry_demo_runner import run_source  # noqa: E402


def rotate(q, value):
    w, x, y, z = q
    vx, vy, vz = value
    tx, ty, tz = 2 * (y * vz - z * vy), 2 * (z * vx - x * vz), 2 * (x * vy - y * vx)
    return (
        vx + w * tx + (y * tz - z * ty),
        vy + w * ty + (z * tx - x * tz),
        vz + w * tz + (x * ty - y * tx),
    )

for name in ("analytic", "obj", "ply"):
    plan = run_source(name)["pose_plan"]
    summary = plan["pose_summary"]
    assert summary["invalid_pose_count"] == 0
    assert summary["quaternion_invalid_count"] == 0
    assert summary["unresolved_orientation_flip_count"] == 0
    assert summary["pose_discontinuity_count"] == 0
    assert 250 <= summary["minimum_standoff_mm"] <= summary["maximum_standoff_mm"] <= 650
    assert summary["maximum_incidence_angle_deg"] <= 15
    assert summary["maximum_orientation_step_deg"] <= 12
    for pose in plan["poses"]:
        q = pose["orientation_quaternion"]
        values = tuple(float(q[key]) for key in ("w", "x", "y", "z"))
        assert abs(math.sqrt(sum(value * value for value in values)) - 1) < 1e-6
        axis = rotate(values, (0.0, 0.0, -1.0))
        normal = tuple(float(pose["surface_normal"][key]) for key in ("x", "y", "z"))
        assert sum(axis[index] * -normal[index] for index in range(3)) > 0.999999
print("nozzle pose check: PASS")
