# INFRASTRUCTURE
import json
import logging
import re
import subprocess
import time
from pathlib import Path

import httpx

_log = logging.getLogger(__name__)

TIMESTAMP_DIR = Path.home() / ".rag-locks"

TEST_QUERY = "What is the meaning of RAG evaluation?"
HTTPX_TIMEOUT = 300.0
INTER_QUERY_DELAY_S = 0.1

RERANK_TEST_DOCS = [
    (
        f"Document {i:02d}: Retrieval-augmented generation (RAG) combines dense vector search "
        f"with language model generation to improve factual grounding and answer relevance. "
        f"Embedding quality, chunk granularity, and reranker calibration are the primary "
        f"levers for retrieval quality improvement in production RAG pipelines."
    )
    for i in range(50)
]


# FUNCTIONS

def _sample_vram_from_logs(names: list[str]) -> float:
    total_mib = 0.0
    pattern = re.compile(r"MTL0[^=]*?buffer size\s*=\s*([\d.]+)\s*MiB")
    for sf in sorted(TIMESTAMP_DIR.glob("server-port-*.json")):
        try:
            state = json.loads(sf.read_text())
        except (json.JSONDecodeError, OSError) as e:
            _log.debug("state file read error %s: %s", sf, e)
            continue
        if state.get("name") not in names:
            continue
        log_path = state.get("log_path", "")
        if not log_path or not Path(log_path).exists():
            continue
        try:
            for line in Path(log_path).open():
                m = pattern.search(line)
                if m:
                    total_mib += float(m.group(1))
        except OSError as e:
            _log.warning("could not read log %s: %s", log_path, e)
    return total_mib


def _sample_vram_system() -> float | None:
    try:
        result = subprocess.run(
            ["system_profiler", "SPDisplaysDataType"],
            capture_output=True, text=True, timeout=15,
        )
        for line in result.stdout.splitlines():
            if "VRAM" in line:
                m = re.search(r"(\d+)\s*MB", line)
                if m:
                    return float(m.group(1))
    except subprocess.SubprocessError as e:
        _log.warning("system_profiler failed: %s", e)
    return None


def _run_queries(
    n: int, embedding_url: str | None, reranker_url: str | None
) -> tuple[list[float], int]:
    latencies: list[float] = []
    timeouts = 0
    for _ in range(n):
        t0 = time.time()
        timed_out = False
        try:
            if embedding_url:
                resp = httpx.post(
                    f"{embedding_url}/v1/embeddings",
                    json={"input": [TEST_QUERY], "model": "Qwen3-Embedding-8B"},
                    timeout=HTTPX_TIMEOUT,
                )
                resp.raise_for_status()
            if reranker_url:
                resp2 = httpx.post(
                    f"{reranker_url}/v1/rerank",
                    json={
                        "query": TEST_QUERY,
                        "documents": RERANK_TEST_DOCS,
                        "top_n": len(RERANK_TEST_DOCS),
                    },
                    timeout=HTTPX_TIMEOUT,
                )
                resp2.raise_for_status()
        except httpx.TimeoutException:
            timed_out = True
            timeouts += 1
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            _log.warning("query error: %s", e)
            timed_out = True
            timeouts += 1
        elapsed_ms = (time.time() - t0) * 1000
        latencies.append(elapsed_ms)
        if not timed_out and INTER_QUERY_DELAY_S:
            time.sleep(INTER_QUERY_DELAY_S)
    return latencies, timeouts


def _compute_stats(latencies: list[float]) -> dict:
    if not latencies:
        return {"mean": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0, "n": 0}
    s = sorted(latencies)
    n = len(s)
    return {
        "mean": sum(s) / n,
        "p50":  s[int(n * 0.50)],
        "p95":  s[min(int(n * 0.95), n - 1)],
        "p99":  s[min(int(n * 0.99), n - 1)],
        "max":  s[-1],
        "n":    n,
    }
