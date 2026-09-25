# INFRASTRUCTURE
from pathlib import Path

from src.rag.log_setup import get_logger
from src.rag.server_state import iter_state_files, require_preset
from src.rag.server_utils import stop_by_state

logger = get_logger("server_stop")


# ORCHESTRATOR

def stop(name: str) -> bool:
    require_preset(name)
    entry = find_state_entry(name)
    if entry is None:
        logger.info(f"{name} not running (no state file)")
        return False
    stop_entry(name, entry)
    return True


# FUNCTIONS

def find_state_entry(name: str) -> tuple[Path, dict] | None:
    for sf, state in iter_state_files():
        if state.get("name") == name:
            return sf, state
    return None


def stop_entry(name: str, entry: tuple[Path, dict]) -> None:
    sf, state = entry
    stop_by_state(state, sf, caller="stop", reason=f"user-requested stop({name})")
