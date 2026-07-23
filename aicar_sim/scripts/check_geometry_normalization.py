import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aicar_sim.geometry_demo_runner import run_source  # noqa: E402

for name in ("analytic", "obj", "ply"):
    geometry = run_source(name)["geometry"]
    bbox = geometry["bounding_box"]
    dimensions = (
        bbox["x_max_mm"] - bbox["x_min_mm"],
        bbox["y_max_mm"] - bbox["y_min_mm"],
        bbox["z_max_mm"] - bbox["z_min_mm"],
    )
    assert geometry["unit"] == "mm"
    assert geometry["coordinate_system"]["handedness"] == "right"
    assert all(math.isfinite(value) and value > 0 for value in dimensions)
    assert geometry["dimension_summary"]["maximum_mismatch_ratio"] <= 0.05
print("geometry normalization check: PASS")
