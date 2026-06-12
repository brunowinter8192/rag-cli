# INFRASTRUCTURE
import json
import logging
import os
import signal
import socket
import subprocess
import time
from pathlib import Path

import httpx

from . import error_log

LOG_DIR = Path.home() / ".rag-locks" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
RAG_ROOT = Path(os.getenv("RAG_PROJECT_ROOT", str(Path(__file__).parent.parent.parent)))

logging.basicConfig(
    filename=LOG_DIR / "server_manager.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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

EMBEDDING_8B_PORT = int(os.getenv("EMBEDDING_PORT", "8081"))
EMBEDDING_06B_PORT = int(os.getenv("EMBEDDING_06B_PORT", "8084"))
RERANKER_06B_PORT = int(os.getenv("RERANKER_PORT", "8082"))
RERANKER_8B_PORT = int(os.getenv("RERANKER_8B_PORT", "8085"))
GENERATOR_4B_PORT = int(os.getenv("GENERATOR_PORT", "8086"))
SPLADE_PORT = int(os.getenv("SPLADE_PORT", "8083"))

# Insertion order matters: when client calls find_server_url("embedding") and
# multiple variants are running, the FIRST matching entry in iteration order
# wins. Keep the canonical default for each class FIRST.
#
# default=True → started by `rag-cli server start` without args + by ensure_ready
#                for search/index workflows. Non-default variants are visible as
#                presets but only start when explicitly named.
SERVERS = {
    "embedding-8b": {
        "default_port": EMBEDDING_8B_PORT,
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
        "default_port": EMBEDDING_06B_PORT,
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
        "default_port": RERANKER_06B_PORT,
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
        "default_port": RERANKER_8B_PORT,
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
        "default_port": GENERATOR_4B_PORT,
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
        "default_port": SPLADE_PORT,
        "model_path": SPLADE_MODEL,
        "mode": "splade",
        "type": "uvicorn",
        "uvicorn_app": "src.rag.splade_server:app",
        "timeout": 60,
        # splade is used by NEITHER indexing (index_json_workflow is dense-only; sparse
        # stays NULL) NOR retrieval (no search/fusion path references sparse_embedding).
        # Only backfill-splade uses it, via ensure_ready("splade") direct-preset path.
        # Empty required_for → ensure_ready("index"/"search") will NOT auto-start it.
        "required_for": [],
        "default": True,
        "exclusive_with": [],
    },
}

# Preset names — arbitrary starts may not collide with these
_PRESET_NAMES: frozenset[str] = frozenset(SERVERS.keys())

# Map llama-server mode → external class name used by find_server_url() prefix-match.
# Modes that match their class name (embedding, splade) need no entry here.
_MODE_TO_CLASS: dict[str, str] = {
    "rerank": "reranker",
    "generate": "generator",
}

# Map class-name (embedding / reranker / splade / generator) → list of preset variant
# names, in default-first order. Used by find_server_url() prefix-match for backward
# compatibility with client calls find_server_url("embedding") etc.
_CLASS_MAP: dict[str, list[str]] = {}
for _n, _c in SERVERS.items():
    _CLASS_MAP.setdefault(_MODE_TO_CLASS.get(_c["mode"], _c["mode"]), []).append(_n)
# splade/embedding class names match their mode already; keep insertion order = default first


# FUNCTIONS

# Find the first PID listening on a port; returns None if port is free
def find_pid_on_port(port: int) -> int | None:
    pids = find_all_pids_on_port(port)
    return pids[0] if pids else None


# Find all PIDs listening on a port (-sTCP:LISTEN excludes outbound connectors
# that share the port number — prevents killing proxy/client processes on stop)
def find_all_pids_on_port(port: int) -> list[int]:
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}", "-sTCP:LISTEN"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return [int(p) for p in result.stdout.strip().split("\n") if p.strip()]
    except Exception as e:
        logging.warning(f"PID lookup failed: {e}")
    return []


# Return PIDs of all running llama-server processes via pgrep -x (exact comm match)
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


# Health check by port (no SERVERS lookup — works for preset and arbitrary servers)
# Retries on transient failure: callers may take destructive action (stop+restart)
# on a False return — a single httpx timeout (GPU busy, network hiccup) must not
# trigger that. Default: 3 attempts (2 retries) with 300ms backoff. Total worst
# case ~6.6s on full failure.
def _check_health_port(port: int, retries: int = 2, backoff_s: float = 0.3) -> bool:
    for attempt in range(retries + 1):
        try:
            if httpx.get(f"http://localhost:{port}/health", timeout=2.0).status_code == 200:
                return True
        except Exception:
            pass
        if attempt < retries:
            time.sleep(backoff_s)
    return False


# SIGTERM → wait → SIGKILL a server described by its state dict; unlinks state file.
# caller + reason are LIFECYCLE EVIDENCE: every kill of a managed process must leave
# a trail in error_log (server-name, port, pid, kill-method, who-asked, why).
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


# Return True if the process is alive (os.kill(pid, 0) succeeds)
def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


# OS-assigned free port via socket(0)+bind+close
def _allocate_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


# Return default_port if free, else allocate dynamic; None → always dynamic
def _resolve_port(default_port: int | None) -> int:
    if default_port is None:
        return _allocate_port()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', default_port))
            return default_port
    except OSError:
        dynamic = _allocate_port()
        logging.info(f"Default port {default_port} busy, using dynamic port {dynamic}")
        return dynamic


# Write ~/.rag-locks/server-port-{port}.json with box state immediately after Popen
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


# Bump state-file mtime to register activity; no-op if file was just unlinked (race: watchdog)
def _touch_state_file(port: int) -> None:
    try:
        os.utime(TIMESTAMP_DIR / f"server-port-{port}.json", None)
    except FileNotFoundError:
        logging.debug(f"_touch_state_file: port {port} state file gone (watchdog race), skipping")


# Remove state file for a port; safe if never written or already gone.
# caller + reason are LIFECYCLE EVIDENCE — every state-file removal logged
# so any future "where did my server go?" investigation has a starting point.
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
