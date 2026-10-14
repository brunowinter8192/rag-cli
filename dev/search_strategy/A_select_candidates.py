# INFRASTRUCTURE

import glob
import json
import os
import random
from datetime import datetime
from pathlib import Path

PRODUCTION_SEARCH_LOG = Path("/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/rag-cli/src/rag/logs/search.jsonl")
TRANSCRIPT_GLOB = os.path.expanduser("~/.claude/projects/*/*.jsonl")
OUTPUT_FILE = Path(__file__).parent / "data" / "candidates.json"
SEED = 20261014
LOG_START = "2026-09-18"
EXCLUDED_PROJECT_MARKERS = ("ragstrat", "kvpreport", "ragkvp")
MATCH_WINDOW_SECONDS = 120
CONTEXT_CHARS = 1500
CALL_MARKER = "rag-cli search"


# ORCHESTRATOR

def select_candidates_workflow() -> None:
    searches = load_searches()
    calls = load_transcript_calls()
    joined = join_searches_to_calls(searches, calls)
    ordered = order_by_stratum(joined)
    write_candidates(ordered)
    print_summary(ordered)


# FUNCTIONS

def write_candidates(ordered: dict) -> None:
    OUTPUT_FILE.write_text(json.dumps(ordered, indent=1, ensure_ascii=False))


def load_searches() -> list[dict]:
    records = [json.loads(line) for line in PRODUCTION_SEARCH_LOG.read_text().splitlines() if line.strip()]
    return [r for r in records if r["ts"][:10] >= LOG_START and r["hit_count"] > 0]


def load_transcript_calls() -> list[dict]:
    calls = []
    for path in glob.glob(TRANSCRIPT_GLOB):
        if any(marker in path for marker in EXCLUDED_PROJECT_MARKERS):
            continue
        calls.extend(extract_calls(path))
    return calls


def extract_calls(path: str) -> list[dict]:
    lines = Path(path).read_text(errors="replace").splitlines()
    calls = []
    last_user = ""
    last_assistant = ""
    for line in lines:
        message = parse_message(line)
        if message is None:
            continue
        role, content, timestamp = message
        if role == "user":
            text = text_of_blocks(content)
            if text:
                last_user = text
        if role == "assistant":
            text = text_of_blocks(content)
            if text:
                last_assistant = text
            calls.extend(calls_in_blocks(content, timestamp, path, last_user, last_assistant))
    return calls


def parse_message(line: str) -> tuple[str, list | str, str] | None:
    if '"message"' not in line:
        return None
    try:
        record = json.loads(line)
    except json.JSONDecodeError:
        return None
    message = record.get("message") or {}
    role = message.get("role")
    content = message.get("content")
    if role not in ("user", "assistant") or content is None:
        return None
    return role, content, record.get("timestamp") or ""


def text_of_blocks(content: list | str) -> str:
    if isinstance(content, str):
        return content.strip()
    parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
    return "\n".join(parts).strip()


def calls_in_blocks(content: list | str, timestamp: str, path: str, user_text: str, assistant_text: str) -> list[dict]:
    if isinstance(content, str):
        return []
    found = []
    for block in content:
        if block.get("type") != "tool_use" or block.get("name") != "Bash":
            continue
        command = (block.get("input") or {}).get("command", "")
        if CALL_MARKER in command:
            found.append({
                "transcript": path,
                "timestamp": timestamp,
                "command": command,
                "user_text": user_text[-CONTEXT_CHARS:],
                "assistant_text": assistant_text[-CONTEXT_CHARS:],
            })
    return found


def join_searches_to_calls(searches: list[dict], calls: list[dict]) -> list[dict]:
    joined = []
    for search in searches:
        call = find_call(search, calls)
        if call is not None:
            joined.append(build_candidate(search, call))
    return joined


def find_call(search: dict, calls: list[dict]) -> dict | None:
    for call in calls:
        if search["collection"] not in call["command"] or search["query"][:40] not in call["command"]:
            continue
        if seconds_apart(search["ts"], call["timestamp"]) < MATCH_WINDOW_SECONDS:
            return call
    return None


def seconds_apart(first: str, second: str) -> float:
    return abs((parse_time(first) - parse_time(second)).total_seconds())


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def build_candidate(search: dict, call: dict) -> dict:
    return {
        "search_id": search["search_id"],
        "ts": search["ts"],
        "stratum": stratum_of(search["collection"]),
        "collection": search["collection"],
        "document": search["document"],
        "exclude": search["exclude"],
        "query": search["query"],
        "transcript": os.path.basename(call["transcript"]),
        "project": os.path.basename(os.path.dirname(call["transcript"])),
        "user_text": call["user_text"],
        "assistant_text": call["assistant_text"],
    }


def stratum_of(collection: str) -> str:
    if collection.endswith("-reference"):
        return "reference"
    if collection.endswith("-docs"):
        return "docs"
    return "other"


def order_by_stratum(candidates: list[dict]) -> dict:
    generator = random.Random(SEED)
    ordered = {}
    for stratum in ("reference", "docs", "other"):
        members = sorted((c for c in candidates if c["stratum"] == stratum), key=lambda c: c["search_id"])
        generator.shuffle(members)
        ordered[stratum] = members
    return ordered


def print_summary(ordered: dict) -> None:
    for stratum, members in ordered.items():
        print(stratum, len(members))


if __name__ == "__main__":
    select_candidates_workflow()
