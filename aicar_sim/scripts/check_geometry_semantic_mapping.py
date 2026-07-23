import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aicar_sim.geometry_demo_runner import run_source  # noqa: E402

required = {"roof", "left_side", "right_side", "front", "rear", "left_front_wheel", "left_rear_wheel", "right_front_wheel", "right_rear_wheel"}
for name in ("analytic", "obj", "stl", "ply"):
    geometry = run_source(name)["geometry"]
    actual = {item["patch_id"] for item in geometry["semantic_patches"] if item["sample_count"] > 0}
    assert actual == required
    assert geometry["semantic_summary"]["missing_patches"] == []
print("geometry semantic mapping check: PASS (9 patches, 4 wheel patches)")
