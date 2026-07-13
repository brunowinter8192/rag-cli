# INFRASTRUCTURE
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import httpx

import p1_retriever as _retriever

EMBEDDING_HEALTH_URL = "http://localhost:8081/health"
SPLADE_HEALTH_URL = "http://localhost:8083/health"
RERANKER_HEALTH_URL = "http://localhost:8082/health"

ALL_MODES = ["dense", "sparse", "hybrid", "hybrid+rerank", "cc", "cc+rerank"]


# ORCHESTRATOR

def run_sandbox(collection: str, queries_path: str, top_k: int, modes: list[str]) -> None:
    _check_servers(modes)

    queries = _load_queries(queries_path)
    print(f"Running {len(queries)} queries x {len(modes)} modes on collection '{collection}'")

    results_by_query = {}
    for query in queries:
        results_by_query[query] = _run_query(query, collection, top_k, modes)

    _write_report(results_by_query, collection, top_k, modes)


# FUNCTIONS

# Check required servers are healthy based on modes
def _check_servers(modes: list[str]) -> None:
    checks = [("embedding (8081)", EMBEDDING_HEALTH_URL)]
    if any(m in modes for m in ["sparse", "hybrid", "hybrid+rerank", "cc", "cc+rerank"]):
        checks.append(("SPLADE (8083)", SPLADE_HEALTH_URL))
    if any("rerank" in m for m in modes):
        checks.append(("reranker (8082)", RERANKER_HEALTH_URL))

    for name, url in checks:
        try:
            resp = httpx.get(url, timeout=3.0)
            if resp.status_code != 200:
                print(f"ERROR: {name} server unhealthy (HTTP {resp.status_code}). Start servers: ./start.sh")
                sys.exit(1)
        except Exception as e:
            print(f"ERROR: {name} server not reachable ({e}). Start servers: ./start.sh")
            sys.exit(1)


# Load queries list from JSON file
def _load_queries(queries_path: str) -> list[str]:
    path = Path(queries_path)
    if not path.exists():
        print(f"ERROR: queries file not found: {queries_path}")
        sys.exit(1)
    with open(path) as f:
        queries = json.load(f)
    if not isinstance(queries, list):
        print(f"ERROR: queries file must contain a JSON array of strings")
        sys.exit(1)
    return queries


# Run a single query through all requested modes
def _run_query(query: str, collection: str, top_k: int, modes: list[str]) -> dict:
    results = {}
    for mode in modes:
        try:
            if mode == "dense":
                hits = _retriever.retrieve_dense(query, collection, top_k)
            elif mode == "sparse":
                hits = _retriever.retrieve_sparse(query, collection, top_k)
            elif mode == "hybrid":
                hits = _retriever.retrieve_hybrid(query, collection, top_k)
            elif mode == "hybrid+rerank":
                candidates = _retriever.retrieve_hybrid(query, collection, top_k * 5)
                hits = _retriever.rerank(query, candidates, top_k)
            elif mode == "cc":
                hits = _retriever.retrieve_cc(query, collection, top_k)
            elif mode == "cc+rerank":
                hits = _retriever.retrieve_cc_rerank(query, collection, top_k)
            else:
                hits = []
            results[mode] = hits
        except Exception as e:
            results[mode] = {"error": str(e)}
    return results


# Write MD report to md/
def _write_report(results_by_query: dict, collection: str, top_k: int, modes: list[str]) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path(__file__).parent / "md"
    report_path = report_dir / f"retrieval_{collection}_{timestamp}.md"
    report_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Retrieval Sandbox: {collection}",
        f"",
        f"**Timestamp:** {timestamp}  ",
        f"**Top-k:** {top_k}  ",
        f"**Modes:** {', '.join(modes)}",
        f"",
        f"---",
    ]

    for qi, (query, mode_results) in enumerate(results_by_query.items(), start=1):
        lines += [f"", f"## Query {qi}: \"{query}\"", f""]

        for mode in modes:
            lines += [f"", f"### {mode}", f""]
            hits = mode_results.get(mode, [])

            if isinstance(hits, dict) and "error" in hits:
                lines.append(f"**ERROR:** {hits['error']}")
                continue

            if not hits:
                lines.append("_No results._")
                continue

            for rank, hit in enumerate(hits, start=1):
                doc = hit.get("document", "")
                score = hit.get("score", 0)
                chunk_index = hit.get("chunk_index", "?")
                content = hit.get("content", "")
                display_content = content if len(content) <= 400 else content[:-400]
                lines.append(f"#### Rank {rank} | Score: {score} | Chunk: {chunk_index} | Document: {doc}")
                lines.append(f"")
                lines.append(display_content)
                lines.append(f"")

    report_path.write_text("\n".join(lines) + "\n")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test retrieval modes on indexed collection")
    parser.add_argument("--collection", required=True, help="Collection name to query")
    parser.add_argument("--queries", required=True, help="Path to JSON file with queries list")
    parser.add_argument("--top-k", type=int, default=5, help="Results per query per mode (default: 5)")
    parser.add_argument("--modes", default="dense,sparse,hybrid,cc",
                        help="Comma-separated modes (default: dense,sparse,hybrid,cc)")
    args = parser.parse_args()

    modes = [m.strip() for m in args.modes.split(",")]
    invalid = [m for m in modes if m not in ALL_MODES]
    if invalid:
        print(f"ERROR: Unknown modes: {invalid}. Valid: {ALL_MODES}")
        sys.exit(1)

    run_sandbox(args.collection, args.queries, args.top_k, modes)
