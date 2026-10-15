# INFRASTRUCTURE
from dev.kvp.kvp_classify import rendered_output_chars

KIND_HIT = "hit"
KIND_ZERO = "zero"
STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_ERROR = "ERROR"
CHANGE_FIXED = "fixed"
CHANGE_REGRESSED = "regressed"
CHANGE_RANK_MOVED = "rank moved"
CHANGE_UNCHANGED = "unchanged"
CHANGE_NEW = "new case"


# FUNCTIONS

def evaluate_case(case: dict, record: dict, content_lines: list[dict]) -> dict:
    expect = case["expect"]
    rank = best_rank(record["hits"], expect.get("targets", []))
    passed = record["hit_count"] == 0 if expect["kind"] == KIND_ZERO else rank is not None
    return {
        "name": case["name"],
        "kind": expect["kind"],
        "status": STATUS_PASS if passed else STATUS_FAIL,
        "rank": rank,
        "result_count": record["hit_count"],
        "candidates": record["candidates"],
        "top_score": record["hits"][0]["score"] if record["hits"] else None,
        "duration_ms": record["duration_ms"],
        "output_chars": rendered_output_chars(record, sorted(content_lines, key=lambda l: l["rank"])),
        "code_version": record.get("code_version"),
        "fingerprint": record.get("config_fingerprint"),
        "error": None,
    }


def error_result(case: dict, message: str) -> dict:
    return {
        "name": case["name"], "kind": case["expect"]["kind"], "status": STATUS_ERROR, "rank": None,
        "result_count": None, "candidates": None, "top_score": None, "duration_ms": None,
        "output_chars": None, "code_version": None, "fingerprint": None, "error": message,
    }


def best_rank(hits: list[dict], targets: list[dict]) -> int | None:
    ranks = [
        hit["rank"] for hit in hits for target in targets
        if hit["document"] == target["document"] and hit["chunk_index"] in target["chunks"]
    ]
    return min(ranks) if ranks else None


def compare_runs(baseline: list[dict], current: list[dict]) -> list[dict]:
    baseline_by_name = {r["name"]: r for r in baseline}
    return [_compare_case(baseline_by_name.get(r["name"]), r) for r in current]


def summarize(results: list[dict]) -> dict:
    return {
        "cases": len(results),
        "passed": sum(1 for r in results if r["status"] == STATUS_PASS),
        "failed": sum(1 for r in results if r["status"] == STATUS_FAIL),
        "errors": sum(1 for r in results if r["status"] == STATUS_ERROR),
    }


def render_canary_report(meta: dict, results: list[dict], comparison: list[dict] | None) -> str:
    sections = [
        _render_header(meta, summarize(results)),
        _render_results(results),
        _render_comparison(comparison, meta["baseline"]) if comparison is not None else "",
    ]
    return "\n\n".join(s for s in sections if s) + "\n"


def _compare_case(before: dict | None, after: dict) -> dict:
    return {
        "name": after["name"],
        "change": _change_kind(before, after),
        "before_status": before["status"] if before else None,
        "after_status": after["status"],
        "before_rank": before["rank"] if before else None,
        "after_rank": after["rank"],
        "before_count": before["result_count"] if before else None,
        "after_count": after["result_count"],
        "before_chars": before["output_chars"] if before else None,
        "after_chars": after["output_chars"],
    }


def _change_kind(before: dict | None, after: dict) -> str:
    if before is None:
        return CHANGE_NEW
    if before["status"] != STATUS_PASS and after["status"] == STATUS_PASS:
        return CHANGE_FIXED
    if before["status"] == STATUS_PASS and after["status"] != STATUS_PASS:
        return CHANGE_REGRESSED
    if before["rank"] != after["rank"]:
        return CHANGE_RANK_MOVED
    return CHANGE_UNCHANGED


def _render_header(meta: dict, summary: dict) -> str:
    lines = [
        "# KVP canary run",
        "",
        f"- Generated: {meta['generated']}",
        f"- Code version: {meta['code_version']}",
        f"- Cases file: `{meta['cases_file']}`",
        f"- Baseline: {meta['baseline'] or 'none'}",
        f"- Cases: {summary['cases']}, passed {summary['passed']}, failed {summary['failed']}, errors {summary['errors']}",
        f"- Production log untouched: {meta['isolation']}",
        "- A hit case passes when an expected (document, chunk) appears anywhere in the returned list, whatever its length. The result count is recorded per case and never assumed.",
        "- Rank is the position in the returned list; compare ranks only between runs that return lists of the same length.",
        "- Docs collections are re-indexed and shift chunk indexes; the cases therefore use reference collections.",
    ]
    return "\n".join(lines)


def _render_results(results: list[dict]) -> str:
    rows = [
        [r["name"], r["kind"], r["status"], r["rank"] or "-", r["result_count"], r["candidates"], r["top_score"], r["duration_ms"], r["output_chars"], r["fingerprint"] or "-", r["error"] or ""]
        for r in results
    ]
    headers = ["case", "kind", "status", "rank of expected hit", "results", "candidates", "top score", "ms", "output chars", "fingerprint", "error"]
    return "## Results\n\n" + _table(headers, rows)


def _render_comparison(comparison: list[dict], baseline_path: str | None) -> str:
    rows = [
        [c["name"], c["change"], f"{c['before_status']} -> {c['after_status']}", f"{c['before_rank']} -> {c['after_rank']}",
         f"{c['before_count']} -> {c['after_count']}", f"{c['before_chars']} -> {c['after_chars']}"]
        for c in comparison
    ]
    return f"## Comparison with baseline `{baseline_path}`\n\n" + _table(["case", "change", "status", "rank", "results", "output chars"], rows)


def _table(headers: list[str], rows: list[list]) -> str:
    if not rows:
        return "(none)"
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in row) + " |" for row in rows]
    return "\n".join(lines)
