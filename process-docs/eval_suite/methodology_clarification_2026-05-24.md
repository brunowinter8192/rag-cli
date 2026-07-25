# Eval Methodology Clarification — 2026-05-24

## Status

Session clarification of the eval methodology after 14 days pending.
Four core points:

1. **Relevance-by-construction** replaces doc-level approximation and LLM-judge — resolves the eval-trust pain point.
2. **`queries_test_db.json` schema extension** with `expected_chunks` (the chunks the query was built from).
3. **`collections` metadata table** as a prerequisite for sweeps across different indexing configs (chunk size, model, with/without sparse) — its own thematic area, only linked here.
4. **`DENSE_SCORE_THRESHOLD = 0.01` removal** — side decision, the top_k=12 cap is the real ceiling.

Plus a snapshot of what test_db currently is, plus the open SPLADE question that moves into the sweep.

## Test-DB Snapshot (as of 2026-05-24)

7 papers, 250 chunks, consistently academic RAG/retrieval methodology, English, prose with embedded tables + code:

| Document | Chunks | Avg Chars | Max Chars |
|---|---|---|---|
| Fusion_Functions_Hybrid_Retrieval | 70 | 1713 | 1993 |
| RAG_Evaluation_Survey_2025 | 65 | 1834 | 2053 |
| Qwen3_Embedding | 32 | 1758 | 2213 |
| Rethinking_Chunk_Size_Long_Document | 25 | 1704 | 2363 |
| RAGAS_Evaluation_Framework | 24 | 1696 | 2038 |
| Pipeline_Optimization | 22 | 1809 | 1995 |
| SPLADE_v3 | 12 | 1683 | 1998 |

Acknowledged weakness: **a single domain cluster**. Eval results from this collection say "for RAG-methodology papers, X is good" — not whether X is also good for API docs (Monitor_CC_reference), trading books (Trading), or our own technical docs (RAG-docs / Monitor_CC-docs). The extension path stays as outlined elsewhere: extend test_db with other domains every few weeks and re-eval against the larger collection. The current snapshot is sufficient as a baseline.

## Relevance-by-Construction

**Before (wrong mental model):** eval relevance was treated as having an approximation gap that needed closing via either doc-level heuristic (`expected_documents` as "relevant = every chunk from this file"), substring matching (`expected_snippets` as "relevant = the chunk containing this string"), or LLM-judge (RAGAS-style).

**Actually:** the 17 queries came about by a worker reading the MDs and formulating queries based on what was read. At query-formulation time, the worker knew with 100% certainty which text was the query's source. Relevance was not an estimation problem — it was an input datum. The query exists only because a specific chunk exists and was used as its template.

Consequence:

- **No LLM-judge needed.** RAGAS and similar frameworks need an LLM-judge because there queries and documents exist independently — relevance must be approximated after the fact. Here the query comes from the document; relevance is fixed by design.
- **Doc-level approximation drops out for Recall@K.** Currently `Recall@K` counts every chunk from `expected_documents` as relevant. With 70 chunks in Fusion_Functions, all 70 are "relevant" even though only 1-2 were the query's source. Wrong, and fixable via constructive chunk indices.
- **`snippet_recall` becomes a sanity check, not the primary metric.** With the chunk index directly in the test set, substring matching on the snippet is now only a robustness check — "did the system really return the expected wording". The primary metric becomes position-based on the constructive chunk.

Trade-off of the construction method (keep transparent): the definition is *strict*. If another chunk in the collection happens to contain the same information (a duplicate in a survey-paper section, a re-statement in a second paper), it does not count as relevant — only the original chunk the query was built from does. This is precision-oriented, not content-level recall-oriented. For our pipeline verification (does the system reach the expected source?), that is exactly right; for "can the system find every content-matching spot", it would be too narrow. The latter is not this eval's goal.

## Schema Extension `queries_test_db.json`

Before:
```json
{
  "query": "...",
  "type": "factual",
  "expected_documents": ["X.md"],
  "expected_snippets": ["..."]
}
```

After:
```json
{
  "query": "...",
  "type": "factual",
  "expected_documents": ["X.md"],
  "expected_chunks": [{"document": "X.md", "chunk_index": 17}, ...],
  "expected_snippets": ["..."]
}
```

`expected_chunks` is the by-construction list of source chunks. A query can have multiple source chunks (cross-document queries, like the two at the end of test_db, have at least two). If a snippet spans a chunk boundary (possible with our 400-char overlap), enter both chunks.

**Migration task for the 17 existing queries:** mechanical — for each query, find the existing snippet in the DB (or the MD), read off the chunk index, record it. Edge cases by hand: snippet spanning a chunk boundary, snippet with whitespace drift against DB content, snippet paraphrased rather than literal (shouldn't happen since the queries are grep-verified, but check).

## Metric Semantics Under the New Definition

`snippet_recall` (sanity check): per query, the share of `expected_snippets` that appear as a substring in any top-K hit. 1.0 if all, 0.0 if none. Robust against chunk-index drift on re-indexing with a different chunk size, but sensitive to wording drift.

`doc_recall` (diagnostic): per query, did *any* chunk from each `expected_documents` make it into top-K. Binary per expected doc, aggregated over the list. If `doc_recall=1` but the new chunk-level Recall=0 → right source found but wrong spot within it → a chunking/ranking problem in retrieval.

**`Recall@K` (chunk-level, newly defined):** |`expected_chunks` in top-K| / |`expected_chunks` total|. The "total" is now a small number (1-3 per query), not the whole file. This makes Recall@K an honest metric: "of the chunks that caused this query, how many came back".

**`MRR@K` (Mean Reciprocal Rank):** 1 / position of the first `expected_chunks` hit in top-K. 0 if none. Measures "how high up is the constructive source". Matters when the system only surfaces top results.

**`NDCG@K` (Normalized DCG):** standard IR metric, sums relevance with a log discount by position, normalized against the ideal ordering. With binary relevance (chunk ∈ expected_chunks or not) on constructive ground truth: measures ranking quality precisely — the system is penalized both for missing hits and for hits at a poor position. This is the discriminative metric of choice for config comparisons (α sweep, mode sweep, top_k sweep).

**Which is primary for our decisions?** Proposal: NDCG@K as the primary metric for sweep comparisons (discriminative, ranking-aware), Recall@K as an "absolute coverage" plausibility check, snippet_recall as a sanity check against wording drift. doc_recall only as a diagnostic when the main metrics show poor values and we want to understand whether the document was found at all.

## SPLADE Question Stays Open, Moves Into the Sweep

User question this session: do we need SPLADE in retrieval at all, or is it only an indexing-time boost? Answer from code inspection: SPLADE is actively used at query time — in `search_hybrid` the query is sparse-embedded, matched against the `sparse_embedding` column, and fused with the dense branch via CC fusion. Without SPLADE in retrieval, the entire sparse branch drops out → `search_hybrid` reduces to pure dense (or dense + BM25 as a lexical substitute).

Historical evidence is mixed:
- searxng (technical docs, n=2337): hybrid with SPLADE *worse* than dense (NDCG@3 0.298 vs 0.465). SPLADE hurts.
- qwen3_paper (academic, n=66): hybrid better, sparse alone even better than dense. SPLADE helps.
- RAG_MCP (mixed, n=483): CC α=0.8 with SPLADE +6pp snippet recall over dense. SPLADE helps.

Production distribution is mixed — we have *no* solid evidence on whether SPLADE helps or hurts in aggregate for us. **Decision:** no premature SPLADE removal; instead the `--sweep mode` run in the next eval stage includes dense / sparse / hybrid / cc as comparison modes on test_db. If the result clearly favors dense, the consequence is its own discussion: remove SPLADE from indexing (drop the server, drop the sparsevec column, the nnz-corruption bug becomes irrelevant) and switch retrieval to dense-only. But that is evidence-gated, not intuition-driven.

## DENSE_SCORE_THRESHOLD = 0.01 — Removal

`src/rag/retriever.py:23` defines `DENSE_SCORE_THRESHOLD = 0.01` with the comment "noise floor; was 0.5 (unverified Haiku heuristic)". Applied in `search_workflow` and `search_hybrid_workflow` (no-rerank branch) to the top-K results after fusion.

Mechanics: `top_k = min(top_k, 12)` is the hard cap on how many hits come back at all. The filter afterward only kills hits *within the top-12* that fall below 0.01 cosine. In practice: dense cosine on relevant matches sits in the 0.4-0.8 range, on non-relevant ones 0.1-0.3. Values < 0.01 are extremely rare and mean "the collection has nothing for the query".

Effect: in 99% of cases the filter changes nothing. In the 1% case where nothing matches: the user gets 0 hits instead of 12 garbage hits. That would be arguable as a feature ("honest no-result signal"), but:

- The value has been explicitly marked "unverified" since 2026-05-11
- Nobody measures against it
- Edge case (only 1% of cases), and in that edge case the user can also read off the low scores from 12 results themselves
- Consistency: we'd rather remove uncalibrated defaults than keep them unverified in the code

**Decision:** remove the threshold. `filter_by_score(results, DENSE_SCORE_THRESHOLD)` calls in `search_workflow` and `search_hybrid_workflow` (no-rerank) come out. The BM25 branch (`search_keyword_workflow`) uses a separate `0.05` value, which stays untouched (BM25 is a different scale, its own discussion).

The reranking configuration doc needs updating after the code change — the mention of the `DENSE_SCORE_THRESHOLD = 0.01` "unverified" pending item drops out.

## Collections Metadata Table — Its Own Topic, Only Linked Here

User requirement: for each collection it must be queryable from the DB what it was indexed with (embedding model, sparse model, chunk size, overlap, etc.), so eval reports have clean provenance.

The current `documents` table schema has no such metadata column:
```
id, content, collection, document, chunk_index, total_chunks, embedding, sparse_embedding, tsv
```

Proposal: a new `collections` table with:
```
name PK, embedding_model, embedding_dims, sparse_model (nullable),
chunk_size, overlap, db_name, indexed_at, doc_count, chunk_count, notes
```

Non-reindex migration: schema migration + indexer update (writes a row on every index run, upserts on re-index), backfill of the existing eight collections from known configs already on record. test_db gets its entry with the values captured today.

Side effect: `rag-cli list_collections` can also show model + chunk size — a self-describing system.

**Topic splitting:** this is infrastructure work touching several pipeline steps (indexing pipeline, retrieval CLI, eval reports). Its own thematic area holds the detail discussion; the eval thread only references "required for clean sweep-report provenance".

## Updated Worker Pipeline for the Next Stages

In dependency order:

1. **Methodology update** (this entry plus updating the eval methodology docs plus the `queries_test_db.json` schema extension with chunk indices). Prerequisite for everything else.
2. **Collections metadata table** (schema migration, indexer update, backfill, eval reports consume the new table). Prerequisite for (4) so new test_db variants have clean provenance.
3. **Remove DENSE_SCORE_THRESHOLD** (small, can run parallel to (2) or as a side commit within it).
4. **Chunk-size sweep on test_db / test_db_2 / test_db_3** with 2000/1000/512-char chunk size, same source MDs, same 17 queries (chunk indices in queries_test_db.json must track per variant — either separate queries files per variant or a schema hack with a chunk-size-conditional index). Eval run, reports, config updates.
5. **`--sweep mode` on the current test_db** (separate from or together with (4)) — answers the SPLADE question conclusively.
6. **Tickets** for MCP Auto-Collection routing and Graph RAG (creation only, no code this session).

(1)-(3) are feasible this or next session. (4) needs 3x indexing runs + a sweep run, its own session. (5) can run with (4) or separately. (6) at the end.

## Open Questions

- **Chunk indices per chunk-size variant.** If test_db_2 is indexed with chunk_size=1000, chunk boundaries differ → the same source text sits at different chunk indices. The `expected_chunks` from queries_test_db.json are chunk-size specific. The solution must come with the methodology worker task (1): either a separate queries file per test_db variant with adjusted indices, or eval code that remaps an "expected text span" onto the variant (more complex, more robust). Proposal: a separate queries file per variant (queries_test_db.json, queries_test_db_2.json, queries_test_db_3.json), mechanically derivable from the source-MD position of the expected_snippet.
- **Cross-document queries** (Q16, Q17 in test_db) are especially sensitive to the strict construction definition — when both source docs must be found, Recall@K is relative to 2, not 1. Already correct in the new schema (`expected_chunks` as a list spanning multiple documents), but check during migration whether the existing Q16/Q17 really have one or more chunks per source doc.
- **Whether snippet_recall stays** — once chunk index becomes the primary metric, substring matching on the snippet is largely redundant (if the chunk was hit, the snippet was in it by construction). But as a robustness test against "the system found the right chunk but mis-cut it / a different chunk boundary was active at indexing time", it's worth keeping. Resolved in worker (1).

## Sources

- RAG_reference collection: RAGAS_Evaluation_Framework (LLM-judge pattern as an alternative we EXPLICITLY do not need), RAG_Evaluation_Survey_2025 (metric taxonomy), Fusion_Functions_Hybrid_Retrieval (NDCG as the IR standard)
