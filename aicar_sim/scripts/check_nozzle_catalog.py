import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aicar_sim.nozzle_model import REQUIRED_NOZZLE_FIELDS, load_nozzle_catalog  # noqa: E402


def main() -> None:
    catalog = load_nozzle_catalog()
    nozzles = catalog.get("nozzles", [])
    if len(nozzles) < 5:
        raise AssertionError(f"expected at least 5 nozzles, got {len(nozzles)}")

    for nozzle in nozzles:
        missing = [field for field in REQUIRED_NOZZLE_FIELDS if field not in nozzle]
        if missing:
            raise AssertionError(f"{nozzle.get('nozzle_id')}: missing {missing}")
        if not nozzle["target_zones"]:
            raise AssertionError(f"{nozzle['nozzle_id']}: target_zones is empty")

    print("PASS nozzle catalog")
    print("AI car nozzle catalog check OK")


if __name__ == "__main__":
    main()
