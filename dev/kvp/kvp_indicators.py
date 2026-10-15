# INFRASTRUCTURE
import statistics
from collections import Counter, defaultdict

from dev.kvp.kvp_classify import (
    classify_command_result,
    first_line,
    is_cold_start,
    is_provenance_complete,
    project_of_cwd,
    reference_owner,
    reference_relation,
    rendered_output_chars,
)
from dev.kvp.kvp_config import (
    ALL_GROUP,
    EXPAND_DOCUMENT,
    EXPAND_EXACT,
    LOG_FAILURE_CODES,
    PERSIST_THRESHOLD_CHARS,
    RELATION_FOREIGN,
    RELATION_OWN,
    RESULT_HOOK_BLOCKED,
    RESULT_PERSISTED,
    SCORE_PROFILE_RANKS,
    SLOWEST_WARM_LISTED,
)
from dev.kvp.kvp_join import sessions_of
from dev.kvp.kvp_load import parse_ts, version_of

FOREIGN_HISTOGRAM_CAP = 3
QUERY_PREVIEW_CHARS = 60
NO_LATER_SEARCH = "none"


# FUNCTIONS

def build_search_items(
    records: list[dict], contents: dict[str, list[dict]], registry: dict[str, dict],
    start_times: list, joined: list[dict],
) -> list[dict]:
    call_by_search = {j["record"]["search_id"]: j["call"] for j in joined}
    return [
        {
            "record": r,
            "version": version_of(r),
            "output_chars": rendered_output_chars(r, contents.get(r["search_id"], [])),
            "cold": is_cold_start(r, start_times),
            "complete": is_provenance_complete(r, registry),
            "call": call_by_search.get(r["search_id"]),
        }
        for r in records
    ]


def split_by_version(items: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        groups[item["version"]].append(item)
    return {ALL_GROUP: items, **dict(sorted(groups.items()))}


def compute_report_data(
    items: list[dict], attributions: list[dict], unjoined: list[dict], readbacks: list[dict],
    errors: list[dict], projects: set[str], expands: list[dict],
) -> dict:
    context = {
        "attributions": attributions,
        "readbacks": readbacks,
        "projects": projects,
    }
    groups = split_by_version(items)
    return {
        "groups": {
            name: {
                "technical": technical_indicators(group),
                "relevance": relevance_indicators(group, context),
                "usefulness": usefulness_indicators(group, context),
            }
            for name, group in groups.items()
        },
        "slowest_warm": slowest_warm(items),
        "attempts": attempt_indicators(items, unjoined),
        "zero_hit_rows": zero_hit_rows(items),
        "reference_collections": reference_collection_rows(items, projects),
        "expands": {"total": len(expands), "unattributed": sum(1 for a in attributions if a["kind"] is None)},
        "log_failures": {code: sum(1 for e in errors if e["code"] == code) for code in LOG_FAILURE_CODES},
    }


def technical_indicators(items: list[dict]) -> dict:
    records = [i["record"] for i in items]
    warm = sorted(i["record"]["duration_ms"] for i in items if not i["cold"])
    cold = sorted(i["record"]["duration_ms"] for i in items if i["cold"])
    sizes = sorted(i["output_chars"] for i in items)
    full_length = max((r["hit_count"] for r in records), default=0)
    return {
        "searches": len(items),
        "provenance_complete": sum(1 for i in items if i["complete"]),
        "zero_hit": sum(1 for r in records if r["hit_count"] == 0),
        "zero_hit_no_candidates": sum(1 for r in records if r["hit_count"] == 0 and r["candidates"] == 0),
        "partial": sum(1 for r in records if 0 < r["hit_count"] < full_length),
        "full_length": full_length,
        "cold": len(cold),
        "cold_p50": _percentile(cold, 0.5),
        "warm": len(warm),
        "warm_p50": _percentile(warm, 0.5),
        "warm_p90": _percentile(warm, 0.9),
        "warm_max": warm[-1] if warm else None,
        "output_p50": _percentile(sizes, 0.5),
        "output_p90": _percentile(sizes, 0.9),
        "output_max": sizes[-1] if sizes else None,
        "output_over_threshold": sum(1 for s in sizes if s > PERSIST_THRESHOLD_CHARS),
    }


def relevance_indicators(items: list[dict], context: dict) -> dict:
    search_ids = {i["record"]["search_id"] for i in items}
    mine = [a for a in context["attributions"] if a["search_id"] in search_ids]
    exact = [a for a in mine if a["kind"] == EXPAND_EXACT]
    document_level = [a for a in mine if a["kind"] == EXPAND_DOCUMENT]
    lists = [i["record"] for i in items if i["record"]["hit_count"] >= 2]
    distinct = [len({h["document"] for h in r["hits"]}) for r in lists]
    return {
        "searches": len(items),
        "searches_with_exact_expand": len({a["search_id"] for a in exact}),
        "searches_with_document_expand": len({a["search_id"] for a in document_level}),
        "exact_expands": len(exact),
        "document_expands": len(document_level),
        "exact_rank_counts": dict(sorted(Counter(a["rank"] for a in exact).items())),
        "lists_considered": len(lists),
        "median_distinct_documents": statistics.median(distinct) if distinct else None,
        "single_document_lists": sum(1 for d in distinct if d == 1),
        "score_profile": score_profile(items),
    }


def score_profile(items: list[dict]) -> dict[int, dict]:
    profile = {}
    for rank in SCORE_PROFILE_RANKS:
        scores = [h["score"] for i in items for h in i["record"]["hits"] if h["rank"] == rank]
        profile[rank] = {"n": len(scores), "median": round(statistics.median(scores), 4) if scores else None}
    return profile


def usefulness_indicators(items: list[dict], context: dict) -> dict:
    with_call = [i for i in items if i["call"] is not None]
    return {
        "overflow": overflow_indicators(with_call, context["readbacks"]),
        "reach": reference_reach(with_call, context["projects"]),
    }


def overflow_indicators(with_call: list[dict], readbacks: list[dict]) -> dict:
    searches_per_command = Counter(i["call"]["tool_use_id"] for i in with_call)
    commands: dict[str, dict] = {}
    for item in with_call:
        commands.setdefault(item["call"]["tool_use_id"], item["call"])
    results = {tid: classify_command_result(call["result_text"]) for tid, call in commands.items()}
    persisted = [tid for tid, r in results.items() if r.state == RESULT_PERSISTED]
    return {
        "commands": len(commands),
        "persisted": len(persisted),
        "read_back": sum(1 for tid in persisted if _was_read_back(commands[tid], results[tid], readbacks)),
        "single_commands": sum(1 for n in searches_per_command.values() if n == 1),
        "single_persisted": sum(1 for tid in persisted if searches_per_command[tid] == 1),
        "multi_commands": sum(1 for n in searches_per_command.values() if n > 1),
        "multi_persisted": sum(1 for tid in persisted if searches_per_command[tid] > 1),
    }


def reference_reach(with_call: list[dict], projects: set[str]) -> dict:
    sessions = _session_relations(with_call, projects)
    foreign_counts = [len({c for c, rel in rels if rel == RELATION_FOREIGN}) for rels in sessions.values()]
    return {
        "sessions": len(sessions),
        "with_reference": sum(1 for rels in sessions.values() if rels),
        "with_foreign": sum(1 for rels in sessions.values() if any(rel == RELATION_FOREIGN for _, rel in rels)),
        "with_own": sum(1 for rels in sessions.values() if any(rel == RELATION_OWN for _, rel in rels)),
        "foreign_histogram": dict(sorted(Counter(min(n, FOREIGN_HISTOGRAM_CAP) for n in foreign_counts).items())),
        "unknown_project_sessions": sum(1 for i in _first_per_session(with_call) if project_of_cwd(i["call"]["cwd"], projects) is None),
        "reference_searches": sum(1 for i in with_call if reference_owner(i["record"]["collection"])),
    }


def attempt_indicators(items: list[dict], unjoined: list[dict]) -> dict:
    results = [classify_command_result(c["result_text"]) for c in unjoined]
    no_log_samples = [
        (c["tool_use_ts"][:19], c["collection"], first_line(c["result_text"]))
        for c, r in zip(unjoined, results) if r.state != RESULT_HOOK_BLOCKED
    ]
    hooks = Counter(r.hook for r in results if r.state == RESULT_HOOK_BLOCKED)
    joined_count = sum(1 for i in items if i["call"] is not None)
    return {
        "attempts": joined_count + len(unjoined),
        "executed_with_log_row": joined_count,
        "hook_blocked": sum(hooks.values()),
        "hooks": dict(hooks.most_common()),
        "executed_without_log_row": len(no_log_samples),
        "no_log_samples": no_log_samples,
        "searches_without_call": sum(1 for i in items if i["call"] is None),
    }


def slowest_warm(items: list[dict]) -> list[dict]:
    warm = sorted((i for i in items if not i["cold"]), key=lambda i: -i["record"]["duration_ms"])
    return [
        {"ts": i["record"]["ts"][:19], "version": i["version"], "duration_ms": i["record"]["duration_ms"], "collection": i["record"]["collection"]}
        for i in warm[:SLOWEST_WARM_LISTED]
    ]


def zero_hit_rows(items: list[dict]) -> list[dict]:
    joined = [{"call": i["call"], "record": i["record"]} for i in items if i["call"] is not None]
    sessions = sessions_of(joined)
    rows = []
    for item in sorted((i for i in items if i["record"]["hit_count"] == 0), key=lambda i: i["record"]["ts"]):
        record = item["record"]
        rows.append({
            "ts": record["ts"][:19], "version": item["version"], "collection": record["collection"],
            "document": record["document"], "candidates": record["candidates"],
            "query": record["query"][:QUERY_PREVIEW_CHARS], "next_gap_s": _next_gap_seconds(item, sessions),
        })
    return rows


def reference_collection_rows(items: list[dict], projects: set[str]) -> list[dict]:
    per_collection: dict[str, dict] = defaultdict(lambda: {"own": 0, "foreign": 0, "unknown_project": 0, "own_sessions": set(), "foreign_sessions": set()})
    for item in (i for i in items if i["call"] is not None):
        collection = item["record"]["collection"]
        relation = reference_relation(collection, project_of_cwd(item["call"]["cwd"], projects))
        if relation is None:
            continue
        per_collection[collection][relation] += 1
        if relation in (RELATION_OWN, RELATION_FOREIGN):
            per_collection[collection][f"{relation}_sessions"].add(item["call"]["session_id"])
    return [
        {"collection": c, "own": v["own"], "foreign": v["foreign"], "unknown_project": v["unknown_project"],
         "own_sessions": len(v["own_sessions"]), "foreign_sessions": len(v["foreign_sessions"])}
        for c, v in sorted(per_collection.items())
    ]


def _session_relations(with_call: list[dict], projects: set[str]) -> dict[str, set[tuple[str, str]]]:
    sessions: dict[str, set[tuple[str, str]]] = {}
    for item in with_call:
        touched = sessions.setdefault(item["call"]["session_id"], set())
        collection = item["record"]["collection"]
        relation = reference_relation(collection, project_of_cwd(item["call"]["cwd"], projects))
        if relation is not None:
            touched.add((collection, relation))
    return sessions


def _first_per_session(with_call: list[dict]) -> list[dict]:
    first: dict[str, dict] = {}
    for item in sorted(with_call, key=lambda i: i["record"]["ts"]):
        first.setdefault(item["call"]["session_id"], item)
    return list(first.values())


def _was_read_back(call: dict, result, readbacks: list[dict]) -> bool:
    if not result.saved_path:
        return False
    return any(
        r["session_id"] == call["session_id"] and r["ts"] > call["result_ts"] and result.saved_path in r["text"]
        for r in readbacks
    )


def _next_gap_seconds(item: dict, sessions: dict[str, list[dict]]) -> float | str | None:
    if item["call"] is None:
        return None
    later = [j for j in sessions[item["call"]["session_id"]] if j["record"]["ts"] > item["record"]["ts"]]
    if not later:
        return NO_LATER_SEARCH
    return (parse_ts(later[0]["record"]["ts"]) - parse_ts(item["record"]["ts"])).total_seconds()


def _percentile(sorted_values: list[int], quantile: float) -> int | None:
    if not sorted_values:
        return None
    return sorted_values[min(len(sorted_values) - 1, int(len(sorted_values) * quantile))]
