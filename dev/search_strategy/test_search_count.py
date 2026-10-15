# INFRASTRUCTURE

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from strand_runner import load_rag, run_strands

PERSIST_LIMIT_BYTES = 30000
CHAINED_SEARCHES = 3
P90_CHUNK_CHARS = 2000


# ORCHESTRATOR

def run_all() -> None:
    run_strands([
        test_search_returns_default_count_from_many_candidates,
        test_search_hands_default_count_to_reranker,
        test_fewer_candidates_than_default_count_all_returned,
        test_chained_searches_stay_below_persist_limit,
        test_no_results_message_points_at_filters_not_wording,
    ])


# FUNCTIONS

def stub_search(search_cmd, candidate_count: int) -> list[int]:
    seen_top_k: list[int] = []
    candidates = [{"content": "c", "collection": "col", "document": "d.md", "chunk_index": i, "score": 0.5} for i in range(candidate_count)]
    search_cmd.retrieve_candidates = lambda query, collection, document, exclude: ([0.0], candidates)

    def fake_rerank(query, documents, top_k):
        seen_top_k.append(top_k)
        return [{**doc, "score": 1.0 - 0.01 * i} for i, doc in enumerate(documents[:top_k])]

    search_cmd.rerank_workflow = fake_rerank
    search_cmd.record_search = lambda *args: None
    return seen_top_k


def test_search_returns_default_count_from_many_candidates(workdir: Path) -> None:
    search_cmd = load_rag("search_cmd")
    stub_search(search_cmd, 30)
    results = search_cmd.search_workflow("q", "col")
    assert len(results) == search_cmd.RERANK_TOP_K
    assert search_cmd.RERANK_TOP_K < 12


def test_search_hands_default_count_to_reranker(workdir: Path) -> None:
    search_cmd = load_rag("search_cmd")
    seen = stub_search(search_cmd, 30)
    search_cmd.search_workflow("q", "col")
    assert seen == [search_cmd.RERANK_TOP_K]


def test_fewer_candidates_than_default_count_all_returned(workdir: Path) -> None:
    search_cmd = load_rag("search_cmd")
    stub_search(search_cmd, 2)
    assert len(search_cmd.search_workflow("q", "col")) == 2


def test_chained_searches_stay_below_persist_limit(workdir: Path) -> None:
    search_cmd = load_rag("search_cmd")
    formatting = load_rag("formatting")
    results = [{"score": 0.5, "collection": "wise2627-reference", "document": "LUEAG_Literatur_WelgeEulerichCorporateGovernanceManagement_2021.md",
                "chunk_index": 100 + i, "content": "a" * P90_CHUNK_CHARS + "ü" * 20} for i in range(search_cmd.RERANK_TOP_K)]
    one_search = formatting.format_results(results)
    chained = "\n".join([one_search] * CHAINED_SEARCHES)
    assert len(chained.encode("utf-8")) < PERSIST_LIMIT_BYTES, len(chained.encode("utf-8"))


def test_no_results_message_points_at_filters_not_wording(workdir: Path) -> None:
    formatting = load_rag("formatting")
    message = formatting.format_no_results()
    assert "0 candidates" in message
    assert "wording" in message
    assert "--document" in message
    assert "list_documents" in message


if __name__ == "__main__":
    run_all()
