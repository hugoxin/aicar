"""Load and validate Stage2.3 nozzle models."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_NOZZLE_DIR = PROJECT_ROOT / "data" / "nozzles"
DEFAULT_CATALOG_PATH = DEFAULT_NOZZLE_DIR / "demo_nozzle_catalog.json"
DEFAULT_MAPPING_PATH = DEFAULT_NOZZLE_DIR / "demo_nozzle_zone_mapping.json"
REQUIRED_NOZZLE_FIELDS = (
    "nozzle_id",
    "display_name",
    "media_type",
    "pressure_level",
    "spray_angle_deg",
    "recommended_distance_mm",
    "effective_width_mm",
    "flow_l_min",
    "target_zones",
)
REQUIRED_ZONE_MAPPING_FIELDS = (
    "zone_id",
    "priority",
    "coverage_target_percent",
    "pass_count_hint",
    "nozzles",
)


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _resolve_path(path: str | Path | None, default_path: Path) -> Path:
    if path is None:
        return default_path
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = Path.cwd() / resolved
    return resolved.resolve()


def validate_nozzle_catalog(catalog: dict) -> None:
    nozzles = catalog.get("nozzles", [])
    if not isinstance(nozzles, list) or not nozzles:
        raise ValueError("nozzle catalog must contain a non-empty nozzles list")

    seen = set()
    for nozzle in nozzles:
        missing = [field for field in REQUIRED_NOZZLE_FIELDS if field not in nozzle]
        if missing:
            raise ValueError(
                f"nozzle {nozzle.get('nozzle_id', '<unknown>')} missing fields: {missing}"
            )
        nozzle_id = nozzle["nozzle_id"]
        if nozzle_id in seen:
            raise ValueError(f"duplicate nozzle_id: {nozzle_id}")
        seen.add(nozzle_id)
        if not nozzle["target_zones"]:
            raise ValueError(f"nozzle {nozzle_id} target_zones must not be empty")


def validate_nozzle_zone_mapping(mapping: dict, catalog: dict | None = None) -> None:
    zone_mappings = mapping.get("zone_mappings", [])
    if not isinstance(zone_mappings, list) or not zone_mappings:
        raise ValueError("nozzle zone mapping must contain a non-empty zone_mappings list")

    catalog_ids = set()
    if catalog is not None:
        catalog_ids = {nozzle["nozzle_id"] for nozzle in catalog.get("nozzles", [])}

    seen_zones = set()
    for zone_mapping in zone_mappings:
        missing = [
            field for field in REQUIRED_ZONE_MAPPING_FIELDS if field not in zone_mapping
        ]
        if missing:
            raise ValueError(
                f"zone mapping {zone_mapping.get('zone_id', '<unknown>')} missing fields: {missing}"
            )
        zone_id = zone_mapping["zone_id"]
        if zone_id in seen_zones:
            raise ValueError(f"duplicate zone_id in mapping: {zone_id}")
        seen_zones.add(zone_id)
        if not zone_mapping["nozzles"]:
            raise ValueError(f"zone mapping {zone_id} must include at least one nozzle")
        if catalog_ids:
            for nozzle_ref in zone_mapping["nozzles"]:
                nozzle_id = nozzle_ref["nozzle_id"]
                if nozzle_id not in catalog_ids:
                    raise ValueError(
                        f"zone mapping {zone_id} references unknown nozzle_id: {nozzle_id}"
                    )


def load_nozzle_catalog(path: str | Path | None = None) -> dict:
    catalog_path = _resolve_path(path, DEFAULT_CATALOG_PATH)
    catalog = _load_json(catalog_path)
    validate_nozzle_catalog(catalog)
    catalog["catalog_path"] = str(catalog_path)
    return catalog


def load_nozzle_zone_mapping(path: str | Path | None = None) -> dict:
    mapping_path = _resolve_path(path, DEFAULT_MAPPING_PATH)
    mapping = _load_json(mapping_path)
    validate_nozzle_zone_mapping(mapping)
    mapping["mapping_path"] = str(mapping_path)
    return mapping


def _nozzle_index(catalog: dict) -> dict:
    return {nozzle["nozzle_id"]: nozzle for nozzle in catalog.get("nozzles", [])}


def _mapping_index(mapping: dict) -> dict:
    return {item["zone_id"]: item for item in mapping.get("zone_mappings", [])}


def get_nozzles_for_zone(zone_id: str, catalog: dict, mapping: dict) -> list[dict]:
    """Return nozzle assignments for a surface zone."""
    validate_nozzle_catalog(catalog)
    validate_nozzle_zone_mapping(mapping, catalog)

    zone_mapping = _mapping_index(mapping).get(zone_id)
    if zone_mapping is None:
        return []

    nozzles_by_id = _nozzle_index(catalog)
    assignments = []
    for nozzle_ref in zone_mapping["nozzles"]:
        nozzle = dict(nozzles_by_id[nozzle_ref["nozzle_id"]])
        nozzle["pass_count_hint"] = int(
            nozzle_ref.get("pass_count_hint", zone_mapping["pass_count_hint"])
        )
        assignments.append(nozzle)
    return assignments
