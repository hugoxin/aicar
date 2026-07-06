import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aicar_sim.abstract_path import build_zone_path_segment  # noqa: E402


SAFE_ENVELOPE = {
    "x_min_mm": -1180,
    "x_max_mm": 1180,
    "y_min_mm": -2650,
    "y_max_mm": 2650,
    "z_min_mm": 0,
    "z_max_mm": 1670,
}

NOZZLE = {
    "nozzle_id": "top_high_pressure",
    "media_type": "water",
    "recommended_distance_mm": 350,
}

WHEEL_NOZZLE = {
    "nozzle_id": "wheel_focused_nozzle",
    "media_type": "water",
    "recommended_distance_mm": 280,
}

ZONES = {
    "roof": {
        "zone_id": "roof",
        "safe_envelope": SAFE_ENVELOPE,
        "bounds": {
            "x_min_mm": -900,
            "x_max_mm": 900,
            "y_min_mm": -2350,
            "y_max_mm": 2350,
            "z_min_mm": 1305,
            "z_max_mm": 1450,
        },
    },
    "left_side": {
        "zone_id": "left_side",
        "safe_envelope": SAFE_ENVELOPE,
        "bounds": {
            "x_min_mm": -900,
            "x_max_mm": -900,
            "y_min_mm": -2350,
            "y_max_mm": 2350,
            "z_min_mm": 261,
            "z_max_mm": 1450,
        },
    },
    "right_side": {
        "zone_id": "right_side",
        "safe_envelope": SAFE_ENVELOPE,
        "bounds": {
            "x_min_mm": 900,
            "x_max_mm": 900,
            "y_min_mm": -2350,
            "y_max_mm": 2350,
            "z_min_mm": 261,
            "z_max_mm": 1450,
        },
    },
    "front": {
        "zone_id": "front",
        "safe_envelope": SAFE_ENVELOPE,
        "bounds": {
            "x_min_mm": -900,
            "x_max_mm": 900,
            "y_min_mm": 2350,
            "y_max_mm": 2350,
            "z_min_mm": 0,
            "z_max_mm": 1450,
        },
    },
    "rear": {
        "zone_id": "rear",
        "safe_envelope": SAFE_ENVELOPE,
        "bounds": {
            "x_min_mm": -900,
            "x_max_mm": 900,
            "y_min_mm": -2350,
            "y_max_mm": -2350,
            "z_min_mm": 0,
            "z_max_mm": 1450,
        },
    },
    "wheels": {
        "zone_id": "wheels",
        "safe_envelope": SAFE_ENVELOPE,
        "bounds": {
            "x_min_mm": -900,
            "x_max_mm": 900,
            "y_min_mm": -2350,
            "y_max_mm": 2350,
            "z_min_mm": 0,
            "z_max_mm": 652,
        },
        "sub_zones": [
            {
                "zone_id": "front_left_wheel",
                "bounds": {
                    "x_min_mm": -1044,
                    "x_max_mm": -756,
                    "y_min_mm": 1128,
                    "y_max_mm": 1880,
                    "z_min_mm": 0,
                    "z_max_mm": 652,
                },
            },
            {
                "zone_id": "front_right_wheel",
                "bounds": {
                    "x_min_mm": 756,
                    "x_max_mm": 1044,
                    "y_min_mm": 1128,
                    "y_max_mm": 1880,
                    "z_min_mm": 0,
                    "z_max_mm": 652,
                },
            },
            {
                "zone_id": "rear_left_wheel",
                "bounds": {
                    "x_min_mm": -1044,
                    "x_max_mm": -756,
                    "y_min_mm": -1880,
                    "y_max_mm": -1128,
                    "z_min_mm": 0,
                    "z_max_mm": 652,
                },
            },
            {
                "zone_id": "rear_right_wheel",
                "bounds": {
                    "x_min_mm": 756,
                    "x_max_mm": 1044,
                    "y_min_mm": -1880,
                    "y_max_mm": -1128,
                    "z_min_mm": 0,
                    "z_max_mm": 652,
                },
            },
        ],
    },
}


def assert_segment(segment: dict, min_points: int) -> None:
    if len(segment["points"]) < min_points:
        raise AssertionError(f"expected at least {min_points} points")
    for point in segment["points"]:
        for field in ("x_mm", "y_mm", "z_mm", "speed_mm_s"):
            if field not in point:
                raise AssertionError(f"point missing field: {field}")


def main() -> None:
    for index, zone_id in enumerate(
        ("roof", "left_side", "right_side", "front", "rear"),
        start=1,
    ):
        segment = build_zone_path_segment(
            "demo_state",
            ZONES[zone_id],
            NOZZLE,
            10,
            index,
        )
        assert_segment(segment, 2)
        print(f"PASS {zone_id} abstract path")

    wheel_segment = build_zone_path_segment(
        "wheel_clean",
        ZONES["wheels"],
        WHEEL_NOZZLE,
        8,
        6,
    )
    assert_segment(wheel_segment, 4)
    if wheel_segment["path_type"] != "focused_points":
        raise AssertionError("wheels must use focused_points")
    print("PASS wheels abstract path")
    print("AI car abstract path check OK")


if __name__ == "__main__":
    main()
