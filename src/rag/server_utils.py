# INFRASTRUCTURE
import json
import os
import signal
import socket
import subprocess
import time
from pathlib import Path

import httpx

from . import error_log
from .log_setup import get_logger

LOG_DIR = Path.home() / ".rag-locks" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
RAG_ROOT = Path(os.getenv("RAG_PROJECT_ROOT", str(Path(__file__).parent.parent.parent)))

logger = get_logger("server_utils")

IDLE_TIMEOUT = int(os.getenv("RAG_SERVER_IDLE_TIMEOUT", "3600"))
TIMESTAMP_DIR = Path.home() / ".rag-locks"
WATCHDOG_INTERVAL = 30
WATCHDOG_PID_FILE = Path.home() / ".rag-locks" / "watchdog.pid"

LLAMA_SERVER_PATH = os.getenv("LLAMA_SERVER_PATH", str(RAG_ROOT / "llama.cpp/build/bin/llama-server"))
EMBEDDING_8B_MODEL_PATH = os.getenv("EMBEDDING_MODEL_PATH", str(RAG_ROOT / "models/Qwen3-Embedding-8B-Q8_0.gguf"))
EMBEDDING_06B_MODEL_PATH = os.getenv("EMBEDDING_06B_MODEL_PATH", str(RAG_ROOT / "models/Qwen3-Embedding-0.6B-Q8_0.gguf"))
RERANKER_06B_MODEL_PATH = os.getenv("RERANKER_MODEL_PATH", str(RAG_ROOT / "models/qwen3-reranker-0.6b-q8_0.gguf"))
RERANKER_8B_MODEL_PATH = os.getenv("RERANKER_8B_MODEL_PATH", str(RAG_ROOT / "models/Qwen3-Reranker-8B-Q8_0.gguf"))
GENERATOR_4B_MODEL_PATH = os.getenv("GENERATOR_MODEL_PATH", str(RAG_ROOT / "models/Qwen3-4B-Instruct-2507-Q8_0.gguf"))
SPLADE_MODEL = "naver/splade-v3"

SERVERS = {
    "embedding-8b": {
        "model_path": EMBEDDING_8B_MODEL_PATH,
        "mode": "embedding",
        "type": "llama",
        "extra_flags": ["-ngl", "99", "-c", "2048", "-np", "1", "-b", "4096", "-ub", "4096"],
        "timeout": 90,
        "required_for": ["search", "index"],
        "default": True,
        "exclusive_with": ["embedding-0.6b"],
    },
    "embedding-0.6b": {
        "model_path": EMBEDDING_06B_MODEL_PATH,
        "mode": "embedding",
        "type": "llama",
        "extra_flags": ["-ngl", "99", "-c", "2048", "-np", "1", "-b", "4096", "-ub", "4096"],
        "timeout": 90,
        "required_for": ["search", "index"],
        "default": False,
        "exclusive_with": ["embedding-8b"],
    },
    "reranker-0.6b": {
        "model_path": RERANKER_06B_MODEL_PATH,
        "mode": "rerank",
        "type": "llama",
        "extra_flags": ["-ngl", "99", "-c", "32768", "-np", "1", "-b", "4096", "-ub", "4096"],
        "timeout": 90,
        "required_for": ["rerank"],
        "default": True,
        "exclusive_with": ["reranker-8b"],
    },
    "reranker-8b": {
        "model_path": RERANKER_8B_MODEL_PATH,
        "mode": "rerank",
        "type": "llama",
        "extra_flags": ["-ngl", "99", "-c", "32768", "-np", "1", "-b", "4096", "-ub", "4096"],
        "timeout": 90,
        "required_for": ["rerank"],
        "default": False,
        "exclusive_with": ["reranker-0.6b"],
    },
    "generator-4b": {
        "model_path": GENERATOR_4B_MODEL_PATH,
        "mode": "generate",
        "type": "llama",
        "extra_flags": ["-ngl", "99", "-c", "8192", "-np", "1", "-b", "4096", "-ub", "4096"],
        "timeout": 90,
        "required_for": ["generate"],
        "default": False,
        "exclusive_with": [],
    },
    "splade": {
        "model_path": SPLADE_MODEL,
        "mode": "splade",
        "type": "uvicorn",
        "uvicorn_app": "src.rag.splade_server:app",
        "timeout": 60,
        "required_for": [],
        "default": True,
        "exclusive_with": [],
    },
}

_PRESET_NAMES: frozenset[str] = frozenset(SERVERS.keys())

_MODE_TO_CLASS: dict[str, str] = {
    "rerank": "reranker",
    "generate": "generator",
}

_CLASS_MAP: dict[str, list[str]] = {}
for _n, _c in SERVERS.items():
    _CLASS_MAP.setdefault(_MODE_TO_CLASS.get(_c["mode"], _c["mode"]), []).append(_n)


# FUNCTIONS

def find_pid_on_port(port: int) -> int | None:
    pids = find_all_pids_on_port(port)
    return pids[0] if pids else None


def find_all_pids_on_port(port: int) -> list[int]:
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}", "-sTCP:LISTEN"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return [int(p) for p in result.stdout.strip().split("\n") if p.strip()]
    except Exception as e:
        logger.warning(f"PID lookup failed: {e}")
    return []


def pgrep_llama_server() -> list[int]:
    try:
        result = subprocess.run(
            ["pgrep", "-x", "llama-server"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return [int(p) for p in result.stdout.strip().split("\n") if p.strip()]
    except Exception:
        pass
    return []


def _check_health_port(port: int) -> bool:
    try:
        return httpx.get(f"http://localhost:{port}/health", timeout=2.0).status_code == 200
    except Exception:
        return False


def _stop_by_state(state: dict, state_file: Path, *, caller: str, reason: str) -> None:
    pid, port = state["pid"], state["port"]
    name = state.get("name") or f"port-{port}"

    error_log.write(name, "stop_initiated", reason,
                    pid=pid, port=port, caller=caller, state_file=str(state_file))

    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        error_log.write(name, "stop_completed", "process already dead at SIGTERM",
                        pid=pid, port=port, caller=caller, kill_method="not_required")
        state_file.unlink(missing_ok=True)
        return

    for _ in range(10):
        time.sleep(0.5)
        if not _pid_alive(pid):
            error_log.write(name, "stop_completed", "exited cleanly after SIGTERM",
                            pid=pid, port=port, caller=caller, kill_method="sigterm")
            state_file.unlink(missing_ok=True)
            return

    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    error_log.write(name, "stop_completed", "force-killed after 5s SIGTERM grace expired",
                    pid=pid, port=port, caller=caller, kill_method="sigkill")
    state_file.unlink(missing_ok=True)


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def _allocate_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def _resolve_port(port: int | None) -> int:
    if port is None:
        return _allocate_port()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', port))
            return port
    except OSError:
        dynamic = _allocate_port()
        logger.info(f"Port {port} busy, using dynamic port {dynamic}")
        return dynamic


def _write_state_file(*, pid: int, port: int, model_path: str, model_name: str,
                      mode: str, name: str | None, log_path: str) -> Path:
    state = {
        "pid": pid, "port": port,
        "model_path": model_path, "model_name": model_name,
        "mode": mode,
        "start_time": time.time(),
        "log_path": log_path,
        "name": name,
    }
    path = TIMESTAMP_DIR / f"server-port-{port}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))
    return path


def _touch_state_file(port: int) -> None:
    try:
        os.utime(TIMESTAMP_DIR / f"server-port-{port}.json", None)
    except FileNotFoundError:
        logger.debug(f"_touch_state_file: port {port} state file gone (watchdog race), skipping")


def _unlink_state_file(port: int, *, caller: str, reason: str) -> None:
    path = TIMESTAMP_DIR / f"server-port-{port}.json"
    if path.exists():
        try:
            state = json.loads(path.read_text())
            name = state.get("name") or f"port-{port}"
            pid = state.get("pid")
        except (json.JSONDecodeError, OSError):
            name = f"port-{port}"
            pid = None
        error_log.write(name, "state_unlinked", reason,
                        pid=pid, port=port, caller=caller, state_file=str(path))
    path.unlink(missing_ok=True)
