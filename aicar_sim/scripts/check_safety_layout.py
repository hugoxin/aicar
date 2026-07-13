import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.motion_model import is_point_inside_workspace, load_motion_model  # noqa: E402
from aicar_sim.obstacle_model import load_safety_layout, point_inside_aabb  # noqa: E402
from aicar_sim.safety_zone import apply_safety_zone_annotations, resolve_dynamic_safety_zones  # noqa: E402
from aicar_sim.task_allocator import load_actuator_system  # noqa: E402


def main() -> None:
    layout = load_safety_layout(PROJECT_ROOT / "data/safety_models/demo_wash_bay_safety_layout.json")
    system = load_actuator_system(PROJECT_ROOT / "data/actuator_systems/demo_multi_actuator_system.json")
    motion = load_motion_model(PROJECT_ROOT / "data/motion_models/demo_cartesian_gantry.json")
    zone_types = [zone["zone_type"] for zone in layout["safety_zones"]]
    for required in ("forbidden", "slow", "shared_interlock", "safe_stop"):
        if required not in zone_types:
            raise SystemExit(f"missing safety zone type: {required}")
    if zone_types.count("safe_stop") < len(system["actuators"]):
        raise SystemExit("not enough safe-stop zones")
    if not all(is_point_inside_workspace(item["home_position"], motion) for item in system["actuators"]):
        raise SystemExit("actuator home position is outside the workspace")
    for actuator in system["actuators"]:
        if any(point_inside_aabb(actuator["home_position"], obstacle["bounds"]) for obstacle in layout["static_obstacles"]):
            raise SystemExit(f"actuator home position intersects static obstacle: {actuator['actuator_id']}")
    envelope = {"x_min_mm": -100, "x_max_mm": 100, "y_min_mm": -100, "y_max_mm": 100, "z_min_mm": 0, "z_max_mm": 100}
    resolved = resolve_dynamic_safety_zones(layout, envelope)
    sample = [
        {"x_mm": 0, "y_mm": 0, "z_mm": 50, "velocity_mm_s": 100},
        {"x_mm": 125, "y_mm": 0, "z_mm": 50, "velocity_mm_s": 100},
    ]
    annotated = apply_safety_zone_annotations(sample, resolved)
    if not annotated[0]["forbidden"] or annotated[0]["speed_scale"] != 0:
        raise SystemExit("synthetic forbidden-zone policy did not activate")
    if "slow" not in annotated[1]["zone_policy"] or annotated[1]["speed_scale"] > 0.5:
        raise SystemExit("synthetic slow-zone policy did not reduce speed")
    print(f"static_obstacle_count: {len(layout['static_obstacles'])}")
    print(f"safety_zone_count: {len(layout['safety_zones'])}")
    print("PASS stage4 safety layout")
    print("AI car safety layout check OK")


if __name__ == "__main__":
    main()
