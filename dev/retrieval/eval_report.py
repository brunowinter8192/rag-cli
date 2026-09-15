# INFRASTRUCTURE
from datetime import datetime
from pathlib import Path

from eval_config import SWEEP_RANGES, THRESHOLD_IGNORED_MODES, PREFIX_NOOP_MODES


# FUNCTIONS

def _format_ranks(ranks: list[int]) -> str:
    if not ranks:
        return "-"
    return ", ".join(str(r) for r in ranks)


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


def _query_result_lines(qi: int, qr: dict) -> list[str]:
    entry = qr["entry"]
    doc_match = qr["doc_match"]
    snippet_match = qr["snippet_match"]

    doc_found = sum(1 for d in doc_match if d["found"])
    doc_total = len(doc_match)
    doc_pct = int(100 * doc_found / doc_total) if doc_total else 0

    snip_found = sum(1 for s in snippet_match if s["found"])
    snip_total = len(snippet_match)
    snip_pct = int(100 * snip_found / snip_total) if snip_total else 0

    lines = [f"", f"## Query {qi}: \"{entry['query']}\"", f""]
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
    return lines


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
        lines += _query_result_lines(qi, qr)

    lines += _build_summary(query_results)

    report_path.write_text("\n".join(lines) + "\n")
    print(f"Report: {report_path}")


def _collect_query_stats(query_results: list[dict]) -> dict:
    doc_recalls, snip_recalls, ndcg_vals, mrr_vals, recall_k_vals = [], [], [], [], []
    full_doc_match = full_snip_match = zero_snip_match = 0
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

    return {
        "doc_recalls": doc_recalls, "snip_recalls": snip_recalls,
        "ndcg_vals": ndcg_vals, "mrr_vals": mrr_vals, "recall_k_vals": recall_k_vals,
        "full_doc_match": full_doc_match, "full_snip_match": full_snip_match, "zero_snip_match": zero_snip_match,
        "type_stats": type_stats,
    }


def _summary_aggregate_lines(stats: dict, query_results: list[dict], top_k_label, k_label) -> list[str]:
    total = len(query_results)
    avg_doc = sum(stats["doc_recalls"]) / total if total else 0
    avg_snip = sum(stats["snip_recalls"]) / total if total else 0
    avg_ndcg = sum(stats["ndcg_vals"]) / total if total else 0
    avg_mrr = sum(stats["mrr_vals"]) / total if total else 0
    avg_recall_k = sum(stats["recall_k_vals"]) / total if total else 0
    lat_vals = [qr.get("latency_ms", 0.0) for qr in query_results]
    mean_lat = sum(lat_vals) / total if total else 0

    return [
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
        f"| Queries with 100% doc match | {stats['full_doc_match']}/{total} |",
        f"| Queries with 100% snippet match | {stats['full_snip_match']}/{total} |",
        f"| Queries with 0 snippet match | {stats['zero_snip_match']}/{total} |",
    ]


def _type_breakdown_lines(type_stats: dict, k_label) -> list[str]:
    lines = [
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


def _build_summary(query_results: list[dict]) -> list[str]:
    stats = _collect_query_stats(query_results)
    top_k_label = len(query_results[0]["hits"]) if query_results else "?"
    k_label = query_results[0]["rank_metrics"]["k"] if query_results and query_results[0].get("rank_metrics") else top_k_label

    lines = _summary_aggregate_lines(stats, query_results, top_k_label, k_label)
    lines += _type_breakdown_lines(stats["type_stats"], k_label)
    return lines


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
