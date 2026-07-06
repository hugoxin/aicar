import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aicar_sim.nozzle_model import (  # noqa: E402
    load_nozzle_catalog,
    load_nozzle_zone_mapping,
    validate_nozzle_zone_mapping,
)


REQUIRED_ZONES = {"roof", "left_side", "right_side", "front", "rear", "wheels"}


def main() -> None:
    catalog = load_nozzle_catalog()
    mapping = load_nozzle_zone_mapping()
    validate_nozzle_zone_mapping(mapping, catalog)

    mapped_zones = {item["zone_id"] for item in mapping["zone_mappings"]}
    missing = REQUIRED_ZONES - mapped_zones
    if missing:
        raise AssertionError(f"missing zone mappings: {sorted(missing)}")

    print("PASS nozzle zone mapping")
    print("AI car nozzle zone mapping check OK")


if __name__ == "__main__":
    main()
