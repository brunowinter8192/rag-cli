# INFRASTRUCTURE

import os
import signal
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from strand_runner import load_rag, run_strands


# ORCHESTRATOR

def run_all() -> None:
    run_strands([
        test_dead_pid_file_is_logged_and_watchdog_respawned,
    ])


# FUNCTIONS

def test_dead_pid_file_is_logged_and_watchdog_respawned(workdir: Path) -> None:
    watchdog = load_rag("watchdog")
    dead_pid = _dead_pid()
    watchdog.WATCHDOG_PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    watchdog.WATCHDOG_PID_FILE.write_text(str(dead_pid))
    watchdog._ensure_watchdog_process()
    new_pid = int(watchdog.WATCHDOG_PID_FILE.read_text())
    try:
        assert new_pid != dead_pid
        for handler in watchdog.logger.handlers:
            handler.flush()
        log_text = (workdir / "src" / "rag" / "logs" / "watchdog.log").read_text()
        assert f"stale watchdog pid file: pid {dead_pid} is not running" in log_text, log_text
    finally:
        os.kill(new_pid, signal.SIGTERM)


def _dead_pid() -> int:
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()
    return proc.pid


if __name__ == "__main__":
    run_all()
