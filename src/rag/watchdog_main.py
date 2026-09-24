# INFRASTRUCTURE
from .log_setup import get_logger

logger = get_logger("watchdog_main")


# ORCHESTRATOR
if __name__ == '__main__':
    from . import server_manager
    try:
        server_manager._watchdog_loop()
    except Exception:
        logger.exception("watchdog loop aborted")
        raise
