# INFRASTRUCTURE
from datetime import datetime
from pathlib import Path


# FUNCTIONS

def _cross_table_block(param1: str, param2: str, values1: list, values2: list, results: dict, cell_fn) -> list[str]:
    col_header = " | ".join(f"{param2}={v}" for v in values2)
    sep = " | ".join("---" for _ in values2)
    lines = [f"| {param1} \\ {param2} | {col_header} |", f"|---|{sep}|"]
    for v1 in values1:
        cells = [cell_fn(results[(v1, v2)]) for v2 in values2]
        lines.append(f"| {v1} | " + " | ".join(cells) + " |")
    return lines


def _cross_best_cell(results: dict) -> tuple:
    best_key = max(results.keys(), key=lambda k: (results[k][1], results[k][2]))
    return best_key, results[best_key]


def _cross_header_lines(param1: str, param2: str, values1: list, values2: list, base_config: dict, timestamp: str) -> list[str]:
    fixed = {k: v for k, v in base_config.items() if k not in (param1, param2)}
    fixed_str = ", ".join(f"{k}={v}" for k, v in fixed.items())
    return [
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


def _cross_primary_block(param1: str, param2: str, values1: list, values2: list, results: dict) -> tuple[list[str], tuple, tuple]:
    lines = _cross_table_block(param1, param2, values1, values2, results,
        lambda r: f"{r[1]:.0%} ({r[2]:.3f}) [{r[5]:.0f}ms]")
    best_key, best = _cross_best_cell(results)
    lines += [
        f"",
        f"**Best cell:** `{param1}={best_key[0]}, {param2}={best_key[1]}` — snippet_recall={best[1]:.0%}, NDCG={best[2]:.3f}, MRR={best[3]:.3f}",
    ]
    return lines, best_key, best


def _cross_secondary_sections(param1: str, param2: str, values1: list, values2: list, results: dict) -> list[str]:
    lines = [f"", f"---", f"", f"## Secondary: NDCG@K", f""]
    lines += _cross_table_block(param1, param2, values1, values2, results, lambda r: f"{r[2]:.3f}")

    lines += [f"", f"## Secondary: MRR@K", f""]
    lines += _cross_table_block(param1, param2, values1, values2, results, lambda r: f"{r[3]:.3f}")

    lines += [f"", f"## Secondary: Recall@K (chunk-level)", f""]
    lines += _cross_table_block(param1, param2, values1, values2, results, lambda r: f"{r[4]:.1%}")

    lines += [f"", f"## Secondary: Doc Recall (diagnostic)", f""]
    lines += _cross_table_block(param1, param2, values1, values2, results, lambda r: f"{r[0]:.0%}")

    lines += [f"", f"## Secondary: Latency (mean_warm_ms)", f""]
    lines += _cross_table_block(param1, param2, values1, values2, results, lambda r: f"{r[5]:.0f}ms")

    return lines


def _cross_summary_section(param1: str, param2: str, best_key: tuple, best: tuple) -> list[str]:
    return [
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


def _cross_notes_section(param1: str, param2: str, values1: list, values2: list, results: dict) -> list[str]:
    lines = []
    if param2 == "top_k":
        lines.append("**Notes:**")
        for v1 in values1:
            snips = [results[(v1, v2)][1] for v2 in values2]
            max_gain = max(snips) - min(snips)
            if max_gain >= 0.10:
                peak_v2 = values2[snips.index(max(snips))]
                lines.append(f"- `{param1}={v1}`: snippet_recall spans {min(snips):.0%}–{max(snips):.0%} (gain {max_gain:.0%}); peaks at {param2}={peak_v2}")
        lines.append("")
    return lines


def _write_cross_sweep_report(results: dict, param1: str, param2: str, values1: list, values2: list, base_config: dict) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path(__file__).parent / "md"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"cross_{param1}_{param2}_{base_config['collection']}_{timestamp}.md"

    lines = _cross_header_lines(param1, param2, values1, values2, base_config, timestamp)
    primary_lines, best_key, best = _cross_primary_block(param1, param2, values1, values2, results)
    lines += primary_lines
    lines += _cross_secondary_sections(param1, param2, values1, values2, results)
    lines += _cross_summary_section(param1, param2, best_key, best)
    lines += _cross_notes_section(param1, param2, values1, values2, results)

    report_path.write_text("\n".join(lines) + "\n")
    print(f"Cross-sweep report: {report_path}")
