# INFRASTRUCTURE
from pathlib import Path

from src.rag import error_log
from src.rag.config import LLAMA_SERVER_PATH, RAG_ROOT, SERVER_LOG_DIR
from src.rag.log_setup import get_logger
from src.rag.server_launch import build_llama_cmd, build_uvicorn_cmd, launch
from src.rag.server_state import iter_state_files, require_preset
from src.rag.server_utils import SERVERS, allocate_port, check_health_port, pid_alive, stop_by_state

logger = get_logger("server_start")


# ORCHESTRATOR

def start(name: str) -> bool:
    require_preset(name)
    cfg = SERVERS[name]
    record_start_initiated(name, cfg)
    if handle_existing_instance(name):
        return False
    port = allocate_port()
    cmd, log_path, cwd, model_name = build_launch_spec(name, cfg, port)
    logger.info(f"Starting {name} on port {port}...")
    return launch(cmd, cwd, log_path, port, cfg["model_path"], model_name,
                  cfg["mode"], name, cfg["timeout"], name, "start")


# FUNCTIONS

def record_start_initiated(name: str, cfg: dict) -> None:
    error_log.write(name, "start_initiated", f"start({name}) called",
                    caller="start", model_path=cfg["model_path"])


def handle_existing_instance(name: str) -> bool:
    for sf, state in iter_state_files():
        if state.get("name") == name and pid_alive(state["pid"]):
            if check_health_port(state["port"]):
                logger.info(f"{name} already running on port {state['port']} (PID {state['pid']})")
                return True
            replace_unhealthy_instance(name, sf, state)
            return False
    return False


def replace_unhealthy_instance(name: str, sf: Path, state: dict) -> None:
    logger.warning(f"{name} alive on port {state['port']} but unhealthy, stopping for restart")
    error_log.write(name, "single_instance_alive_replaced",
                    f"existing {name} alive on port {state['port']} (PID {state['pid']}) but unhealthy — replacing",
                    caller="start", existing_pid=state["pid"], existing_port=state["port"])
    stop_by_state(state, sf,
                  caller="start",
                  reason=f"alive but check_health_port({state['port']}) returned False at start-time")


def build_launch_spec(name: str, cfg: dict, port: int) -> tuple[list[str], Path, str | None, str]:
    if cfg["type"] == "llama":
        return build_llama_spec(name, cfg, port)
    return build_uvicorn_spec(name, cfg, port)


def build_uvicorn_spec(name: str, cfg: dict, port: int) -> tuple[list[str], Path, str | None, str]:
    venv_python = str(RAG_ROOT / "venv/bin/python")
    if not Path(venv_python).exists():
        raise RuntimeError(f"Cannot start {name}: {venv_python} not found.")
    cmd = build_uvicorn_cmd(cfg["uvicorn_app"], port)
    return cmd, SERVER_LOG_DIR / "splade_server.log", str(RAG_ROOT), cfg["model_path"]


def build_llama_spec(name: str, cfg: dict, port: int) -> tuple[list[str], Path, str | None, str]:
    binary = Path(LLAMA_SERVER_PATH)
    if not binary.exists():
        raise RuntimeError(
            f"Cannot start {name}: {binary} not found. "
            f"cd <RAG_ROOT> && ./start.sh"
        )
    cmd = build_llama_cmd(cfg["model_path"], port, cfg["mode"], cfg["extra_flags"])
    return cmd, SERVER_LOG_DIR / f"llama-port-{port}.log", None, Path(cfg["model_path"]).stem
