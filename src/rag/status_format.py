# INFRASTRUCTURE
from datetime import datetime, timezone


# ORCHESTRATOR

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


def _elapsed(iso: str) -> str:
    secs = int((datetime.now(timezone.utc) - datetime.fromisoformat(iso)).total_seconds())
    return format_duration(secs)


def format_duration(secs: int) -> str:
    mins, s = divmod(secs, 60)
    hrs, m = divmod(mins, 60)
    if hrs:
        return f"{hrs}h{m:02d}m"
    if mins:
        return f"{mins}m{s:02d}s"
    return f"{secs}s"


def _format_servers(servers: dict) -> list[str]:
    lines = ["Servers:"]
    for name, s in servers.items():
        status = "RUNNING" if s["running"] else "STOPPED"
        health = "healthy" if s["healthy"] else ("unhealthy" if s["running"] else "—")
        last = _format_last_used(s["last_used_secs"])
        port_str = str(s["port"]) if s["port"] else "-"
        lines.append(f"  {name:<12} :{port_str:<5} {status:<8} {health}{last}")
    return lines


def _format_last_used(secs: float | None) -> str:
    if secs is None:
        return ""
    return f"  last_used: {format_duration(int(secs))} ago"


def _format_postgres(pg: dict) -> list[str]:
    if pg["reachable"]:
        return [f"Postgres:  REACHABLE (:{pg['port']})"]
    return [f"Postgres:  UNREACHABLE (:{pg['port']}) — {pg['error']}"]
