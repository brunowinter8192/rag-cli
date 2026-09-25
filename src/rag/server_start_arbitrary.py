# INFRASTRUCTURE
import json
from pathlib import Path

from src.rag import error_log
from src.rag.config import LLAMA_SERVER_PATH, LOCK_DIR, SERVER_LOG_DIR
from src.rag.log_setup import get_logger
from src.rag.server_launch import MODE_FLAGS, build_llama_cmd, launch
from src.rag.server_state import iter_state_files
from src.rag.server_utils import PRESET_NAMES, check_health_port, find_pid_on_port, pid_alive, resolve_port

logger = get_logger("server_start_arbitrary")

ARBITRARY_LAUNCH_FLAGS = ["-ngl", "99"]
ARBITRARY_TIMEOUT = 90


# ORCHESTRATOR

def start_arbitrary(model_path: str, port: int | None, mode: str, name: str | None = None) -> bool:
    validate_mode(mode)
    if name is not None:
        check_name_collision(name)
    port = resolve_port(port)
    label = reclaim_or_clear_port_state(port)
    if label:
        return report_already_running(label, port)
    require_free_port(port)
    require_llama_binary()
    cmd = build_llama_cmd(model_path, port, mode, ARBITRARY_LAUNCH_FLAGS)
    model_name = Path(model_path).stem
    label_for_log = name or f"port-{port}"
    record_start(label_for_log, model_name, model_path, port, mode)
    return launch(cmd, None, SERVER_LOG_DIR / f"llama-port-{port}.log", port, model_path, model_name,
                  mode, name, ARBITRARY_TIMEOUT, label_for_log, "start_arbitrary")


# FUNCTIONS

def validate_mode(mode: str) -> None:
    if mode not in MODE_FLAGS:
        raise ValueError(
            f"mode must be 'embedding' or 'rerank' for arbitrary start (got '{mode}'). "
            f"Use the 'splade' preset for SPLADE."
        )


def reclaim_or_clear_port_state(port: int) -> str | None:
    state_file = LOCK_DIR / f"server-port-{port}.json"
    if not state_file.exists():
        return None
    existing = json.loads(state_file.read_text())
    if pid_alive(existing["pid"]) and check_health_port(port):
        return existing.get("name") or f"port-{port}"
    state_file.unlink(missing_ok=True)
    return None


def require_free_port(port: int) -> None:
    pid = find_pid_on_port(port)
    if pid is not None:
        raise RuntimeError(f"Port {port} in use by PID {pid} (not managed by box). Stop it first.")


def require_llama_binary() -> None:
    binary = Path(LLAMA_SERVER_PATH)
    if not binary.exists():
        raise RuntimeError(
            f"llama-server not found at {binary}. Build it or set LLAMA_SERVER_PATH."
        )


def record_start(label: str, model_name: str, model_path: str, port: int, mode: str) -> None:
    logger.info(f"Starting arbitrary {mode} server on port {port} ({model_name})...")
    error_log.write(label, "start_initiated",
                    f"start_arbitrary({label}, port={port}) called",
                    caller="start_arbitrary", model_path=model_path, mode=mode)


def check_name_collision(name: str) -> None:
    if name in PRESET_NAMES:
        raise ValueError(
            f"Name {name!r} is a preset name; use `rag-cli server start {name}` instead."
        )
    for _, state in iter_state_files():
        if state.get("name") == name and pid_alive(state["pid"]):
            raise ValueError(
                f"Name {name!r} already in use by server on port {state['port']}. "
                f"Choose a different --name or stop the existing server first."
            )


def report_already_running(label: str, port: int) -> bool:
    logger.info(f"Arbitrary start: {label} already running on port {port}")
    return False
