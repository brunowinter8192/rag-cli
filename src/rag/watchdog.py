# INFRASTRUCTURE
import json
import os
import signal
import subprocess
import sys
import time

from . import error_log
from .server_utils import (
    TIMESTAMP_DIR, IDLE_TIMEOUT, WATCHDOG_INTERVAL, WATCHDOG_PID_FILE, RAG_ROOT,
    _pid_alive, _check_health_port, pgrep_llama_server, _stop_by_state,
)
from .log_setup import get_logger

logger = get_logger("watchdog")


# FUNCTIONS

def _ensure_watchdog_process() -> None:
    if WATCHDOG_PID_FILE.exists():
        try:
            pid = int(WATCHDOG_PID_FILE.read_text().strip())
            os.kill(pid, 0)
            return
        except (ProcessLookupError, ValueError, OSError):
            pass
    WATCHDOG_PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.Popen(
        [sys.executable, '-m', 'src.rag.watchdog_main'],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=str(RAG_ROOT),
    )
    WATCHDOG_PID_FILE.write_text(str(p.pid))
    logger.info(f"Watchdog process spawned (PID {p.pid}, idle timeout: {IDLE_TIMEOUT}s)")


def _watchdog_loop() -> None:
    _purge_orphans()
    while True:
        time.sleep(WATCHDOG_INTERVAL)
        _watchdog_tick()


def _watchdog_tick() -> None:
    _purge_orphans()
    now = time.time()
    for state_file in TIMESTAMP_DIR.glob("server-port-*.json"):
        try:
            state = json.loads(state_file.read_text())
        except (json.JSONDecodeError, FileNotFoundError, OSError):
            continue
        pid, port = state["pid"], state["port"]
        if not _pid_alive(pid):
            name = state.get("name") or f"port-{port}"
            error_log.write(name, "watchdog_unlinked_dead",
                            f"state file claimed PID {pid} on port {port} but process is dead — auto-unlinking stale state",
                            caller="watchdog", pid=pid, port=port,
                            state_file=str(state_file))
            state_file.unlink(missing_ok=True)
            continue
        if not _check_health_port(port):
            continue
        idle = now - state_file.stat().st_mtime
        if idle > IDLE_TIMEOUT:
            label = state.get("name") or f"port-{port}"
            logger.info(f"Watchdog: {label} idle {idle:.0f}s, stopping")
            _stop_by_state(state, state_file,
                           caller="watchdog",
                           reason=f"idle {idle:.0f}s exceeds IDLE_TIMEOUT={IDLE_TIMEOUT}s")


def _purge_orphans() -> None:
    registered_pids: set[int] = set()
    for sf in TIMESTAMP_DIR.glob("server-port-*.json"):
        try:
            registered_pids.add(json.loads(sf.read_text())["pid"])
        except (json.JSONDecodeError, FileNotFoundError, KeyError, OSError):
            continue
    live_pids = set(pgrep_llama_server())
    orphan_pids = live_pids - registered_pids
    if not orphan_pids:
        return
    n_orphans = len(orphan_pids)
    for pid in orphan_pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    deadline = time.time() + 5.0
    while time.time() < deadline:
        time.sleep(0.5)
        still = {p for p in orphan_pids if _pid_alive(p)}
        if not still:
            break
        orphan_pids = still
    sigkilled: list[int] = []
    for pid in orphan_pids:
        try:
            os.kill(pid, signal.SIGKILL)
            sigkilled.append(pid)
        except ProcessLookupError:
            pass
    logger.info(f"Watchdog purge: killed {n_orphans} orphan llama-server PID(s)")
    error_log.write("orphan", "watchdog_killed_orphan",
                    f"purge killed {n_orphans} unregistered llama-server PID(s)",
                    caller="watchdog", n_pids=n_orphans, sigkilled=sigkilled)
