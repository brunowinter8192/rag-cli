# NULL Embeddings — Qwen3-Embedding-8B Tokenizer Bug (FIXED 2026-05-06)

## Symptom

Indexing runs silently dropped ~3-4% of chunks. Indexer reported "Indexed 704 chunks" but DB only stored 678. No error message visible to the operator — the loss surfaced only when querying chunk count via `rag-cli list_collections` and comparing against the chunker's output.

## Reproduction

`searxng_reference` collection, 704 chunks across 59 markdown files. Re-running the entire indexing pipeline against the same chunks.json files reproduced **exactly** the same 26 missing `(document, chunk_index)` pairs every time:

| Document | Failing chunk indices |
|---|---|
| `crawl4ai__complete-sdk-reference.md` | 27, 28, 29, 72, 73, 74, 75, 76, 77, 78, 107, 108, 109, 147 (14) |
| `crawl4ai__core__deep-crawling.md` | 2, 3, 4, 5 (4) |
| `crawl4ai__core__markdown-generation.md` | 3, 4, 5, 6, 7, 8, 9, 10 (8) |

100% deterministic across runs, all on the same three docs (the only ones with substantial Python code blocks in this corpus).

## Root Cause

`Qwen3-Embedding-8B` requires a task-specific prefix on inputs. Without prefix, the tokenizer produces a state for certain code-heavy chunks (typically those starting with bare `import` or `from X import Y` at the chunk boundary) that the model cannot encode — the embed call returns HTTP 200 with `{"embedding": [None, None, ... 4096x]}` instead of throwing. The indexer's `store_chunks` correctly detected and skipped these via warning, but the warning went to the embedder log file (not stdout), and the workflow's final summary printed the input-chunk count rather than the actually-stored count, masking the loss.

## Hypotheses Ruled Out

| Hypothesis | Test | Result |
|---|---|---|
| Server state degradation over uptime | Killed embedding server (5d uptime), re-ran the same 26 chunks | Still NULL on fresh server — uptime irrelevant |
| Batch-size effect (32-batch vs single) | Sent same chunks individually | Same NULLs in single calls |
| GPU memory fragmentation | Restart resets memory | Bug persists after restart |
| Statistical / random | 10 trials of chunk 3 in a row | NULL 10/10 — deterministic |

## Fix

`src/rag/indexer.py:parallel_embed` now passes `prefix="search_document: "` to `embed_workflow`. With the prefix, all 26 previously-failing chunks embed correctly; verified 0/26 NULL in re-test.

Diff (commit `<see git log>`):

```python
# Before
emb_future = executor.submit(embed_workflow, texts)

# After
emb_future = executor.submit(embed_workflow, texts, "search_document: ")
```

The prefix is a Qwen3 task convention (analogous models use `search_query: ` for retrieval queries). Embedding shapes are now consistent with the model's training distribution, and the all-None edge case is eliminated.

## Visibility — Same-Indexing-Run Detection

Even with the prefix fix, future tokenizer regressions / unknown content patterns could produce NULLs again. Added two safety nets in the same change:

1. `store_chunks` now returns the `skipped` count (was unused before).
2. `index_json_workflow` aggregates `skipped` per file and returns the actually-indexed count (was returning the input count, masking losses).
3. `workflow.py index-dir` final summary prints a `⚠️  WARNING: N chunks (X.X%) skipped due to NULL embeddings.` block when `chunked > indexed`. Operator-visible at run-time, not buried in a log.

## Status After Fix

| Run | Chunks chunked | Chunks indexed | NULL skipped |
|---|---|---|---|
| Original (2026-05-06, no prefix) | 704 | 678 | 26 |
| After fix (2026-05-06, with prefix) | 704 | 704 | 0 |

## Notes for Future Investigations

- This bug existed independently in `decisions/index02_dense_embedding.md` as a "Known Issue" with the documented fix. **The fix had been validated but never integrated into the production code path.** Decisions docs describe SOLL state; if a fix is documented as validated but the code says otherwise, the doc lies. Sanity-check by reading the actual call site, not the decision file alone.
- A symptom that survives a server restart in deterministic form is content-driven; a symptom that survives one restart but not another is likely state-driven or environmental. We confused ourselves on this run by stopping investigation after the first restart yielded mixed results — should have re-tested with full batch shape (32-parallel), which matches the production indexer path.
- The `embedder.log` file (`src/rag/logs/embedder.log`) had the NULL warnings the whole time. Nobody read it. Stale logs and run-time output diverging is itself a class of bug — solved here by the workflow.py warning block.
