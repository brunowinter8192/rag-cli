# Overlap match probe report — 2026-09-02

Measurement only. No changes to `src/`. Probe: `dev/rag-chunking/A_overlap_match_probe.py`. Raw output: `dev/rag-chunking/md/probe_output_20260902_072843.md`. Read-only against the prod `rag` DB (`get_connection(purpose="read")`).

## Dataset

Adjacent chunk pairs (chunk_index i, i+1) pulled per document, via `query_documents` + `fetch_chunk_range` from `src/rag/db.py`:

| Collection | Documents | Pairs |
|---|---|---|
| `github_releases` | 100 | 143 |
| `rag-cli-docs` | 116 | 417 |
| `trading-reference` (large reference collection, largest by chunk count at 13,240 chunks) | 98 | 13,142 |
| **Total** | 314 | **13,702** |

All three collections were indexed with the chunker's defaults (chunk_size=2000, overlap=400, word-aligned), matching `merge_with_overlap` in `src/rag/chunker.py`.

## Variants measured

- **(a)** the real `find_overlap` (`src/rag/retriever.py`) as shipped, `max_overlap=300`
- **(b)** the real `find_overlap`, `max_overlap=2000` (raised cap, same algorithm, imported unmodified)
- **(c)** (b) plus whitespace-normalized suffix/prefix matching (collapse whitespace runs to one space on both sides, scan on the normalized strings, then map the matched length back to the exact original-text cut index in chunk i+1)

## Headline numbers

| Variant | github_releases zero% | rag-cli-docs zero% | trading-reference zero% | Overall zero% (n=13,702) |
|---|---|---|---|---|
| (a) cap=300 | 97.9% | 97.4% | 92.2% | 92.4% |
| (b) cap=2000 | 0.0% | 0.0% | 0.0% | 0.0% |
| (c) cap=2000 + ws-tolerant | 0.0% | 0.0% | 0.0% | 0.0% |

Match-length distributions (overall, n=13,702): (a) mean=9.7, median=0.0, max=300 (capped). (b) and (c): mean=402.7, median=394.0, min=10, max=2000 — both variants produce **bit-for-bit identical** min/max/mean/median in every collection, and a per-pair diff count of **0 disagreements out of 13,702 pairs**.

## Which mechanism dominates

Mechanism 1 (the `max_overlap=300` cap sitting below the real ~400-char overlap) fully explains the observed failures. Evidence:

- Raising the cap alone (variant b, same unmodified `find_overlap` code) already drives zero-match from 92.4% down to 0.0% overall, with median match length 394 chars — consistent with the configured `overlap=400` minus the word-alignment trim (`get_word_aligned_overlap` in `src/rag/chunker.py` rounds the cut to the nearest following space, always shrinking the raw 400-char window).
- Under (a), the handful of non-zero matches (mean 9.7, some pairs hitting the 300 cap) are the minority of pairs whose true overlap already happened to be ≤300 chars (e.g. short trailing splits near a document boundary) — not evidence of a second failure mode, just the tail of the same capped-search problem.

Mechanism 2 (whitespace asymmetry between the stripped chunk tail and the unstripped overlap-seed head) does **not** manifest as an observable failure in this data: variant (c) never disagrees with variant (b) — 0 diffs across all 13,702 pairs, in every one of the three collections. Reading `merge_with_overlap` again confirms why: `get_word_aligned_overlap` cuts on a space and returns `raw[space_idx + 1:]`, i.e. the seed text for chunk i+1 already starts right after a space, and the corresponding tail of chunk i (`current.strip()`) ends without trailing whitespace — the two boundaries the seed and the source text are read from are the same in-memory slice, so no whitespace divergence is actually introduced between them on this data. The theoretical risk described in the task background did not reproduce.

## Does variant (c) close the gap completely?

Yes, on the measured 13,702 pairs across all three collections: 0 residual zero-match pairs under (c). Raising the cap alone (b) already reaches 0% zero-match; (c)'s whitespace tolerance adds no additional matches and removes no matches — it is a no-op on this dataset. No residual-failure excerpts to report because there were none.

## Caveats / things a fix should watch for

- **`trading-reference` min=10 match (variant b/c):** `Tsay2010AnalysisFinancialTimeSeries.md` @ chunk_index 752 — a degenerate table/code-block boundary (`nf.bn$k` R console output) where the genuine word-aligned overlap collapses to a short numeric/table fragment. Not a bug, just a low-content boundary; a fix should not assume overlap length is always close to 400.
- **`trading-reference` max=2000 match (variant b/c), i.e. the raised cap was hit:** `HorvathKokoszka2012InferenceFunctionalData.md` @ chunk_index 210 — a PDF-extraction artifact of thousands of repeated `\)` characters. Because the content is highly repetitive, the true suffix/prefix match likely extends past the 2000-char cap probed here; a fixed large cap can still under- or over-match on degenerate repetitive text. A production fix should bound the search near the configured `overlap` parameter (e.g. `overlap + word-alignment slack`) rather than picking an arbitrary large constant, to avoid both re-introducing the original capping bug and picking up spurious long matches in repetitive content.
- All three collections were chunked with the same `chunk_size=2000/overlap=400` config; this probe does not cover collections indexed with different chunk_size/overlap settings, if any exist.
