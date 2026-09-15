# INFRASTRUCTURE
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "indexing"))

import httpx

import p1_retriever as _retriever
import p2_embedder as _embedder
import p3_sparse_embedder as _sparse_embedder
from eval_config import PREFIX_NOOP_MODES

EMBEDDING_HEALTH_URL = os.getenv("EMBEDDING_HEALTH_URL", "http://localhost:8081/health")
SPLADE_HEALTH_URL = os.getenv("SPLADE_HEALTH_URL", "http://localhost:8083/health")
RERANKER_HEALTH_URL = os.getenv("RERANKER_HEALTH_URL", "http://localhost:8082/health")
RERANKER_8B_HEALTH_URL = os.getenv("RERANKER_8B_HEALTH_URL", "http://localhost:8085/health")

TIMESTAMP_DIR = Path.home() / ".rag-locks"
RAG_ROOT = Path(__file__).parent.parent.parent
VENV_PYTHON = str(RAG_ROOT / "venv/bin/python")

MODE_CONSTELLATIONS: dict[str, list[str]] = {
    "dense":               ["embedding-8b"],
    "sparse":              ["splade"],
    "bm25":                [],
    "hybrid":              ["embedding-8b", "splade"],
    "cc":                  ["embedding-8b", "splade"],
    "cc+rerank":           ["embedding-8b", "splade", "reranker-0.6b"],
    "hybrid+rerank":       ["embedding-8b", "splade", "reranker-0.6b"],
    "cc+rerank-8b":        ["embedding-8b", "splade", "reranker-8b"],
    "hybrid+rerank-8b":    ["embedding-8b", "splade", "reranker-8b"],
    "dense+rerank-0.6b":   ["embedding-8b", "reranker-0.6b"],
    "dense+rerank-8b":     ["embedding-8b", "reranker-8b"],
}


# FUNCTIONS

def _check_servers(modes: list[str]) -> None:
    checks = []
    if any(m not in PREFIX_NOOP_MODES for m in modes):
        checks.append(("embedding (8081)", EMBEDDING_HEALTH_URL))
    _splade_modes = {"sparse", "hybrid", "cc", "cc+rerank", "hybrid+rerank", "cc+rerank-8b", "hybrid+rerank-8b"}
    if any(m in _splade_modes for m in modes):
        checks.append(("SPLADE (8083)", SPLADE_HEALTH_URL))
    if any(m in modes for m in ["cc+rerank", "hybrid+rerank", "dense+rerank-0.6b"]):
        checks.append(("reranker-0.6b (8082)", RERANKER_HEALTH_URL))
    if any(m in modes for m in ["cc+rerank-8b", "hybrid+rerank-8b", "dense+rerank-8b"]):
        checks.append(("reranker-8b (8085)", RERANKER_8B_HEALTH_URL))
    for name, url in checks:
        try:
            resp = httpx.get(url, timeout=3.0)
            if resp.status_code != 200:
                print(f"ERROR: {name} server unhealthy (HTTP {resp.status_code}). Start servers: ./start.sh")
                sys.exit(1)
        except Exception as e:
            print(f"ERROR: {name} server not reachable ({e}). Start servers: ./start.sh")
            sys.exit(1)


def _ensure_constellation_for_mode(mode: str) -> None:
    servers = MODE_CONSTELLATIONS.get(mode, [])
    if not servers:
        return
    names_json = json.dumps(servers)
    script = (
        f"from src.rag.server_manager import ensure_constellation; "
        f"ensure_constellation({names_json})"
    )
    print(f"  [constellation] {mode} → {servers}")
    subprocess.run([VENV_PYTHON, "-c", script], cwd=str(RAG_ROOT), check=True, timeout=360)
    _patch_retriever_urls(servers)


def _patch_retriever_urls(servers: list[str]) -> None:
    if "embedding-8b" in servers or "embedding-0.6b" in servers:
        server = "embedding-8b" if "embedding-8b" in servers else "embedding-0.6b"
        try:
            url = _lookup_server_url(server, path="/v1/embeddings")
        except RuntimeError as e:
            print(f"    [url-patch] WARNING: {e}", flush=True)
        else:
            _embedder.EMBEDDING_URL = url
            print(f"    [url-patch] embedding → {url}", flush=True)
    if "splade" in servers:
        try:
            url = _lookup_server_url("splade", path="/v1/sparse-embeddings")
        except RuntimeError as e:
            print(f"    [url-patch] WARNING: {e}", flush=True)
        else:
            _sparse_embedder.SPLADE_URL = url
            print(f"    [url-patch] splade → {url}", flush=True)
    for reranker in ("reranker-0.6b", "reranker-8b"):
        if reranker in servers:
            try:
                url = _lookup_server_url(reranker, path="/v1/rerank")
            except RuntimeError as e:
                print(f"    [url-patch] WARNING: {e}", flush=True)
            else:
                _retriever.RERANKER_URL = url
                print(f"    [url-patch] reranker → {url}", flush=True)
            break


def _lookup_server_url(server_name: str, path: str = "/v1/rerank") -> str:
    for sf in sorted(TIMESTAMP_DIR.glob("server-port-*.json")):
        try:
            state = json.loads(sf.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if state.get("name") == server_name:
            return f"http://localhost:{state['port']}{path}"
    raise RuntimeError(f"No running state file for server: {server_name}")
