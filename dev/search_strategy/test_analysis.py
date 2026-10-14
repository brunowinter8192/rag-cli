# INFRASTRUCTURE

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from strand_runner import run_strands


# ORCHESTRATOR

def run_all() -> None:
    run_strands([
        test_parse_judgments_reads_grade_and_aspects,
        test_list_metrics_counts_distinct_relevant_and_aspects,
        test_unjudged_chunk_counts_as_not_relevant,
        test_compare_treats_missing_and_equal_as_ties,
        test_verdict_needs_two_thirds_of_decided_needs,
        test_default_count_takes_smallest_k_within_one_need_of_baseline,
        test_default_count_respects_inline_cap,
        test_strategy_requires_asp_gain_and_wins,
        test_sibling_lists_print_four_queries_times_depth,
        test_sibling_agreement_groups_by_returning_queries,
        test_known_item_rank_finds_first_match,
        test_cohen_kappa_perfect_and_chance,
        test_first_answer_rank_and_distinct_share,
    ])


# FUNCTIONS

def run(arm: str, label: str, chunk_indices: list[int], depth: int = 12) -> dict:
    hits = [{"document": "d.md", "chunk_index": i, "score": 0.5} for i in chunk_indices]
    return {"arm": arm, "label": label, "collection": "c", "hits": hits, "depth": depth}


def key(index: int) -> str:
    return f"c|d.md|{index}"


def test_parse_judgments_reads_grade_and_aspects(workdir: Path) -> None:
    from metrics import parse_judgments
    parsed = parse_judgments("# header\nN01-c01 2 a1,a3\nN01-c02 0\n")
    assert parsed["N01-c01"] == (2, frozenset({"a1", "a3"}))
    assert parsed["N01-c02"] == (0, frozenset())
    assert len(parsed) == 2


def test_list_metrics_counts_distinct_relevant_and_aspects(workdir: Path) -> None:
    from metrics import list_metrics
    judged = {key(1): (2, frozenset({"a1"})), key(2): (1, frozenset({"a2"})), key(3): (0, frozenset())}
    universe = frozenset({"a1", "a2", "a3"})
    result = list_metrics([key(1), key(1), key(2), key(3)], judged, universe)
    assert result["printed"] == 4
    assert result["hit"] == 1
    assert result["rel"] == 2
    assert result["p"] == 0.75
    assert abs(result["asp"] - 2 / 3) < 1e-9
    assert result["reldocs"] == 1


def test_unjudged_chunk_counts_as_not_relevant(workdir: Path) -> None:
    from metrics import list_metrics
    result = list_metrics([key(9)], {}, frozenset({"a1"}))
    assert result["hit"] == 0 and result["rel"] == 0 and result["asp"] == 0.0


def test_compare_treats_missing_and_equal_as_ties(workdir: Path) -> None:
    from metrics import compare
    assert compare([1.0, 0.5, None, 0.2], [0.5, 0.5, 1.0, 0.9]) == (1, 1, 2)


def test_verdict_needs_two_thirds_of_decided_needs(workdir: Path) -> None:
    from decisions import verdict
    assert verdict(4, 2) == "supported"
    assert verdict(3, 2) == "inconclusive"
    assert verdict(1, 4) == "not supported"
    assert verdict(0, 0) == "inconclusive"


def test_default_count_takes_smallest_k_within_one_need_of_baseline(workdir: Path) -> None:
    from decisions import decide_default_count
    hit_a = {3: 8, 4: 9, 5: 9, 6: 10, 8: 10, 12: 10}
    hit_g = {3: 9, 4: 9, 5: 10, 6: 10, 8: 10, 12: 10}
    result = decide_default_count(hit_a, hit_g)
    assert result["k_star"] == 4
    assert result["confirmed_on_guided_queries"] is True


def test_default_count_respects_inline_cap(workdir: Path) -> None:
    from decisions import decide_default_count
    hit_a = {3: 2, 4: 3, 5: 4, 6: 9, 8: 10, 12: 10}
    result = decide_default_count(hit_a, dict(hit_a))
    assert result["k_star"] is None


def test_strategy_requires_asp_gain_and_wins(workdir: Path) -> None:
    from decisions import decide_strategy
    better = [{"hit": 1, "asp": 0.8}, {"hit": 1, "asp": 0.6}, {"hit": 0, "asp": 0.5}]
    baseline = [{"hit": 1, "asp": 0.5}, {"hit": 1, "asp": 0.6}, {"hit": 0, "asp": 0.2}]
    assert decide_strategy(better, baseline)["adopt_siblings"] is True
    assert decide_strategy(baseline, better)["adopt_siblings"] is False


def test_sibling_lists_print_four_queries_times_depth(workdir: Path) -> None:
    from metrics import named_lists
    runs = [run("A", "A", list(range(12))), run("G", "G", list(range(100, 112))),
            run("S", "s2", list(range(200, 212))), run("S", "s3", list(range(300, 312))), run("S", "s4", list(range(400, 412)))]
    lists = named_lists(runs)
    assert len(lists["S@3"]) == 12
    assert lists["S@3"][:3] == [key(100), key(101), key(102)]
    assert len(lists["A@4"]) == 4


def test_sibling_agreement_groups_by_returning_queries(workdir: Path) -> None:
    from metrics import sibling_agreement
    by_arm = {("G", "G"): run("G", "G", [1, 2, 3]), ("S", "s2"): run("S", "s2", [1, 4, 5]),
              ("S", "s3"): run("S", "s3", [6, 7, 8]), ("S", "s4"): run("S", "s4", [9, 10, 11])}
    judged = {key(1): (2, frozenset({"a1"}))}
    grouped = sibling_agreement(by_arm, judged)
    assert grouped[2] == [1]
    assert len(grouped[1]) == 10


def test_known_item_rank_finds_first_match(workdir: Path) -> None:
    from metrics import known_item_rank
    result = known_item_rank(run("A", "A", [5, 6, 7, 8]), [{"document": "d.md", "chunk_index": 7}, {"document": "d.md", "chunk_index": 8}])
    assert result == 3
    assert known_item_rank(run("A", "A", [1]), [{"document": "d.md", "chunk_index": 9}]) is None


def test_cohen_kappa_perfect_and_chance(workdir: Path) -> None:
    from metrics import cohen_kappa
    assert cohen_kappa([1, 0, 1, 0], [1, 0, 1, 0]) == 1.0
    assert abs(cohen_kappa([1, 1, 0, 0], [1, 0, 1, 0])) < 1e-9


def test_first_answer_rank_and_distinct_share(workdir: Path) -> None:
    from metrics import distinct_share, first_answer_rank
    judged = {key(2): (1, frozenset()), key(3): (2, frozenset({"a1"}))}
    assert first_answer_rank([key(1), key(2), key(3)], judged) == 3
    assert first_answer_rank([key(1), key(2)], judged) is None
    assert distinct_share([key(1), key(1), key(2), key(3)]) == 0.75


if __name__ == "__main__":
    run_all()
