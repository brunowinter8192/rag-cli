# INFRASTRUCTURE

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from strand_runner import run_strands

from dev.kvp.kvp_classify import known_projects
from dev.kvp.kvp_indicators import (
    attempt_indicators,
    build_search_items,
    compute_report_data,
    overflow_indicators,
    reference_reach,
    technical_indicators,
)
from dev.kvp.kvp_join import attribute_expands, join_calls_to_searches
from dev.kvp.kvp_load import group_contents_by_search, index_registry, parse_ts, read_jsonl
from dev.kvp.kvp_transcripts import load_transcripts

FIXTURES = Path(__file__).parent / "fixtures"
CHAIN_IDS = ("20261014T193416557682_289ee8", "20261014T193421106275_1f358b")


# ORCHESTRATOR

def run_all() -> None:
    run_strands([
        test_join_pairs_each_search_of_a_chain_and_leaves_hook_and_failed_calls_unjoined,
        test_expand_is_attributed_exactly_then_by_document_then_not_at_all,
        test_technical_counts_on_real_records,
        test_overflow_counts_chained_persisted_output_and_its_read_back,
        test_reach_separates_own_and_foreign_reference_sessions,
        test_attempts_count_hook_blocks_and_calls_without_log_row,
        test_report_data_has_one_group_per_version_plus_all,
    ])


# FUNCTIONS

def _load():
    records = read_jsonl(FIXTURES / "search.jsonl")
    calls, readbacks = load_transcripts(str(FIXTURES / "transcript.jsonl"), None, None)
    joined, unjoined = join_calls_to_searches(calls, records)
    contents = group_contents_by_search(read_jsonl(FIXTURES / "search_content.jsonl"), {r["search_id"] for r in records})
    registry = index_registry(read_jsonl(FIXTURES / "config_registry.jsonl"))
    starts = [parse_ts(e["ts"]) for e in read_jsonl(FIXTURES / "errors.jsonl") if e["code"] == "start_initiated"]
    items = build_search_items(records, contents, registry, starts, joined)
    return records, calls, readbacks, joined, unjoined, items


def test_join_pairs_each_search_of_a_chain_and_leaves_hook_and_failed_calls_unjoined(workdir: Path) -> None:
    _, _, _, joined, unjoined, _ = _load()
    chain_ids = [j["record"]["search_id"] for j in joined if j["call"]["tool_use_id"].endswith("h3eeYX")]
    assert chain_ids == list(CHAIN_IDS)
    assert len(joined) == 4
    assert len(unjoined) == 3


def test_expand_is_attributed_exactly_then_by_document_then_not_at_all(workdir: Path) -> None:
    records = read_jsonl(FIXTURES / "search.jsonl")
    expands = read_jsonl(FIXTURES / "expand.jsonl")
    attributions = attribute_expands(expands, records)
    assert [(a["kind"], a["rank"]) for a in attributions] == [("exact", 1), ("document", 1), ("document", 1)]
    without_source = [r for r in records if r["search_id"] != "20260918T172433955662_471ae8"]
    assert attribute_expands(expands[:1], without_source)[0]["kind"] is None


def test_technical_counts_on_real_records(workdir: Path) -> None:
    *_, items = _load()
    technical = technical_indicators(items)
    assert technical["searches"] == 9
    assert technical["zero_hit"] == 2 and technical["zero_hit_no_candidates"] == 2
    assert technical["provenance_complete"] == 7
    assert technical["cold"] == 1 and technical["cold_p50"] == 10864
    assert technical["full_length"] == 12 and technical["partial"] == 0


def test_overflow_counts_chained_persisted_output_and_its_read_back(workdir: Path) -> None:
    _, _, readbacks, _, _, items = _load()
    overflow = overflow_indicators([i for i in items if i["call"] is not None], readbacks)
    assert overflow == {
        "commands": 3, "persisted": 1, "read_back": 1,
        "single_commands": 2, "single_persisted": 0, "multi_commands": 1, "multi_persisted": 1,
    }


def test_reach_separates_own_and_foreign_reference_sessions(workdir: Path) -> None:
    records, *_, items = _load()
    reach = reference_reach([i for i in items if i["call"] is not None], known_projects(records))
    assert reach["sessions"] == 2
    assert reach["with_reference"] == 2 and reach["with_own"] == 1 and reach["with_foreign"] == 1
    assert reach["foreign_histogram"] == {0: 1, 1: 1}
    assert reach["reference_searches"] == 4


def test_attempts_count_hook_blocks_and_calls_without_log_row(workdir: Path) -> None:
    *_, unjoined, items = _load()
    attempts = attempt_indicators(items, unjoined)
    assert attempts["attempts"] == 7
    assert attempts["hook_blocked"] == 1
    assert list(attempts["hooks"]) == ["block_cli_chained.py: Chaining CLIs with ; or && is fine; piping a CLI's output into another command is not."]
    assert attempts["executed_without_log_row"] == 2
    assert attempts["searches_without_call"] == 5


def test_report_data_has_one_group_per_version_plus_all(workdir: Path) -> None:
    records, _, readbacks, _, unjoined, items = _load()
    expands = read_jsonl(FIXTURES / "expand.jsonl")
    data = compute_report_data(items, attribute_expands(expands, records), unjoined, readbacks, [], known_projects(records), expands)
    assert list(data["groups"]) == ["all", "unversioned"]
    assert data["expands"] == {"total": 3, "unattributed": 0}
    assert data["groups"]["all"]["technical"] == data["groups"]["unversioned"]["technical"]


if __name__ == "__main__":
    run_all()
