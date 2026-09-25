# INFRASTRUCTURE
from src.rag.server_state import find_server_url
from src.rag.server_utils import SERVERS, check_health_port, find_pid_on_port


# ORCHESTRATOR

def status() -> dict[str, dict]:
    return {name: describe_server(name) for name in SERVERS}


# FUNCTIONS

def describe_server(name: str) -> dict:
    url = find_server_url(name)
    if not url:
        return {"running": False, "pid": None, "port": None, "healthy": False}
    port = int(url.split(":")[-1])
    pid = find_pid_on_port(port)
    healthy = check_health_port(port) if pid else False
    return {"running": pid is not None, "pid": pid, "port": port, "healthy": healthy}
