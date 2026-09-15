# INFRASTRUCTURE

import importlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

_chunker = importlib.import_module(".".join(["src", "rag", "chunker"]))
_retriever = importlib.import_module(".".join(["src", "rag", "retriever"]))

chunk_semantic = _chunker.chunk_semantic
DEFAULT_OVERLAP = _chunker.DEFAULT_OVERLAP
find_overlap = _retriever.find_overlap
merge_chunks = _retriever.merge_chunks

CHUNK_SIZE = 2000
FAILURES = []


# ORCHESTRATOR

def run_all() -> None:
    test_bound_covers_real_overlap()
    test_merge_dedups_without_separator()
    test_zero_overlap_keeps_separator()
    test_bound_stays_capped_on_degenerate_repetition()
    report()


# FUNCTIONS

def _to_chunk_dicts(chunks: list[str]) -> list[dict]:
    return [{"content": c, "chunk_index": i} for i, c in enumerate(chunks)]


def _build_source(num_sentences: int = 400) -> str:
    sentences = [f"This is sentence number {i} in a long continuous paragraph about testing." for i in range(num_sentences)]
    return " ".join(sentences)


def _check(label: str, condition: bool, detail: str) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}: {detail}")
    if not condition:
        FAILURES.append(label)


def test_bound_covers_real_overlap() -> None:
    source = _build_source()
    chunks = chunk_semantic(source, CHUNK_SIZE, DEFAULT_OVERLAP)
    _check("chunk_count", len(chunks) >= 3, f"produced {len(chunks)} chunks (need >=3)")

    overlaps = [find_overlap(chunks[i], chunks[i + 1]) for i in range(len(chunks) - 1)]
    _check(
        "overlap_exceeds_old_cap",
        any(o > 300 for o in overlaps),
        f"overlaps={overlaps} — at least one must exceed the old max_overlap=300",
    )
    _check(
        "overlap_within_new_bound",
        all(o <= DEFAULT_OVERLAP for o in overlaps),
        f"overlaps={overlaps} must all stay <= DEFAULT_OVERLAP={DEFAULT_OVERLAP}",
    )
    _check(
        "find_overlap_default_is_configured_overlap",
        find_overlap.__defaults__[0] == DEFAULT_OVERLAP,
        f"find_overlap default max_overlap={find_overlap.__defaults__[0]} (expected {DEFAULT_OVERLAP})",
    )


def test_merge_dedups_without_separator() -> None:
    source = _build_source()
    chunks = chunk_semantic(source, CHUNK_SIZE, DEFAULT_OVERLAP)
    chunk_dicts = _to_chunk_dicts(chunks)
    merged = merge_chunks(chunk_dicts)

    expected_len = len(chunks[0])
    for i in range(1, len(chunks)):
        overlap = find_overlap(chunks[i - 1], chunks[i])
        expected_len += (len(chunks[i]) - overlap) if overlap > 0 else (2 + len(chunks[i]))
    _check(
        "merged_length_matches_dedup_formula",
        len(merged) == expected_len,
        f"len(merged)={len(merged)} expected={expected_len}",
    )

    boundary_marker = chunks[1][:60]
    _check(
        "boundary_text_appears_once",
        merged.count(boundary_marker) == 1,
        f"'{boundary_marker[:30]}...' appears {merged.count(boundary_marker)}x in merged output (want 1)",
    )


def test_zero_overlap_keeps_separator() -> None:
    chunk_dicts = [
        {"content": "Completely unrelated first chunk about apples.", "chunk_index": 0},
        {"content": "Totally different second chunk about spacecraft.", "chunk_index": 1},
    ]
    merged = merge_chunks(chunk_dicts)
    expected = chunk_dicts[0]["content"] + "\n\n" + chunk_dicts[1]["content"]
    _check("zero_overlap_separator_preserved", merged == expected, f"merged={merged!r}")


def test_bound_stays_capped_on_degenerate_repetition() -> None:
    text1 = "x" * 5000
    text2 = "x" * 5000
    overlap = find_overlap(text1, text2)
    _check(
        "degenerate_repetition_capped",
        overlap <= DEFAULT_OVERLAP,
        f"overlap={overlap} must stay <= DEFAULT_OVERLAP={DEFAULT_OVERLAP} on 5000-char repeated input",
    )


def report() -> None:
    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) failed: {FAILURES}")
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    run_all()
