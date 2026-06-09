# INFRASTRUCTURE
import fcntl
import json
import logging
import os
import pathlib
import threading
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

LOCK_DIR = pathlib.Path.home() / ".rag-locks"
_FLOCK_FILE = LOCK_DIR / "rag.flock"   # held open while lock is active
_DATA_FILE = LOCK_DIR / "rag.lock"     # JSON details (written atomically)

# Auto-heartbeat interval — long-running operations (indexing/embedding) don't
# call heartbeat()/update_progress() between steps; without periodic updates the
# heartbeat goes stale and `rag-cli status` falsely reports the process as hung.
_HEARTBEAT_INTERVAL = 30

# Commands that perform embedding/indexing; get kind="index" in the lock JSON.
# All other commands (search, list, read, delete) get kind="query".
_INDEXING_COMMANDS: frozenset = frozenset({"index", "update_docs"})


class LockBusyError(RuntimeError):
    pass


# ORCHESTRATOR

class acquire:
    """Context manager that acquires the global RAG lock at construction time.

    Raises LockBusyError immediately if the lock is held by another process.
    Usage:
        try:
            lock_ctx = lock.acquire("index-dir", {"collection": "..."})
        except lock.LockBusyError as e:
            sys.exit(f"Error: {e}")
        with lock_ctx:
            # do work
    """

    def __init__(self, command: str, args: dict):
        LOCK_DIR.mkdir(parents=True, exist_ok=True)
        cleanup_stale()
        self._fd = open(_FLOCK_FILE, "a")
        try:
            fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self._fd.close()
            _raise_busy()
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
        # Auto-heartbeat thread — keeps heartbeat fresh during long indexing loops
        # without requiring callers to remember explicit heartbeat() calls.
        # Daemon thread → dies with the process if __exit__ is skipped.
        self._stop_heartbeat = threading.Event()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True
        )
        self._heartbeat_thread.start()

    def _heartbeat_loop(self) -> None:
        while not self._stop_heartbeat.wait(_HEARTBEAT_INTERVAL):
            heartbeat()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._stop_heartbeat.set()
        try:
            _DATA_FILE.unlink(missing_ok=True)
        except OSError as e:
            # Filesystem race during cleanup (file already removed, perm change)
            # is non-fatal — process is exiting the lock context regardless.
            logger.warning("lock data file cleanup failed: %s", e)
        fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
        self._fd.close()


# FUNCTIONS

def update_progress(done: int, total: int, current_document: str, collection: str | None = None) -> None:
    data = read()
    if data is None:
        return
    data["progress"] = {"done": done, "total": total, "current_document": current_document, "collection": collection}
    data["heartbeat"] = datetime.now(timezone.utc).isoformat()
    _write_atomic(data)


def heartbeat() -> None:
    data = read()
    if data is None:
        return
    data["heartbeat"] = datetime.now(timezone.utc).isoformat()
    _write_atomic(data)


def read() -> dict | None:
    try:
        return json.loads(_DATA_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def cleanup_stale() -> bool:
    """Remove lockfile if the owning PID is no longer alive. Returns True if cleaned up."""
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
        _DATA_FILE.unlink(missing_ok=True)
        return True
    except PermissionError:
        return False


def _raise_busy() -> None:
    info = read()
    if info is None:
        raise LockBusyError("rag busy: lock held but details unavailable")
    started = datetime.fromisoformat(info["started_at"])
    elapsed = int((datetime.now(timezone.utc) - started).total_seconds())
    mins, secs = divmod(elapsed, 60)
    elapsed_str = f"{mins}m{secs:02d}s" if mins else f"{secs}s"
    prog = info.get("progress") or {}
    prog_str = ""
    if prog:
        prog_str = f", progress {prog['done']}/{prog['total']} ({prog['current_document']})"
    collection = info.get("args", {}).get("collection") or info.get("args", {}).get("input", "?")
    raise LockBusyError(
        f"rag busy: {info['command']} running"
        f" (collection: {collection})"
        f" since {elapsed_str} ago, PID {info['pid']}{prog_str}"
    )


def _write_atomic(data: dict) -> None:
    tmp = _DATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.rename(_DATA_FILE)
