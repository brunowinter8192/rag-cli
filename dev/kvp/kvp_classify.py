# INFRASTRUCTURE
import re
from datetime import datetime, timedelta
from typing import NamedTuple

from dev.kvp.kvp_config import (
    COLD_START_LEFT_MARGIN_SECONDS,
    DOCS_SUFFIX,
    REFERENCE_SUFFIX,
    RELATION_FOREIGN,
    RELATION_OWN,
    RELATION_UNKNOWN_PROJECT,
    RESULT_EXECUTED,
    RESULT_HOOK_BLOCKED,
    RESULT_PERSISTED,
)
from dev.kvp.kvp_load import parse_ts
from src.rag.formatting import format_results

HOOK_MARKER = "hook error"
HOOK_HEAD_CHARS = 300
HOOK_PATTERN = re.compile(r"hook error: \[[^\]]*?([^/\s\]]+)\]: ([^\n]*)")
PERSISTED_PREFIX = "<persisted-output>"
PERSISTED_PATH_PATTERN = re.compile(r"Full output saved to: (\S+)")
PERSISTED_SIZE_PATTERN = re.compile(r"Output too large \(([\d.]+)KB\)")
HOOK_MESSAGE_CHARS = 90
FIRST_LINE_CHARS = 120
PROVENANCE_FIELDS = (("embedding", "preset"), ("embedding", "model_name"), ("reranker", "preset"), ("reranker", "model_name"))


class CommandResult(NamedTuple):
    state: str
    hook: str | None
    saved_path: str | None
    persisted_kb: float | None


# FUNCTIONS

def classify_command_result(text: str) -> CommandResult:
    if HOOK_MARKER in text[:HOOK_HEAD_CHARS]:
        match = HOOK_PATTERN.search(text)
        hook = f"{match.group(1)}: {match.group(2)[:HOOK_MESSAGE_CHARS]}" if match else text[:HOOK_MESSAGE_CHARS]
        return CommandResult(RESULT_HOOK_BLOCKED, hook, None, None)
    if text.startswith(PERSISTED_PREFIX):
        path = PERSISTED_PATH_PATTERN.search(text)
        size = PERSISTED_SIZE_PATTERN.search(text)
        return CommandResult(RESULT_PERSISTED, None, path.group(1) if path else None, float(size.group(1)) if size else None)
    return CommandResult(RESULT_EXECUTED, None, None, None)


def first_line(text: str) -> str:
    stripped = text.strip()
    return stripped.splitlines()[0][:FIRST_LINE_CHARS] if stripped else "(empty result)"


def known_projects(records: list[dict]) -> set[str]:
    projects = set()
    for record in records:
        for suffix in (DOCS_SUFFIX, REFERENCE_SUFFIX):
            collection = record.get("collection") or ""
            if collection.endswith(suffix):
                projects.add(collection[: -len(suffix)])
    return projects


def project_of_cwd(cwd: str | None, projects: set[str]) -> str | None:
    if not cwd:
        return None
    parts = cwd.split("/")
    if ".claude" in parts:
        parts = parts[: parts.index(".claude")]
    for part in reversed(parts):
        if part in projects:
            return part
    return None


def reference_owner(collection: str | None) -> str | None:
    if collection and collection.endswith(REFERENCE_SUFFIX):
        return collection[: -len(REFERENCE_SUFFIX)]
    return None


def reference_relation(collection: str | None, session_project: str | None) -> str | None:
    owner = reference_owner(collection)
    if owner is None:
        return None
    if session_project is None:
        return RELATION_UNKNOWN_PROJECT
    return RELATION_OWN if owner == session_project else RELATION_FOREIGN


def is_cold_start(record: dict, start_times: list[datetime]) -> bool:
    end = parse_ts(record["ts"])
    begin = end - timedelta(milliseconds=record["duration_ms"], seconds=COLD_START_LEFT_MARGIN_SECONDS)
    return any(begin <= start <= end for start in start_times)


def is_provenance_complete(record: dict, registry: dict[str, dict]) -> bool:
    fingerprint = record.get("config_fingerprint")
    entry = registry.get(fingerprint) if fingerprint else None
    if entry is None:
        return False
    return all(entry.get(section, {}).get(field) for section, field in PROVENANCE_FIELDS)


def rendered_output_chars(record: dict, content_lines: list[dict]) -> int:
    hits = [
        {"score": hit["score"], "collection": record["collection"], "document": hit["document"],
         "chunk_index": hit["chunk_index"], "content": line["content"]}
        for hit, line in zip(record["hits"], content_lines)
    ]
    return len(format_results(hits)) if hits else 0
