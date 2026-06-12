# INFRASTRUCTURE
import json
import logging
import subprocess
import time
from pathlib import Path

from . import error_log
from .server_utils import (
    SERVERS, _CLASS_MAP, _PRESET_NAMES, TIMESTAMP_DIR, LOG_DIR, RAG_ROOT,
    LLAMA_SERVER_PATH, _pid_alive, find_pid_on_port,
    _allocate_port, _check_health_port, _resolve_port, _stop_by_state,
    _write_state_file, _unlink_state_file,
)


# ORCHESTRATOR

# Return status of all servers: running, pid, port, healthy per server name
def status() -> dict[str, dict]:
    result = {}
    for name in SERVERS:
        url = find_server_url(name)
        if url:
            port = int(url.split(":")[-1])
            pid = find_pid_on_port(port)
            healthy = _check_health_port(port) if pid else False
        else:
            port = None
            pid = None
            healthy = False
        result[name] = {
            "running": pid is not None,
            "pid": pid,
            "port": port,
            "healthy": healthy,
        }
    return result


# Start a preset server; resolves port dynamically, writes state file immediately after Popen
def start(name: str) -> bool:
    if name not in SERVERS:
        raise ValueError(f"Unknown server: {name}. Available: {list(SERVERS.keys())}")

    cfg = SERVERS[name]
    error_log.write(name, "start_initiated", f"start({name}) called",
                    caller="start", model_path=cfg["model_path"])

    # Check for live state file with this name — single-instance enforcement
    for sf in sorted(TIMESTAMP_DIR.glob("server-port-*.json")):
        try:
            state = json.loads(sf.read_text())
        except (json.JSONDecodeError, FileNotFoundError, OSError):
            continue
        if state.get("name") == name and _pid_alive(state["pid"]):
            if _check_health_port(state["port"]):
                logging.info(f"{name} already running on port {state['port']} (PID {state['pid']})")
                return False
            # Alive but unhealthy → stop and restart on a fresh port
            logging.warning(f"{name} alive on port {state['port']} but unhealthy, stopping for restart")
            error_log.write(name, "single_instance_alive_replaced",
                            f"existing {name} alive on port {state['port']} (PID {state['pid']}) but unhealthy — replacing",
                            caller="start", existing_pid=state["pid"], existing_port=state["port"])
            _stop_by_state(state, sf,
                           caller="start",
                           reason=f"alive but _check_health_port({state['port']}) returned False at start-time")
            break

    port = _allocate_port()

    if cfg["type"] == "llama":
        binary = Path(LLAMA_SERVER_PATH)
        if not binary.exists():
            raise RuntimeError(
                f"Cannot start {name}: {binary} not found. "
                f"cd <RAG_ROOT> && ./start.sh"
            )
        cmd = _build_llama_cmd(cfg["model_path"], port, cfg["mode"], cfg["extra_flags"])
        log_path = LOG_DIR / f"llama-port-{port}.log"
        log_fh = open(log_path, "w")
        log_stderr = subprocess.STDOUT
        cwd = None
        model_name = Path(cfg["model_path"]).stem
    else:  # uvicorn (splade)
        venv_python = str(RAG_ROOT / "venv/bin/python")
        if not Path(venv_python).exists():
            raise RuntimeError(f"Cannot start {name}: {venv_python} not found.")
        cmd = _build_uvicorn_cmd(cfg["uvicorn_app"], port)
        log_path = LOG_DIR / "splade_server.log"
        log_fh = open(log_path, "w")
        log_stderr = subprocess.STDOUT
        cwd = str(RAG_ROOT)
        model_name = cfg["model_path"]

    logging.info(f"Starting {name} on port {port}...")
    proc = subprocess.Popen(cmd, stdout=log_fh, stderr=log_stderr, cwd=cwd)
    if log_fh is not subprocess.DEVNULL:
        log_fh.close()  # parent closes; child retains its fd copy

    _write_state_file(
        pid=proc.pid, port=port,
        model_path=cfg["model_path"], model_name=model_name,
        mode=cfg["mode"], name=name,
        log_path=str(log_path),
    )

    return _wait_for_health(
        proc=proc, port=port,
        model_path=cfg["model_path"], model_name=model_name,
        mode=cfg["mode"], name=name, log_path=str(log_path),
        timeout=cfg["timeout"], label=name, caller="start",
    )


# Stop a preset server; kills the PID recorded in the state file only.
# No port-based fallback — if no state file exists, the server is not running.
# This prevents killing unrelated processes that happen to share a port.
def stop(name: str) -> bool:
    if name not in SERVERS:
        raise ValueError(f"Unknown server: {name}. Available: {list(SERVERS.keys())}")

    for sf in sorted(TIMESTAMP_DIR.glob("server-port-*.json")):
        try:
            state = json.loads(sf.read_text())
        except (json.JSONDecodeError, FileNotFoundError, OSError):
            continue
        if state.get("name") == name:
            _stop_by_state(state, sf, caller="stop",
                           reason=f"user-requested stop({name})")
            return True

    logging.info(f"{name} not running (no state file)")
    return False


# Restart a server
def restart(name: str) -> bool:
    stop(name)
    return start(name)


# Start an arbitrary llama-server; port is optional (None → fully dynamic)
def start_arbitrary(model_path: str, port: int | None, mode: str, name: str | None = None) -> bool:
    if mode not in {"embedding", "rerank"}:
        raise ValueError(
            f"mode must be 'embedding' or 'rerank' for arbitrary start (got '{mode}'). "
            f"Use the 'splade' preset for SPLADE."
        )

    # Name collision check — must come before port resolution
    if name is not None:
        if name in _PRESET_NAMES:
            raise ValueError(
                f"Name {name!r} is a preset name; use `rag-cli server start {name}` instead."
            )
        for sf in TIMESTAMP_DIR.glob("server-port-*.json"):
            try:
                state = json.loads(sf.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            if state.get("name") == name and _pid_alive(state["pid"]):
                raise ValueError(
                    f"Name {name!r} already in use by server on port {state['port']}. "
                    f"Choose a different --name or stop the existing server first."
                )

    port = _resolve_port(port)

    # Check for existing managed server on this port
    state_file = TIMESTAMP_DIR / f"server-port-{port}.json"
    if state_file.exists():
        try:
            existing = json.loads(state_file.read_text())
            if _pid_alive(existing["pid"]) and _check_health_port(port):
                label = existing.get("name") or f"port-{port}"
                logging.info(f"Arbitrary start: {label} already running on port {port}")
                return False
        except (json.JSONDecodeError, KeyError, OSError):
            pass
        state_file.unlink(missing_ok=True)

    pid = find_pid_on_port(port)
    if pid is not None:
        raise RuntimeError(f"Port {port} in use by PID {pid} (not managed by box). Stop it first.")

    binary = Path(LLAMA_SERVER_PATH)
    if not binary.exists():
        raise RuntimeError(
            f"llama-server not found at {binary}. Build it or set LLAMA_SERVER_PATH."
        )

    mode_flag = "--embedding" if mode == "embedding" else "--rerank"
    cmd = [
        LLAMA_SERVER_PATH, "-m", model_path,
        mode_flag, "--host", "0.0.0.0", "--port", str(port),
        "-ngl", "99",
    ]
    model_name = Path(model_path).stem
    log_path = LOG_DIR / f"llama-port-{port}.log"

    logging.info(f"Starting arbitrary {mode} server on port {port} ({model_name})...")

    log_fh = open(log_path, "w")
    proc = subprocess.Popen(cmd, stdout=log_fh, stderr=subprocess.STDOUT)
    log_fh.close()

    _write_state_file(
        pid=proc.pid, port=port,
        model_path=model_path, model_name=model_name,
        mode=mode, name=name,
        log_path=str(log_path),
    )

    timeout = 90
    label_for_log = name or f"port-{port}"
    error_log.write(label_for_log, "start_initiated",
                    f"start_arbitrary({label_for_log}, port={port}) called",
                    caller="start_arbitrary", model_path=model_path, mode=mode)
    return _wait_for_health(
        proc=proc, port=port,
        model_path=model_path, model_name=model_name,
        mode=mode, name=name, log_path=str(log_path),
        timeout=timeout, label=label_for_log, caller="start_arbitrary",
    )


# Resolve a class-name (embedding / reranker / splade) to the default variant preset name.
# Returns the input unchanged if not a class name.
def _resolve_class_to_default(name: str) -> str:
    variants = _CLASS_MAP.get(name)
    if not variants:
        return name
    for v in variants:
        if SERVERS[v].get("default"):
            return v
    return variants[0]  # fallback: first in insertion order


# Start all default servers (one per class); non-default variants must be started by name.
# Returns name → 'started'|'already_running'|'error: ...'
def start_all() -> dict[str, str]:
    results = {}
    for name, cfg in SERVERS.items():
        if not cfg.get("default"):
            continue
        try:
            started = start(name)
            results[name] = "started" if started else "already_running"
        except Exception as e:
            results[name] = f"error: {e}"
    return results


# Stop ALL servers (both default and non-default), regardless of whether they're running.
# Returns name → 'stopped'|'not_running'
def stop_all() -> dict[str, str]:
    results = {}
    for name in SERVERS:
        stopped = stop(name)
        results[name] = "stopped" if stopped else "not_running"
    return results


# FUNCTIONS

# Return http://localhost:{port} for a running server matching name.
# Match strategy:
#   1. Exact match wins (e.g. find_server_url("embedding-8b")).
#   2. Class-prefix fallback for legacy callers: find_server_url("embedding")
#      → returns the FIRST running variant in SERVERS insertion order
#      (i.e. the default variant if it's running, else next).
# Client modules (embedder.py / reranker.py / sparse_embedder.py) call with
# class-name strings — the prefix path keeps them working without changes
# when SERVERS holds multiple variants per class.
def find_server_url(name: str) -> str | None:
    states_by_name: dict[str, dict] = {}
    for sf in sorted(TIMESTAMP_DIR.glob("server-port-*.json")):
        try:
            state = json.loads(sf.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        sn = state.get("name")
        if sn:
            states_by_name[sn] = state

    # 1. Exact match
    if name in states_by_name:
        return f"http://localhost:{states_by_name[name]['port']}"

    # 2. Class-prefix fallback: iterate variants in SERVERS insertion order,
    #    return first one that's running.
    variants = _CLASS_MAP.get(name, [])
    for v in variants:
        if v in states_by_name:
            return f"http://localhost:{states_by_name[v]['port']}"

    return None


# Check if a server responds; state-file-only — no state file means not running.
# Accepts preset name OR class name (embedding / reranker / splade).
def check_health(name: str) -> bool:
    url = find_server_url(name)
    if not url:
        return False
    return _check_health_port(int(url.split(":")[-1]))


# Health-poll wait loop: polls until /health responds, rewrites state file with actual PID
# if it differs from proc.pid, logs success; unlinks state file on any exception.
def _wait_for_health(
    proc: subprocess.Popen, port: int, model_path: str, model_name: str,
    mode: str, name: str | None, log_path: str, timeout: int, label: str, caller: str,
) -> bool:
    try:
        for i in range(timeout):
            time.sleep(1)
            if _check_health_port(port):
                actual_pid = find_pid_on_port(port)
                if actual_pid is not None and actual_pid != proc.pid:
                    _write_state_file(pid=actual_pid, port=port, model_path=model_path,
                                      model_name=model_name, mode=mode, name=name, log_path=log_path)
                final_pid = actual_pid or proc.pid
                logging.info(f"{label} started on port {port} (PID {final_pid}) after {i + 1}s")
                error_log.write(label, "start_succeeded", f"{label} healthy on port {port} after {i + 1}s",
                                caller=caller, pid=final_pid, port=port, elapsed_s=i + 1)
                return True
        raise RuntimeError(f"Failed to start {label} on port {port} after {timeout}s")
    except Exception:
        _unlink_state_file(port, caller=caller,
                           reason=f"{caller}({label}, port={port}) failed: did not become healthy in {timeout}s")
        raise


# Mapping: llama-server mode → CLI flag. Modes not in this dict use llama-server's
# default behavior (no mode flag) — that's the text-generation case.
_MODE_FLAGS: dict[str, str] = {
    "embedding": "--embedding",
    "rerank": "--rerank",
}


# Build llama-server cmd for a given model, port, mode, and extra flags
def _build_llama_cmd(model_path: str, port: int, mode: str, extra_flags: list[str]) -> list[str]:
    cmd = [LLAMA_SERVER_PATH, "-m", model_path]
    if mode in _MODE_FLAGS:
        cmd.append(_MODE_FLAGS[mode])
    cmd.extend(["--host", "0.0.0.0", "--port", str(port), *extra_flags])
    return cmd


# Build uvicorn cmd for a given app and port
def _build_uvicorn_cmd(uvicorn_app: str, port: int) -> list[str]:
    return [
        str(RAG_ROOT / "venv/bin/python"), "-m", "uvicorn",
        uvicorn_app, "--host", "0.0.0.0", "--port", str(port),
    ]
