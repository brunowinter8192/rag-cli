# INFRASTRUCTURE

import copy
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from strand_runner import load_rag, run_strands

from dev.kvp.kvp_canary_logic import compare_runs, error_result, evaluate_case
from dev.kvp.kvp_config import CANARY_CASES_PATH
from dev.kvp.kvp_load import read_jsonl

FIXTURES = Path(__file__).parent / "fixtures"
GRUNDEI = "LUEAG_Literatur_GrundeiZaumseilAufsichtsratCorporateGovernance_2012.md"
MISS_ID = "20261014T193416557682_289ee8"
FOUND_ID = "20261014T194244456175_8887c3"
ZERO_ID = "20260924T174912090329_66fe08"


# ORCHESTRATOR

def run_all() -> None:
    run_strands([
        test_cases_file_is_well_formed_and_holds_the_zipperling_case,
        test_cases_repeat_the_observed_searches_exactly,
        test_observed_miss_fails_observed_find_passes_zero_case_passes,
        test_pass_criterion_does_not_assume_twelve_results,
        test_comparison_marks_fixed_regressed_and_unchanged,
        test_failed_search_becomes_an_error_result,
        test_isolation_keeps_canary_records_out_of_the_production_log,
    ])


# FUNCTIONS

def _cases() -> dict[str, dict]:
    return {c["name"]: c for c in json.loads(CANARY_CASES_PATH.read_text(encoding="utf-8"))}


def _record(search_id: str) -> dict:
    return {r["search_id"]: r for r in read_jsonl(FIXTURES / "search.jsonl")}[search_id]


def _content(search_id: str) -> list[dict]:
    return [l for l in read_jsonl(FIXTURES / "search_content.jsonl") if l["search_id"] == search_id]


def _case_for(search_id: str) -> dict:
    return next(c for c in _cases().values() if c["observed_search_id"] == search_id)


def test_cases_file_is_well_formed_and_holds_the_zipperling_case(workdir: Path) -> None:
    cases = _cases()
    assert len(cases) == 11
    for case in cases.values():
        assert {"name", "query", "collection", "document", "exclude", "expect", "observed_search_id", "origin"} <= set(case)
        assert case["expect"]["kind"] in ("hit", "zero")
    for name in ("zipperling_definition_miss_a", "zipperling_definition_miss_b"):
        assert cases[name]["expect"]["targets"] == [{"document": GRUNDEI, "chunks": [33, 34]}]
        assert cases[name]["collection"] == "wise2627-reference"


def test_cases_repeat_the_observed_searches_exactly(workdir: Path) -> None:
    for search_id in (MISS_ID, FOUND_ID, ZERO_ID):
        case, record = _case_for(search_id), _record(search_id)
        assert (case["query"], case["collection"], case["document"], case["exclude"]) == (
            record["query"], record["collection"], record["document"], record["exclude"]
        )


def test_observed_miss_fails_observed_find_passes_zero_case_passes(workdir: Path) -> None:
    miss = evaluate_case(_case_for(MISS_ID), _record(MISS_ID), _content(MISS_ID))
    found = evaluate_case(_case_for(FOUND_ID), _record(FOUND_ID), _content(FOUND_ID))
    zero = evaluate_case(_case_for(ZERO_ID), _record(ZERO_ID), _content(ZERO_ID))
    assert (miss["status"], miss["rank"], miss["result_count"]) == ("FAIL", None, 12)
    assert (found["status"], found["rank"]) == ("PASS", 3)
    assert (zero["status"], zero["result_count"], zero["candidates"]) == ("PASS", 0, 0)
    assert found["output_chars"] > 0 and zero["output_chars"] == 0


def test_pass_criterion_does_not_assume_twelve_results(workdir: Path) -> None:
    case, record = _case_for(FOUND_ID), copy.deepcopy(_record(FOUND_ID))
    record["hits"], record["hit_count"] = record["hits"][:5], 5
    assert evaluate_case(case, record, _content(FOUND_ID))["status"] == "PASS"
    record["hits"], record["hit_count"] = record["hits"][:2], 2
    assert evaluate_case(case, record, _content(FOUND_ID))["status"] == "FAIL"


def test_comparison_marks_fixed_regressed_and_unchanged(workdir: Path) -> None:
    case = _case_for(FOUND_ID)
    passing = evaluate_case(case, _record(FOUND_ID), _content(FOUND_ID))
    failing = {**passing, "status": "FAIL", "rank": None}
    assert compare_runs([failing], [passing])[0]["change"] == "fixed"
    assert compare_runs([passing], [failing])[0]["change"] == "regressed"
    assert compare_runs([passing], [passing])[0]["change"] == "unchanged"
    assert compare_runs([], [passing])[0]["change"] == "new case"


def test_failed_search_becomes_an_error_result(workdir: Path) -> None:
    result = error_result(_case_for(FOUND_ID), "RuntimeError: embedding server unreachable")
    assert result["status"] == "ERROR" and result["error"].startswith("RuntimeError")


def test_isolation_keeps_canary_records_out_of_the_production_log(workdir: Path) -> None:
    for name in [m for m in sys.modules if m == "src" or m.startswith("src.")]:
        del sys.modules[name]
    from dev.kvp import kvp_canary
    retrieval_log = load_rag("retrieval_log")
    assert str(workdir) in str(retrieval_log.SEARCH_LOG_FILE), "the strand must run against its own copy of src"
    assert kvp_canary.retrieval_log is retrieval_log
    production_paths = kvp_canary.production_search_logs()
    run_dir = kvp_canary.isolate_logs()
    hits = [{"document": "a.md", "chunk_index": 3, "score": 0.5, "content": "text"}]
    retrieval_log.log_search("canary probe", "c", None, None, 1, hits, time.perf_counter(), 4096, 30)
    isolated = read_jsonl(run_dir / "search.jsonl")
    assert len(isolated) == 1 and isolated[0]["query"] == "canary probe"
    assert not production_paths[0].exists()
    assert kvp_canary.check_isolation([isolated[0]["search_id"]], production_paths).startswith("yes")
    production_paths[0].parent.mkdir(parents=True, exist_ok=True)
    production_paths[0].write_text(json.dumps(isolated[0]) + "\n")
    assert kvp_canary.check_isolation([isolated[0]["search_id"]], production_paths).startswith("NO")


if __name__ == "__main__":
    run_all()
