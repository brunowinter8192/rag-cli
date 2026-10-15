# INFRASTRUCTURE

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from strand_runner import run_strands

from dev.kvp.kvp_load import parse_window_bound
from dev.kvp.kvp_transcripts import load_transcripts, parse_search_commands

FIXTURES = Path(__file__).parent / "fixtures"
TRANSCRIPT = str(FIXTURES / "transcript.jsonl")
CHAIN_TOOL_USE = "toolu_01WDYJpb6Yn2vsEKT9h3eeYX"


# ORCHESTRATOR

def run_all() -> None:
    run_strands([
        test_chained_command_yields_both_searches_with_filter,
        test_flags_and_redirect_tokens_do_not_leak_into_arguments,
        test_non_search_rag_cli_commands_are_ignored,
        test_results_attach_to_every_search_of_a_chained_command,
        test_saved_path_read_back_is_captured,
        test_window_drops_calls_outside_the_margin,
    ])


# FUNCTIONS

def test_chained_command_yields_both_searches_with_filter(workdir: Path) -> None:
    calls, _ = load_transcripts(TRANSCRIPT, None, None)
    chain = [c for c in calls if c["tool_use_id"] == CHAIN_TOOL_USE]
    assert [c["query"] for c in chain] == [
        "externe Kontrolle Definition externe Überwachung Unternehmensführung",
        "externe Corporate Governance Mechanismen Disziplinierung Management",
    ]
    assert all(c["collection"] == "wise2627-reference" and c["document"] == "LUEAG_%" and c["exclude"] is None for c in chain)
    assert chain[0]["session_id"] == "41b5aaa4-b661-482c-b349-249b9e55ac43"
    assert chain[0]["cwd"] == "/Users/brunowinter2000/Documents/wise2627"


def test_flags_and_redirect_tokens_do_not_leak_into_arguments(workdir: Path) -> None:
    parsed = parse_search_commands("cd /tmp && rag-cli search 'a query' my-docs --exclude 'process-docs/%' 2>&1; echo done")
    assert parsed == [{"query": "a query", "collection": "my-docs", "document": None, "exclude": "process-docs/%"}]


def test_non_search_rag_cli_commands_are_ignored(workdir: Path) -> None:
    assert parse_search_commands("rag-cli list_collections --filter reference") == []
    assert parse_search_commands("rag-cli expand_chunks wise2627-reference doc.md 3 --after 2") == []


def test_results_attach_to_every_search_of_a_chained_command(workdir: Path) -> None:
    calls, _ = load_transcripts(TRANSCRIPT, None, None)
    chain = [c for c in calls if c["tool_use_id"] == CHAIN_TOOL_USE]
    assert {c["result_ts"] for c in chain} == {"2026-10-14T19:34:21.138Z"}
    assert all(c["result_text"].startswith("<persisted-output>") for c in chain)


def test_saved_path_read_back_is_captured(workdir: Path) -> None:
    _, readbacks = load_transcripts(TRANSCRIPT, None, None)
    assert len(readbacks) == 1
    assert readbacks[0]["text"].startswith("poread ") and readbacks[0]["text"].endswith("/tool-results/botakosep.txt")
    assert readbacks[0]["session_id"] == "41b5aaa4-b661-482c-b349-249b9e55ac43"


def test_window_drops_calls_outside_the_margin(workdir: Path) -> None:
    since = parse_window_bound("2026-10-14T00:00:00")
    calls, _ = load_transcripts(TRANSCRIPT, since, None)
    assert {c["tool_use_ts"][:10] for c in calls} == {"2026-10-14"}


if __name__ == "__main__":
    run_all()
