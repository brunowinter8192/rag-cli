"""
A_constellation_profile.py — GPU server constellation performance measurement.

Measures VRAM footprint, cold/warm query latency, and timeout rate for each
defined server constellation on M4 Pro hardware. Results feed constellation
exclusivity decisions (cross-class exclusive_with values in server_utils.py).

DO NOT EXECUTE IN THIS WORKER SESSION.
Script is prepared for next-session profiling run on a clean server state.

Usage:
    ./venv/bin/python dev/server_management/A_constellation_profile.py \\
        --constellation embedding-8b-solo
    ./venv/bin/python dev/server_management/A_constellation_profile.py --all

Output: dev/server_management/md/profile_YYYYMMDD_HHMMSS.md
"""

# INFRASTRUCTURE
import argparse
import json
import logging
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

logging.basicConfig(level=logging.WARNING)
_log = logging.getLogger(__name__)

RAG_ROOT = Path(__file__).parent.parent.parent
VENV_PYTHON = str(RAG_ROOT / "venv/bin/python")
TIMESTAMP_DIR = Path.home() / ".rag-locks"
REPORTS_DIR = Path(__file__).parent / "md"

# All constellations to profile; order matches task spec
CONSTELLATIONS: dict[str, list[str]] = {
    "embedding-8b-solo":               ["embedding-8b"],
    "embedding-0.6b-solo":             ["embedding-0.6b"],
    "embedding-8b+splade":             ["embedding-8b", "splade"],
    "embedding-8b+reranker-0.6b":      ["embedding-8b", "reranker-0.6b"],
    "embedding-8b+reranker-0.6b+splade": ["embedding-8b", "reranker-0.6b", "splade"],
    "embedding-8b+reranker-8b":        ["embedding-8b", "reranker-8b"],
    "embedding-8b+reranker-8b+splade": ["embedding-8b", "reranker-8b", "splade"],
    "embedding-0.6b+reranker-8b":      ["embedding-0.6b", "reranker-8b"],
}

TEST_QUERY = "What is the meaning of RAG evaluation?"
COLD_N = 5
WARM_N = 50
HTTPX_TIMEOUT = 300.0          # seconds per request before counting as timeout
CONSTELLATION_TIMEOUT = 360    # seconds for ensure_constellation subprocess
HEALTH_POLL_TIMEOUT = 120      # seconds to confirm health after constellation setup
INTER_QUERY_DELAY_S = 0.1      # brief pause between warm queries (avoid burst)
INTER_CONSTELLATION_DELAY_S = 5  # pause between constellations when running --all

# 50 moderately-sized test documents — realistic rerank batch without DB access.
# Each ~280 chars (≈70 tokens), simulating retrieved paragraph chunks.
RERANK_TEST_DOCS = [
    (
        f"Document {i:02d}: Retrieval-augmented generation (RAG) combines dense vector search "
        f"with language model generation to improve factual grounding and answer relevance. "
        f"Embedding quality, chunk granularity, and reranker calibration are the primary "
        f"levers for retrieval quality improvement in production RAG pipelines."
    )
    for i in range(50)
]


# ORCHESTRATOR

# Profile one constellation end-to-end; returns result dict for report.
def profile_constellation_workflow(constellation_name: str) -> dict:
    servers = CONSTELLATIONS[constellation_name]
    embedding_server = next((s for s in servers if "embedding" in s), None)
    reranker_server = next((s for s in servers if "reranker" in s), None)

    print(f"\n{'=' * 62}")
    print(f"  Profiling: {constellation_name}")
    print(f"  Servers:   {servers}")
    print(f"{'=' * 62}")

    print("  [1/6] Setting constellation via ensure_constellation...")
    try:
        _ensure_constellation(servers)
    except Exception as e:
        return {"constellation": constellation_name, "servers": servers, "error": str(e)}

    print("  [2/6] Polling health...")
    if not _wait_all_healthy(servers, HEALTH_POLL_TIMEOUT):
        return {
            "constellation": constellation_name, "servers": servers,
            "error": f"servers not healthy within {HEALTH_POLL_TIMEOUT}s",
        }

    print("  [3/6] Sampling VRAM from server logs...")
    vram_log_mib = _sample_vram_from_logs(servers)
    vram_sys_mib = _sample_vram_system()

    embedding_url = _get_server_url(embedding_server) if embedding_server else None
    reranker_url = _get_server_url(reranker_server) if reranker_server else None

    if embedding_server and not embedding_url:
        return {
            "constellation": constellation_name, "servers": servers,
            "error": f"URL not found for {embedding_server} after successful health check",
        }

    print(f"  [4/6] Cold queries (n={COLD_N})...")
    cold_latencies, cold_timeouts = _run_queries(COLD_N, embedding_url, reranker_url)
    cold_stats = _compute_stats(cold_latencies)

    print(f"  [5/6] Warm queries (n={WARM_N})...")
    warm_latencies, warm_timeouts = _run_queries(WARM_N, embedding_url, reranker_url)
    warm_stats = _compute_stats(warm_latencies)

    print(
        f"  [6/6] Done. VRAM(log)={vram_log_mib / 1024:.1f}GB  "
        f"warm_p50={warm_stats['p50']:.0f}ms  timeouts={warm_timeouts}/{WARM_N}"
    )

    return {
        "constellation": constellation_name,
        "servers": servers,
        "vram_log_mib": vram_log_mib,
        "vram_sys_mib": vram_sys_mib,
        "cold_n": COLD_N,
        "cold_stats": cold_stats,
        "cold_timeouts": cold_timeouts,
        "warm_n": WARM_N,
        "warm_stats": warm_stats,
        "warm_timeouts": warm_timeouts,
    }


# FUNCTIONS

# Set constellation via src.rag.server_manager.ensure_constellation (subprocess).
# Dev convention: no src/ imports in dev/ scripts; subprocess keeps them isolated.
def _ensure_constellation(names: list[str]) -> None:
    names_json = json.dumps(names)
    script = (
        f"from src.rag.server_manager import ensure_constellation; "
        f"ensure_constellation({names_json})"
    )
    result = subprocess.run(
        [VENV_PYTHON, "-c", script],
        cwd=str(RAG_ROOT),
        capture_output=True, text=True,
        timeout=CONSTELLATION_TIMEOUT,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"ensure_constellation({names}) exited {result.returncode}:\n{result.stderr}"
        )


# Poll /health for every server in the constellation until all respond 200 or timeout.
def _wait_all_healthy(names: list[str], timeout: int) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        all_ok = True
        for name in names:
            url = _get_server_url(name)
            if not url:
                all_ok = False
                break
            try:
                resp = httpx.get(f"{url}/health", timeout=3.0)
                if resp.status_code != 200:
                    all_ok = False
                    break
            except httpx.RequestError as e:
                _log.debug("health poll %s: %s", name, e)
                all_ok = False
                break
        if all_ok:
            return True
        time.sleep(2)
    return False


# Read state files to find URL for a named preset server.
def _get_server_url(preset_name: str) -> str | None:
    for sf in sorted(TIMESTAMP_DIR.glob("server-port-*.json")):
        try:
            state = json.loads(sf.read_text())
        except (json.JSONDecodeError, OSError) as e:
            _log.debug("state file read error %s: %s", sf, e)
            continue
        if state.get("name") == preset_name:
            return f"http://localhost:{state['port']}"
    return None


# Sum all MTL0 Metal buffer sizes from llama startup logs for the given preset names.
# Matches all three MTL0 allocation lines (model weights + KV cache + compute scratch),
# which together equal the total Metal GPU allocation announced by llama_params_fit_impl.
# CPU buffer lines (CPU_Mapped, CPU output, CPU compute) are excluded — GPU only.
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


# Total in-use GPU memory snapshot via system_profiler; best-effort on Apple Silicon.
# Returns MiB or None if system_profiler doesn't expose VRAM usage on this hardware.
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


# Run n queries (embed + optional rerank); returns (latencies_ms, timeout_count).
# Timeouts still contribute their wall-clock time to latencies for conservative stats.
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


# Compute percentile stats from a latency list (ms).
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


# Write per-constellation sections + comparison table to output_path.
def _write_report(all_results: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: list[str] = []

    lines.append("# Constellation Profile Report\n\n")
    lines.append(f"Generated: {ts}\n")
    lines.append(f"Test query: `{TEST_QUERY}`\n")
    lines.append(f"Cold N: {COLD_N} | Warm N: {WARM_N} | HTTPX timeout: {HTTPX_TIMEOUT:.0f}s\n\n")
    lines.append("---\n\n")

    for r in all_results:
        lines.append(f"## {r['constellation']}\n\n")
        lines.append(f"**Servers:** {', '.join(r['servers'])}\n\n")
        if "error" in r:
            lines.append(f"**ERROR:** {r['error']}\n\n")
            continue
        vram_gb = r["vram_log_mib"] / 1024
        lines.append(
            f"**VRAM (Metal log sum):** {r['vram_log_mib']:.0f} MiB ({vram_gb:.2f} GB)\n"
        )
        if r["vram_sys_mib"] is not None:
            lines.append(
                f"**VRAM (system_profiler):** {r['vram_sys_mib']:.0f} MiB "
                f"({r['vram_sys_mib'] / 1024:.2f} GB)\n"
            )
        lines.append("\n**Cold queries**\n\n")
        cs = r["cold_stats"]
        lines.append(
            f"Timeouts: {r['cold_timeouts']}/{r['cold_n']} | "
            f"p50: {cs['p50']:.0f}ms | p95: {cs['p95']:.0f}ms | "
            f"p99: {cs['p99']:.0f}ms | max: {cs['max']:.0f}ms\n\n"
        )
        lines.append("**Warm queries**\n\n")
        ws = r["warm_stats"]
        lines.append(
            f"Timeouts: {r['warm_timeouts']}/{r['warm_n']} | "
            f"p50: {ws['p50']:.0f}ms | p95: {ws['p95']:.0f}ms | "
            f"p99: {ws['p99']:.0f}ms | max: {ws['max']:.0f}ms\n\n"
        )

    lines.append("---\n\n")
    lines.append("## Comparison Table\n\n")
    lines.append(
        "| Constellation | VRAM (GB) | Cold p50 (ms) | Warm p50 (ms) "
        "| Warm p95 (ms) | Timeouts/50 |\n"
    )
    lines.append("|---|---|---|---|---|---|\n")
    for r in all_results:
        if "error" in r:
            lines.append(f"| {r['constellation']} | ERROR | — | — | — | — |\n")
            continue
        vram_gb = r["vram_log_mib"] / 1024
        lines.append(
            f"| {r['constellation']} | {vram_gb:.1f} | {r['cold_stats']['p50']:.0f} | "
            f"{r['warm_stats']['p50']:.0f} | {r['warm_stats']['p95']:.0f} | "
            f"{r['warm_timeouts']} |\n"
        )

    output_path.write_text("".join(lines))
    print(f"\nReport: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Profile GPU server constellations for latency and VRAM."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--constellation", choices=list(CONSTELLATIONS.keys()),
        metavar="NAME", help="Profile a single constellation",
    )
    group.add_argument(
        "--all", action="store_true",
        help="Profile all constellations in sequence (writes single combined report)",
    )
    parser.add_argument("--cold-n", type=int, default=None, metavar="N",
                        help="Override COLD_N (default: 5)")
    parser.add_argument("--warm-n", type=int, default=None, metavar="N",
                        help="Override WARM_N (default: 50)")
    parser.add_argument("--rerank-docs", type=int, default=None, metavar="N",
                        help="Override rerank batch size (default: 50 docs)")
    args = parser.parse_args()

    if args.cold_n is not None:
        COLD_N = args.cold_n
    if args.warm_n is not None:
        WARM_N = args.warm_n
    if args.rerank_docs is not None:
        RERANK_TEST_DOCS = RERANK_TEST_DOCS[:args.rerank_docs]

    names_to_run = list(CONSTELLATIONS.keys()) if args.all else [args.constellation]

    all_results: list[dict] = []
    for i, name in enumerate(names_to_run):
        result = profile_constellation_workflow(name)
        all_results.append(result)
        if args.all and i < len(names_to_run) - 1:
            print(f"  Pausing {INTER_CONSTELLATION_DELAY_S}s before next constellation...")
            time.sleep(INTER_CONSTELLATION_DELAY_S)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"profile_{ts}.md"
    _write_report(all_results, report_path)
