import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aicar_sim.vehicle_envelope import SURFACE_ZONE_IDS, build_vehicle_envelope  # noqa: E402
from aicar_sim.wash_profile import load_wash_profile  # noqa: E402


VEHICLES_DIR = PROJECT_ROOT / "data" / "vehicles"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main() -> None:
    for vehicle_type in ("sedan", "suv", "mpv"):
        vehicle_model = load_json(VEHICLES_DIR / f"{vehicle_type}.json")
        wash_profile = load_wash_profile(vehicle_model["wash_profile"])
        envelope = build_vehicle_envelope(vehicle_model, wash_profile)
        box = envelope["bounding_box"]
        safe = envelope["safe_envelope"]

        if box["x_max_mm"] - box["x_min_mm"] != vehicle_model["width_mm"]:
            raise AssertionError(f"{vehicle_type}: bounding box width mismatch")
        if box["y_max_mm"] - box["y_min_mm"] != vehicle_model["length_mm"]:
            raise AssertionError(f"{vehicle_type}: bounding box length mismatch")
        if box["z_max_mm"] - box["z_min_mm"] != vehicle_model["height_mm"]:
            raise AssertionError(f"{vehicle_type}: bounding box height mismatch")

        if safe["x_min_mm"] >= box["x_min_mm"] or safe["x_max_mm"] <= box["x_max_mm"]:
            raise AssertionError(f"{vehicle_type}: safe x envelope is not larger")
        if safe["y_min_mm"] >= box["y_min_mm"] or safe["y_max_mm"] <= box["y_max_mm"]:
            raise AssertionError(f"{vehicle_type}: safe y envelope is not larger")
        if safe["z_max_mm"] <= box["z_max_mm"]:
            raise AssertionError(f"{vehicle_type}: safe z envelope is not taller")

        zones = {zone["zone_id"] for zone in envelope["surface_zones"]}
        missing = set(SURFACE_ZONE_IDS) - zones
        if missing:
            raise AssertionError(f"{vehicle_type}: missing zones {sorted(missing)}")

        print(f"PASS {vehicle_type} envelope")

    print("AI car vehicle envelope check OK")


if __name__ == "__main__":
    main()
