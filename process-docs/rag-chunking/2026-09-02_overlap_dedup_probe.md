# Overlap-dedup measurement probe — 2026-09-02

## Question

`read_document`'s `merge_chunks` (`src/rag/retriever.py`) is supposed to strip the duplicated overlap text when stitching adjacent chunks back together, via `find_overlap`. In production output the overlap text was observed appearing twice. Two mechanisms were suspected going in:

1. `find_overlap`'s `max_overlap=300` cap sits below the real overlap the chunker produces (`overlap=400` in `src/rag/chunker.py`'s `merge_with_overlap`), so the true overlap window is never inside the search range.
2. Whitespace asymmetry: `merge_with_overlap` appends `current.strip()` for the finished chunk, while the overlap seed for the next chunk (`get_word_aligned_overlap`) is taken from the unstripped `current` — a plausible source of suffix/prefix divergence even if the cap were raised.

## Method

Built `dev/rag-chunking/A_overlap_match_probe.py`, a read-only probe against the prod `rag` DB. It loads `src/rag/retriever.py` and `src/rag/db.py` dynamically (importlib) so the measurement exercises the shipped `find_overlap` and DB helpers unmodified rather than a re-implementation — re-implementing would have measured the wrong thing.

For every adjacent chunk pair (chunk_index i, i+1) per document in three collections — `github_releases` (143 pairs), `rag-cli-docs` (417 pairs), and `trading-reference` (13,142 pairs, chosen as the large reference collection at 13,240 total chunks) — it computed the overlap match length under:
- (a) `find_overlap` as shipped, cap=300
- (b) `find_overlap`, cap raised to 2000 (same algorithm, unmodified)
- (c) (b) plus whitespace-normalized suffix/prefix matching: both texts get whitespace runs collapsed to a single space, the same size-descending scan runs on the normalized strings, and the matched length is mapped back to the exact unnormalized cut index in chunk i+1 (so the result stays directly usable as a slice index, same contract as `find_overlap`'s return value)

13,702 pairs total across 314 documents.

## Findings

Mechanism 1 dominates completely. Raising the cap alone (variant b, unmodified `find_overlap`) took overall zero-match from 92.4% (variant a) to 0.0%, with match-length median 394 chars — consistent with the configured 400-char overlap minus the word-alignment trim in `get_word_aligned_overlap`. The residual non-zero matches under variant (a) are just the minority of pairs whose true overlap happened to already be ≤300 chars (short trailing splits near document boundaries), not a second failure mode.

Mechanism 2 did not reproduce on real data. Variant (c) vs variant (b): 0 disagreements across all 13,702 pairs, in every collection — identical min/max/mean/median distributions. Re-reading `merge_with_overlap` explains why: `get_word_aligned_overlap` already cuts on a space and returns `raw[space_idx + 1:]`, so the overlap seed for chunk i+1 starts right after a space — the same boundary convention `current.strip()` produces at the tail of chunk i. The theoretical divergence the two extraction paths could have introduced doesn't actually occur for this chunker's implementation. This was a genuine dead end: the whitespace-tolerant matching logic was built and measured, and it turned out to be a no-op on the corpus tested.

Two edge cases surfaced worth carrying into a fix design, neither a bug in the probe or a sign mechanism 2 is real:
- A min=10-char match (`Tsay2010AnalysisFinancialTimeSeries.md` @ chunk_index 752) on a degenerate R-console/table boundary — true content overlap can legitimately be much shorter than 400 chars.
- A max=2000 match, i.e. the raised cap itself was hit (`HorvathKokoszka2012InferenceFunctionalData.md` @ chunk_index 210) — a PDF-extraction artifact of thousands of repeated `\)` characters, where a fixed large cap risks under- or over-matching on highly repetitive content. This suggests a fix should bound the search near the configured `overlap` parameter (plus alignment slack) rather than pick an arbitrary large constant.

## Decision for the next milestone

The fix only needs to address mechanism 1 (raise/parameterize the cap). The whitespace-tolerant matching built for variant (c) is not required by the measured evidence — building it into `src/` would add complexity with no observed benefit on the collections tested. Full detail numbers and residual/diff excerpts: `dev/rag-chunking/2026-09-02_overlap_match_probe_report.md` and `dev/rag-chunking/md/probe_output_20260902_072843.md`.
