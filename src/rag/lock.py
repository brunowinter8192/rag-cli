# INFRASTRUCTURE
import fcntl
import json
import os
import threading
from contextlib import contextmanager
from datetime import datetime, timezone

from src.rag.config import LOCK_DIR
from src.rag.log_setup import get_logger

logger = get_logger("lock")

_FLOCK_FILE = LOCK_DIR / "rag.flock"
_DATA_FILE = LOCK_DIR / "rag.lock"

_HEARTBEAT_INTERVAL = 30

_INDEXING_COMMANDS: frozenset = frozenset({"index", "update_docs"})


class LockBusyError(RuntimeError):
    pass


# ORCHESTRATOR

@contextmanager
def acquire(command: str, args: dict):
    fd = take_flock()
    write_lock_record(command, args)
    stop_heartbeat = start_heartbeat()
    try:
        yield
    finally:
        release(fd, stop_heartbeat)


# FUNCTIONS

def take_flock():
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    cleanup_stale()
    fd = open(_FLOCK_FILE, "a")
    try:
        fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        fd.close()
        _raise_busy()
    return fd


def cleanup_stale() -> bool:
    data = read()
    if data is None:
        return False
    pid = data.get("pid")
    if pid is None:
        _DATA_FILE.unlink(missing_ok=True)
        return True
    try:
        os.kill(pid, 0)
        return False
    except ProcessLookupError:
        logger.info(f"stale lock removed: pid {pid} is not running")
        _DATA_FILE.unlink(missing_ok=True)
        return True


def read() -> dict | None:
    try:
        return json.loads(_DATA_FILE.read_text())
    except FileNotFoundError:
        return None


def _raise_busy() -> None:
    info = read()
    if info is None:
        raise LockBusyError("rag busy: lock held but details unavailable")
    started = datetime.fromisoformat(info["started_at"])
    elapsed = int((datetime.now(timezone.utc) - started).total_seconds())
    mins, secs = divmod(elapsed, 60)
    elapsed_str = f"{mins}m{secs:02d}s" if mins else f"{secs}s"
    prog = info["progress"]
    prog_str = ""
    if prog:
        doc_str = f"{prog['done']}/{prog['total']} docs"
        if prog.get("chunks_total"):
            doc_str += f" · {prog['chunks_done']}/{prog['chunks_total']} chunks"
        prog_str = f", progress {doc_str} ({prog['current_document']})"
    collection = info.get("args", {}).get("collection") or info.get("args", {}).get("input", "?")
    raise LockBusyError(
        f"rag busy: {info['command']} running"
        f" (collection: {collection})"
        f" since {elapsed_str} ago, PID {info['pid']}{prog_str}"
    )


def write_lock_record(command: str, args: dict) -> None:
    data = {
        "pid": os.getpid(),
        "command": command,
        "kind": "index" if command in _INDEXING_COMMANDS else "query",
        "args": args,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "progress": {},
        "heartbeat": datetime.now(timezone.utc).isoformat(),
    }
    _write_atomic(data)


def _write_atomic(data: dict) -> None:
    tmp = _DATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.rename(_DATA_FILE)


def start_heartbeat() -> threading.Event:
    stop_event = threading.Event()
    threading.Thread(target=heartbeat_loop, args=(stop_event,), daemon=True).start()
    return stop_event


def heartbeat_loop(stop_event: threading.Event) -> None:
    while not stop_event.wait(_HEARTBEAT_INTERVAL):
        heartbeat()


def heartbeat() -> None:
    data = read()
    if data is None:
        return
    data["heartbeat"] = datetime.now(timezone.utc).isoformat()
    _write_atomic(data)


def release(fd, stop_heartbeat: threading.Event) -> None:
    stop_heartbeat.set()
    _DATA_FILE.unlink(missing_ok=True)
    fcntl.flock(fd.fileno(), fcntl.LOCK_UN)
    fd.close()


def update_progress(
    done: int,
    total: int,
    current_document: str,
    collection: str | None = None,
    chunks_done: int | None = None,
    chunks_total: int | None = None,
) -> None:
    data = read()
    if data is None:
        return
    progress = {"done": done, "total": total, "current_document": current_document, "collection": collection}
    if chunks_done is not None:
        progress["chunks_done"] = chunks_done
    if chunks_total is not None:
        progress["chunks_total"] = chunks_total
    data["progress"] = progress
    data["heartbeat"] = datetime.now(timezone.utc).isoformat()
    _write_atomic(data)
