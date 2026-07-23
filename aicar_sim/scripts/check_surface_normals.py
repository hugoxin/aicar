import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aicar_sim.geometry_demo_runner import run_source  # noqa: E402

for name in ("analytic", "obj", "stl", "ply"):
    geometry = run_source(name)["geometry"]
    assert geometry["normal_summary"]["invalid_normal_count"] == 0
    assert geometry["normal_summary"]["unresolved_flip_count"] == 0
    for normal in geometry["point_normals"]:
        length = math.sqrt(sum(float(normal[axis]) ** 2 for axis in ("x", "y", "z")))
        assert 0.99 <= length <= 1.01
print("surface normal check: PASS")
