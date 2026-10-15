# INFRASTRUCTURE
from dev.kvp.kvp_config import ALL_GROUP, PERSIST_THRESHOLD_CHARS, SCORE_PROFILE_RANKS


# FUNCTIONS

def render_report(meta: dict, data: dict) -> str:
    sections = [
        _render_header(meta),
        _render_technical(data),
        _render_relevance(data),
        _render_usefulness(data),
        _render_not_covered(),
    ]
    return "\n\n".join(sections) + "\n"


def _render_header(meta: dict) -> str:
    counts = ", ".join(f"{name}: {count}" for name, count in meta["counts"].items())
    lines = [
        "# KVP report",
        "",
        f"- Generated: {meta['generated']}",
        f"- Window: since {meta['since'] or 'beginning'} until {meta['until'] or 'now'}",
        f"- Log dir: `{meta['log_dir']}`",
        f"- Transcripts: `{meta['transcripts_glob']}`",
        f"- Records in window: {counts}",
        "- Every verdict is derived offline by `dev/kvp/`; the production logs hold facts only.",
        "- `code_version` is stamped on search and expand records written after the stamp change; older records appear as `unversioned`.",
        "- The time of day of the 2026-10-14 caller-rule change is unknown. Before/after comparisons of caller behaviour (cross-project reference reach) are possible at date granularity only, through `--since`/`--until`.",
        "- Transcript-based figures count only searches that joined a transcript call; the joined share is given under technical indicators.",
    ]
    return "\n".join(lines)


def _render_technical(data: dict) -> str:
    groups = data["groups"]
    main_rows = [
        [name, t["searches"], _ratio(t["provenance_complete"], t["searches"]),
         f"{t['zero_hit']} ({t['zero_hit_no_candidates']} with 0 candidates)",
         f"{t['partial']} (full list = {t['full_length']})", _ratio(t["cold"], t["searches"])]
        for name, g in groups.items() for t in [g["technical"]]
    ]
    latency_rows = [
        [name, t["cold"], t["cold_p50"], t["warm"], t["warm_p50"], t["warm_p90"], t["warm_max"]]
        for name, g in groups.items() for t in [g["technical"]]
    ]
    size_rows = [
        [name, t["output_p50"], t["output_p90"], t["output_max"], _ratio(t["output_over_threshold"], t["searches"])]
        for name, g in groups.items() for t in [g["technical"]]
    ]
    attempts = data["attempts"]
    return "\n\n".join([
        "## Technical",
        "### Provenance, empty and partial lists, cold starts (per code version)\n\nProvenance complete = fingerprint present and its registry entry names embedding preset and model plus reranker preset and model. Partial = 1 to (full list - 1) hits, where full list is the longest list in the group. Cold = a server start was initiated during the search.\n\n"
        + _table(["code_version", "searches", "provenance complete", "zero hits", "partial lists", "cold starts"], main_rows),
        "### Latency in ms (per code version)\n\n" + _table(["code_version", "cold n", "cold p50", "warm n", "warm p50", "warm p90", "warm max"], latency_rows),
        "### Slowest warm searches\n\n" + _table(["ts", "code_version", "duration ms", "collection"], [[s["ts"], s["version"], s["duration_ms"], s["collection"]] for s in data["slowest_warm"]]),
        f"### Output size per search in characters (per code version)\n\nRendered from the content sidecar with the production formatter. {PERSIST_THRESHOLD_CHARS} characters is the smallest size at which Claude Code persisted a rag-cli output in the observed transcripts.\n\n"
        + _table(["code_version", "p50", "p90", "max", f"> {PERSIST_THRESHOLD_CHARS}"], size_rows),
        "### Agent calls (transcripts)\n\n"
        + _table(["attempted searches", "executed, joined to a log row", "blocked by a hook", "executed, no log row", "log rows without a transcript call"],
                 [[attempts["attempts"], attempts["executed_with_log_row"], attempts["hook_blocked"], attempts["executed_without_log_row"], attempts["searches_without_call"]]]),
        "Hook blocks by hook:\n\n" + _table(["hook", "count"], [[h, n] for h, n in attempts["hooks"].items()]),
        "Executed without a log row (failed searches write no record):\n\n" + _table(["ts", "collection", "first output line"], [list(s) for s in attempts["no_log_samples"]]),
        "### Log failures in errors.jsonl\n\n" + _table(["code", "count"], [[c, n] for c, n in data["log_failures"].items()]),
    ])


def _render_relevance(data: dict) -> str:
    groups = data["groups"]
    click_rows = [
        [name, r["searches"], _ratio(r["searches_with_exact_expand"], r["searches"]), _ratio(r["searches_with_document_expand"], r["searches"]),
         r["exact_expands"], r["document_expands"], ", ".join(f"{rank}:{n}" for rank, n in r["exact_rank_counts"].items()) or "-"]
        for name, g in groups.items() for r in [g["relevance"]]
    ]
    dominance_rows = [
        [name, r["lists_considered"], r["median_distinct_documents"], _ratio(r["single_document_lists"], r["lists_considered"])]
        for name, g in groups.items() for r in [g["relevance"]]
    ]
    score_rows = [
        [name, *[f"{r['score_profile'][rank]['median']} (n={r['score_profile'][rank]['n']})" for rank in SCORE_PROFILE_RANKS]]
        for name, g in groups.items() for r in [g["relevance"]]
    ]
    expands = data["expands"]
    return "\n\n".join([
        "## Relevance (click data and descriptive facts, no relevance verdicts)",
        f"### Search to expand_chunks\n\nAn expand is attributed to the latest search in the same collection within 60 minutes before it. `exact` = the expanded (document, chunk) is a hit of that search; `document` = same document, other chunk. Expands in window: {expands['total']}, without any attributed search: {expands['unattributed']} (counted in the all row only).\n\n"
        + _table(["code_version", "searches", "with exact expand", "with document expand", "exact expands", "document expands", "rank of exact expand (rank:count)"], click_rows),
        "### Document dominance (lists with at least 2 hits)\n\n" + _table(["code_version", "lists", "median distinct documents", "lists from one document only"], dominance_rows),
        "### Reranker score profile (median score at rank)\n\n" + _table(["code_version", *[f"rank {r}" for r in SCORE_PROFILE_RANKS]], score_rows),
    ])


def _render_usefulness(data: dict) -> str:
    groups = data["groups"]
    overflow_rows = [
        [name, u["overflow"]["commands"], _ratio(u["overflow"]["persisted"], u["overflow"]["commands"]),
         _ratio(u["overflow"]["single_persisted"], u["overflow"]["single_commands"]),
         _ratio(u["overflow"]["multi_persisted"], u["overflow"]["multi_commands"]), u["overflow"]["read_back"]]
        for name, g in groups.items() for u in [g["usefulness"]]
    ]
    reach_rows = [
        [name, u["reach"]["sessions"], _ratio(u["reach"]["with_reference"], u["reach"]["sessions"]),
         _ratio(u["reach"]["with_foreign"], u["reach"]["sessions"]), _ratio(u["reach"]["with_own"], u["reach"]["sessions"]),
         ", ".join(f"{n}{'+' if n >= 3 else ''}:{c}" for n, c in u["reach"]["foreign_histogram"].items()) or "-",
         u["reach"]["reference_searches"], u["reach"]["unknown_project_sessions"]]
        for name, g in groups.items() for u in [g["usefulness"]]
    ]
    collection_rows = [
        [c["collection"], c["own"], c["foreign"], c["unknown_project"], c["own_sessions"], c["foreign_sessions"]]
        for c in data["reference_collections"]
    ]
    zero_rows = [
        [z["ts"], z["version"], z["collection"], z["document"] or "-", z["candidates"], z["query"], _gap_cell(z["next_gap_s"])]
        for z in data["zero_hit_rows"]
    ]
    return "\n\n".join([
        "## Usefulness (proxies from transcripts)",
        "### Context overflow\n\nSearch commands joined to a log row whose output Claude Code persisted instead of showing, and how many of those were read back by a later Bash or Read of the saved path (extra tool calls).\n\n"
        + _table(["code_version", "joined commands", "persisted", "persisted, one search in the command", "persisted, several searches in the command", "persisted outputs read back"], overflow_rows),
        "### Cross-project reference reach\n\nSession project comes from the transcript working directory, own/foreign from the collection prefix (`<project>-reference`). Facts only; the target is judged by the orchestrator.\n\n"
        + _table(["code_version", "sessions", "with a reference search", "with a foreign reference search", "with an own reference search", "distinct foreign reference collections per session (n:sessions)", "reference searches", "sessions with unknown project"], reach_rows),
        "Per reference collection (all versions):\n\n" + _table(["collection", "own searches", "foreign searches", "unknown-project searches", "own sessions", "foreign sessions"], collection_rows),
        "### Searches with zero hits\n\nNext gap = seconds until the next search of the same session; `none` = no later search in that session; `-` = not joined to a transcript.\n\n"
        + _table(["ts", "code_version", "collection", "document filter", "candidates", "query", "next search in session"], zero_rows),
    ])


def _render_not_covered() -> str:
    return (
        "## Not covered\n\n"
        "- Whether the agent closed its information gap is not measured; no judge is used.\n"
        "- Relevance of hits is not judged. Reranker scores saturate (a 0.99 score on an unrelated chunk was observed), so they are shown as a profile only.\n"
        "- A fuzzy reformulation rate is not computed; it would need a similarity threshold that the observed pairs do not support.\n"
        "- Searches that failed before logging leave no log row; they appear only under agent calls.\n"
        "- Session project is a heuristic from the working directory."
    )


def _gap_cell(gap) -> str:
    if gap is None:
        return "-"
    return gap if isinstance(gap, str) else f"{gap:.0f} s"


def _table(headers: list[str], rows: list[list]) -> str:
    if not rows:
        return "(none)"
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(_cell(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def _cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _ratio(part: int, whole: int) -> str:
    return f"{part}/{whole} ({part / whole * 100:.1f} %)" if whole else "-"
