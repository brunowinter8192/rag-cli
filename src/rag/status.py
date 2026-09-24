# INFRASTRUCTURE
import time
from datetime import datetime, timezone

from .lock import read as read_lock
from .server_manager import TIMESTAMP_DIR, status as box_status


# ORCHESTRATOR

def gather() -> dict:
    return {
        "lock": _lock_status(),
        "servers": _server_status(),
        "postgres": _postgres_status(),
    }


def format_status(info: dict) -> str:
    lines = []
    lines.extend(_format_lock(info["lock"]))
    lines.append("")
    lines.extend(_format_servers(info["servers"]))
    lines.append("")
    lines.extend(_format_postgres(info["postgres"]))
    return "\n".join(lines)


# FUNCTIONS

def _format_lock(lock: dict) -> list[str]:
    if not lock["held"]:
        return ["Lock:    FREE"]
    d = lock["data"]
    elapsed_str = _elapsed(d["started_at"])
    heartbeat_str = _elapsed(d["heartbeat"])
    prog = d["progress"]
    prog_str = ""
    if prog:
        doc_str = f"{prog['done']}/{prog['total']} docs"
        if prog.get("chunks_total"):
            doc_str += f" · {prog['chunks_done']}/{prog['chunks_total']} chunks"
        prog_str = (
            f"\n         Progress: {doc_str}"
            f" — {prog['current_document']}"
        )
    stale_warn = ""
    if lock.get("stale_heartbeat"):
        stale_warn = " (!) heartbeat stale"
    return [
        f"Lock:    HELD by PID {d['pid']} ({d['command']}) "
        f"since {elapsed_str} ago"
        f" [heartbeat: {heartbeat_str}{stale_warn}]{prog_str}"
    ]


def _format_servers(servers: dict) -> list[str]:
    lines = ["Servers:"]
    for name, s in servers.items():
        status = "RUNNING" if s["running"] else "STOPPED"
        health = "healthy" if s["healthy"] else ("unhealthy" if s["running"] else "—")
        last = f"  last_used: {s['last_used']}" if s["last_used"] else ""
        port_str = str(s["port"]) if s["port"] else "-"
        lines.append(f"  {name:<12} :{port_str:<5} {status:<8} {health}{last}")
    return lines


def _format_postgres(pg: dict) -> list[str]:
    if pg["reachable"]:
        return [f"Postgres:  REACHABLE (:{pg['port']})"]
    return [f"Postgres:  UNREACHABLE (:{pg['port']}) — {pg['error']}"]


def _lock_status() -> dict:
    data = read_lock()
    if data is None:
        return {"held": False, "data": None, "stale_heartbeat": False}
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(data["heartbeat"])).total_seconds()
    stale = age > 60
    return {"held": True, "data": data, "stale_heartbeat": stale}


def _server_status() -> dict:
    box = box_status()
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


def _state_file_idle(port: int) -> float | None:
    return time.time() - (TIMESTAMP_DIR / f"server-port-{port}.json").stat().st_mtime


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
    except psycopg2.OperationalError as e:
        return {"reachable": False, "port": POSTGRES_PORT, "error": str(e)}


def _elapsed(iso: str) -> str:
    dt = datetime.fromisoformat(iso)
    secs = int((datetime.now(timezone.utc) - dt).total_seconds())
    mins, s = divmod(secs, 60)
    hrs, m = divmod(mins, 60)
    if hrs:
        return f"{hrs}h{m:02d}m"
    if mins:
        return f"{mins}m{s:02d}s"
    return f"{secs}s"


def _format_last_used(secs: float | None) -> str:
    if secs is None:
        return ""
    secs = int(secs)
    mins, s = divmod(secs, 60)
    hrs, m = divmod(mins, 60)
    if hrs:
        return f"{hrs}h{m:02d}m ago"
    if mins:
        return f"{mins}m{s:02d}s ago"
    return f"{secs}s ago"
