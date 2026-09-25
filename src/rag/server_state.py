# INFRASTRUCTURE
import json

from src.rag.config import LOCK_DIR
from src.rag.server_utils import SERVERS, build_class_map, check_health_port, pid_alive


# FUNCTIONS

def require_preset(name: str) -> None:
    if name not in SERVERS:
        raise ValueError(f"Unknown server: {name}. Available: {list(SERVERS.keys())}")


def iter_state_files():
    for sf in sorted(LOCK_DIR.glob("server-port-*.json")):
        yield sf, json.loads(sf.read_text())


def find_server_state(name: str) -> dict | None:
    states_by_name: dict[str, dict] = {}
    for _, state in iter_state_files():
        sn = state.get("name")
        if sn:
            states_by_name[sn] = state

    if name in states_by_name:
        return states_by_name[name]

    for variant in build_class_map().get(name, []):
        if variant in states_by_name:
            return states_by_name[variant]

    return None


def find_server_url(name: str) -> str | None:
    state = find_server_state(name)
    return f"http://localhost:{state['port']}" if state else None


def check_health(name: str) -> bool:
    url = find_server_url(name)
    if not url:
        return False
    return check_health_port(int(url.split(":")[-1]))


def get_running_presets() -> list[str]:
    running = []
    for _, state in iter_state_files():
        name = state.get("name")
        if name and name in SERVERS and pid_alive(state["pid"]):
            running.append(name)
    return running


def resolve_class_to_default(name: str) -> str:
    variants = build_class_map().get(name)
    if not variants:
        return name
    for variant in variants:
        if SERVERS[variant]["default"]:
            return variant
    return variants[0]
