import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = json.loads((ROOT / "data/nozzle_pose_profiles/demo_nozzle_pose_profile.json").read_text(encoding="utf-8"))
assert p["position"]["preferred_standoff_mm"] == 350
assert p["position"]["hard_minimum_clearance_mm"] == 250
assert p["position"]["maximum_standoff_mm"] == 650
assert p["orientation"]["maximum_incidence_angle_deg"] == 15
assert p["orientation"]["maximum_orientation_step_deg"] == 12
print("nozzle pose profile check: PASS")
