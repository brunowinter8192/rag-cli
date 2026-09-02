# dev/rag-chunking/

## Role

Measurement and regression scripts for `read_document`'s overlap deduplication (`merge_chunks` + `find_overlap` in `src/rag/retriever.py`). The 2026-09-02 measurement found the cap (300) sat below the real word-aligned overlap (~400) as the dominant failure cause; the fix (find_overlap's bound derived from `chunker.DEFAULT_OVERLAP`, `merge_chunks` skipping the `"\n\n"` separator on a real overlap match) now lives in `src/rag/retriever.py`. `A_overlap_match_probe.py` stays read-only against the prod `rag` DB — no writes, no schema changes.

## Scripts

### A_overlap_match_probe.py

**Purpose:** For every adjacent chunk pair (chunk_index i, i+1) per document in a set of real collections, measure the overlap match length under three variants and report the distribution:
- (a) `find_overlap` pinned to the pre-fix cap (`max_overlap=ORIGINAL_CAP=300`) — kept explicit so this variant stays comparable across the fix, independent of `find_overlap`'s live default
- (b) `find_overlap` with a raised cap (`max_overlap=RAISED_CAP=2000`)
- (c) (b) plus whitespace-normalized suffix/prefix matching, with the match position mapped back to the exact (unnormalized) cut index in the second chunk

Loads `src/rag/retriever.py` and `src/rag/db.py` dynamically (`importlib`) rather than re-implementing their logic, so the measurement exercises the real production code, per the task that produced this script.

**Collections probed (edit `COLLECTIONS` constant to change):** `github_releases`, `rag-cli-docs`, `trading-reference`.

**Usage:**
```bash
./venv/bin/python dev/rag-chunking/A_overlap_match_probe.py > /tmp/probe_run.md 2>&1
```

**Output:** `md/probe_output_<timestamp>.md` — per-collection and overall distribution stats (n, zero%, min, max, mean, median) for all three variants, residual variant-(c) zero-match pairs with excerpts, pairs where (b) and (c) disagree (isolates the whitespace mechanism from the cap mechanism), and the lowest/highest non-zero variant-(b) match per collection with excerpts.

**Findings as of 2026-09-02:** see `2026-09-02_overlap_match_probe_report.md` in this directory.

### test_overlap_dedup.py

**Purpose:** Pins the milestone-2 fix in `src/rag/retriever.py` — `find_overlap`'s bound (now `DEFAULT_OVERLAP` from `src/rag/chunker.py` instead of a hardcoded 300) and `merge_chunks`' separator (only inserted on a zero-match fallback, not across a deduped overlap). Builds real chunk chains via the real chunker (`chunk_semantic`, chunk_size=2000/overlap=400) in-memory — no DB, no GPU, no network. Also covers a synthetic degenerate-repetition case to pin that the bound stays capped at `DEFAULT_OVERLAP` rather than growing unbounded on repetitive text. Loads `src/rag/chunker.py` and `src/rag/retriever.py` dynamically (`importlib`), same convention as `A_overlap_match_probe.py`.

**Usage:**
```bash
./venv/bin/python dev/rag-chunking/test_overlap_dedup.py
```

**Output:** stdout PASS/FAIL per check, non-zero exit code on any failure.
