# INFRASTRUCTURE

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from strand_runner import load_rag, run_strands


# ORCHESTRATOR

def run_all() -> None:
    run_strands([
        test_dead_pid_lock_is_removed_and_logged,
    ])


# FUNCTIONS

def _dead_pid() -> int:
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()
    return proc.pid


def test_dead_pid_lock_is_removed_and_logged(workdir: Path) -> None:
    lock = load_rag("lock")
    lock.LOCK_DIR.mkdir(parents=True, exist_ok=True)
    pid = _dead_pid()
    lock._DATA_FILE.write_text(json.dumps({"pid": pid}))
    assert lock.cleanup_stale() is True
    assert not lock._DATA_FILE.exists()
    for handler in lock.logger.handlers:
        handler.flush()
    log_text = (workdir / "src" / "rag" / "logs" / "lock.log").read_text()
    assert f"stale lock removed: pid {pid} is not running" in log_text, log_text


if __name__ == "__main__":
    run_all()
