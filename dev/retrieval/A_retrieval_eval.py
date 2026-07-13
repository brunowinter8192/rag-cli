# INFRASTRUCTURE
import argparse
import json
import math
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "indexing"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import httpx

import p1_retriever as _retriever
import p2_embedder as _embedder
import p3_sparse_embedder as _sparse_embedder
from eval_config import BASELINE, SWEEP_RANGES

EMBEDDING_HEALTH_URL = os.getenv("EMBEDDING_HEALTH_URL", "http://localhost:8081/health")
SPLADE_HEALTH_URL = os.getenv("SPLADE_HEALTH_URL", "http://localhost:8083/health")
RERANKER_HEALTH_URL = os.getenv("RERANKER_HEALTH_URL", "http://localhost:8082/health")
RERANKER_8B_HEALTH_URL = os.getenv("RERANKER_8B_HEALTH_URL", "http://localhost:8085/health")

TIMESTAMP_DIR = Path.home() / ".rag-locks"
RAG_ROOT = Path(__file__).parent.parent.parent
VENV_PYTHON = str(RAG_ROOT / "venv/bin/python")

# mode → required server presets (used by _ensure_constellation_for_mode)
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

# Modes where score_threshold is not meaningful (score scale not comparable to cosine)
THRESHOLD_IGNORED_MODES = {
    "hybrid", "hybrid+rerank", "bm25",
    "cc+rerank-8b", "hybrid+rerank-8b", "dense+rerank-0.6b", "dense+rerank-8b",
}
# Modes where query_prefix has no effect (no dense embedding step)
PREFIX_NOOP_MODES = {"sparse", "bm25"}


# ORCHESTRATOR

def run_baseline(queries_path: str, config: dict) -> None:
    collection = config["collection"]
    mode = config["mode"]
    if MODE_CONSTELLATIONS.get(mode):
        _ensure_constellation_for_mode(mode)   # starts servers + patches dynamic-port URLs
    else:
        _check_servers([mode])
    queries = _load_queries(queries_path)
    _verify_drift(queries, collection)
    print(f"Running baseline: {len(queries)} queries | mode={config['mode']} | top_k={config['top_k']} | collection={collection}")

    query_results = []
    total_q = len(queries)
    for qi, entry in enumerate(queries, 1):
        hits, latency_ms = _run_query(entry["query"], collection, config)
        print(f"  [q{qi}/{total_q}] mode={config['mode']} top_k={config['top_k']} latency={latency_ms:.0f}ms", flush=True)
        query_results.append({
            "entry": entry,
            "hits": hits,
            "latency_ms": latency_ms,
            "doc_match": _check_document_match(entry["expected_documents"], hits),
            "snippet_match": _check_snippet_match(entry["expected_chunks"], hits),
            "rank_metrics": _compute_rank_metrics(hits, entry["expected_chunks"], config["top_k"]),
        })

    _write_report(query_results, collection, config, label="baseline")


def run_cross_sweep(queries_path: str, param1: str, param2: str, base_config: dict,
                    restrict_values: list[str] | None = None) -> None:
    for p in (param1, param2):
        if p not in SWEEP_RANGES:
            print(f"ERROR: '{p}' is not a sweepable parameter. Valid: {sorted(SWEEP_RANGES)}")
            sys.exit(1)

    collection = base_config["collection"]
    # restrict_values applies to whichever param is "mode"
    values1 = (restrict_values if restrict_values and param1 == "mode" else None) or SWEEP_RANGES[param1]
    values2 = (restrict_values if restrict_values and param2 == "mode" else None) or SWEEP_RANGES[param2]

    # For non-mode sweeps, do upfront server check; for mode sweeps, constellation is managed per-iteration.
    mode_is_swept = param1 == "mode" or param2 == "mode"
    if not mode_is_swept:
        _check_servers([base_config["mode"]])

    queries = _load_queries(queries_path)
    _verify_drift(queries, collection)
    print(f"Running cross-sweep: {param1} × {param2} | {len(values1)}×{len(values2)}={len(values1)*len(values2)} configs | {len(queries)} queries | collection={collection}")

    # results[(v1, v2)] = (avg_doc, avg_snip, avg_ndcg, avg_mrr, avg_recall_k, mean_latency_ms)
    results: dict[tuple, tuple] = {}
    total_configs = len(values1) * len(values2)
    total_q = len(queries)
    done = 0
    for v1 in values1:
        if param1 == "mode":
            _ensure_constellation_for_mode(v1)
        for v2 in values2:
            if param2 == "mode":
                _ensure_constellation_for_mode(v2)
            config = {**base_config, param1: v1, param2: v2}
            query_results = []
            for qi, entry in enumerate(queries, 1):
                hits, latency_ms = _run_query(entry["query"], collection, config)
                print(f"  [q{qi}/{total_q}] mode={config['mode']} top_k={config['top_k']} latency={latency_ms:.0f}ms", flush=True)
                query_results.append({
                    "entry": entry,
                    "hits": hits,
                    "latency_ms": latency_ms,
                    "doc_match": _check_document_match(entry["expected_documents"], hits),
                    "snippet_match": _check_snippet_match(entry["expected_chunks"], hits),
                    "rank_metrics": _compute_rank_metrics(hits, entry["expected_chunks"], config["top_k"]),
                })
            results[(v1, v2)] = _compute_avg_metrics(query_results)
            done += 1
            r = results[(v1, v2)]
            print(f"  [{done}/{total_configs}] {param1}={v1} {param2}={v2}: snippet_recall={r[1]:.0%} NDCG={r[2]:.3f} mean_lat={r[5]:.0f}ms")

    _write_cross_sweep_report(results, param1, param2, values1, values2, base_config)


def run_sweep(queries_path: str, param: str, base_config: dict,
              restrict_values: list[str] | None = None) -> None:
    if param not in SWEEP_RANGES:
        print(f"ERROR: '{param}' is not a sweepable parameter. Valid: {sorted(SWEEP_RANGES)}")
        sys.exit(1)

    collection = base_config["collection"]
    values = restrict_values if restrict_values is not None else SWEEP_RANGES[param]
    if param != "mode":
        mode = base_config["mode"]
        if MODE_CONSTELLATIONS.get(mode):
            _ensure_constellation_for_mode(mode)   # starts servers + patches dynamic-port URLs
        else:
            _check_servers([mode])

    queries = _load_queries(queries_path)
    _verify_drift(queries, collection)
    print(f"Running sweep: {param} over {values} | {len(queries)} queries | collection={collection}")

    comparison_rows = []
    total_q = len(queries)
    for val in values:
        config = {**base_config, param: val}
        if param == "mode":
            _ensure_constellation_for_mode(val)
        query_results = []
        for qi, entry in enumerate(queries, 1):
            hits, latency_ms = _run_query(entry["query"], collection, config)
            print(f"  [q{qi}/{total_q}] mode={config['mode']} top_k={config['top_k']} latency={latency_ms:.0f}ms", flush=True)
            query_results.append({
                "entry": entry,
                "hits": hits,
                "latency_ms": latency_ms,
                "doc_match": _check_document_match(entry["expected_documents"], hits),
                "snippet_match": _check_snippet_match(entry["expected_chunks"], hits),
                "rank_metrics": _compute_rank_metrics(hits, entry["expected_chunks"], config["top_k"]),
            })

        label = f"sweep_{param}_{val}"
        _write_report(query_results, collection, config, label=label, sweep_param=param)
        avg_doc, avg_snip, avg_ndcg, avg_mrr, avg_recall_k, mean_lat = _compute_avg_metrics(query_results)
        comparison_rows.append((param, val, config["mode"], avg_doc, avg_snip, avg_ndcg, avg_mrr, avg_recall_k, mean_lat))

    _write_sweep_comparison(comparison_rows, param, base_config)


# FUNCTIONS

# Check required servers are healthy based on modes
def _check_servers(modes: list[str]) -> None:
    checks = []
    if any(m not in PREFIX_NOOP_MODES for m in modes):  # dense embedding needed for all except sparse/bm25
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


# Ensure the correct server constellation is running for a mode (subprocess, dev convention).
# Idempotent: healthy servers are left alone; only missing/wrong servers are changed.
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


# Patch module-level URL globals in p2/p3/p1 to reflect dynamic ports from ~/.rag-locks state files.
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


# Read ~/.rag-locks state files to find the URL for a named preset server.
def _lookup_server_url(server_name: str, path: str = "/v1/rerank") -> str:
    for sf in sorted(TIMESTAMP_DIR.glob("server-port-*.json")):
        try:
            state = json.loads(sf.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if state.get("name") == server_name:
            return f"http://localhost:{state['port']}{path}"
    raise RuntimeError(f"No running state file for server: {server_name}")


# Rerank results using a cross-encoder at an explicit URL (avoids p1_retriever's hardcoded port).
def _rerank_at(query: str, results: list[dict], top_k: int, url: str) -> list[dict]:
    contents = [r["content"] for r in results]
    response = httpx.post(
        url,
        json={"query": query, "documents": contents, "top_n": len(contents)},
        timeout=300.0,
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


# Load query objects from JSON file
def _load_queries(queries_path: str) -> list[dict]:
    path = Path(queries_path)
    if not path.exists():
        print(f"ERROR: queries file not found: {queries_path}")
        sys.exit(1)
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, dict) and "queries" in data:
        return data["queries"]
    if isinstance(data, list):
        return data
    print("ERROR: queries file must contain a JSON object with 'queries' key or a JSON array")
    sys.exit(1)


# Resolve queries file path: explicit --queries path or auto-derive from collection name
def _resolve_queries_path(collection: str, explicit_path: str | None) -> str:
    if explicit_path:
        return explicit_path
    derived = Path(__file__).parent / f"queries_{collection}.json"
    return str(derived)


# Assert each expected_chunks identifying_quote is a substring of its chunk content in the active collection
def _verify_drift(queries: list[dict], collection: str) -> None:
    from p4_db import get_connection
    conn = get_connection()
    errors = []
    try:
        with conn.cursor() as cur:
            for qi, entry in enumerate(queries, 1):
                for ec in entry.get("expected_chunks", []):
                    cur.execute(
                        "SELECT 1 FROM documents WHERE collection=%s AND document=%s AND chunk_index=%s AND content LIKE %s",
                        (collection, ec["document"], ec["chunk_index"], f"%{ec['identifying_quote']}%"),
                    )
                    if not cur.fetchone():
                        errors.append(
                            f"Q{qi} {ec['document']}[{ec['chunk_index']}]: quote not in collection={collection}: '{ec['identifying_quote'][:60]}'"
                        )
    finally:
        conn.close()
    if errors:
        print("ERROR: Drift-detector — identifying_quotes do not match current index:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)


# Run a single query with full config; returns (hits, latency_ms)
def _run_query(query: str, collection: str, config: dict) -> tuple[list[dict], float]:
    mode = config["mode"]
    top_k = config["top_k"]
    alpha = config["alpha"]
    rrf_k = config["rrf_k"]
    score_threshold = config["score_threshold"]
    query_prefix = config["query_prefix"]

    t0 = time.perf_counter()
    try:
        if mode == "dense":
            hits = _retriever.retrieve_dense(query, collection, top_k, query_prefix=query_prefix)
        elif mode == "sparse":
            hits = _retriever.retrieve_sparse(query, collection, top_k)
        elif mode == "bm25":
            hits = _retriever.retrieve_bm25(query, collection, top_k)
        elif mode == "hybrid":
            hits = _retriever.retrieve_hybrid(query, collection, top_k, rrf_k=rrf_k, query_prefix=query_prefix)
        elif mode == "cc":
            hits = _retriever.retrieve_cc(query, collection, top_k, alpha=alpha, query_prefix=query_prefix)
        elif mode == "cc+rerank":
            url = _lookup_server_url("reranker-0.6b")
            hits = _retriever.retrieve_cc(query, collection, config["rerank_candidates"], alpha=alpha, query_prefix=query_prefix)
            hits = _rerank_at(query, hits, top_k, url)
        elif mode == "hybrid+rerank":
            url = _lookup_server_url("reranker-0.6b")
            hits = _retriever.retrieve_hybrid(query, collection, config["rerank_candidates"], rrf_k=rrf_k, query_prefix=query_prefix)
            hits = _rerank_at(query, hits, top_k, url)
        elif mode == "cc+rerank-8b":
            url = _lookup_server_url("reranker-8b")
            hits = _retriever.retrieve_cc(query, collection, config["rerank_candidates"], alpha=alpha, query_prefix=query_prefix)
            hits = _rerank_at(query, hits, top_k, url)
        elif mode == "hybrid+rerank-8b":
            url = _lookup_server_url("reranker-8b")
            hits = _retriever.retrieve_hybrid(query, collection, config["rerank_candidates"], rrf_k=rrf_k, query_prefix=query_prefix)
            hits = _rerank_at(query, hits, top_k, url)
        elif mode == "dense+rerank-0.6b":
            url = _lookup_server_url("reranker-0.6b")
            hits = _retriever.retrieve_dense(query, collection, config["rerank_candidates"], query_prefix=query_prefix)
            hits = _rerank_at(query, hits, top_k, url)
        elif mode == "dense+rerank-8b":
            url = _lookup_server_url("reranker-8b")
            hits = _retriever.retrieve_dense(query, collection, config["rerank_candidates"], query_prefix=query_prefix)
            hits = _rerank_at(query, hits, top_k, url)
        else:
            hits = []
    except Exception as e:
        latency_ms = (time.perf_counter() - t0) * 1000
        print(f"WARNING: query failed ({e}): {query[:60]}")
        return [], latency_ms

    latency_ms = (time.perf_counter() - t0) * 1000

    if score_threshold > 0.0 and mode not in THRESHOLD_IGNORED_MODES:
        hits = [h for h in hits if h.get("score", 0) >= score_threshold]

    return hits, latency_ms


# Check which expected documents were found and at which ranks (diagnostic)
def _check_document_match(expected_docs: list[str], hits: list[dict]) -> list[dict]:
    results = []
    for doc in expected_docs:
        ranks = [rank for rank, h in enumerate(hits, 1) if h.get("document") == doc]
        results.append({"doc": doc, "found": bool(ranks), "ranks": ranks})
    return results


# Check which expected_chunks identifying_quotes appear as substrings in any hit's content
def _check_snippet_match(expected_chunks: list[dict], hits: list[dict]) -> list[dict]:
    results = []
    for ec in expected_chunks:
        quote = ec["identifying_quote"]
        found_rank = None
        for rank, h in enumerate(hits, 1):
            if quote.lower() in h.get("content", "").lower():
                found_rank = rank
                break
        results.append({"snippet": quote, "found": found_rank is not None, "rank": found_rank})
    return results


# Compute NDCG@K with binary relevance (rel=1 if (hit.document, hit.chunk_index) in expected_set)
# DCG@k = Σ (2^rel_i - 1) / log2(i+1), IDCG = DCG of perfect ranking using total_relevant
def _compute_ndcg_at_k(hits: list[dict], expected_set: set, total_relevant: int, k: int) -> float:
    rels = [1 if (h.get("document"), h.get("chunk_index")) in expected_set else 0 for h in hits[:k]]
    dcg = sum(r / math.log2(i + 2) for i, r in enumerate(rels))
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(total_relevant, k)))
    return min(1.0, dcg / idcg) if idcg > 0 else 0.0


# Compute MRR@K: 1/rank of first relevant hit in top K, 0 if none
def _compute_mrr_at_k(hits: list[dict], expected_set: set, k: int) -> float:
    for rank, h in enumerate(hits[:k], 1):
        if (h.get("document"), h.get("chunk_index")) in expected_set:
            return 1.0 / rank
    return 0.0


# Compute Recall@K: expected_chunks retrieved in top K / total expected_chunks
def _compute_recall_at_k(hits: list[dict], expected_set: set, total_relevant: int, k: int) -> float:
    if total_relevant == 0:
        return 0.0
    retrieved_relevant = sum(1 for h in hits[:k] if (h.get("document"), h.get("chunk_index")) in expected_set)
    return retrieved_relevant / total_relevant


# Bundle NDCG@K, MRR@K, Recall@K using expected_chunks as binary ground truth
def _compute_rank_metrics(hits: list[dict], expected_chunks: list[dict], k: int) -> dict:
    expected_set = {(ec["document"], ec["chunk_index"]) for ec in expected_chunks}
    total_relevant = len(expected_chunks)
    return {
        "ndcg_at_k": _compute_ndcg_at_k(hits, expected_set, total_relevant, k),
        "mrr_at_k": _compute_mrr_at_k(hits, expected_set, k),
        "recall_at_k": _compute_recall_at_k(hits, expected_set, total_relevant, k),
        "k": k,
    }


# Format rank list as compact string like "Rank 1, 2, 5" or "-"
def _format_ranks(ranks: list[int]) -> str:
    if not ranks:
        return "-"
    return ", ".join(str(r) for r in ranks)


# Build config table lines for report header
def _config_header_lines(config: dict, sweep_param: str | None = None) -> list[str]:
    lines = ["", "**Config:**", "", "| Param | Value | Note |", "|-------|-------|------|"]
    mode = config["mode"]
    for key, val in config.items():
        note = ""
        if key == "score_threshold" and mode in THRESHOLD_IGNORED_MODES:
            note = "⚠ ignored — score scale not comparable for rrf/bm25/rerank"
        elif key == "query_prefix" and mode in PREFIX_NOOP_MODES:
            note = "no-op — no dense embedding step for sparse/bm25"
        marker = " ← swept" if key == sweep_param else ""
        lines.append(f"| {key} | {val}{marker} | {note} |")
    return lines


# Write MD evaluation report to md/
def _write_report(query_results: list[dict], collection: str, config: dict, label: str, sweep_param: str | None = None) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path(__file__).parent / "md"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"eval_{label}_{timestamp}.md"

    mode = config["mode"]
    threshold_ignored = mode in THRESHOLD_IGNORED_MODES and config["score_threshold"] > 0.0
    prefix_noop = mode in PREFIX_NOOP_MODES

    lines = [
        f"# Retrieval Evaluation: {collection}",
        f"",
        f"**Label:** {label} | **Timestamp:** {timestamp}",
    ]

    if threshold_ignored:
        lines += [
            "",
            f"> ⚠ **Note:** score_threshold={config['score_threshold']} ignored for mode=`{mode}` — score scales not comparable for rrf/bm25/rerank.",
        ]
    if prefix_noop:
        lines += [
            "",
            f"> ℹ **Note:** query_prefix={config['query_prefix']} is a no-op for mode=`{mode}` — no dense embedding step.",
        ]

    lines += _config_header_lines(config, sweep_param)
    lines += ["", "---"]

    for qi, qr in enumerate(query_results, start=1):
        entry = qr["entry"]
        doc_match = qr["doc_match"]
        snippet_match = qr["snippet_match"]

        doc_found = sum(1 for d in doc_match if d["found"])
        doc_total = len(doc_match)
        doc_pct = int(100 * doc_found / doc_total) if doc_total else 0

        snip_found = sum(1 for s in snippet_match if s["found"])
        snip_total = len(snippet_match)
        snip_pct = int(100 * snip_found / snip_total) if snip_total else 0

        lines += [f"", f"## Query {qi}: \"{entry['query']}\"", f""]
        lines.append(f"**Document Match (diagnostic):** {doc_found}/{doc_total} ({doc_pct}%)")
        for dm in doc_match:
            ranks_str = _format_ranks(dm["ranks"])
            status = f"Found (Rank {ranks_str})" if dm["found"] else "MISSING"
            lines.append(f"- {dm['doc']} — {status}")

        lines.append(f"")
        lines.append(f"**Snippet Recall (identifying_quotes):** {snip_found}/{snip_total} ({snip_pct}%)")
        for sm in snippet_match:
            status = f"Found in Rank {sm['rank']}" if sm["found"] else "MISSING"
            lines.append(f"- \"{sm['snippet']}\" — {status}")

        rm = qr.get("rank_metrics")
        if rm:
            k = rm["k"]
            lines += [
                f"",
                f"**Rank Metrics @{k}:**",
                f"| Metric | Value |",
                f"|--------|-------|",
                f"| NDCG@{k} | {rm['ndcg_at_k']:.3f} |",
                f"| MRR@{k} | {rm['mrr_at_k']:.3f} |",
                f"| Recall@{k} (chunk-level) | {rm['recall_at_k']:.1%} |",
            ]

        lines += [f"", f"---"]

    lines += _build_summary(query_results)

    report_path.write_text("\n".join(lines) + "\n")
    print(f"Report: {report_path}")


# Compute average doc recall, snippet recall, rank metrics, and latency across all query results
def _compute_avg_metrics(query_results: list[dict]) -> tuple[float, float, float, float, float, float]:
    doc_recalls = []
    snip_recalls = []
    ndcg_vals = []
    mrr_vals = []
    recall_k_vals = []
    lat_vals = []
    for qr in query_results:
        doc_match = qr["doc_match"]
        snippet_match = qr["snippet_match"]
        rm = qr.get("rank_metrics", {})
        doc_recalls.append(sum(1 for d in doc_match if d["found"]) / len(doc_match) if doc_match else 0)
        snip_recalls.append(sum(1 for s in snippet_match if s["found"]) / len(snippet_match) if snippet_match else 0)
        ndcg_vals.append(rm.get("ndcg_at_k", 0.0))
        mrr_vals.append(rm.get("mrr_at_k", 0.0))
        recall_k_vals.append(rm.get("recall_at_k", 0.0))
        lat_vals.append(qr.get("latency_ms", 0.0))
    total = len(query_results)
    return (
        sum(doc_recalls) / total if total else 0,
        sum(snip_recalls) / total if total else 0,
        sum(ndcg_vals) / total if total else 0,
        sum(mrr_vals) / total if total else 0,
        sum(recall_k_vals) / total if total else 0,
        sum(lat_vals) / total if total else 0,
    )


# Write sweep comparison MD report with all swept values + baseline fixed params
def _write_sweep_comparison(rows: list[tuple], param: str, base_config: dict) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path(__file__).parent / "md"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"sweep_{param}_{timestamp}.md"

    fixed = {k: v for k, v in base_config.items() if k != param}
    fixed_str = ", ".join(f"{k}={v}" for k, v in fixed.items())

    lines = [
        f"# Retrieval Sweep: {param}",
        f"",
        f"**Swept:** `{param}` over `{SWEEP_RANGES[param]}`",
        f"**Fixed (BASELINE):** {fixed_str}",
        f"**Timestamp:** {timestamp}",
    ]

    if param == "score_threshold":
        affected = [v for v in SWEEP_RANGES[param] if v > 0.0]
        if affected and base_config["mode"] in THRESHOLD_IGNORED_MODES:
            lines += [
                "",
                f"> ⚠ **Note:** score_threshold ignored for mode=`{base_config['mode']}` — score scales not comparable for rrf/bm25/rerank. All threshold values will produce identical results.",
            ]
    if param == "query_prefix" and base_config["mode"] in PREFIX_NOOP_MODES:
        lines += [
            "",
            f"> ℹ **Note:** query_prefix is a no-op for mode=`{base_config['mode']}` — no dense embedding step for sparse/bm25. True/False results will be identical.",
        ]

    lines += [
        "",
        f"| {param} | Mode | Doc Recall | Snippet Recall | NDCG@K | MRR@K | Recall@K | Latency (mean_ms) |",
        f"|{'-'*len(param)}-|------|-----------|----------------|--------|-------|---------|-----------------|",
    ]
    for swept_param, val, mode, avg_doc, avg_snip, avg_ndcg, avg_mrr, avg_recall_k, mean_lat in rows:
        lines.append(f"| {val} | {mode} | {avg_doc:.0%} | {avg_snip:.0%} | {avg_ndcg:.3f} | {avg_mrr:.3f} | {avg_recall_k:.1%} | {mean_lat:.0f}ms |")

    report_path.write_text("\n".join(lines) + "\n")
    print(f"Sweep comparison: {report_path}")


# Write cross-product sweep comparison MD: primary snippet_recall matrix + secondary metric matrices
def _write_cross_sweep_report(results: dict, param1: str, param2: str, values1: list, values2: list, base_config: dict) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path(__file__).parent / "md"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"cross_{param1}_{param2}_{base_config['collection']}_{timestamp}.md"

    fixed = {k: v for k, v in base_config.items() if k not in (param1, param2)}
    fixed_str = ", ".join(f"{k}={v}" for k, v in fixed.items())

    lines = [
        f"# Cross-Product Sweep: {param1} × {param2}",
        f"",
        f"**Timestamp:** {timestamp}",
        f"**Collection:** {base_config['collection']}",
        f"**Swept:** `{param1}` ({len(values1)} values) × `{param2}` ({len(values2)} values) = {len(values1)*len(values2)} configs",
        f"**Fixed:** {fixed_str}",
        f"",
        f"---",
        f"",
        f"## Primary: Snippet Recall  (format: `snippet% (NDCG)`)",
        f"",
    ]

    # Header row
    col_header = " | ".join(f"{param2}={v}" for v in values2)
    sep = " | ".join("---" for _ in values2)
    lines.append(f"| {param1} \\ {param2} | {col_header} |")
    lines.append(f"|---|{sep}|")
    for v1 in values1:
        cells = []
        for v2 in values2:
            avg_doc, avg_snip, avg_ndcg, avg_mrr, avg_recall_k, mean_lat = results[(v1, v2)]
            cells.append(f"{avg_snip:.0%} ({avg_ndcg:.3f}) [{mean_lat:.0f}ms]")
        lines.append(f"| {v1} | " + " | ".join(cells) + " |")

    # Find best cell by snippet_recall, tie-break NDCG
    best_key = max(results.keys(), key=lambda k: (results[k][1], results[k][2]))
    best = results[best_key]
    lines += [
        f"",
        f"**Best cell:** `{param1}={best_key[0]}, {param2}={best_key[1]}` — snippet_recall={best[1]:.0%}, NDCG={best[2]:.3f}, MRR={best[3]:.3f}",
        f"",
        f"---",
        f"",
        f"## Secondary: NDCG@K",
        f"",
    ]

    lines.append(f"| {param1} \\ {param2} | {col_header} |")
    lines.append(f"|---|{sep}|")
    for v1 in values1:
        cells = [f"{results[(v1, v2)][2]:.3f}" for v2 in values2]
        lines.append(f"| {v1} | " + " | ".join(cells) + " |")

    lines += [f"", f"## Secondary: MRR@K", f""]
    lines.append(f"| {param1} \\ {param2} | {col_header} |")
    lines.append(f"|---|{sep}|")
    for v1 in values1:
        cells = [f"{results[(v1, v2)][3]:.3f}" for v2 in values2]
        lines.append(f"| {v1} | " + " | ".join(cells) + " |")

    lines += [f"", f"## Secondary: Recall@K (chunk-level)", f""]
    lines.append(f"| {param1} \\ {param2} | {col_header} |")
    lines.append(f"|---|{sep}|")
    for v1 in values1:
        cells = [f"{results[(v1, v2)][4]:.1%}" for v2 in values2]
        lines.append(f"| {v1} | " + " | ".join(cells) + " |")

    lines += [f"", f"## Secondary: Doc Recall (diagnostic)", f""]
    lines.append(f"| {param1} \\ {param2} | {col_header} |")
    lines.append(f"|---|{sep}|")
    for v1 in values1:
        cells = [f"{results[(v1, v2)][0]:.0%}" for v2 in values2]
        lines.append(f"| {v1} | " + " | ".join(cells) + " |")

    lines += [f"", f"## Secondary: Latency (mean_warm_ms)", f""]
    lines.append(f"| {param1} \\ {param2} | {col_header} |")
    lines.append(f"|---|{sep}|")
    for v1 in values1:
        cells = [f"{results[(v1, v2)][5]:.0f}ms" for v2 in values2]
        lines.append(f"| {v1} | " + " | ".join(cells) + " |")

    lines += [
        f"",
        f"---",
        f"",
        f"## Summary",
        f"",
        f"**Winner:** `{param1}={best_key[0]}, {param2}={best_key[1]}`",
        f"- snippet_recall: {best[1]:.0%} (primary)",
        f"- NDCG@{best_key[1]}: {best[2]:.3f} (tie-breaker)",
        f"- MRR@{best_key[1]}: {best[3]:.3f}",
        f"- Recall@{best_key[1]}: {best[4]:.1%}",
        f"- doc_recall: {best[0]:.0%}",
        f"- mean_latency: {best[5]:.0f}ms",
        f"",
    ]

    # Narrative: highlight any notable jumps across top_k dimension (only when param2 is top_k)
    if param2 == "top_k":
        lines.append("**Notes:**")
        for v1 in values1:
            snips = [results[(v1, v2)][1] for v2 in values2]
            max_gain = max(snips) - min(snips)
            if max_gain >= 0.10:
                peak_v2 = values2[snips.index(max(snips))]
                lines.append(f"- `{param1}={v1}`: snippet_recall spans {min(snips):.0%}–{max(snips):.0%} (gain {max_gain:.0%}); peaks at {param2}={peak_v2}")
        lines.append("")

    report_path.write_text("\n".join(lines) + "\n")
    print(f"Cross-sweep report: {report_path}")


# Build summary section with aggregate metrics
def _build_summary(query_results: list[dict]) -> list[str]:
    total = len(query_results)
    doc_recalls = []
    snip_recalls = []
    ndcg_vals = []
    mrr_vals = []
    recall_k_vals = []
    full_doc_match = 0
    full_snip_match = 0
    zero_snip_match = 0
    type_stats: dict[str, dict] = {}

    for qr in query_results:
        entry = qr["entry"]
        doc_match = qr["doc_match"]
        snippet_match = qr["snippet_match"]
        rm = qr.get("rank_metrics", {})

        doc_r = sum(1 for d in doc_match if d["found"]) / len(doc_match) if doc_match else 0
        snip_r = sum(1 for s in snippet_match if s["found"]) / len(snippet_match) if snippet_match else 0

        doc_recalls.append(doc_r)
        snip_recalls.append(snip_r)
        ndcg_vals.append(rm.get("ndcg_at_k", 0.0))
        mrr_vals.append(rm.get("mrr_at_k", 0.0))
        recall_k_vals.append(rm.get("recall_at_k", 0.0))

        if doc_r == 1.0:
            full_doc_match += 1
        if snip_r == 1.0:
            full_snip_match += 1
        if snip_r == 0.0:
            zero_snip_match += 1

        qtype = entry.get("type", "unknown")
        if qtype not in type_stats:
            type_stats[qtype] = {"count": 0, "doc_recalls": [], "snip_recalls": [], "ndcg_vals": [], "mrr_vals": [], "recall_k_vals": []}
        type_stats[qtype]["count"] += 1
        type_stats[qtype]["doc_recalls"].append(doc_r)
        type_stats[qtype]["snip_recalls"].append(snip_r)
        type_stats[qtype]["ndcg_vals"].append(rm.get("ndcg_at_k", 0.0))
        type_stats[qtype]["mrr_vals"].append(rm.get("mrr_at_k", 0.0))
        type_stats[qtype]["recall_k_vals"].append(rm.get("recall_at_k", 0.0))

    avg_doc = sum(doc_recalls) / total if total else 0
    avg_snip = sum(snip_recalls) / total if total else 0
    avg_ndcg = sum(ndcg_vals) / total if total else 0
    avg_mrr = sum(mrr_vals) / total if total else 0
    avg_recall_k = sum(recall_k_vals) / total if total else 0
    lat_vals = [qr.get("latency_ms", 0.0) for qr in query_results]
    mean_lat = sum(lat_vals) / total if total else 0
    top_k_label = len(query_results[0]["hits"]) if query_results else "?"
    k_label = query_results[0]["rank_metrics"]["k"] if query_results and query_results[0].get("rank_metrics") else top_k_label

    lines = [
        f"",
        f"## Summary",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Document Recall @{top_k_label} (diagnostic, avg) | {avg_doc:.0%} |",
        f"| Snippet Recall @{top_k_label} (identifying_quotes, avg) | {avg_snip:.0%} |",
        f"| NDCG@{k_label} (avg) | {avg_ndcg:.3f} |",
        f"| MRR@{k_label} (avg) | {avg_mrr:.3f} |",
        f"| Recall@{k_label} chunk-level (avg) | {avg_recall_k:.1%} |",
        f"| Mean Query Latency (warm_ms) | {mean_lat:.0f}ms |",
        f"| Queries with 100% doc match | {full_doc_match}/{total} |",
        f"| Queries with 100% snippet match | {full_snip_match}/{total} |",
        f"| Queries with 0 snippet match | {zero_snip_match}/{total} |",
        f"",
        f"### By Query Type",
        f"| Type | Count | Avg Doc Recall | Avg Snippet Recall | Avg NDCG@{k_label} | Avg MRR@{k_label} | Avg Recall@{k_label} |",
        f"|------|-------|---------------|-------------------|------|------|------|",
    ]

    for qtype, stats in sorted(type_stats.items()):
        avg_d = sum(stats["doc_recalls"]) / stats["count"]
        avg_s = sum(stats["snip_recalls"]) / stats["count"]
        avg_n = sum(stats["ndcg_vals"]) / stats["count"]
        avg_m = sum(stats["mrr_vals"]) / stats["count"]
        avg_rk = sum(stats["recall_k_vals"]) / stats["count"]
        lines.append(f"| {qtype} | {stats['count']} | {avg_d:.0%} | {avg_s:.0%} | {avg_n:.3f} | {avg_m:.3f} | {avg_rk:.1%} |")

    return lines


# Parse key=val override strings into a dict
def _parse_overrides(override_list: list[str], base_config: dict) -> dict:
    config = dict(base_config)
    for item in override_list or []:
        if "=" not in item:
            print(f"ERROR: --override must be key=val (got: '{item}')")
            sys.exit(1)
        key, raw_val = item.split("=", 1)
        if key not in config:
            print(f"ERROR: --override key '{key}' not in BASELINE. Valid keys: {sorted(config)}")
            sys.exit(1)
        original = base_config[key]
        if isinstance(original, bool):
            config[key] = raw_val.lower() in ("true", "1", "yes")
        elif isinstance(original, int):
            config[key] = int(raw_val)
        elif isinstance(original, float):
            config[key] = float(raw_val)
        else:
            config[key] = raw_val
    return config


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate retrieval against expected_chunks ground truth")
    parser.add_argument("--collection", default=None, help="Collection to query — shorthand for --override collection=X")
    parser.add_argument("--queries", default=None, help="Queries JSON path (default: auto-derived from collection)")
    parser.add_argument("--baseline", action="store_true", help="Run single pass at BASELINE config values")
    parser.add_argument("--sweep", metavar="PARAM", help="Sweep PARAM over SWEEP_RANGES[PARAM]; others fixed at BASELINE")
    parser.add_argument("--sweep-cross", metavar=("PARAM1", "PARAM2"), nargs=2, help="Cross-product sweep PARAM1 × PARAM2 over SWEEP_RANGES; others fixed at BASELINE")
    parser.add_argument("--override", metavar="key=val", action="append", help="Override a BASELINE key (repeatable)")
    parser.add_argument("--restrict-modes", metavar="M1,M2,...", default=None,
                        help="Restrict --sweep/--sweep-cross mode dimension to this comma-separated subset of SWEEP_RANGES['mode']")
    args = parser.parse_args()

    if not args.baseline and not args.sweep and not args.sweep_cross:
        parser.error("Specify --baseline, --sweep PARAM, or --sweep-cross PARAM1 PARAM2")

    config = _parse_overrides(args.override, BASELINE)
    if args.collection:
        config["collection"] = args.collection
    queries_path = _resolve_queries_path(config["collection"], args.queries)

    restrict_values = None
    if args.restrict_modes:
        restrict_values = [m.strip() for m in args.restrict_modes.split(",")]
        unknown = [m for m in restrict_values if m not in SWEEP_RANGES["mode"]]
        if unknown:
            parser.error(f"Unknown modes in --restrict-modes: {unknown}. Valid: {SWEEP_RANGES['mode']}")

    if args.sweep_cross:
        run_cross_sweep(queries_path, args.sweep_cross[0], args.sweep_cross[1], config, restrict_values)
    elif args.sweep:
        run_sweep(queries_path, args.sweep, config, restrict_values)
    else:
        run_baseline(queries_path, config)
