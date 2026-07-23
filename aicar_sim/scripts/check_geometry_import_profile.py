import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
profile = json.loads((ROOT / "data/geometry_profiles/demo_geometry_import_profile.json").read_text(encoding="utf-8"))
assert set(profile["supported_sources"]) == {"ANALYTIC_REFERENCE", "CAD_MESH", "POINT_CLOUD"}
assert set(profile["mesh"]["supported_formats"]) == {"obj_ascii", "stl_ascii"}
assert {"ply_ascii", "xyz", "csv"}.issubset(profile["point_cloud"]["supported_formats"])
assert profile["normalization"]["target_unit"] == "mm"
print("geometry import profile check: PASS")
