# dev/rag-chunking/

## Role

Measurement scripts investigating why `read_document`'s overlap deduplication (`merge_chunks` + `find_overlap` in `src/rag/retriever.py`) fails on real chunked collections. Read-only against the prod `rag` DB — no fixes live here.

## Scripts

### A_overlap_match_probe.py

**Purpose:** For every adjacent chunk pair (chunk_index i, i+1) per document in a set of real collections, measure the overlap match length under three variants and report the distribution:
- (a) the real `find_overlap` as shipped (`max_overlap=300`)
- (b) the real `find_overlap` with a raised cap (`max_overlap=2000`)
- (c) (b) plus whitespace-normalized suffix/prefix matching, with the match position mapped back to the exact (unnormalized) cut index in the second chunk

Loads `src/rag/retriever.py` and `src/rag/db.py` dynamically (`importlib`) rather than re-implementing their logic, so the measurement exercises the real production code, per the task that produced this script.

**Collections probed (edit `COLLECTIONS` constant to change):** `github_releases`, `rag-cli-docs`, `trading-reference`.

**Usage:**
```bash
./venv/bin/python dev/rag-chunking/A_overlap_match_probe.py > /tmp/probe_run.md 2>&1
```

**Output:** `md/probe_output_<timestamp>.md` — per-collection and overall distribution stats (n, zero%, min, max, mean, median) for all three variants, residual variant-(c) zero-match pairs with excerpts, pairs where (b) and (c) disagree (isolates the whitespace mechanism from the cap mechanism), and the lowest/highest non-zero variant-(b) match per collection with excerpts.

**Findings as of 2026-09-02:** see `2026-09-02_overlap_match_probe_report.md` in this directory.
