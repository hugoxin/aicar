"""Load and validate Stage2.2 wash bay models."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WASH_BAYS_DIR = PROJECT_ROOT / "data" / "wash_bays"
REQUIRED_TOP_LEVEL_FIELDS = (
    "wash_bay_id",
    "coordinate_system",
    "bay_dimensions",
    "vehicle_alignment",
    "gantry",
    "safety_margin",
)
REQUIRED_DIMENSION_FIELDS = ("length_mm", "width_mm", "height_mm")
REQUIRED_COORDINATE_FIELDS = ("unit", "origin", "x_axis", "y_axis", "z_axis")
REQUIRED_GANTRY_FIELDS = (
    "rail_y_min_mm",
    "rail_y_max_mm",
    "rail_x_left_mm",
    "rail_x_right_mm",
    "max_z_mm",
)


def validate_wash_bay(bay: dict) -> None:
    """Validate required wash bay fields."""
    missing = [field for field in REQUIRED_TOP_LEVEL_FIELDS if field not in bay]
    if missing:
        raise ValueError(f"wash bay missing required fields: {missing}")

    for group_name, required_fields in (
        ("bay_dimensions", REQUIRED_DIMENSION_FIELDS),
        ("coordinate_system", REQUIRED_COORDINATE_FIELDS),
        ("gantry", REQUIRED_GANTRY_FIELDS),
    ):
        group = bay.get(group_name, {})
        group_missing = [field for field in required_fields if field not in group]
        if group_missing:
            raise ValueError(f"wash bay {group_name} missing fields: {group_missing}")


def load_wash_bay(
    bay_id: str = "demo_wash_bay",
    bays_dir: str | Path | None = None,
) -> dict:
    """Load a wash bay JSON by id or explicit path."""
    candidate = Path(bay_id)
    if candidate.suffix.lower() == ".json" or candidate.is_absolute():
        path = candidate
        if not path.is_absolute():
            path = Path.cwd() / path
    else:
        root = Path(bays_dir) if bays_dir else DEFAULT_WASH_BAYS_DIR
        path = root / f"{bay_id}.json"

    with path.open("r", encoding="utf-8") as file:
        bay = json.load(file)
    validate_wash_bay(bay)
    bay["bay_model_path"] = str(path.resolve())
    return bay
