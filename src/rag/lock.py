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
_FLOCK_FILE = LOCK_DIR / "rag.flock"
_DATA_FILE = LOCK_DIR / "rag.lock"

_HEARTBEAT_INTERVAL = 30

_INDEXING_COMMANDS: frozenset = frozenset({"index", "update_docs"})


class LockBusyError(RuntimeError):
    pass


# ORCHESTRATOR

class acquire:

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
            logger.warning("lock data file cleanup failed: %s", e)
        fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
        self._fd.close()


# FUNCTIONS

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
        doc_str = f"{prog.get('done', 0)}/{prog.get('total', 0)} docs"
        if prog.get("chunks_total"):
            doc_str += f" · {prog.get('chunks_done', 0)}/{prog['chunks_total']} chunks"
        prog_str = f", progress {doc_str} ({prog.get('current_document', '?')})"
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
