# INFRASTRUCTURE
from src.rag.log_setup import get_logger
from src.rag.watchdog import watchdog_loop

logger = get_logger("watchdog_main")


# ORCHESTRATOR

def run_watchdog() -> None:
    try:
        watchdog_loop()
    except Exception:
        logger.exception("watchdog loop aborted")
        raise


if __name__ == '__main__':
    run_watchdog()
