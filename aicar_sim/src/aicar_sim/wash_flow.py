"""Load and validate Stage2.4 wash flow configurations."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FLOW_CONFIG_PATH = PROJECT_ROOT / "data" / "wash_flows" / "demo_wash_flow.json"
REQUIRED_FLOW_FIELDS = (
    "flow_id",
    "initial_state",
    "terminal_states",
    "states",
)
REQUIRED_STATE_FIELDS = ("state_id", "display_name", "state_type", "next_states")


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_wash_flow_config(path: str | Path | None = None) -> dict:
    """Load a wash flow config JSON."""
    config_path = Path(path) if path else DEFAULT_FLOW_CONFIG_PATH
    if not config_path.is_absolute():
        config_path = Path.cwd() / config_path
    config = _load_json(config_path)
    validate_wash_flow_config(config)
    config["flow_config_path"] = str(config_path.resolve())
    return config


def _state_index(config: dict) -> dict:
    return {state["state_id"]: state for state in config.get("states", [])}


def get_state(config: dict, state_id: str) -> dict:
    """Return a state by id."""
    state = _state_index(config).get(state_id)
    if state is None:
        raise KeyError(f"wash flow state not found: {state_id}")
    return state


def validate_wash_flow_config(config: dict, wash_strategy_plan: dict | None = None) -> None:
    """Validate flow state references and optional strategy stage references."""
    missing = [field for field in REQUIRED_FLOW_FIELDS if field not in config]
    if missing:
        raise ValueError(f"wash flow config missing fields: {missing}")

    states = config.get("states", [])
    if not isinstance(states, list) or not states:
        raise ValueError("wash flow config states must be a non-empty list")

    seen = set()
    for state in states:
        state_missing = [field for field in REQUIRED_STATE_FIELDS if field not in state]
        if state_missing:
            raise ValueError(
                f"state {state.get('state_id', '<unknown>')} missing fields: {state_missing}"
            )
        state_id = state["state_id"]
        if state_id in seen:
            raise ValueError(f"duplicate wash flow state_id: {state_id}")
        seen.add(state_id)

    if config["initial_state"] not in seen:
        raise ValueError(f"initial_state not found: {config['initial_state']}")

    for terminal_state in config["terminal_states"]:
        if terminal_state not in seen:
            raise ValueError(f"terminal_state not found: {terminal_state}")

    terminal_set = set(config["terminal_states"])
    for state in states:
        state_id = state["state_id"]
        next_states = state.get("next_states", [])
        for next_state in next_states:
            if next_state not in seen:
                raise ValueError(f"{state_id} references unknown next_state: {next_state}")
        if state_id not in terminal_set and not next_states:
            raise ValueError(f"non-terminal state must have next_states: {state_id}")

    if wash_strategy_plan is not None:
        known_stage_ids = {
            stage["stage_id"] for stage in wash_strategy_plan.get("stages", [])
        }
        for state in states:
            stage_id = state.get("strategy_stage_id")
            if stage_id and stage_id not in known_stage_ids:
                raise ValueError(
                    f"state {state['state_id']} references unknown strategy_stage_id: {stage_id}"
                )


def get_linear_flow_sequence(config: dict) -> list[dict]:
    """Follow the first next_state from initial_state until a terminal state."""
    validate_wash_flow_config(config)
    terminal_set = set(config["terminal_states"])
    current_id = config["initial_state"]
    visited = set()
    sequence = []

    while True:
        if current_id in visited:
            raise ValueError(f"wash flow sequence contains a loop at state: {current_id}")
        visited.add(current_id)
        state = get_state(config, current_id)
        sequence.append(state)
        if current_id in terminal_set:
            break
        next_states = state.get("next_states", [])
        if not next_states:
            raise ValueError(f"state has no next state: {current_id}")
        current_id = next_states[0]

    return sequence
