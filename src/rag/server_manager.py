# INFRASTRUCTURE

import json

from .log_setup import get_logger
from .server_utils import (
    SERVERS, _CLASS_MAP, _MODE_TO_CLASS, _PRESET_NAMES,
    TIMESTAMP_DIR, WATCHDOG_PID_FILE, IDLE_TIMEOUT, WATCHDOG_INTERVAL,
    RAG_ROOT, LLAMA_SERVER_PATH, LOG_DIR,
    find_pid_on_port, find_all_pids_on_port, pgrep_llama_server,
    _pid_alive, _check_health_port, _allocate_port, _resolve_port,
    _stop_by_state, _write_state_file, _unlink_state_file, _touch_state_file,
)
from .server_lifecycle import (
    start, stop, restart, start_arbitrary,
    _resolve_class_to_default, start_all, stop_all,
    find_server_url, check_health, status,
    _build_llama_cmd, _build_uvicorn_cmd,
)
from .watchdog import _ensure_watchdog_process, _watchdog_loop
from .server_cli import cli_server

logger = get_logger("server_manager")


# ORCHESTRATOR

def ensure_ready(target: str) -> None:
    if target in SERVERS:
        if not check_health(target):
            _stop_exclusive(target)
            start(target)
        _ensure_watchdog_process()
        return

    if target in _CLASS_MAP:
        preset = _resolve_class_to_default(target)
        for v in _CLASS_MAP[target]:
            if check_health(v):
                _ensure_watchdog_process()
                return
        _stop_exclusive(preset)
        start(preset)
        _ensure_watchdog_process()
        return

    if target == "search_rerank":
        needed_ops = ["search", "rerank"]
    else:
        needed_ops = [target]

    needed_servers: set[str] = set()
    for op in needed_ops:
        for name, cfg in SERVERS.items():
            if op in cfg["required_for"] and cfg.get("default"):
                needed_servers.add(name)

    for name in needed_servers:
        cls = _MODE_TO_CLASS.get(SERVERS[name]["mode"], SERVERS[name]["mode"])
        if any(check_health(v) for v in _CLASS_MAP.get(cls, [name])):
            continue
        _stop_exclusive(name)
        start(name)

    _ensure_watchdog_process()


def ensure_constellation(server_names: list[str]) -> None:
    running = _get_running_presets()
    for name in running:
        if name not in server_names:
            logger.info(
                f"constellation-stop: {name} stopped, not in requested constellation {server_names}"
            )
            stop(name)
    for name in server_names:
        ensure_ready(name)
    _ensure_watchdog_process()


# FUNCTIONS

def _stop_exclusive(name: str) -> None:
    running = _get_running_presets()
    for exclusive_name in SERVERS[name].get("exclusive_with", []):
        if exclusive_name in running:
            logger.info(
                f"exclusive-stop: {exclusive_name} stopped because {name} requires exclusivity"
            )
            stop(exclusive_name)


def _get_running_presets() -> list[str]:
    running = []
    for sf in sorted(TIMESTAMP_DIR.glob("server-port-*.json")):
        try:
            state = json.loads(sf.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        name = state.get("name")
        if name and name in SERVERS and _pid_alive(state.get("pid", -1)):
            running.append(name)
    return running
