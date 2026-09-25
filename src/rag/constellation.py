# INFRASTRUCTURE
from src.rag.log_setup import get_logger
from src.rag.server_manager import ensure_ready
from src.rag.server_state import get_running_presets
from src.rag.server_stop import stop
from src.rag.watchdog import ensure_watchdog_process

logger = get_logger("constellation")


# ORCHESTRATOR

def ensure_constellation(server_names: list[str]) -> None:
    stop_unrequested(get_running_presets(), server_names)
    ensure_all_ready(server_names)
    ensure_watchdog_process()


# FUNCTIONS

def stop_unrequested(running: list[str], server_names: list[str]) -> None:
    for name in running:
        if name not in server_names:
            logger.info(
                f"constellation-stop: {name} stopped, not in requested constellation {server_names}"
            )
            stop(name)


def ensure_all_ready(server_names: list[str]) -> None:
    for name in server_names:
        ensure_ready(name)
