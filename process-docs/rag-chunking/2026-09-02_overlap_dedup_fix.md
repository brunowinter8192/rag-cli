# Overlap-dedup fix — 2026-09-02

## Starting point

Follow-on to the same-day measurement (see `process-docs/rag-chunking/` for the probe entry): mechanism 1 (the `find_overlap` cap of 300 sitting below the real ~394-398-char word-aligned overlap) was confirmed as the dominant, sufficient explanation for the observed double-overlap output; mechanism 2 (whitespace asymmetry) did not reproduce and needed no code change.

## Change

`src/rag/retriever.py`:
- `find_overlap`'s `max_overlap` default changed from the hardcoded `300` to `DEFAULT_OVERLAP` (imported from `src/rag/chunker.py`, value 400). Deliberately not raised to an arbitrary large constant (e.g. the 2000 used for measurement purposes) — the measurement's degenerate-repetition edge case (`HorvathKokoszka2012InferenceFunctionalData.md`, thousands of repeated `\)` chars, hit the raised cap outright) showed a large fixed cap risks over-matching on repetitive content. Bounding at the chunker's own configured overlap is safe because `get_word_aligned_overlap` in `chunker.py` only ever trims a chunk's raw `[-overlap:]` slice down (cuts after the first space it finds), so a real overlap can never exceed the configured value.
- `merge_chunks` now only appends the `"\n\n"` join separator on the zero-match branch; a real overlap match continues the deduped remainder directly, since the separator was itself being duplicated content-adjacent to the un-stripped join.

## Verification

Constructed-data test (`dev/rag-chunking/test_overlap_dedup.py`, chunks built via the real `chunk_semantic`, no DB/GPU): 8 checks, all pass — real overlaps now measured up to 394 chars (previously invisible to the 300 cap), stay ≤400, merged output length matches the exact dedup-length formula, boundary text appears exactly once, the zero-overlap fallback still inserts `"\n\n"`, and a synthetic 5000-char repeated-character pair still returns ≤400 (bound-safety property holds).

Real-data spot check against the prod `rag` DB (read-only): `trading-reference/Hamilton1994TimeSeriesAnalysis.md`, first 4 chunks — real overlaps 393/396/396 chars, merged length matched the dedup formula exactly (6466 chars), each of the three boundary markers appeared exactly once in the merged text. `cli.py read_document trading-reference Hamilton1994TimeSeriesAnalysis.md 0 --after 2` run end-to-end against prod — output has no visible duplicated overlap.

Caller check: `merge_chunks`'s only caller is `read_document_workflow`; its only caller is `cli.py:_cmd_read_document` → `_format_read_document`, which reads only `chunk_index`/`before`/`after`/`document`/`content` off the returned dict — none of those keys or types changed, confirmed via grep across the repo plus the live CLI run above.

## Follow-on maintenance

`dev/rag-chunking/A_overlap_match_probe.py`'s variant (a) previously called `find_overlap(text1, text2)` relying on the shipped default to represent "the pre-fix cap of 300" for comparison. Since the fix changes that default, the probe was updated to pass `max_overlap=ORIGINAL_CAP` (300) explicitly, so re-running the probe after this fix still reproduces the original milestone-1 numbers for variant (a) rather than silently collapsing to the same result as variant (b).
