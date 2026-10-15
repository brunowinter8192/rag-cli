# INFRASTRUCTURE
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from dev.kvp.kvp_config import UNVERSIONED


# FUNCTIONS

def parse_ts(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def parse_window_bound(value: str | None) -> datetime | None:
    return parse_ts(value) if value else None


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def in_window(ts: datetime, since: datetime | None, until: datetime | None) -> bool:
    return (since is None or ts >= since) and (until is None or ts <= until)


def filter_window(records: list[dict], since: datetime | None, until: datetime | None) -> list[dict]:
    return [r for r in records if in_window(parse_ts(r["ts"]), since, until)]


def group_contents_by_search(content_lines: list[dict], search_ids: set[str]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for line in content_lines:
        if line["search_id"] in search_ids:
            grouped[line["search_id"]].append(line)
    return {search_id: sorted(lines, key=lambda l: l["rank"]) for search_id, lines in grouped.items()}


def index_registry(entries: list[dict]) -> dict[str, dict]:
    return {entry["fingerprint"]: entry for entry in entries}


def version_of(record: dict) -> str:
    return record.get("code_version") or UNVERSIONED
