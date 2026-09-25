# INFRASTRUCTURE
from src.rag.log_setup import get_logger
from src.rag.server_start import start
from src.rag.server_state import check_health, get_running_presets, resolve_class_to_default
from src.rag.server_stop import stop
from src.rag.server_utils import MODE_TO_CLASS, SERVERS, build_class_map
from src.rag.watchdog import ensure_watchdog_process

logger = get_logger("server_manager")


# ORCHESTRATOR

def ensure_ready(target: str) -> None:
    if target in SERVERS:
        ensure_preset_ready(target)
    elif target in build_class_map():
        ensure_class_ready(target)
    else:
        ensure_operation_ready(target)
    ensure_watchdog_process()


# FUNCTIONS

def ensure_preset_ready(name: str) -> None:
    if not check_health(name):
        stop_exclusive(name)
        start(name)


def stop_exclusive(name: str) -> None:
    running = get_running_presets()
    for exclusive_name in SERVERS[name]["exclusive_with"]:
        if exclusive_name in running:
            logger.info(
                f"exclusive-stop: {exclusive_name} stopped because {name} requires exclusivity"
            )
            stop(exclusive_name)


def ensure_class_ready(server_class: str) -> None:
    if any(check_health(variant) for variant in build_class_map()[server_class]):
        return
    preset = resolve_class_to_default(server_class)
    stop_exclusive(preset)
    start(preset)


def ensure_operation_ready(target: str) -> None:
    for name in needed_servers(target):
        cls = MODE_TO_CLASS.get(SERVERS[name]["mode"], SERVERS[name]["mode"])
        if any(check_health(variant) for variant in build_class_map()[cls]):
            continue
        stop_exclusive(name)
        start(name)


def needed_servers(target: str) -> set[str]:
    needed_ops = ["search", "rerank"] if target == "search_rerank" else [target]
    needed: set[str] = set()
    for op in needed_ops:
        for name, cfg in SERVERS.items():
            if op in cfg["required_for"] and cfg["default"]:
                needed.add(name)
    return needed
