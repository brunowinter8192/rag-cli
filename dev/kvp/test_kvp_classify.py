# INFRASTRUCTURE

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from strand_runner import run_strands

from dev.kvp.kvp_classify import (
    classify_command_result,
    is_cold_start,
    is_provenance_complete,
    known_projects,
    project_of_cwd,
    reference_relation,
    rendered_output_chars,
)
from dev.kvp.kvp_load import index_registry, parse_ts, read_jsonl
from dev.kvp.kvp_transcripts import load_transcripts

FIXTURES = Path(__file__).parent / "fixtures"
COLD_SEARCH_ID = "20260920T090935377581_f05af0"
WARM_SEARCH_ID = "20261014T194244456175_8887c3"
NO_FINGERPRINT_ID = "20260918T172433955662_471ae8"
INCOMPLETE_REGISTRY_ID = "20260926T215804017149_f54541"


# ORCHESTRATOR

def run_all() -> None:
    run_strands([
        test_persisted_stub_gives_path_and_size,
        test_hook_block_names_hook_and_message,
        test_normal_output_is_executed,
        test_project_comes_from_cwd_with_worktree_stripped,
        test_reference_relation_own_foreign_unknown_and_none,
        test_cold_start_needs_a_start_event_inside_the_search,
        test_provenance_needs_fingerprint_and_named_models,
        test_output_chars_match_the_cli_format,
    ])


# FUNCTIONS

def _transcript_calls() -> dict[str, dict]:
    calls, _ = load_transcripts(str(FIXTURES / "transcript.jsonl"), None, None)
    return {c["tool_use_id"][-6:]: c for c in calls}


def _records() -> dict[str, dict]:
    return {r["search_id"]: r for r in read_jsonl(FIXTURES / "search.jsonl")}


def test_persisted_stub_gives_path_and_size(workdir: Path) -> None:
    result = classify_command_result(_transcript_calls()["h3eeYX"]["result_text"])
    assert result.state == "persisted"
    assert result.persisted_kb == 42.1
    assert result.saved_path.endswith("/41b5aaa4-b661-482c-b349-249b9e55ac43/tool-results/botakosep.txt")


def test_hook_block_names_hook_and_message(workdir: Path) -> None:
    result = classify_command_result(_transcript_calls()["Yah9eQ"]["result_text"])
    assert result.state == "hook_blocked"
    assert result.hook.startswith("block_cli_chained.py: Chaining CLIs with ; or && is fine; piping")


def test_normal_output_is_executed(workdir: Path) -> None:
    result = classify_command_result(_transcript_calls()["N6ddLz"]["result_text"])
    assert result.state == "executed"
    assert result.saved_path is None


def test_project_comes_from_cwd_with_worktree_stripped(workdir: Path) -> None:
    projects = {"monitor-cc", "general", "wise2627", "websearch"}
    assert project_of_cwd("/Users/brunowinter2000/Documents/ai/monitor-cc/.claude/worktrees/ragcli", projects) == "monitor-cc"
    assert project_of_cwd("/Users/brunowinter2000/Documents/general/dokumente/goethe/studium", projects) == "general"
    assert project_of_cwd("/Users/brunowinter2000/Documents/wise2627/tracker", projects) == "wise2627"
    assert project_of_cwd("/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/websearch/.claude/worktrees/kvp", projects) == "websearch"
    assert project_of_cwd("/tmp/elsewhere", projects) is None
    assert known_projects(list(_records().values())) == {"rag-cli", "general", "wise2627", "goethe-bwl", "monitor-cc"}


def test_reference_relation_own_foreign_unknown_and_none(workdir: Path) -> None:
    assert reference_relation("wise2627-reference", "wise2627") == "own"
    assert reference_relation("goethe-bwl-reference", "general") == "foreign"
    assert reference_relation("goethe-bwl-reference", None) == "unknown_project"
    assert reference_relation("general-docs", "general") is None
    assert reference_relation("github_issues", "general") is None


def test_cold_start_needs_a_start_event_inside_the_search(workdir: Path) -> None:
    errors = read_jsonl(FIXTURES / "errors.jsonl")
    starts = [parse_ts(e["ts"]) for e in errors if e["code"] == "start_initiated"]
    records = _records()
    assert len(starts) == 2
    assert is_cold_start(records[COLD_SEARCH_ID], starts) is True
    assert is_cold_start(records[WARM_SEARCH_ID], starts) is False


def test_provenance_needs_fingerprint_and_named_models(workdir: Path) -> None:
    registry = index_registry(read_jsonl(FIXTURES / "config_registry.jsonl"))
    records = _records()
    assert is_provenance_complete(records[WARM_SEARCH_ID], registry) is True
    assert is_provenance_complete(records[NO_FINGERPRINT_ID], registry) is False
    assert records[INCOMPLETE_REGISTRY_ID]["config_fingerprint"] == "e22ba2a5ec1280a6"
    assert is_provenance_complete(records[INCOMPLETE_REGISTRY_ID], registry) is False


def test_output_chars_match_the_cli_format(workdir: Path) -> None:
    record = {"collection": "c", "hits": [{"rank": 1, "document": "d.md", "chunk_index": 3, "score": 0.5}]}
    expected = "--- Result 1 (score: 0.5) ---\nCollection: c | Document: d.md | Chunk: 3\nabc\n"
    assert rendered_output_chars(record, [{"rank": 1, "content": "abc"}]) == len(expected)
    assert rendered_output_chars({"collection": "c", "hits": []}, []) == 0


if __name__ == "__main__":
    run_all()
