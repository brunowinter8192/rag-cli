# INFRASTRUCTURE

import importlib
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# From src/rag/db.py: read-only connection + chunk fetch helpers (prod `rag` DB)
_db = importlib.import_module(".".join(["src", "rag", "db"]))
# From src/rag/retriever.py: real find_overlap under test (loaded dynamically so this
# module still passes as dependency-free — see A_overlap_match_probe usage note in DOCS.md)
_retriever = importlib.import_module(".".join(["src", "rag", "retriever"]))

get_connection = _db.get_connection
query_documents = _db.query_documents
fetch_chunk_range = _db.fetch_chunk_range
find_overlap = _retriever.find_overlap

COLLECTIONS = ["github_releases", "rag-cli-docs", "trading-reference"]
RAISED_CAP = 2000
RESIDUAL_EXCERPT_CHARS = 150
REPORT_DIR = Path(__file__).parent / "md"
REPORT_DIR.mkdir(exist_ok=True)


# ORCHESTRATOR

def probe_workflow() -> None:
    all_pairs = collect_pairs(COLLECTIONS)
    results = measure_all_variants(all_pairs)
    report_path = write_report(results)
    print_summary(results)
    print(f"\nFull detail written to: {report_path}")


# FUNCTIONS

# Pull all adjacent chunk pairs (chunk_index i, i+1) per document, for each collection
def collect_pairs(collections: list[str]) -> list[dict]:
    conn = get_connection(purpose="read")
    pairs = []
    for collection in collections:
        docs = query_documents(conn, collection)
        for doc in docs:
            document = doc["document"]
            chunks = fetch_chunk_range(conn, collection, document, 0, 10**7)
            for i in range(len(chunks) - 1):
                pairs.append({
                    "collection": collection,
                    "document": document,
                    "chunk_index": chunks[i]["chunk_index"],
                    "text1": chunks[i]["content"],
                    "text2": chunks[i + 1]["content"],
                })
    conn.close()
    return pairs


# Collapse whitespace runs to a single space; return normalized text + map from
# normalized index back to the original-text index (mapping[-1] == len(text))
def normalize_with_map(text: str) -> tuple[str, list[int]]:
    norm_chars = []
    idx_map = []
    i = 0
    n = len(text)
    while i < n:
        if text[i].isspace():
            norm_chars.append(" ")
            idx_map.append(i)
            while i < n and text[i].isspace():
                i += 1
        else:
            norm_chars.append(text[i])
            idx_map.append(i)
            i += 1
    idx_map.append(n)
    return "".join(norm_chars), idx_map


# Variant (c): whitespace-normalized suffix/prefix match, cut position mapped back
# to the exact (unnormalized) index in text2 so it stays usable by merge_chunks
def find_overlap_ws_tolerant(text1: str, text2: str, max_overlap: int = RAISED_CAP) -> int:
    norm1, _ = normalize_with_map(text1)
    norm2, map2 = normalize_with_map(text2)
    for size in range(min(len(norm1), len(norm2), max_overlap), 0, -1):
        if norm1[-size:] == norm2[:size]:
            return map2[size]
    return 0


# Run variants (a) current cap 300, (b) raised cap, (c) raised cap + ws-tolerant on every pair.
# Also tracks where (b) and (c) disagree — that gap isolates the whitespace-asymmetry mechanism
# from the cap mechanism, since both variants share the same raised cap.
def measure_all_variants(pairs: list[dict]) -> dict:
    per_collection = {}
    for pair in pairs:
        collection = pair["collection"]
        text1, text2 = pair["text1"], pair["text2"]
        a = find_overlap(text1, text2)
        b = find_overlap(text1, text2, max_overlap=RAISED_CAP)
        c = find_overlap_ws_tolerant(text1, text2, max_overlap=RAISED_CAP)

        bucket = per_collection.setdefault(collection, {
            "a": [], "b": [], "c": [], "residual_c": [], "b_vs_c_diffs": [], "pairs": [],
        })
        bucket["a"].append(a)
        bucket["b"].append(b)
        bucket["c"].append(c)
        bucket["pairs"].append(pair)
        if c == 0:
            bucket["residual_c"].append({
                "document": pair["document"],
                "chunk_index": pair["chunk_index"],
                "tail1": text1[-RESIDUAL_EXCERPT_CHARS:],
                "head2": text2[:RESIDUAL_EXCERPT_CHARS],
            })
        if b != c:
            bucket["b_vs_c_diffs"].append({
                "document": pair["document"],
                "chunk_index": pair["chunk_index"],
                "b": b,
                "c": c,
                "tail1": text1[-RESIDUAL_EXCERPT_CHARS:],
                "head2": text2[:RESIDUAL_EXCERPT_CHARS],
            })
    return per_collection


# Distribution summary for one variant's match-length list
def summarize_variant(values: list[int]) -> dict:
    if not values:
        return {"n": 0, "zero_pct": 0.0, "min": 0, "max": 0, "mean": 0.0, "median": 0}
    zero = sum(1 for v in values if v == 0)
    return {
        "n": len(values),
        "zero_pct": round(100 * zero / len(values), 1),
        "min": min(values),
        "max": max(values),
        "mean": round(statistics.mean(values), 1),
        "median": statistics.median(values),
    }


def print_summary(results: dict) -> None:
    print(f"{'collection':<20} {'pairs':>6}  {'a zero%':>8} {'b zero%':>8} {'c zero%':>8}")
    for collection, bucket in results.items():
        sa = summarize_variant(bucket["a"])
        sb = summarize_variant(bucket["b"])
        sc = summarize_variant(bucket["c"])
        print(f"{collection:<20} {sa['n']:>6}  {sa['zero_pct']:>7}% {sb['zero_pct']:>7}% {sc['zero_pct']:>7}%")


# Lowest/highest non-zero (b) match in a collection — sanity-check outliers
def extremes_section(bucket: dict) -> list[str]:
    b_values = bucket["b"]
    pairs = bucket["pairs"]
    nonzero = [(v, p) for v, p in zip(b_values, pairs) if v > 0]
    if not nonzero:
        return []
    min_v, min_p = min(nonzero, key=lambda x: x[0])
    max_v, max_p = max(nonzero, key=lambda x: x[0])
    lines = ["### Extremes of variant (b) match length", ""]
    for label, v, p in [("min", min_v, min_p), ("max", max_v, max_p)]:
        lines.append(f"- {label}={v}: `{p['document']}` @ chunk_index {p['chunk_index']}")
        lines.append(f"  - tail1: `{p['text1'][-RESIDUAL_EXCERPT_CHARS:]!r}`")
        lines.append(f"  - head2: `{p['text2'][:RESIDUAL_EXCERPT_CHARS]!r}`")
    lines.append("")
    return lines


def write_report(results: dict) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"probe_output_{timestamp}.md"
    lines = ["# Overlap match probe — raw output", ""]
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"Collections: {', '.join(results.keys())}")
    lines.append(f"Variants: (a) find_overlap cap=300 (current), (b) find_overlap cap={RAISED_CAP}, "
                 f"(c) whitespace-tolerant cap={RAISED_CAP}")
    lines.append("")

    lines.append("## Overall (all collections combined)")
    lines.append("")
    for variant_key, label in [("a", "(a) cap=300"), ("b", f"(b) cap={RAISED_CAP}"), ("c", f"(c) ws-tolerant cap={RAISED_CAP}")]:
        combined = [v for bucket in results.values() for v in bucket[variant_key]]
        s = summarize_variant(combined)
        lines.append(f"- {label}: n={s['n']} zero%={s['zero_pct']} min={s['min']} max={s['max']} "
                     f"mean={s['mean']} median={s['median']}")
    total_diffs = sum(len(b["b_vs_c_diffs"]) for b in results.values())
    lines.append(f"- (b) vs (c) disagreements: {total_diffs}")
    lines.append("")

    for collection, bucket in results.items():
        lines.append(f"## {collection}")
        lines.append("")
        for variant_key, label in [("a", "(a) cap=300"), ("b", f"(b) cap={RAISED_CAP}"), ("c", f"(c) ws-tolerant cap={RAISED_CAP}")]:
            s = summarize_variant(bucket[variant_key])
            lines.append(f"- {label}: n={s['n']} zero%={s['zero_pct']} min={s['min']} max={s['max']} "
                         f"mean={s['mean']} median={s['median']}")
        lines.append("")

        residual = bucket["residual_c"]
        lines.append(f"### Residual zero-match pairs under variant (c): {len(residual)}")
        lines.append("")
        for r in residual:
            lines.append(f"- `{r['document']}` @ chunk_index {r['chunk_index']}")
            lines.append(f"  - tail1: `{r['tail1']!r}`")
            lines.append(f"  - head2: `{r['head2']!r}`")
        lines.append("")

        diffs = bucket["b_vs_c_diffs"]
        lines.append(f"### Pairs where (b) and (c) disagree (isolates whitespace mechanism): {len(diffs)}")
        lines.append("")
        for d in diffs[:20]:
            lines.append(f"- `{d['document']}` @ chunk_index {d['chunk_index']}: b={d['b']} c={d['c']}")
            lines.append(f"  - tail1: `{d['tail1']!r}`")
            lines.append(f"  - head2: `{d['head2']!r}`")
        if len(diffs) > 20:
            lines.append(f"  - ... {len(diffs) - 20} more not shown")
        lines.append("")

        lines.extend(extremes_section(bucket))

    path.write_text("\n".join(lines))
    return path


if __name__ == "__main__":
    probe_workflow()
