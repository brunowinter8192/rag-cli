# INFRASTRUCTURE
import time
from datetime import datetime, timezone

from .lock import read as read_lock
from .server_manager import TIMESTAMP_DIR, status as box_status


# ORCHESTRATOR

def gather() -> dict:
    """Gather lock state, GPU server health, and Postgres reachability."""
    return {
        "lock": _lock_status(),
        "servers": _server_status(),
        "postgres": _postgres_status(),
    }


def format_status(info: dict) -> str:
    lines = []

    # Lock
    lock = info["lock"]
    if lock["held"]:
        d = lock["data"]
        elapsed_str = _elapsed(d["started_at"])
        heartbeat_str = _elapsed(d.get("heartbeat", d["started_at"]))
        prog = d.get("progress") or {}
        prog_str = ""
        if prog:
            prog_str = (
                f"\n         Progress: {prog['done']}/{prog['total']} chunks"
                f" — {prog['current_document']}"
            )
        stale_warn = ""
        if lock.get("stale_heartbeat"):
            stale_warn = " ⚠ heartbeat stale"
        lines.append(
            f"Lock:    HELD by PID {d['pid']} ({d['command']}) "
            f"since {elapsed_str} ago"
            f" [heartbeat: {heartbeat_str}{stale_warn}]{prog_str}"
        )
    else:
        lines.append("Lock:    FREE")

    lines.append("")

    # Servers
    lines.append("Servers:")
    for name, s in info["servers"].items():
        status = "RUNNING" if s["running"] else "STOPPED"
        health = "healthy" if s["healthy"] else ("unhealthy" if s["running"] else "—")
        last = f"  last_used: {s['last_used']}" if s["last_used"] else ""
        port_str = str(s["port"]) if s["port"] else "-"
        lines.append(f"  {name:<12} :{port_str:<5} {status:<8} {health}{last}")

    lines.append("")

    # Postgres
    pg = info["postgres"]
    if pg["reachable"]:
        lines.append(f"Postgres:  REACHABLE (:{pg['port']})")
    else:
        lines.append(f"Postgres:  UNREACHABLE (:{pg['port']}) — {pg['error']}")

    return "\n".join(lines)


# FUNCTIONS

def _lock_status() -> dict:
    data = read_lock()
    if data is None:
        return {"held": False, "data": None, "stale_heartbeat": False}
    hb = data.get("heartbeat", data.get("started_at"))
    stale = False
    if hb:
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(hb)).total_seconds()
        stale = age > 60
    return {"held": True, "data": data, "stale_heartbeat": stale}


def _server_status() -> dict:
    """Bridge to Box server_manager.status() — adds last_used (state-file mtime) per server."""
    box = box_status()  # {name: {running, pid, port, healthy}}
    result = {}
    for name, info in box.items():
        last_used_secs = _state_file_idle(info["port"]) if info["port"] else None
        result[name] = {
            "running": info["running"],
            "healthy": info["healthy"],
            "port": info["port"],
            "last_used": _format_last_used(last_used_secs),
        }
    return result


# Seconds since last inference activity, derived from state-file mtime; None on missing file
def _state_file_idle(port: int) -> float | None:
    try:
        return time.time() - (TIMESTAMP_DIR / f"server-port-{port}.json").stat().st_mtime
    except (FileNotFoundError, OSError):
        return None


def _postgres_status() -> dict:
    from .db import POSTGRES_PORT
    import psycopg2
    from .db import POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST, port=POSTGRES_PORT,
            user=POSTGRES_USER, password=POSTGRES_PASSWORD,
            dbname=POSTGRES_DB, connect_timeout=2,
        )
        conn.close()
        return {"reachable": True, "port": POSTGRES_PORT, "error": None}
    except Exception as e:
        return {"reachable": False, "port": POSTGRES_PORT, "error": str(e)}


def _elapsed(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
        secs = int((datetime.now(timezone.utc) - dt).total_seconds())
        if secs < 0:
            secs = 0
        mins, s = divmod(secs, 60)
        hrs, m = divmod(mins, 60)
        if hrs:
            return f"{hrs}h{m:02d}m"
        if mins:
            return f"{mins}m{s:02d}s"
        return f"{secs}s"
    except Exception:
        return "?"


def _format_last_used(secs: float | None) -> str:
    """Format seconds-since-last-activity. None or negative → empty string."""
    if secs is None or secs < 0:
        return ""
    secs = int(secs)
    mins, s = divmod(secs, 60)
    hrs, m = divmod(mins, 60)
    if hrs:
        return f"{hrs}h{m:02d}m ago"
    if mins:
        return f"{mins}m{s:02d}s ago"
    return f"{secs}s ago"
