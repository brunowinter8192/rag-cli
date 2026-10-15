# INFRASTRUCTURE
import glob
import json
import shlex
from datetime import datetime, timedelta
from pathlib import Path

from dev.kvp.kvp_load import in_window, parse_ts

RAG_CLI_NAME = "rag-cli"
SEARCH_COMMAND = "search"
BASH_TOOL = "Bash"
READ_TOOL = "Read"
OPERATOR_CHARS = frozenset(";&|<>()")
VALUE_FLAGS = ("--document", "--exclude")
READBACK_MARKER = "/tool-results/"
COMMAND_PREFIX_WORDS = frozenset({"do", "then", "exec", "time"})
QUOTE_CHARS = "'\""
CALL_LOAD_MARGIN_MINUTES = 10


# FUNCTIONS

def load_transcripts(pattern: str, since: datetime | None, until: datetime | None) -> tuple[list[dict], list[dict]]:
    margin = timedelta(minutes=CALL_LOAD_MARGIN_MINUTES)
    calls: list[dict] = []
    readbacks: list[dict] = []
    for path in sorted(glob.glob(pattern)):
        file_calls, file_readbacks = read_transcript(Path(path))
        calls += [c for c in file_calls if in_window(parse_ts(c["tool_use_ts"]), _shift(since, -margin), _shift(until, margin))]
        readbacks += file_readbacks
    return sorted(calls, key=lambda c: c["tool_use_ts"]), readbacks


def read_transcript(path: Path) -> tuple[list[dict], list[dict]]:
    calls: list[dict] = []
    readbacks: list[dict] = []
    pending: dict[str, list[dict]] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if RAG_CLI_NAME not in line and "tool_use_id" not in line and READBACK_MARKER not in line:
            continue
        record = _parse_line(line)
        if record is None:
            continue
        for block in _content_blocks(record):
            _consume_block(block, record, pending, calls, readbacks)
    return calls, readbacks


def parse_search_commands(command: str) -> list[dict]:
    tokens = _tokenize(command)
    found = []
    index = 0
    while index < len(tokens):
        if _is_search_invocation(tokens, index):
            segment, index = _take_segment(tokens, index + 2)
            found.append(_search_arguments(segment))
        else:
            index += 1
    return found


def _shift(bound: datetime | None, delta: timedelta) -> datetime | None:
    return bound + delta if bound else None


def _parse_line(line: str) -> dict | None:
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def _content_blocks(record: dict) -> list[dict]:
    content = (record.get("message") or {}).get("content")
    return [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []


def _consume_block(block: dict, record: dict, pending: dict, calls: list[dict], readbacks: list[dict]) -> None:
    if block.get("type") == "tool_use":
        _consume_tool_use(block, record, pending, calls, readbacks)
    elif block.get("type") == "tool_result" and block.get("tool_use_id") in pending:
        text = _result_text(block.get("content"))
        for call in pending[block["tool_use_id"]]:
            call["result_ts"] = record["timestamp"]
            call["result_text"] = text


def _consume_tool_use(block: dict, record: dict, pending: dict, calls: list[dict], readbacks: list[dict]) -> None:
    tool_input = block.get("input") or {}
    text = tool_input.get("command", "") if block.get("name") == BASH_TOOL else tool_input.get("file_path", "")
    if block.get("name") in (BASH_TOOL, READ_TOOL) and READBACK_MARKER in text:
        readbacks.append({"session_id": record.get("sessionId"), "ts": record["timestamp"], "text": text})
    if block.get("name") != BASH_TOOL or RAG_CLI_NAME not in text:
        return
    for arguments in parse_search_commands(text):
        call = {
            **arguments, "tool_use_id": block["id"], "session_id": record.get("sessionId"), "cwd": record.get("cwd"),
            "tool_use_ts": record["timestamp"], "result_ts": None, "result_text": "",
        }
        calls.append(call)
        pending.setdefault(block["id"], []).append(call)


def _result_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(part.get("text", "") for part in content if isinstance(part, dict))
    return ""


def _is_search_invocation(tokens: list[str], index: int) -> bool:
    if tokens[index].split("/")[-1] != RAG_CLI_NAME or index + 1 >= len(tokens) or tokens[index + 1] != SEARCH_COMMAND:
        return False
    return index == 0 or set(tokens[index - 1]) <= OPERATOR_CHARS or tokens[index - 1] in COMMAND_PREFIX_WORDS


def _newlines_to_separators(command: str) -> str:
    out = []
    quote = None
    for position, char in enumerate(command):
        if quote:
            quote = None if char == quote and command[position - 1] != "\\" else quote
        elif char in QUOTE_CHARS:
            quote = char
        out.append(" ; " if char == "\n" and quote is None else char)
    return "".join(out)


def _tokenize(command: str) -> list[str]:
    try:
        lexer = shlex.shlex(_newlines_to_separators(command), posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        return list(lexer)
    except ValueError:
        return []


def _take_segment(tokens: list[str], start: int) -> tuple[list[str], int]:
    end = start
    while end < len(tokens) and not set(tokens[end]) <= OPERATOR_CHARS:
        end += 1
    return tokens[start:end], end


def _search_arguments(segment: list[str]) -> dict:
    positional: list[str] = []
    filters: dict[str, str] = {}
    index = 0
    while index < len(segment):
        if segment[index] in VALUE_FLAGS and index + 1 < len(segment):
            filters[segment[index]] = segment[index + 1]
            index += 2
        elif segment[index].startswith("--"):
            index += 1
        else:
            positional.append(segment[index])
            index += 1
    return {
        "query": positional[0] if positional else None,
        "collection": positional[1] if len(positional) > 1 else None,
        "document": filters.get("--document"),
        "exclude": filters.get("--exclude"),
    }
