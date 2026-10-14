# INFRASTRUCTURE

import importlib
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

DEV_DIR = Path(__file__).parent.parent

sys.path.insert(0, str(DEV_DIR))
sys.path.insert(0, str(DEV_DIR / "retrieval"))
sys.path.insert(0, str(DEV_DIR / "indexing"))
sys.path.insert(0, str(DEV_DIR / "server_management"))

from strand_runner import run_strands

RUNNER_CONFIG = {
    "top_k": 2,
    "alpha": 0.8,
    "rrf_k": 60,
    "query_prefix": True,
    "rerank_candidates": 3,
}
HITS = [
    {"content": "first", "document": "d", "chunk_index": 0, "score": 0.1},
    {"content": "second", "document": "d", "chunk_index": 1, "score": 0.2},
    {"content": "third", "document": "d", "chunk_index": 2, "score": 0.3},
]


# ORCHESTRATOR

def run_all() -> None:
    run_strands([
        test_smell_patches_urls_from_state_files,
        test_smell_skips_patch_for_missing_server,
        test_smell_wait_all_healthy_polls_state_files,
        test_smell_rerank_mode_reaches_reranker,
        test_runner_rerank_mode_reaches_reranker,
        test_constellation_patches_urls_from_state_files,
        test_constellation_warns_for_missing_server,
        test_find_server_url_returns_url_or_none,
        test_require_server_url_raises_for_missing_server,
        test_rerank_at_orders_truncates_and_copies,
        test_rerank_at_default_timeout,
        test_rerank_uses_module_url_and_short_timeout,
    ])


# FUNCTIONS

def test_smell_patches_urls_from_state_files(workdir: Path) -> None:
    smell, retriever, embedder, sparse = _load("B_real_smell", "p1_retriever", "p2_embedder", "p3_sparse_embedder")
    _write_state("embedding-8b", 4101)
    _write_state("splade", 4102)
    _write_state("reranker-8b", 4103)
    smell._patch_retriever_urls(["embedding-8b", "splade", "reranker-8b"])
    assert embedder.EMBEDDING_URL == "http://localhost:4101/v1/embeddings", embedder.EMBEDDING_URL
    assert sparse.SPLADE_URL == "http://localhost:4102/v1/sparse-embeddings", sparse.SPLADE_URL
    assert retriever.RERANKER_URL == "http://localhost:4103/v1/rerank", retriever.RERANKER_URL


def test_smell_skips_patch_for_missing_server(workdir: Path) -> None:
    smell, retriever = _load("B_real_smell", "p1_retriever")
    before = retriever.RERANKER_URL
    smell._patch_retriever_urls(["reranker-0.6b"])
    assert retriever.RERANKER_URL == before, retriever.RERANKER_URL


def test_smell_wait_all_healthy_polls_state_files(workdir: Path) -> None:
    smell, = _load("B_real_smell")
    server, requests = _start_fake_server()
    _write_state("embedding-8b", server.server_port)
    assert smell._wait_all_healthy(["embedding-8b"], 5) is True
    assert smell._wait_all_healthy(["embedding-8b", "splade"], 1) is False
    assert ("GET", "/health") in requests, requests
    server.shutdown()


def test_smell_rerank_mode_reaches_reranker(workdir: Path) -> None:
    smell, retriever = _load("B_real_smell", "p1_retriever")
    server, requests = _start_fake_server()
    _write_state("reranker-0.6b", server.server_port)
    retriever.retrieve_dense = lambda query, collection, top_k, query_prefix: HITS
    smell._run_one_query("dense+rerank-0.6b", "q")
    posts = [body for method, path, body in _posts(requests) if path == "/v1/rerank"]
    assert len(posts) == 1, requests
    assert posts[0]["documents"] == ["first", "second", "third"], posts[0]
    server.shutdown()


def test_runner_rerank_mode_reaches_reranker(workdir: Path) -> None:
    runner, retriever = _load("eval_runner", "p1_retriever")
    server, requests = _start_fake_server()
    _write_state("reranker-8b", server.server_port)
    retriever.retrieve_cc = lambda query, collection, top_k, alpha, query_prefix: HITS
    hits = runner._dispatch_rerank_mode("cc+rerank-8b", "q", "c", RUNNER_CONFIG)
    assert [h["content"] for h in hits] == ["third", "second"], hits
    assert [h["score"] for h in hits] == [0.9, 0.6], hits
    assert HITS[0]["score"] == 0.1, HITS
    server.shutdown()


def test_constellation_patches_urls_from_state_files(workdir: Path) -> None:
    constellation, retriever, embedder, sparse = _load("eval_constellation", "p1_retriever", "p2_embedder", "p3_sparse_embedder")
    _write_state("embedding-8b", 4201)
    _write_state("splade", 4202)
    _write_state("reranker-0.6b", 4203)
    constellation._patch_retriever_urls(["embedding-8b", "splade", "reranker-0.6b"])
    assert embedder.EMBEDDING_URL == "http://localhost:4201/v1/embeddings", embedder.EMBEDDING_URL
    assert sparse.SPLADE_URL == "http://localhost:4202/v1/sparse-embeddings", sparse.SPLADE_URL
    assert retriever.RERANKER_URL == "http://localhost:4203/v1/rerank", retriever.RERANKER_URL


def test_constellation_warns_for_missing_server(workdir: Path) -> None:
    constellation, retriever = _load("eval_constellation", "p1_retriever")
    before = retriever.RERANKER_URL
    constellation._patch_retriever_urls(["reranker-8b"])
    assert retriever.RERANKER_URL == before, retriever.RERANKER_URL


def test_find_server_url_returns_url_or_none(workdir: Path) -> None:
    urls, = _load("server_urls")
    _write_state("splade", 4301)
    assert urls.find_server_url("splade", "/health") == "http://localhost:4301/health"
    assert urls.find_server_url("splade") == "http://localhost:4301/v1/rerank"
    assert urls.find_server_url("reranker-8b") is None


def test_require_server_url_raises_for_missing_server(workdir: Path) -> None:
    urls, = _load("server_urls")
    _write_state("splade", 4302)
    assert urls.require_server_url("splade", "/health") == "http://localhost:4302/health"
    try:
        urls.require_server_url("reranker-8b")
    except RuntimeError as e:
        assert str(e) == "No running state file for server: reranker-8b", str(e)
    else:
        raise AssertionError("missing server did not raise")


def test_rerank_at_orders_truncates_and_copies(workdir: Path) -> None:
    retriever, = _load("p1_retriever")
    server, requests = _start_fake_server()
    hits = retriever.rerank_at("q", HITS, 2, f"http://localhost:{server.server_port}/v1/rerank")
    assert [h["content"] for h in hits] == ["third", "second"], hits
    assert [h["score"] for h in hits] == [0.9, 0.6], hits
    assert HITS[2]["score"] == 0.3, HITS
    assert _posts(requests)[0][2] == {"query": "q", "documents": ["first", "second", "third"], "top_n": 3}, requests
    server.shutdown()


def test_rerank_at_default_timeout(workdir: Path) -> None:
    retriever, = _load("p1_retriever")
    server, requests = _start_fake_server()
    timeouts = _record_timeouts(retriever)
    retriever.rerank_at("q", HITS, 2, f"http://localhost:{server.server_port}/v1/rerank")
    assert timeouts == [300.0], timeouts
    server.shutdown()


def test_rerank_uses_module_url_and_short_timeout(workdir: Path) -> None:
    retriever, = _load("p1_retriever")
    server, requests = _start_fake_server()
    retriever.RERANKER_URL = f"http://localhost:{server.server_port}/v1/rerank"
    timeouts = _record_timeouts(retriever)
    hits = retriever.rerank("q", HITS, 1)
    assert [h["content"] for h in hits] == ["third"], hits
    assert timeouts == [60.0], timeouts
    assert [path for _, path, _ in _posts(requests)] == ["/v1/rerank"], requests
    server.shutdown()


def _load(*names: str) -> list:
    return [importlib.import_module(name) for name in names]


def _write_state(name: str, port: int) -> None:
    lock_dir = Path.home() / ".rag-locks"
    lock_dir.mkdir(exist_ok=True)
    (lock_dir / f"server-port-{port}.json").write_text(json.dumps({"name": name, "port": port}))


def _record_timeouts(retriever) -> list:
    timeouts: list = []
    real_post = retriever.httpx.post

    def recording_post(*args, **kwargs):
        timeouts.append(kwargs["timeout"])
        return real_post(*args, **kwargs)

    retriever.httpx.post = recording_post
    return timeouts


def _posts(requests: list) -> list:
    return [r for r in requests if r[0] == "POST"]


def _start_fake_server() -> tuple[HTTPServer, list]:
    requests: list = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(("GET", self.path))
            self.send_response(200)
            self.end_headers()

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(("POST", self.path, body))
            results = [{"index": i, "relevance_score": (i + 1) * 0.3} for i in range(len(body["documents"]))]
            payload = json.dumps({"results": results}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, requests


if __name__ == "__main__":
    run_all()
