# INFRASTRUCTURE
from collections import defaultdict
from datetime import timedelta

from dev.kvp.kvp_config import (
    EXPAND_ATTRIBUTION_WINDOW_MINUTES,
    EXPAND_DOCUMENT,
    EXPAND_EXACT,
    JOIN_MARGIN_SECONDS,
)
from dev.kvp.kvp_load import parse_ts


# FUNCTIONS

def join_calls_to_searches(calls: list[dict], records: list[dict]) -> tuple[list[dict], list[dict]]:
    by_key = _index_by_search_key(records)
    used: set[str] = set()
    joined, unjoined = [], []
    for call in calls:
        record = _match_record(call, by_key, used)
        if record is None:
            unjoined.append(call)
            continue
        used.add(record["search_id"])
        joined.append({"call": call, "record": record})
    return joined, unjoined


def attribute_expands(expands: list[dict], records: list[dict]) -> list[dict]:
    by_collection: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_collection[record["collection"]].append(record)
    window = timedelta(minutes=EXPAND_ATTRIBUTION_WINDOW_MINUTES)
    return [_attribute_expand(expand, by_collection.get(expand["collection"], []), window) for expand in expands]


def sessions_of(joined: list[dict]) -> dict[str, list[dict]]:
    sessions: dict[str, list[dict]] = defaultdict(list)
    for item in joined:
        sessions[item["call"]["session_id"]].append(item)
    return {sid: sorted(items, key=lambda i: i["record"]["ts"]) for sid, items in sessions.items()}


def search_key(record: dict) -> tuple:
    return (record["query"], record["collection"], record["document"], record["exclude"])


def _index_by_search_key(records: list[dict]) -> dict[tuple, list[dict]]:
    by_key: dict[tuple, list[dict]] = defaultdict(list)
    for record in sorted(records, key=lambda r: r["ts"]):
        by_key[search_key(record)].append(record)
    return by_key


def _match_record(call: dict, by_key: dict[tuple, list[dict]], used: set[str]) -> dict | None:
    if call["result_ts"] is None:
        return None
    margin = timedelta(seconds=JOIN_MARGIN_SECONDS)
    start, end = parse_ts(call["tool_use_ts"]) - margin, parse_ts(call["result_ts"]) + margin
    key = (call["query"], call["collection"], call["document"], call["exclude"])
    for record in by_key.get(key, []):
        if record["search_id"] not in used and start <= parse_ts(record["ts"]) <= end:
            return record
    return None


def _attribute_expand(expand: dict, candidates: list[dict], window: timedelta) -> dict:
    expand_ts = parse_ts(expand["ts"])
    preceding = [r for r in candidates if parse_ts(r["ts"]) <= expand_ts <= parse_ts(r["ts"]) + window]
    for record in sorted(preceding, key=lambda r: r["ts"], reverse=True):
        rank = _rank_of(record, expand, exact=True)
        if rank is not None:
            return {"expand": expand, "search_id": record["search_id"], "kind": EXPAND_EXACT, "rank": rank}
    for record in sorted(preceding, key=lambda r: r["ts"], reverse=True):
        rank = _rank_of(record, expand, exact=False)
        if rank is not None:
            return {"expand": expand, "search_id": record["search_id"], "kind": EXPAND_DOCUMENT, "rank": rank}
    return {"expand": expand, "search_id": None, "kind": None, "rank": None}


def _rank_of(record: dict, expand: dict, exact: bool) -> int | None:
    for hit in record["hits"]:
        if hit["document"] == expand["document"] and (not exact or hit["chunk_index"] == expand["chunk_index"]):
            return hit["rank"]
    return None
