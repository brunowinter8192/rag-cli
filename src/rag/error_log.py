# INFRASTRUCTURE
import json
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
ERRORS_FILE = LOG_DIR / "errors.jsonl"

ERROR_CODES = frozenset({
    "single_instance_alive_replaced",
    "busy",
    "watchdog_unlinked_dead",
    "watchdog_killed_orphan",
    "log_write_failed",
    "log_config_resolve_failed",
})


# FUNCTIONS

def write(server: str, code: str, msg: str, **extra) -> None:
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "server": server,
        "code": code,
        "msg": msg,
        **extra,
    }
    line = json.dumps(entry) + "\n"
    with open(ERRORS_FILE, "a") as fh:
        fh.write(line)


def read_today() -> list[dict]:
    now_local = datetime.now().astimezone()
    today_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    return [e for e in read_all() if datetime.fromisoformat(e["ts"]) >= today_start]


def read_errors_today() -> list[dict]:
    return [e for e in read_today() if e["code"] in ERROR_CODES]


def read_all() -> list[dict]:
    try:
        lines = ERRORS_FILE.read_text().splitlines()
    except FileNotFoundError:
        return []
    result = []
    for line in lines:
        line = line.strip()
        if line:
            result.append(json.loads(line))
    return result
