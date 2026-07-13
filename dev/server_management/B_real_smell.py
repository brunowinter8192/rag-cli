"""
B_real_smell.py — Real-data smell test across all 6 server constellations.

Runs 3 real test_db queries per mode, measures VRAM + cold/warm latency.
Uses actual retrieved chunks (not synthetic docs) for realistic rerank load.

Usage (from Main-Project-Root):
    ./venv/bin/python -u dev/server_management/B_real_smell.py 2>&1 | tee /tmp/smell_real.log
"""

# INFRASTRUCTURE
import json
import logging
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

_log = logging.getLogger(__name__)

RAG_ROOT = Path(__file__).parent.parent.parent
VENV_PYTHON = str(RAG_ROOT / "venv/bin/python")
TIMESTAMP_DIR = Path.home() / ".rag-locks"
REPORTS_DIR = Path(__file__).parent / "md"

# p1_retriever lives in dev/retrieval/, p2/p3/p4 in dev/indexing/
sys.path.insert(0, str(RAG_ROOT / "dev" / "retrieval"))
sys.path.insert(0, str(RAG_ROOT / "dev" / "indexing"))

import p1_retriever as _retriever  # noqa: E402 (after sys.path setup)
import p2_embedder as _embedder    # noqa: E402 (for URL patching after constellation switch)
import p3_sparse_embedder as _sparse_embedder  # noqa: E402

QUERIES_PATH = RAG_ROOT / "dev" / "retrieval" / "queries_test_db.json"
COLLECTION = "test_db"
TOP_K = 12
RERANK_CANDIDATES = 12
HEALTH_POLL_TIMEOUT = 180  # seconds
RERANK_TIMEOUT = 300.0     # seconds — reranker-8b with real chunks can be slow

# Constellations in switch-verification order
CONSTELLATIONS = [
    {
        "label": "C1",
        "servers": ["embedding-8b"],
        "modes": ["dense"],
    },
    {
        "label": "C2",
        "servers": ["embedding-8b", "splade"],
        "modes": ["hybrid", "cc"],
    },
    {
        "label": "C3",
        "servers": ["embedding-8b", "reranker-0.6b"],
        "modes": ["dense+rerank-0.6b"],
    },
    {
        "label": "C4",
        "servers": ["embedding-8b", "reranker-8b"],
        "modes": ["dense+rerank-8b"],
    },
    {
        "label": "C5",
        "servers": ["embedding-8b", "splade", "reranker-0.6b"],
        "modes": ["cc+rerank-0.6b", "hybrid+rerank-0.6b"],
    },
    {
        "label": "C6",
        "servers": ["embedding-8b", "splade", "reranker-8b"],
        "modes": ["cc+rerank-8b", "hybrid+rerank-8b"],
    },
]


# ORCHESTRATOR

def main() -> None:
    queries = _load_queries()
    print(f"Loaded {len(queries)} queries from {QUERIES_PATH}", flush=True)
    print(f"Using first 3: {[q[:50] for q in queries]}", flush=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    all_results: list[dict] = []

    for c in CONSTELLATIONS:
        label = c["label"]
        servers = c["servers"]
        modes = c["modes"]

        print(f"\n{'='*60}", flush=True)
        print(f"[{label}] ensure_constellation: {servers}", flush=True)

        switch_ok = _ensure_constellation(servers, label)
        if not switch_ok:
            all_results.append({"label": label, "servers": servers, "error": "ensure_constellation failed"})
            continue

        print(f"[{label}] health-poll starting...", flush=True)
        t_health = time.time()
        if not _wait_all_healthy(servers, HEALTH_POLL_TIMEOUT):
            elapsed = time.time() - t_health
            all_results.append({"label": label, "servers": servers, "error": f"health timeout after {elapsed:.0f}s"})
            continue
        elapsed = time.time() - t_health
        print(f"[{label}] health check: OK after {elapsed:.0f}s", flush=True)

        _patch_retriever_urls(servers)
        vram_mib = _sample_vram(servers)
        print(f"[{label}] VRAM: {vram_mib/1024:.2f} GB ({vram_mib:.0f} MiB)", flush=True)

        mode_results: list[dict] = []
        for mode in modes:
            latencies = _run_mode_queries(label, mode, queries)
            mode_results.append({"mode": mode, "latencies_ms": latencies})

        all_results.append({
            "label": label,
            "servers": servers,
            "vram_mib": vram_mib,
            "modes": mode_results,
        })

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"smell_{ts}.md"
    _write_report(all_results, report_path)
    print(f"\nReport: {report_path}", flush=True)


# FUNCTIONS

def _load_queries() -> list[str]:
    data = json.loads(QUERIES_PATH.read_text())
    entries = data["queries"] if isinstance(data, dict) else data
    return [e["query"] for e in entries[:3]]


def _ensure_constellation(servers: list[str], label: str) -> bool:
    names_json = json.dumps(servers)
    script = (
        f"from src.rag.server_manager import ensure_constellation; "
        f"ensure_constellation({names_json})"
    )
    try:
        subprocess.run(
            [VENV_PYTHON, "-c", script],
            cwd=str(RAG_ROOT),
            check=True,
            timeout=360,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"[{label}] ERROR ensure_constellation: {e}", flush=True)
        return False


def _wait_all_healthy(servers: list[str], timeout: int) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        all_ok = True
        for name in servers:
            url = _lookup_server_url(name, path="/health")
            if not url:
                all_ok = False
                break
            try:
                resp = httpx.get(url, timeout=3.0)
                if resp.status_code != 200:
                    all_ok = False
                    break
            except httpx.RequestError:
                all_ok = False
                break
        if all_ok:
            return True
        time.sleep(2)
    return False


def _sample_vram(servers: list[str]) -> float:
    pattern = re.compile(r"MTL0[^=]*?buffer size\s*=\s*([\d.]+)\s*MiB")
    total = 0.0
    for sf in sorted(TIMESTAMP_DIR.glob("server-port-*.json")):
        try:
            state = json.loads(sf.read_text())
        except (json.JSONDecodeError, OSError) as e:
            _log.debug("state file read error %s: %s", sf, e)
            continue
        if state.get("name") not in servers:
            continue
        log_path = state.get("log_path", "")
        if not log_path or not Path(log_path).exists():
            continue
        try:
            for line in Path(log_path).open():
                m = pattern.search(line)
                if m:
                    total += float(m.group(1))
        except OSError as e:
            _log.warning("could not read log %s: %s", log_path, e)
    return total


def _lookup_server_url(server_name: str, path: str = "/v1/rerank") -> str | None:
    for sf in sorted(TIMESTAMP_DIR.glob("server-port-*.json")):
        try:
            state = json.loads(sf.read_text())
        except (json.JSONDecodeError, OSError) as e:
            _log.debug("state file read error %s: %s", sf, e)
            continue
        if state.get("name") == server_name:
            return f"http://localhost:{state['port']}{path}"
    return None


def _patch_retriever_urls(servers: list[str]) -> None:
    """Patch module-level URL globals in p2/p3/p1 so retriever calls hit dynamic ports."""
    if "embedding-8b" in servers or "embedding-0.6b" in servers:
        server = "embedding-8b" if "embedding-8b" in servers else "embedding-0.6b"
        url = _lookup_server_url(server, path="/v1/embeddings")
        if url:
            _embedder.EMBEDDING_URL = url
            print(f"    [url-patch] embedding → {url}", flush=True)
    if "splade" in servers:
        url = _lookup_server_url("splade", path="/v1/sparse-embeddings")
        if url:
            _sparse_embedder.SPLADE_URL = url
            print(f"    [url-patch] splade → {url}", flush=True)
    for reranker in ("reranker-0.6b", "reranker-8b"):
        if reranker in servers:
            url = _lookup_server_url(reranker, path="/v1/rerank")
            if url:
                _retriever.RERANKER_URL = url
                print(f"    [url-patch] reranker → {url}", flush=True)
            break


def _rerank_at(query: str, results: list[dict], top_k: int, url: str) -> list[dict]:
    contents = [r["content"] for r in results]
    response = httpx.post(
        url,
        json={"query": query, "documents": contents, "top_n": len(contents)},
        timeout=RERANK_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    ranked = sorted(data.get("results", data), key=lambda x: x["relevance_score"], reverse=True)
    reranked = []
    for item in ranked[:top_k]:
        doc = results[item["index"]].copy()
        doc["score"] = round(item["relevance_score"], 6)
        reranked.append(doc)
    return reranked


def _run_one_query(mode: str, query: str) -> float:
    t0 = time.time()
    try:
        if mode == "dense":
            _retriever.retrieve_dense(query, COLLECTION, TOP_K, query_prefix=True)
        elif mode == "hybrid":
            _retriever.retrieve_hybrid(query, COLLECTION, TOP_K, rrf_k=60, query_prefix=True)
        elif mode == "cc":
            _retriever.retrieve_cc(query, COLLECTION, TOP_K, alpha=0.8, query_prefix=True)
        elif mode in ("dense+rerank-0.6b", "dense+rerank-8b"):
            server = "reranker-0.6b" if "0.6b" in mode else "reranker-8b"
            url = _lookup_server_url(server)
            hits = _retriever.retrieve_dense(query, COLLECTION, RERANK_CANDIDATES, query_prefix=True)
            _rerank_at(query, hits, TOP_K, url)
        elif mode in ("cc+rerank-0.6b", "cc+rerank-8b"):
            server = "reranker-0.6b" if "0.6b" in mode else "reranker-8b"
            url = _lookup_server_url(server)
            hits = _retriever.retrieve_cc(query, COLLECTION, RERANK_CANDIDATES, alpha=0.8, query_prefix=True)
            _rerank_at(query, hits, TOP_K, url)
        elif mode in ("hybrid+rerank-0.6b", "hybrid+rerank-8b"):
            server = "reranker-0.6b" if "0.6b" in mode else "reranker-8b"
            url = _lookup_server_url(server)
            hits = _retriever.retrieve_hybrid(query, COLLECTION, RERANK_CANDIDATES, rrf_k=60, query_prefix=True)
            _rerank_at(query, hits, TOP_K, url)
        else:
            print(f"    WARNING: unknown mode {mode!r}", flush=True)
    except Exception as e:
        print(f"    ERROR mode={mode}: {e}", flush=True)
    return (time.time() - t0) * 1000


def _run_mode_queries(label: str, mode: str, queries: list[str]) -> list[float]:
    latencies: list[float] = []
    for i, q in enumerate(queries):
        tag = "cold" if i == 0 else f"warm{i}"
        ms = _run_one_query(mode, q)
        latencies.append(ms)
        print(f"[{label}] mode={mode} query={i+1} ({tag}) latency={ms:.0f}ms", flush=True)
    return latencies


def _write_report(all_results: list[dict], output_path: Path) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: list[str] = [
        "# Real-Data Smell Test Report\n",
        f"\nGenerated: {ts}\n",
        f"Queries: first 3 from {QUERIES_PATH.name}\n",
        f"Collection: {COLLECTION} | top_k={TOP_K} | rerank_candidates={RERANK_CANDIDATES}\n",
        "\n---\n",
    ]

    for r in all_results:
        label = r["label"]
        lines.append(f"\n## {label}: {r['servers']}\n\n")
        if "error" in r:
            lines.append(f"**ERROR:** {r['error']}\n\n")
            continue
        vram_gb = r["vram_mib"] / 1024
        lines.append(f"**VRAM:** {r['vram_mib']:.0f} MiB ({vram_gb:.2f} GB)\n\n")
        for mr in r["modes"]:
            mode = mr["mode"]
            lats = mr["latencies_ms"]
            cold = lats[0] if lats else 0
            warm = lats[1:] if len(lats) > 1 else []
            mean_warm = sum(warm) / len(warm) if warm else 0
            lines.append(f"### mode={mode}\n\n")
            lines.append("| Query | Latency (ms) | Note |\n")
            lines.append("|-------|-------------|------|\n")
            for i, ms in enumerate(lats):
                note = "cold" if i == 0 else f"warm{i}"
                lines.append(f"| Q{i+1} | {ms:.0f} | {note} |\n")
            if warm:
                lines.append(f"\nMean warm: {mean_warm:.0f} ms\n\n")

    lines.append("\n---\n\n## Summary Table\n\n")
    lines.append("| Constellation | VRAM (GB) | Mode | Cold (ms) | Mean Warm (ms) |\n")
    lines.append("|---|---|---|---|---|\n")
    for r in all_results:
        if "error" in r:
            lines.append(f"| {r['label']} {r['servers']} | ERROR | — | — | — |\n")
            continue
        vram_gb = r["vram_mib"] / 1024
        for mr in r["modes"]:
            lats = mr["latencies_ms"]
            cold = lats[0] if lats else 0
            warm = lats[1:]
            mean_warm = sum(warm) / len(warm) if warm else 0
            lines.append(
                f"| {r['label']} | {vram_gb:.2f} | {mr['mode']} | {cold:.0f} | {mean_warm:.0f} |\n"
            )

    output_path.write_text("".join(lines))


if __name__ == "__main__":
    main()
