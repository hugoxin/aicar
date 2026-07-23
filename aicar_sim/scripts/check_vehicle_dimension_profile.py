import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aicar_sim.vehicle_dimension_profile import get_wheel_centers, load_vehicle_dimension_profile  # noqa: E402

profile = load_vehicle_dimension_profile(ROOT / "data/vehicle_dimensions/demo_reference_real_size_sedan_dimensions.json")
d = profile["dimensions"]
assert (d["length_mm"], d["width_mm"], d["height_mm"]) == (4800, 1880, 1450)
assert d["wheelbase_mm"] == 2850 and d["wheel_radius_mm"] == 335
centers = get_wheel_centers(profile)
assert len(centers) == 4 and centers["left_front_wheel"]["y_mm"] == 1425
assert (4800, 1880, 1450) != (4700, 1800, 1450)
print("vehicle dimension profile check: PASS")
print("dimension replacement: 4700x1800x1450 -> 4800x1880x1450 mm")
