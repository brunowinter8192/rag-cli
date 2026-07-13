# INFRASTRUCTURE

import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "indexing"))
from p4_db import get_connection  # noqa: E402 — sys.path must be set first

QUERIES_PATH = Path(__file__).parent.parent / "retrieval" / "queries_test_db.json"
REPORTS_DIR = Path(__file__).parent / "md"
COLLECTION = "test_db"
DB_NAME = "rag_test"


# ORCHESTRATOR

def coverage_workflow() -> None:
    queries = _load_queries()
    chunks_by_doc = _load_chunks()
    results = _check_all_quotes(queries, chunks_by_doc)
    report_path = _write_report(results, queries)
    print(f"Report: {report_path}")


# FUNCTIONS

def _load_queries() -> list[dict]:
    data = json.loads(QUERIES_PATH.read_text())
    return data["queries"]


def _load_chunks() -> dict[str, list[dict]]:
    conn = get_connection(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT content, document, chunk_index, total_chunks
        FROM documents
        WHERE collection = %s
        ORDER BY document, chunk_index
    """, (COLLECTION,))
    rows = cur.fetchall()
    conn.close()
    by_doc: dict[str, list[dict]] = {}
    for content, document, chunk_index, total_chunks in rows:
        by_doc.setdefault(document, []).append({
            "content": content,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
        })
    return by_doc


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _check_quote(quote: str, doc: str, expected_chunk_index: int, chunks_by_doc: dict) -> dict:
    q_norm = _normalize(quote)
    doc_chunks = chunks_by_doc.get(doc, [])
    # Index chunks by chunk_index for O(1) lookup
    by_idx = {c["chunk_index"]: c for c in doc_chunks}

    # Single-chunk verbatim match (across all chunks in the doc)
    for chunk in doc_chunks:
        if q_norm in _normalize(chunk["content"]):
            return {
                "status": "single",
                "matched_chunk_index": chunk["chunk_index"],
                "expected_chunk_index": expected_chunk_index,
                "index_match": chunk["chunk_index"] == expected_chunk_index,
            }

    # Boundary-split match: concat adjacent pairs (chunk_i + chunk_{i+1})
    for chunk in doc_chunks:
        ci = chunk["chunk_index"]
        if ci + 1 not in by_idx:
            continue
        pair_text = _normalize(chunk["content"] + " " + by_idx[ci + 1]["content"])
        if q_norm in pair_text:
            return {
                "status": "boundary",
                "boundary_chunks": (ci, ci + 1),
                "expected_chunk_index": expected_chunk_index,
            }

    return {
        "status": "missing",
        "expected_chunk_index": expected_chunk_index,
        "doc_found": doc in chunks_by_doc,
    }


def _check_all_quotes(queries: list[dict], chunks_by_doc: dict) -> list[dict]:
    results = []
    for qi, query in enumerate(queries, 1):
        for chunk_spec in query["expected_chunks"]:
            doc = chunk_spec["document"]
            quote = chunk_spec["identifying_quote"]
            expected_idx = chunk_spec["chunk_index"]
            check = _check_quote(quote, doc, expected_idx, chunks_by_doc)
            results.append({
                "query_num": qi,
                "query_text": query["query"],
                "document": doc,
                "quote": quote,
                **check,
            })
    return results


def _write_report(results: list[dict], queries: list[dict]) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"coverage_{ts}.md"

    total = len(results)
    single = [r for r in results if r["status"] == "single"]
    boundary = [r for r in results if r["status"] == "boundary"]
    missing = [r for r in results if r["status"] == "missing"]
    wrong_chunk = [r for r in single if not r.get("index_match")]

    lines = [
        "# Identifying-Quote Verbatim Coverage Audit",
        "",
        f"**Timestamp:** {ts}",
        f"**Collection:** {COLLECTION}",
        f"**Queries:** {len(queries)} | **Total quotes:** {total}",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"| Status | Count | % |",
        f"|---|---|---|",
        f"| Single-chunk verbatim match | {len(single)} | {len(single)/total:.0%} |",
        f"| Boundary-split match (spans 2 chunks) | {len(boundary)} | {len(boundary)/total:.0%} |",
        f"| Not found (no verbatim match anywhere) | {len(missing)} | {len(missing)/total:.0%} |",
        f"| **Total** | **{total}** | **100%** |",
        "",
    ]

    if wrong_chunk:
        lines += [
            f"**Single-chunk index mismatches (found in different chunk than expected):** {len(wrong_chunk)}",
            "",
        ]

    # Per-query table
    lines += [
        "## Per-Query Status",
        "",
        "| Q# | Document | Quote (truncated) | Status | Detail |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        q_short = r["quote"][:55] + ("…" if len(r["quote"]) > 55 else "")
        doc_short = r["document"].replace(".md", "")
        if r["status"] == "single":
            idx = r["matched_chunk_index"]
            exp = r["expected_chunk_index"]
            detail = f"chunk {idx}" + (f" (expected {exp})" if not r["index_match"] else "")
        elif r["status"] == "boundary":
            a, b = r["boundary_chunks"]
            detail = f"spans chunk {a}+{b} (expected {r['expected_chunk_index']})"
        else:
            detail = "not found verbatim"
        lines.append(f"| Q{r['query_num']} | {doc_short} | `{q_short}` | **{r['status']}** | {detail} |")

    # Detail section for non-single results
    if boundary or missing:
        lines += ["", "---", "", "## Problem Quotes Detail", ""]

    for r in boundary:
        a, b = r["boundary_chunks"]
        lines += [
            f"### Q{r['query_num']} — Boundary Split",
            "",
            f"**Query:** {r['query_text']}",
            f"**Document:** {r['document']}",
            f"**Quote:** `{r['quote']}`",
            f"**Expected chunk:** {r['expected_chunk_index']}",
            f"**Found across:** chunk {a} + chunk {b}",
            "",
        ]

    for r in missing:
        lines += [
            f"### Q{r['query_num']} — Not Found",
            "",
            f"**Query:** {r['query_text']}",
            f"**Document:** {r['document']}",
            f"**Quote:** `{r['quote']}`",
            f"**Expected chunk:** {r['expected_chunk_index']}",
            f"**Doc in index:** {'yes' if r['doc_found'] else 'NO — document missing entirely'}",
            "",
        ]

    # Wrong-index detail
    if wrong_chunk:
        lines += ["---", "", "## Index-Mismatch Detail (found but in wrong chunk)", ""]
        for r in wrong_chunk:
            lines += [
                f"### Q{r['query_num']} — Index Mismatch",
                "",
                f"**Quote:** `{r['quote']}`",
                f"**Document:** {r['document']}",
                f"**Expected chunk:** {r['expected_chunk_index']} | **Actual chunk:** {r['matched_chunk_index']}",
                "",
            ]

    path.write_text("\n".join(lines) + "\n")
    return path


if __name__ == "__main__":
    coverage_workflow()
