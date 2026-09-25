# INFRASTRUCTURE

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from strand_runner import load_rag, run_strands

CHUNK_SIZE = 2000


# ORCHESTRATOR

def run_all() -> None:
    run_strands([
        test_bound_covers_real_overlap,
        test_merge_dedups_without_separator,
        test_zero_overlap_keeps_separator,
        test_bound_stays_capped_on_degenerate_repetition,
    ])


# FUNCTIONS

def test_bound_covers_real_overlap(workdir: Path) -> None:
    chunker = load_rag("chunker")
    expand_cmd = load_rag("expand_cmd")
    chunks = chunker.chunk_semantic(_build_source(), CHUNK_SIZE, chunker.DEFAULT_OVERLAP)
    assert len(chunks) >= 3, f"produced {len(chunks)} chunks (need >=3)"
    overlaps = [expand_cmd.find_overlap(chunks[i], chunks[i + 1]) for i in range(len(chunks) - 1)]
    assert any(o > 300 for o in overlaps), f"overlaps={overlaps} — at least one must exceed the old max_overlap=300"
    assert all(o <= chunker.DEFAULT_OVERLAP for o in overlaps), f"overlaps={overlaps} must all stay <= DEFAULT_OVERLAP={chunker.DEFAULT_OVERLAP}"
    assert expand_cmd.find_overlap.__defaults__[0] == chunker.DEFAULT_OVERLAP, (
        f"find_overlap default max_overlap={expand_cmd.find_overlap.__defaults__[0]} (expected {chunker.DEFAULT_OVERLAP})"
    )


def _build_source(num_sentences: int = 400) -> str:
    sentences = [f"This is sentence number {i} in a long continuous paragraph about testing." for i in range(num_sentences)]
    return " ".join(sentences)


def test_merge_dedups_without_separator(workdir: Path) -> None:
    chunker = load_rag("chunker")
    expand_cmd = load_rag("expand_cmd")
    chunks = chunker.chunk_semantic(_build_source(), CHUNK_SIZE, chunker.DEFAULT_OVERLAP)
    merged = expand_cmd.merge_chunks(_to_chunk_dicts(chunks))
    expected_len = len(chunks[0])
    for i in range(1, len(chunks)):
        overlap = expand_cmd.find_overlap(chunks[i - 1], chunks[i])
        expected_len += (len(chunks[i]) - overlap) if overlap > 0 else (2 + len(chunks[i]))
    assert len(merged) == expected_len, f"len(merged)={len(merged)} expected={expected_len}"
    boundary_marker = chunks[1][:60]
    assert merged.count(boundary_marker) == 1, f"boundary text appears {merged.count(boundary_marker)}x (want 1)"


def _to_chunk_dicts(chunks: list[str]) -> list[dict]:
    return [{"content": c, "chunk_index": i} for i, c in enumerate(chunks)]


def test_zero_overlap_keeps_separator(workdir: Path) -> None:
    expand_cmd = load_rag("expand_cmd")
    chunk_dicts = [
        {"content": "Completely unrelated first chunk about apples.", "chunk_index": 0},
        {"content": "Totally different second chunk about spacecraft.", "chunk_index": 1},
    ]
    expected = chunk_dicts[0]["content"] + "\n\n" + chunk_dicts[1]["content"]
    merged = expand_cmd.merge_chunks(chunk_dicts)
    assert merged == expected, f"merged={merged!r}"


def test_bound_stays_capped_on_degenerate_repetition(workdir: Path) -> None:
    chunker = load_rag("chunker")
    expand_cmd = load_rag("expand_cmd")
    overlap = expand_cmd.find_overlap("x" * 5000, "x" * 5000)
    assert overlap <= chunker.DEFAULT_OVERLAP, (
        f"overlap={overlap} must stay <= DEFAULT_OVERLAP={chunker.DEFAULT_OVERLAP} on 5000-char repeated input"
    )


if __name__ == "__main__":
    run_all()
