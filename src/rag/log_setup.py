# INFRASTRUCTURE
import logging
from pathlib import Path

LOG_ROOT = Path(__file__).parent / "logs"
LOG_ROOT.mkdir(exist_ok=True)

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


# FUNCTIONS

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(f"rag.{name}")
    if not logger.handlers:
        handler = logging.FileHandler(LOG_ROOT / f"{name}.log")
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
