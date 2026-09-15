
# INFRASTRUCTURE
import argparse
import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path

import httpx

import constellation_measure as _measure

logging.basicConfig(level=logging.WARNING)
_log = logging.getLogger(__name__)

RAG_ROOT = Path(__file__).parent.parent.parent
VENV_PYTHON = str(RAG_ROOT / "venv/bin/python")
REPORTS_DIR = Path(__file__).parent / "md"

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

COLD_N = 5
WARM_N = 50
CONSTELLATION_TIMEOUT = 360
HEALTH_POLL_TIMEOUT = 120
INTER_CONSTELLATION_DELAY_S = 5


# ORCHESTRATOR

def profile_constellation_workflow(constellation_name: str) -> dict:
    servers, embedding_server, reranker_server = _resolve_constellation_servers(constellation_name)

    print(f"\n{'=' * 62}")
    print(f"  Profiling: {constellation_name}")
    print(f"  Servers:   {servers}")
    print(f"{'=' * 62}")

    error = _setup_constellation(servers)
    if error:
        return {"constellation": constellation_name, "servers": servers, "error": error}

    print("  [3/6] Sampling VRAM from server logs...")
    vram_log_mib = _measure._sample_vram_from_logs(servers)
    vram_sys_mib = _measure._sample_vram_system()

    embedding_url = _get_server_url(embedding_server) if embedding_server else None
    reranker_url = _get_server_url(reranker_server) if reranker_server else None

    if embedding_server and not embedding_url:
        return {
            "constellation": constellation_name, "servers": servers,
            "error": f"URL not found for {embedding_server} after successful health check",
        }

    load = _measure_load(embedding_url, reranker_url)

    print(
        f"  [6/6] Done. VRAM(log)={vram_log_mib / 1024:.1f}GB  "
        f"warm_p50={load['warm_stats']['p50']:.0f}ms  timeouts={load['warm_timeouts']}/{WARM_N}"
    )

    return {
        "constellation": constellation_name,
        "servers": servers,
        "vram_log_mib": vram_log_mib,
        "vram_sys_mib": vram_sys_mib,
        **load,
    }


# FUNCTIONS

def _resolve_constellation_servers(constellation_name: str) -> tuple[list[str], str | None, str | None]:
    servers = CONSTELLATIONS[constellation_name]
    embedding_server = next((s for s in servers if "embedding" in s), None)
    reranker_server = next((s for s in servers if "reranker" in s), None)
    return servers, embedding_server, reranker_server


def _setup_constellation(servers: list[str]) -> str | None:
    print("  [1/6] Setting constellation via ensure_constellation...")
    try:
        _ensure_constellation(servers)
    except Exception as e:
        return str(e)

    print("  [2/6] Polling health...")
    if not _wait_all_healthy(servers, HEALTH_POLL_TIMEOUT):
        return f"servers not healthy within {HEALTH_POLL_TIMEOUT}s"
    return None


def _measure_load(embedding_url: str | None, reranker_url: str | None) -> dict:
    print(f"  [4/6] Cold queries (n={COLD_N})...")
    cold_latencies, cold_timeouts = _measure._run_queries(COLD_N, embedding_url, reranker_url)
    cold_stats = _measure._compute_stats(cold_latencies)

    print(f"  [5/6] Warm queries (n={WARM_N})...")
    warm_latencies, warm_timeouts = _measure._run_queries(WARM_N, embedding_url, reranker_url)
    warm_stats = _measure._compute_stats(warm_latencies)

    return {
        "cold_n": COLD_N, "cold_stats": cold_stats, "cold_timeouts": cold_timeouts,
        "warm_n": WARM_N, "warm_stats": warm_stats, "warm_timeouts": warm_timeouts,
    }


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


def _get_server_url(preset_name: str) -> str | None:
    for sf in sorted(_measure.TIMESTAMP_DIR.glob("server-port-*.json")):
        try:
            state = json.loads(sf.read_text())
        except (json.JSONDecodeError, OSError) as e:
            _log.debug("state file read error %s: %s", sf, e)
            continue
        if state.get("name") == preset_name:
            return f"http://localhost:{state['port']}"
    return None


def _report_header_lines() -> list[str]:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return [
        "# Constellation Profile Report\n\n",
        f"Generated: {ts}\n",
        f"Test query: `{_measure.TEST_QUERY}`\n",
        f"Cold N: {COLD_N} | Warm N: {WARM_N} | HTTPX timeout: {_measure.HTTPX_TIMEOUT:.0f}s\n\n",
        "---\n\n",
    ]


def _constellation_section_lines(r: dict) -> list[str]:
    lines = [f"## {r['constellation']}\n\n", f"**Servers:** {', '.join(r['servers'])}\n\n"]
    if "error" in r:
        lines.append(f"**ERROR:** {r['error']}\n\n")
        return lines
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
    return lines


def _comparison_table_lines(all_results: list[dict]) -> list[str]:
    lines = [
        "---\n\n",
        "## Comparison Table\n\n",
        "| Constellation | VRAM (GB) | Cold p50 (ms) | Warm p50 (ms) "
        "| Warm p95 (ms) | Timeouts/50 |\n",
        "|---|---|---|---|---|---|\n",
    ]
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
    return lines


def _write_report(all_results: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = _report_header_lines()
    for r in all_results:
        lines += _constellation_section_lines(r)
    lines += _comparison_table_lines(all_results)
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
        _measure.RERANK_TEST_DOCS = _measure.RERANK_TEST_DOCS[:args.rerank_docs]

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
