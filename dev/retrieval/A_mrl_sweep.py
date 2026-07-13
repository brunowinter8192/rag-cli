# INFRASTRUCTURE
import json
import sys
from datetime import datetime
from pathlib import Path

import httpx
import numpy as np
import psycopg2
from pgvector.psycopg2 import register_vector

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "indexing"))

import p2_embedder
from p1_retriever import retrieve_sparse

COLLECTION = "RAG_MCP_test"
DIMENSIONS = [256, 512, 768, 1024, 2048, 4096]
TOP_K = 10
CANDIDATES = 50
RRF_K = 60
QUERIES_PATH = Path(__file__).parent / "queries_rag_mcp_test.json"
REPORTS_DIR = Path(__file__).parent / "md"
INSTRUCT_PREFIX = "Instruct: Given a search query, retrieve relevant passages that answer the query\nQuery: "
EMBEDDING_HEALTH_URL = "http://localhost:8081/health"
SPLADE_HEALTH_URL = "http://localhost:8083/health"

DB_HOST = "localhost"
DB_PORT = 5433
DB_USER = "rag"
DB_PASSWORD = "rag"
DB_NAME = "rag_test"


# ORCHESTRATOR

def run_mrl_sweep() -> None:
    _check_embedding_server()
    _check_splade_server()
    queries = _load_queries()
    print(f"Loaded {len(queries)} queries")

    conn = _get_connection()
    print("Fetching document embeddings from DB...")
    doc_rows = _fetch_document_embeddings(conn, COLLECTION)
    print(f"Fetched {len(doc_rows)} document chunks")
    conn.close()

    print("Embedding queries at full 4096d...")
    query_embeddings = _embed_queries(queries)

    print("Fetching sparse results per query (once for all dimensions)...")
    sparse_results_per_query = _fetch_sparse_results(queries)

    dim_results = {}
    for dim in DIMENSIONS:
        print(f"Evaluating {dim}d...")
        dim_results[dim] = _evaluate_dimension(
            queries, query_embeddings, doc_rows, dim, sparse_results_per_query
        )

    _write_report(queries, dim_results)


# FUNCTIONS

# Verify dense embedding server is reachable before starting
def _check_embedding_server() -> None:
    try:
        resp = httpx.get(EMBEDDING_HEALTH_URL, timeout=3.0)
        if resp.status_code != 200:
            print(f"ERROR: embedding server unhealthy (HTTP {resp.status_code}). Run: ./start.sh")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: embedding server not reachable ({e}). Run: ./start.sh")
        sys.exit(1)


# Verify SPLADE server is reachable before starting
def _check_splade_server() -> None:
    try:
        resp = httpx.get(SPLADE_HEALTH_URL, timeout=3.0)
        if resp.status_code != 200:
            print(f"ERROR: SPLADE server unhealthy (HTTP {resp.status_code}). Run: ./start.sh")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: SPLADE server not reachable ({e}). Run: ./start.sh")
        sys.exit(1)


# Load query list from queries_rag_mcp_test.json
def _load_queries() -> list[dict]:
    with open(QUERIES_PATH) as f:
        data = json.load(f)
    return data["queries"]


# Open psycopg2 connection to rag_test with pgvector registered
def _get_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME,
    )
    register_vector(conn)
    return conn


# Fetch all document rows with embeddings for a collection
def _fetch_document_embeddings(conn, collection: str) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT content, collection, document, chunk_index, embedding FROM documents WHERE collection = %s",
            (collection,),
        )
        rows = cur.fetchall()
    return [
        {
            "content": row[0],
            "collection": row[1],
            "document": row[2],
            "chunk_index": row[3],
            "embedding": np.array(row[4], dtype=np.float32),
        }
        for row in rows
    ]


# Embed all queries at full model dimension (4096d), return as numpy arrays
def _embed_queries(queries: list[dict]) -> list[np.ndarray]:
    texts = [q["query"] for q in queries]
    raw = p2_embedder.embed(texts, prefix=INSTRUCT_PREFIX)
    return [np.array(emb, dtype=np.float32) for emb in raw]


# Fetch SPLADE sparse top-CANDIDATES results for each query (dimension-independent)
def _fetch_sparse_results(queries: list[dict]) -> list[list[dict]]:
    results = []
    for q in queries:
        sparse_hits = retrieve_sparse(q["query"], COLLECTION, top_k=CANDIDATES)
        results.append(sparse_hits)
    return results


# Truncate a vector to dim and L2-normalize
def _truncate_normalize(vec: np.ndarray, dim: int) -> np.ndarray:
    v = vec[:dim].copy()
    norm = np.linalg.norm(v)
    if norm > 0:
        v = v / norm
    return v


# Fuse dense and sparse candidate lists using Reciprocal Rank Fusion
def _rrf_fuse(dense_candidates: list[dict], sparse_candidates: list[dict]) -> list[dict]:
    scores: dict = {}
    chunks: dict = {}
    for rank, r in enumerate(dense_candidates, 1):
        key = (r["document"], r["chunk_index"])
        scores[key] = scores.get(key, 0.0) + 1.0 / (RRF_K + rank)
        chunks[key] = r
    for rank, r in enumerate(sparse_candidates, 1):
        key = (r["document"], r["chunk_index"])
        scores[key] = scores.get(key, 0.0) + 1.0 / (RRF_K + rank)
        if key not in chunks:
            chunks[key] = r
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [{**chunks[key], "score": round(score, 6)} for key, score in ranked[:TOP_K]]


# Evaluate all queries at a single MRL dimension, return dense and hybrid results
def _evaluate_dimension(
    queries: list[dict],
    query_embeddings: list[np.ndarray],
    doc_rows: list[dict],
    dim: int,
    sparse_results_per_query: list[list[dict]],
) -> dict:
    doc_embs = np.stack([_truncate_normalize(row["embedding"], dim) for row in doc_rows])

    dense_results = []
    hybrid_results = []

    for query, qemb_full, sparse_top in zip(queries, query_embeddings, sparse_results_per_query):
        qvec = _truncate_normalize(qemb_full, dim)
        scores = doc_embs @ qvec
        top_candidate_indices = np.argsort(scores)[::-1][:CANDIDATES]

        dense_candidates = []
        for idx in top_candidate_indices:
            row = doc_rows[idx]
            dense_candidates.append({
                "content": row["content"],
                "document": row["document"],
                "chunk_index": row["chunk_index"],
                "score": float(scores[idx]),
            })

        dense_hits = dense_candidates[:TOP_K]
        hybrid_hits = _rrf_fuse(dense_candidates, sparse_top)

        dm_dense = _check_document_match(query["expected_documents"], dense_hits)
        sm_dense = _check_snippet_match(query["expected_snippets"], dense_hits)
        dense_results.append({"entry": query, "hits": dense_hits, "doc_match": dm_dense, "snippet_match": sm_dense})

        dm_hybrid = _check_document_match(query["expected_documents"], hybrid_hits)
        sm_hybrid = _check_snippet_match(query["expected_snippets"], hybrid_hits)
        hybrid_results.append({"entry": query, "hits": hybrid_hits, "doc_match": dm_hybrid, "snippet_match": sm_hybrid})

    return {"dense": dense_results, "hybrid": hybrid_results}


# Check which expected documents appear in hits
def _check_document_match(expected_docs: list[str], hits: list[dict]) -> list[dict]:
    results = []
    for doc in expected_docs:
        ranks = [rank for rank, h in enumerate(hits, 1) if h.get("document") == doc]
        results.append({"doc": doc, "found": bool(ranks), "ranks": ranks})
    return results


# Check which expected snippets appear as substrings in any hit's content
def _check_snippet_match(expected_snippets: list[str], hits: list[dict]) -> list[dict]:
    results = []
    for snippet in expected_snippets:
        found_rank = None
        for rank, h in enumerate(hits, 1):
            if snippet.lower() in h.get("content", "").lower():
                found_rank = rank
                break
        results.append({"snippet": snippet, "found": found_rank is not None, "rank": found_rank})
    return results


# Compute aggregate metrics from per-query results list
def _compute_metrics(query_results: list[dict]) -> dict:
    doc_recalls = []
    snip_recalls = []
    for qr in query_results:
        dm = qr["doc_match"]
        sm = qr["snippet_match"]
        doc_r = sum(1 for d in dm if d["found"]) / len(dm) if dm else 0.0
        snip_r = sum(1 for s in sm if s["found"]) / len(sm) if sm else 0.0
        doc_recalls.append(doc_r)
        snip_recalls.append(snip_r)
    total = len(query_results)
    avg_doc = sum(doc_recalls) / total if total else 0.0
    avg_snip = sum(snip_recalls) / total if total else 0.0
    full_doc = sum(1 for r in doc_recalls if r == 1.0)
    full_snip = sum(1 for r in snip_recalls if r == 1.0)
    return {
        "avg_doc": avg_doc,
        "avg_snip": avg_snip,
        "full_doc": full_doc,
        "full_snip": full_snip,
        "doc_recalls": doc_recalls,
        "snip_recalls": snip_recalls,
    }


# Build summary table with one row per (dimension, mode) pair
def _build_summary_table(dim_results: dict) -> list[str]:
    total = len(next(iter(dim_results.values()))["dense"])
    lines = [
        "## Summary",
        "",
        "| Dimension | Mode | Doc Recall @10 | Snippet Recall @10 | 100% Doc Match | 100% Snippet Match |",
        "|-----------|------|---------------|-------------------|----------------|-------------------|",
    ]
    for dim in DIMENSIONS:
        for mode in ("dense", "hybrid"):
            m = _compute_metrics(dim_results[dim][mode])
            lines.append(
                f"| {dim}d | {mode} | {m['avg_doc']:.0%} | {m['avg_snip']:.0%}"
                f" | {m['full_doc']}/{total} | {m['full_snip']}/{total} |"
            )
    return lines


# Build by-query-type breakdown table (type x dimension x mode)
def _build_type_table(queries: list[dict], dim_results: dict) -> list[str]:
    types = sorted(set(q["type"] for q in queries))
    lines = [
        "",
        "## By Query Type",
        "",
        "| Type | Dim | Mode | Doc Recall | Snippet Recall |",
        "|------|-----|------|-----------|---------------|",
    ]
    for qtype in types:
        indices = [i for i, q in enumerate(queries) if q["type"] == qtype]
        for dim in DIMENSIONS:
            for mode in ("dense", "hybrid"):
                qrs = [dim_results[dim][mode][i] for i in indices]
                m = _compute_metrics(qrs)
                lines.append(
                    f"| {qtype} | {dim}d | {mode} | {m['avg_doc']:.0%} | {m['avg_snip']:.0%} |"
                )
    return lines


# Build per-query breakdown for queries where any metric differs across dims or modes
def _build_per_query_breakdown(queries: list[dict], dim_results: dict) -> list[str]:
    lines = ["", "## Per-Query Breakdown (queries where results differ across dimensions or modes)", ""]
    any_entry = False

    for i, query in enumerate(queries):
        per_dim_mode = {}
        for dim in DIMENSIONS:
            for mode in ("dense", "hybrid"):
                qr = dim_results[dim][mode][i]
                dm = qr["doc_match"]
                sm = qr["snippet_match"]
                per_dim_mode[(dim, mode)] = {
                    "doc_found": sum(1 for d in dm if d["found"]),
                    "doc_total": len(dm),
                    "snip_found": sum(1 for s in sm if s["found"]),
                    "snip_total": len(sm),
                    "doc_match": dm,
                }

        all_doc_scores = [v["doc_found"] for v in per_dim_mode.values()]
        all_snip_scores = [v["snip_found"] for v in per_dim_mode.values()]
        if len(set(all_doc_scores)) == 1 and len(set(all_snip_scores)) == 1:
            continue

        any_entry = True
        lines.append(f"### Query {i + 1}: \"{query['query']}\"")
        lines.append("")
        lines.append("| Dim | Mode | Doc Recall | Snippet Recall | Missing Docs |")
        lines.append("|-----|------|-----------|---------------|-------------|")

        for dim in DIMENSIONS:
            for mode in ("dense", "hybrid"):
                pd = per_dim_mode[(dim, mode)]
                missing = [d["doc"] for d in pd["doc_match"] if not d["found"]]
                missing_str = ", ".join(missing) if missing else "-"
                lines.append(
                    f"| {dim}d | {mode} | {pd['doc_found']}/{pd['doc_total']}"
                    f" | {pd['snip_found']}/{pd['snip_total']}"
                    f" | {missing_str} |"
                )
        lines.append("")

    if not any_entry:
        lines.append("*All queries produce identical results across all dimensions and modes.*")
        lines.append("")

    return lines


# Write final MD report to md/
def _write_report(queries: list[dict], dim_results: dict) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"mrl_sweep_{timestamp}.md"

    lines = [
        f"# MRL Dimension Sweep: {COLLECTION}",
        "",
        f"**Timestamp:** {timestamp}  ",
        f"**Dimensions tested:** {', '.join(str(d) for d in DIMENSIONS)}  ",
        f"**Modes:** dense, hybrid (dense + SPLADE-v3 RRF K={RRF_K})  ",
        f"**Queries:** {len(queries)} | **Top-k:** {TOP_K} | **Candidates:** {CANDIDATES}",
        "",
        "---",
        "",
    ]

    lines += _build_summary_table(dim_results)
    lines += _build_type_table(queries, dim_results)
    lines += _build_per_query_breakdown(queries, dim_results)

    report_path.write_text("\n".join(lines) + "\n")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    run_mrl_sweep()
