# INFRASTRUCTURE
import time
from datetime import datetime, timezone

from src.rag.config import LOCK_DIR
from src.rag.db import POSTGRES_PORT, probe_postgres
from src.rag.lock import read as read_lock
from src.rag.server_status import status as box_status


# ORCHESTRATOR

def gather() -> dict:
    return {
        "lock": _lock_status(),
        "servers": _server_status(),
        "postgres": _postgres_status(),
    }


# FUNCTIONS

def _lock_status() -> dict:
    data = read_lock()
    if data is None:
        return {"held": False, "data": None, "stale_heartbeat": False}
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(data["heartbeat"])).total_seconds()
    stale = age > 60
    return {"held": True, "data": data, "stale_heartbeat": stale}


def _server_status() -> dict:
    result = {}
    for name, info in box_status().items():
        idle_secs = _state_file_idle(info["port"]) if info["port"] else None
        result[name] = {
            "running": info["running"],
            "healthy": info["healthy"],
            "port": info["port"],
            "last_used_secs": idle_secs,
        }
    return result


def _state_file_idle(port: int) -> float:
    return time.time() - (LOCK_DIR / f"server-port-{port}.json").stat().st_mtime


def _postgres_status() -> dict:
    error = probe_postgres()
    return {"reachable": error is None, "port": POSTGRES_PORT, "error": error}
