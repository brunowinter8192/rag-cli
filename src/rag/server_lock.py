# INFRASTRUCTURE
import fcntl
import json
import os
import pathlib
from datetime import datetime, timezone

LOCK_DIR = pathlib.Path.home() / ".rag-locks"


class ServerBusyError(RuntimeError):
    pass


# ORCHESTRATOR

class acquire:

    def __init__(self, name: str):
        LOCK_DIR.mkdir(parents=True, exist_ok=True)
        self._name = name
        self._flock_path = LOCK_DIR / f"rag-server-{name}.busy.flock"
        self._data_path = LOCK_DIR / f"rag-server-{name}.busy"
        self._fd = open(self._flock_path, "a")
        try:
            fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self._fd.close()
            _raise_busy(name, self._data_path)
        data = {
            "pid": os.getpid(),
            "cmd": f"rag-server-{name}",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        _write_atomic(self._data_path, data)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        try:
            self._data_path.unlink(missing_ok=True)
        except Exception:
            pass
        fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
        self._fd.close()


# FUNCTIONS

def _raise_busy(name: str, data_path: pathlib.Path) -> None:
    try:
        info = json.loads(data_path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        raise ServerBusyError(f"{name} busy: lock held but details unavailable")
    raise ServerBusyError(
        f"{name} busy: held by PID {info['pid']} ({info['cmd']}) since {info['started_at']}"
    )


def _write_atomic(data_path: pathlib.Path, data: dict) -> None:
    tmp = data_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data))
    tmp.rename(data_path)
