# INFRASTRUCTURE
import subprocess
import time
from pathlib import Path

from src.rag import error_log
from src.rag.config import LLAMA_SERVER_PATH, RAG_ROOT, SERVER_LOG_DIR
from src.rag.log_setup import get_logger
from src.rag.server_utils import (
    check_health_port, find_pid_on_port, unlink_state_file, write_state_file,
)

logger = get_logger("server_launch")

MODE_FLAGS: dict[str, str] = {
    "embedding": "--embedding",
    "rerank": "--rerank",
}


# FUNCTIONS

def build_llama_cmd(model_path: str, port: int, mode: str, extra_flags: list[str]) -> list[str]:
    cmd = [LLAMA_SERVER_PATH, "-m", model_path]
    if mode in MODE_FLAGS:
        cmd.append(MODE_FLAGS[mode])
    cmd.extend(["--host", "0.0.0.0", "--port", str(port), *extra_flags])
    return cmd


def build_uvicorn_cmd(uvicorn_app: str, port: int) -> list[str]:
    return [
        str(RAG_ROOT / "venv/bin/python"), "-m", "uvicorn",
        uvicorn_app, "--host", "0.0.0.0", "--port", str(port),
    ]


def launch(
    cmd: list[str], cwd: str | None, log_path: Path, port: int, model_path: str,
    model_name: str, mode: str, name: str | None, timeout: int, label: str, caller: str,
) -> bool:
    SERVER_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_fh = open(log_path, "w")
    proc = subprocess.Popen(cmd, stdout=log_fh, stderr=subprocess.STDOUT, cwd=cwd)
    log_fh.close()

    write_state_file(
        pid=proc.pid, port=port,
        model_path=model_path, model_name=model_name,
        mode=mode, name=name,
        log_path=str(log_path),
    )

    return wait_for_health(
        proc=proc, port=port,
        model_path=model_path, model_name=model_name,
        mode=mode, name=name, log_path=str(log_path),
        timeout=timeout, label=label, caller=caller,
    )


def wait_for_health(
    proc: subprocess.Popen, port: int, model_path: str, model_name: str,
    mode: str, name: str | None, log_path: str, timeout: int, label: str, caller: str,
) -> bool:
    try:
        for i in range(timeout):
            time.sleep(1)
            if check_health_port(port):
                actual_pid = find_pid_on_port(port)
                if actual_pid is not None and actual_pid != proc.pid:
                    write_state_file(pid=actual_pid, port=port, model_path=model_path,
                                     model_name=model_name, mode=mode, name=name, log_path=log_path)
                final_pid = actual_pid or proc.pid
                logger.info(f"{label} started on port {port} (PID {final_pid}) after {i + 1}s")
                error_log.write(label, "start_succeeded", f"{label} healthy on port {port} after {i + 1}s",
                                caller=caller, pid=final_pid, port=port, elapsed_s=i + 1)
                return True
        raise RuntimeError(f"Failed to start {label} on port {port} after {timeout}s")
    except Exception:
        unlink_state_file(port, caller=caller,
                          reason=f"{caller}({label}, port={port}) failed: did not become healthy in {timeout}s")
        raise
