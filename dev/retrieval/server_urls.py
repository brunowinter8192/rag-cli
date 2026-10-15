# INFRASTRUCTURE
import json
import logging
from pathlib import Path

_log = logging.getLogger(__name__)

TIMESTAMP_DIR = Path.home() / ".rag-locks"


# FUNCTIONS

def require_server_url(server_name: str, path: str = "/v1/rerank") -> str:
    url = find_server_url(server_name, path)
    if url is None:
        raise RuntimeError(f"No running state file for server: {server_name}")
    return url


def find_server_url(server_name: str, path: str = "/v1/rerank") -> str | None:
    for sf in sorted(TIMESTAMP_DIR.glob("server-port-*.json")):
        try:
            state = json.loads(sf.read_text())
        except (json.JSONDecodeError, OSError) as e:
            _log.debug("state file read error %s: %s", sf, e)
            continue
        if state.get("name") == server_name:
            return f"http://localhost:{state['port']}{path}"
    return None
