# Comment/Docstring Triage and DOCS.md Reformat — Module Standards Conformance (2026-09-16)

## Scope

Milestone 2 of the module-standards effort: removed every non-marker comment and every docstring
from the 53 files a project-wide scan flagged (14 docstrings, 505 comments, matching the scan
exactly — verified with an AST+tokenize extractor before touching any file). The three section
markers (`# INFRASTRUCTURE`, `# ORCHESTRATOR`, `# FUNCTIONS`) and shebangs are the only comments
left in place. Every `DOCS.md` in a touched directory (8 files: root, `dev/`, `dev/chunker/`,
`dev/rag-chunking/`, `dev/indexing/`, `dev/retrieval/`, `dev/server_management/`, `src/rag/`) was
rewritten to the strict Role/Public Interface/Flow/Modules/State format.

## How the code edit was verified safe (read this before touching these 53 files again)

Comment/docstring removal was done **mechanically**, not by hand-editing each file. A tokenize-based
stripper (kept nowhere in this repo, it was a throwaway `/tmp` tool — rebuild it from this
description if you need it again) did two things per file:

1. Walked `tokenize.COMMENT` tokens. A comment that is the only content on its physical line
   (whitespace-then-`#`) → delete the whole line. A trailing comment after code → truncate the
   line at the comment start and `rstrip()`. The three markers and a leading `#!` shebang are
   exempted.
2. Walked the AST for module/class/function docstrings (`body[0]` being a string `Expr`) → deleted
   their exact line range.

**Proof of zero code-line drift**, run once per file before writing: tokenize both the original and
the stripped source, keep only `NAME`/`OP`/`NUMBER`/`STRING`/`FSTRING_*` tokens (drop
`COMMENT`/`NL`/`INDENT`/`DEDENT`), remove the docstring `STRING` tokens from the *original* token
stream by value-match, and assert the two token sequences are then identical. All 53 files passed
this check before a single write happened. After writing: `py_compile` on all 53 (clean), and the
extractor re-run on the result showed `doc=0 com=0` project-wide.

This is the same proof technique to reuse for any future comment-only or docstring-only edit across
many files — it is much cheaper than reviewing 53 diffs by eye and it catches a truncation bug
immediately (a token would go missing or shift).

## Triage rule applied

Per comment/docstring: if its substance already appeared in the *pre-rewrite* `DOCS.md` for that
module's directory, or in an existing `process-docs/` entry, it was deleted with nothing else
happening. If not, its exact text was copied below before deletion. "Substance already carried" was
decided by actually reading the owning DOCS.md (as it stood before this milestone's rewrite — see
git history prior to this commit for those originals) and the relevant `process-docs/` areas
(`retrieval`, `server_management`, `rag-chunking`, `indexing`, `infra`, `eval_suite`, `delivery`),
not by guessing from the comment text alone. Where a comment's substance was *partially* covered —
same topic, but the code comment carried a specific number, formula, or edge case the doc didn't —
it was treated as not-covered and relocated whole, to avoid silently dropping the more precise
version.

One deliberate exception found during triage: `src/rag/watchdog.py`'s per-tick comment says orphans
are purged and idle-stop fires when a server's "log hasn't been touched" past `IDLE_TIMEOUT`. The
current architecture (see `process-docs/server_management/watchdog_idle_initial_design.md` and
`box_architecture.md`) keys idle-stop off **state-file mtime**, not log mtime — that switch predates
this session. The comment was relocated as-is (verbatim, per the rule) rather than corrected; fixing
stale comments is out of scope for a milestone that only deletes and relocates. Flagging here so the
next agent doesn't mistake the relocated text for current behavior.

## Triage table

File-by-file counts. "Hits" = comments + docstrings found by the extractor (matches the input scan
exactly, verified before any edit). "Deleted" = substance already covered elsewhere, comment
removed with no further action. "Relocated" = substance not covered, exact text moved to the
`## Salvage from <path>` sections below before deletion.

| File | Hits | Deleted (covered) | Relocated |
|---|---|---|---|
| `src/rag/server_lifecycle.py` | 40 | 9 | 31 |
| `src/rag/server_utils.py` | 36 | 13 | 23 |
| `src/rag/db.py` | 26 | 15 | 11 |
| `src/rag/sync.py` | 22 | 6 | 16 |
| `eval/scripts/validate_pass_c.py` | 21 | 4 | 17 |
| `src/rag/server_manager.py` | 19 | 10 | 9 |
| `dev/rag-chunking/test_overlap_dedup.py` | 19 | 16 | 3 |
| `dev/server_management/A_constellation_profile.py` | 17 | 3 | 14 |
| `dev/rag-chunking/A_overlap_match_probe.py` | 17 | 15 | 2 |
| `dev/retrieval/A_mrl_sweep.py` | 17 | 0 | 17 |
| `eval/scripts/validate_pass_b.py` | 17 | 6 | 11 |
| `src/rag/indexer.py` | 16 | 7 | 9 |
| `src/rag/server_cli.py` | 15 | 8 | 7 |
| `eval/scripts/validate_pass_d.py` | 15 | 1 | 14 |
| `src/rag/lock.py` | 14 | 12 | 2 |
| `dev/server_management/constellation_measure.py` | 13 | 0 | 13 |
| `eval/scripts/validate_pass_a.py` | 12 | 0 | 12 |
| `dev/indexing/p4_db.py` | 11 | 10 | 1 |
| `dev/server_management/B_real_smell.py` | 10 | 3 | 7 |
| `dev/retrieval/eval_report.py` | 9 | 0 | 9 |
| `eval/scripts/audit_leakage.py` | 9 | 0 | 9 |
| `cli.py` | 9 | 8 | 1 |
| `dev/retrieval/eval_cross_report.py` | 8 | 0 | 8 |
| `dev/retrieval/eval_metrics.py` | 8 | 0 | 8 |
| `dev/retrieval/eval_runner.py` | 8 | 0 | 8 |
| `dev/retrieval/p1_retriever.py` | 8 | 7 | 1 |
| `src/rag/status.py` | 7 | 7 | 0 |
| `dev/retrieval/A_retrieval_eval.py` | 7 | 0 | 7 |
| `dev/retrieval/eval_constellation.py` | 7 | 0 | 7 |
| `src/rag/chunker.py` | 6 | 3 | 3 |
| `src/rag/formatting.py` | 6 | 3 | 3 |
| `src/rag/index_cmd.py` | 6 | 5 | 1 |
| `eval/scripts/filter_spans_only.py` | 6 | 3 | 3 |
| `dev/indexing/A_index_collection.py` | 5 | 3 | 2 |
| `dev/indexing/p1_chunker.py` | 5 | 2 | 3 |
| `src/rag/error_log.py` | 4 | 2 | 2 |
| `src/rag/watchdog.py` | 4 | 3 | 1 |
| `dev/retrieval/A_retrieval_sandbox.py` | 4 | 0 | 4 |
| `dev/indexing/A_chunking_stats.py` | 4 | 4 | 0 |
| `dev/chunker/A_quote_coverage.py` | 4 | 0 | 4 |
| `dev/lock_progress/test_update_progress_collection.py` | 4 | 4 | 0 |
| `src/rag/embedder.py` | 3 | 2 | 1 |
| `src/rag/retriever.py` | 3 | 3 | 0 |
| `src/rag/server_lock.py` | 3 | 0 | 3 |
| `dev/indexing/p5_indexer.py` | 3 | 2 | 1 |
| `src/rag/reranker.py` | 2 | 2 | 0 |
| `src/rag/search_primitives.py` | 2 | 2 | 0 |
| `dev/retrieval/eval_config.py` | 2 | 0 | 2 |
| `dev/indexing/p2_embedder.py` | 2 | 2 | 0 |
| `src/rag/splade_server.py` | 1 | 0 | 1 |
| `src/rag/watchdog_main.py` | 1 | 1 | 0 |
| `dev/error_log/analyze_errors.py` | 1 | 1 | 0 |
| `dev/indexing/p3_sparse_embedder.py` | 1 | 1 | 0 |
| **TOTAL** | **519** | **208** | **311** |

Total: 519 hits (505 comments + 14 docstrings) across 53 files — 208 deleted as already-covered,
311 relocated below.

## DOCS.md reformat

All 8 rewritten `DOCS.md` files now carry `### <module>.py (<LOC> LOC)` headings whose LOC value was
checked against a fresh `wc -l` at write time (see the completion checklist in the session report
for the verification run). Everything that didn't fit the five-section format — Usage blocks,
CLI flag tables, JSON examples, a Gotchas section, narrative Role paragraphs beyond one paragraph,
a Documentation Tree index — is salvaged verbatim below, one `## Salvage from <path>` heading per
file, in the same order as the DOCS.md rewrites.

## Salvage from `DOCS.md` (root)

Cut in the milestone-2 format rewrite (Usage blocks, subcommand table, Skip-Logik, Lock model, Gotcha — none fit Role/Public Interface/Flow/Modules/State):

**cli.py subcommand table:**

| Subcommand | Description |
|---|---|
| `search` | Dense retrieval + cross-encoder reranking; top_k=12 fixed (always-rerank, no toggle) |
| `list_collections` | All indexed collections with chunk counts; `--json` outputs `[{collection, chunks}]` array |
| `list_documents` | Documents in a collection |
| `progress` | Indexing progress per document — done/total chunks (pollable during index run) |
| `read_document` | Anchor chunk plus N chunks before and M chunks after |
| `index` | Chunk + index `.md` files from `data/documents/<collection>/`; `--collection` required, `--document` optional; skip-by-default via `indexed_files` hash; `--force` re-embeds all |
| `delete` | Delete chunks + `indexed_files` manifest + on-disk source (`.md` + `.json` sidecar); `--collection` required, `--document` optional |
| `update_docs` | Sync project docs into RAG collection per `.rag-docs.json` manifest; hash-based change detection |
| `server` | GPU server control — status / start / stop / restart [name] |
| `status` | Lock state, GPU server health, Postgres reachability; **lock-exempt** |

**Skip-Logik (`index`):** Per file the SHA256 of the content is compared against the `indexed_files` tracking table (collection, document, sha256). Three buckets per run:

- **skipped** — hash matches an existing entry → no work
- **adopted** — file not in `indexed_files`, but a complete chunk set exists in `documents` (COUNT == MAX(total_chunks)) → register hash without re-embed (one-time bootstrap for collections that pre-date hash tracking)
- **indexed** — missing, partial, or hash-changed → chunk + embed + insert + register hash

GPU servers are only started when there is real work to embed. `--force` bypasses the skip and re-embeds every file (use only when the embedding model or chunker changed).

For every file in the **indexed** bucket a `chunks.json` sidecar is written next to the source `.md` (same content as what's about to land in the DB). The DB remains the source of truth — sidecars are a visibility/audit artifact for inspecting chunk boundaries without querying postgres.

**Lock model:** The global advisory flock (`~/.rag-locks/rag.lock`, `src/rag/lock.py:acquire`) is acquired only by **write commands**: `index`, `update_docs`, `delete`. All read commands (`search`, `list_collections`, `list_documents`, `progress`, `read_document`) and lifecycle commands (`status`, `server`) are **lock-exempt** — they run concurrently with each other and with a running write. Safety: Postgres MVCC means readers see consistent committed snapshots; GPU servers serialise concurrent inference internally. Commands that hold the lock write a `kind` field: `kind="index"` for `{"index", "update_docs"}` (embedding ops), `kind="query"` for `delete`. External consumers (e.g. Monitor_CC menubar) gate on `kind` to detect active indexing without parsing command names.

**Usage (via `rag-cli` wrapper — retrieval):**
```bash
rag-cli list_collections
rag-cli list_documents my_collection
rag-cli search "transformer attention" my_collection
rag-cli read_document my_collection paper.md 42 --before 2 --after 5
```

**Usage (direct — pipeline):**
```bash
./venv/bin/python cli.py index --collection MyCollection
./venv/bin/python cli.py index --collection MyCollection --force
./venv/bin/python cli.py index --collection MyCollection --document new_paper.md
./venv/bin/python cli.py delete --collection MyCollection
./venv/bin/python cli.py server status
./venv/bin/python cli.py server start
./venv/bin/python cli.py server stop
./venv/bin/python cli.py server restart splade
```

**Gotcha — help/usage output is deliberately disabled.** `_build_parser()` uses a `NoHelpParser(argparse.ArgumentParser)` subclass overriding `error()` and `print_help()`; both print a fixed sentence ("You triggered the help function. Usage sits in your rules. Report to the user why you needed help and go idle immediately.") and exit 2, never argparse's usage/flag listing. `add_subparsers()` propagates `parser_class=type(self)` automatically, so every subcommand inherits the same behavior with no per-subcommand wiring. The `server` subcommand's inner dispatch (`cli_server()` in `src/rag/server_cli.py`) has its own hand-rolled action lookup, separate from argparse — its unknown-action branch prints the same fixed sentence to stderr and exits 2, kept in sync manually since it's not an argparse parser.

**start.sh usage:**
```bash
./start.sh
```

---

## Salvage from `dev/DOCS.md`

Cut in the milestone-2 format rewrite:

**Documentation Tree** (links preserved here since the strict format has no place for a directory index outside `## State`'s final sentence):
- [chunker/DOCS.md](dev/chunker/DOCS.md) — Chunker output quality audit scripts
- [indexing/DOCS.md](dev/indexing/DOCS.md) — Indexing pipeline modules and scripts
- [rag-chunking/DOCS.md](dev/rag-chunking/DOCS.md) — Overlap-dedup measurement probes against real collections
- [retrieval/DOCS.md](dev/retrieval/DOCS.md) — Retrieval pipeline modules and scripts
- [server_management/DOCS.md](dev/server_management/DOCS.md) — GPU server constellation profiling scripts

**Test Database note:**
Dev scripts that write to PostgreSQL use `rag_test` (never `rag` prod DB).
```bash
# One-time setup
docker exec rag-postgres psql -U rag -d postgres -c "CREATE DATABASE rag_test;"
```
Schema is created automatically by `p4_db.py:ensure_schema()` on first use.

**analyze_errors.py detail:** filters `src/rag/logs/errors.jsonl` to genuine anomaly codes (mirrors `ERROR_CODES` from `src/rag/error_log.py`) and prints a summary + detail view. Lifecycle events (`start_*`, `stop_*`, `state_unlinked`) are excluded; only the four anomaly classes are shown. Flags: `--all` (full history; default: today only), `--tail N` (detail rows shown; default 10), `--raw` (JSONL dump to stdout for piping).
```bash
./venv/bin/python dev/error_log/analyze_errors.py --all
./venv/bin/python dev/error_log/analyze_errors.py --all --raw | grep watchdog
```

**test_update_progress_collection.py usage:**
```bash
python3 dev/lock_progress/test_update_progress_collection.py
```

---

## Salvage from `dev/chunker/DOCS.md`

**Usage:**
```bash
./venv/bin/python dev/chunker/A_quote_coverage.py
```

**Report sections:** summary stats (single/boundary/missing counts), per-query status table, detail section for boundary and missing cases, index-mismatch detail (quote found in unexpected chunk).

**Configured for:** `test_db` collection on `rag_test` postgres DB, queries from `dev/retrieval/queries_test_db.json`. To run on a different collection/query-set, change `COLLECTION` and `QUERIES_PATH` constants at the top of the script.

---

## Salvage from `dev/rag-chunking/DOCS.md`

**A_overlap_match_probe.py — variant detail:**
- (a) `find_overlap` pinned to the pre-fix cap (`max_overlap=ORIGINAL_CAP=300`) — kept explicit so this variant stays comparable across the fix, independent of `find_overlap`'s live default
- (b) `find_overlap` with a raised cap (`max_overlap=RAISED_CAP=2000`)
- (c) (b) plus whitespace-normalized suffix/prefix matching, with the match position mapped back to the exact (unnormalized) cut index in the second chunk

**Collections probed (edit `COLLECTIONS` constant to change):** `github_releases`, `rag-cli-docs`, `trading-reference`.

**Usage:**
```bash
./venv/bin/python dev/rag-chunking/A_overlap_match_probe.py > /tmp/probe_run.md 2>&1
```

**Output detail:** `md/probe_output_<timestamp>.md` — per-collection and overall distribution stats (n, zero%, min, max, mean, median) for all three variants, residual variant-(c) zero-match pairs with excerpts, pairs where (b) and (c) disagree (isolates the whitespace mechanism from the cap mechanism), and the lowest/highest non-zero variant-(b) match per collection with excerpts.

**Findings as of 2026-09-02:** see `2026-09-02_overlap_match_probe_report.md` in `dev/rag-chunking/`.

**test_overlap_dedup.py usage:**
```bash
./venv/bin/python dev/rag-chunking/test_overlap_dedup.py
```
**Output:** stdout PASS/FAIL per check, non-zero exit code on any failure.

The original Role paragraph also carried this historical framing, cut for being narrative rather than role-level: "The 2026-09-02 measurement found the cap (300) sat below the real word-aligned overlap (~400) as the dominant failure cause; the fix (find_overlap's bound derived from `chunker.DEFAULT_OVERLAP`, `merge_chunks` skipping the `"\n\n"` separator on a real overlap match) now lives in `src/rag/retriever.py`. `A_overlap_match_probe.py` stays read-only against the prod `rag` DB — no writes, no schema changes."

---

## Salvage from `dev/indexing/DOCS.md`

**Config Defaults table:**

| Parameter | Value |
|-----------|-------|
| CHUNK_SIZE | 2000 chars |
| OVERLAP | 400 chars |
| MRL dims | Not applied at index time; `truncate_mrl` available on-the-fly (`p2_embedder.py`) |
| Batch size | 32 |
| DB | rag_test, port 5433, user rag |

**Note (rag_test schema conflict):** If `rag_test` already has a `documents` table with `vector(4096)` from other tools, drop it first:
```bash
docker exec rag-postgres psql -U rag -d rag_test -c "DROP TABLE IF EXISTS documents;"
```

**A_chunking_stats.py CLI flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--source-dir` | required | Directory with `.md` files |
| `--chunk-size` | 2000 | Chunk size in chars |
| `--overlap` | 400 | Overlap in chars |

**A_chunking_stats.py usage:**
```bash
./venv/bin/python dev/indexing/A_chunking_stats.py --source-dir data/documents/RAG_MCP_test
./venv/bin/python dev/indexing/A_chunking_stats.py --source-dir data/documents/RAG_MCP_test --chunk-size 1000 --overlap 200
```

**A_index_collection.py CLI flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--source-dir` | required | Directory with `.md` files |
| `--collection` | source-dir basename | Collection name in DB |
| `--chunk-size` | 2000 | Chunk size in chars |
| `--overlap` | 400 | Overlap in chars |

**A_index_collection.py usage:**
```bash
./venv/bin/python dev/indexing/A_index_collection.py --source-dir data/documents/RAG_MCP_test --collection RAG_MCP_test
./venv/bin/python dev/indexing/A_index_collection.py --source-dir data/documents/RAG_MCP_test --collection RAG_MCP_small --chunk-size 500 --overlap 100
```

**A_index_collection.py note:** After each successful index run the script upserts a row into the `collections` table in `rag_test` via `p4_db.upsert_collection_metadata`. Model/dims/sparse constants (`EMBEDDING_MODEL`, `EMBEDDING_DIMS`, `SPARSE_MODEL`) are defined in INFRASTRUCTURE; `doc_count`/`chunk_count` come from the `stats` dict returned by `index_directory()`.

---

## Salvage from `dev/retrieval/DOCS.md`

This DOCS.md carried extensive narrative content — sweep config JSON examples, per-script CLI flag tables, data-file inventory, and eval-coverage commentary — none of which fits the strict Role/Public Interface/Flow/Modules/State format. Preserved verbatim below.

**p1_retriever.py function table (superseded by module-level Purpose in the rewrite, kept here for the exact signatures):**

| Function | Signature | Description |
|----------|-----------|--------------|
| `retrieve_dense` | `(query, collection, top_k=10, query_prefix=True) -> list[dict]` | Embed query (instruct prefix optional), cosine search |
| `retrieve_sparse` | `(query, collection, top_k=10) -> list[dict]` | SPLADE-embed query, sparse cosine search |
| `retrieve_bm25` | `(query, collection, top_k=10) -> list[dict]` | BM25 full-text search via PostgreSQL tsquery |
| `retrieve_hybrid` | `(query, collection, top_k=10, rrf_k=60, query_prefix=True) -> list[dict]` | Dense + sparse search, RRF fusion |
| `retrieve_cc` | `(query, collection, top_k=10, alpha=0.8, query_prefix=True) -> list[dict]` | Dense + sparse search, Convex Combination fusion |
| `retrieve_cc_rerank` | `(query, collection, top_k=10, alpha=0.8, rerank_candidates=50, query_prefix=True) -> list[dict]` | CC fusion then cross-encoder rerank |
| `rerank` | `(query, results, top_k=10) -> list[dict]` | Cross-encoder rerank via llama-server port 8082 |

**Dense query prefix:** `Instruct: Given a search query, retrieve relevant passages that answer the query\nQuery: `
**query_prefix=False:** passes bare query string to embedder (no instruct prefix). No-op for sparse/bm25 modes.
**Candidates fetched before top_k cutoff:** 50

**A_retrieval_eval.py metrics computed per query + aggregated:**
- `doc_recall` (binary): expected_documents in top-K hits or not
- `snippet_recall` (binary): expected_snippets as substring in any hit's content
- `NDCG@K`: rank-aware, binary relevance (rel=1 if chunk.document ∈ expected_documents)
- `MRR@K`: 1/rank of first relevant hit, 0 if none in top-K
- `Recall@K` (chunk-level): retrieved_relevant / total_relevant_in_collection

**Prerequisites:** Embedding server (8081) always. SPLADE (8083) for sparse, hybrid, cc, cc+rerank, hybrid+rerank modes. Reranker (8082) for any mode containing "rerank".

**Config file example (`eval_config.py`, illustrative — see current file for the live values):**
```python
BASELINE = {
    "mode": "cc", "top_k": 10, "alpha": 0.8, "rrf_k": 60,
    "score_threshold": 0.0, "query_prefix": True,
}
SWEEP_RANGES = {
    "mode": ["dense", "sparse", "hybrid", "cc", "cc+rerank", "hybrid+rerank", "bm25"],
    "top_k": [5, 10, 20], "alpha": [0.5, 0.6, 0.7, 0.8, 0.9],
    "rrf_k": [30, 60, 90], "score_threshold": [0.0, 0.3, 0.5],
    "query_prefix": [True, False],
}
```

**score_threshold** is applied only for cosine-based modes (dense, sparse, cc, cc+rerank). For rrf/bm25/rerank modes, score scales are not comparable — the threshold is silently ignored and the report header carries a warning note.
**query_prefix** is a no-op for pure sparse/bm25 modes (no dense embedding step). The report header carries a note when swept over these modes.

**A_retrieval_eval.py CLI flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--collection` | `test_db` | Collection name to query |
| `--queries` | `dev/retrieval/queries_test_db.json` | Queries JSON path |
| `--baseline` | — | Single run at BASELINE config (+ any `--override`) |
| `--sweep PARAM` | — | Sweep `PARAM` over `SWEEP_RANGES[PARAM]`; others fixed at BASELINE |
| `--override key=val` | — | Override one BASELINE key; repeatable |

Exactly one of `--baseline` or `--sweep PARAM` is required.

**Queries JSON format:**
```json
{
  "queries": [
    {
      "query": "What embedding dimensions does Qwen3 support?",
      "type": "factual",
      "expected_documents": ["Qwen3_Embedding_Paper"],
      "expected_snippets": ["Matryoshka Representation Learning"]
    }
  ]
}
```

**Usage:**
```bash
./venv/bin/python dev/retrieval/A_retrieval_eval.py --baseline
./venv/bin/python dev/retrieval/A_retrieval_eval.py --baseline --override mode=dense --override top_k=20
./venv/bin/python dev/retrieval/A_retrieval_eval.py --sweep alpha
./venv/bin/python dev/retrieval/A_retrieval_eval.py --sweep mode
./venv/bin/python dev/retrieval/A_retrieval_eval.py --sweep score_threshold
./venv/bin/python dev/retrieval/A_retrieval_eval.py --sweep alpha --override top_k=20 --override mode=cc+rerank
```

**A_retrieval_sandbox.py CLI flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--collection` | required | Collection name to query |
| `--queries` | required | Path to JSON file with queries list |
| `--top-k` | `5` | Results per query per mode |
| `--modes` | `dense,sparse,hybrid,cc` | Comma-separated modes |

**Valid modes:** `dense`, `sparse`, `hybrid`, `hybrid+rerank`, `cc`, `cc+rerank`
**Queries JSON format:** `["What embedding dimensions does Qwen3 support?", "How does SPLADE work?"]`
**Usage:**
```bash
./venv/bin/python dev/retrieval/A_retrieval_sandbox.py --collection RAG_MCP_test --queries dev/retrieval/queries.json --top-k 5
./venv/bin/python dev/retrieval/A_retrieval_sandbox.py --collection RAG_MCP_test --queries dev/retrieval/queries.json --modes dense,hybrid,cc
./venv/bin/python dev/retrieval/A_retrieval_sandbox.py --collection RAG_MCP_test --queries dev/retrieval/queries.json --modes cc+rerank --top-k 10
```

**A_mrl_sweep.py:** Sweeps embedding dimensions [256, 512, 768, 1024, 2048, 4096] to evaluate dense and hybrid retrieval quality across MRL truncation levels. Collection and dimensions are hardcoded (`COLLECTION = "RAG_MCP_test"`). Requires full 4096d embeddings already indexed. Prerequisites: embedding server (8081), SPLADE (8083). Output: `md/mrl_sweep_<timestamp>.md`. Usage: `./venv/bin/python dev/retrieval/A_mrl_sweep.py`.

**Data files:**
- `queries_test_db.json` (active): 17 queries with ground truth for the `test_db` collection. Default queries-path for `A_retrieval_eval.py`. Format: JSON object with `"queries"` array, each entry has `query`, `type`, `expected_documents`, `expected_snippets`. All snippets grep-verified in source MDs. Query mix is factual-heavy; conceptual/cross-document coverage is open (worker-generated baseline, user inspection recommended before authoritative eval execution).
- `queries_rag_mcp_test.json` (historical, retained for reference): 20 queries (8 factual, 7 conceptual, 5 cross-document) for the deprecated `RAG_MCP_test` collection. Collection no longer indexed (April 30 data clean-slate). Not in current eval flow.

**Current Test Database State:** `rag_test` (Postgres) holds the `test_db` collection (250 chunks from 7 reference papers: RAGAS_Evaluation_Framework, RAG_Evaluation_Survey_2025, Pipeline_Optimization, Fusion_Functions_Hybrid_Retrieval, Qwen3_Embedding, SPLADE_v3, Rethinking_Chunk_Size_Long_Document — copied from `data/documents/rag-cli-reference/` and re-indexed for isolated eval). Production DB `rag` holds the live collections (RAG-features, RAG-meta, RAG_reference, searxng_reference, Trading, Trading_internal). Strict separation: eval runs against `rag_test`, prod rag-cli runs against `rag`.

**Query Coverage:** 17 queries in `queries_test_db.json` cover the 7 reference papers. All `expected_snippets` are grep-verified against the source MDs. Query-type distribution is factual-heavy (very specific substring hits) — a possible bias of the worker-generated baseline queries toward exact match.

**Pipeline Coverage / Friction Boundary:** What the eval checks today: all retrieval knobs that need no re-indexing — modes (dense/sparse/hybrid/cc/cc+rerank/hybrid+rerank), fusion parameters (RRF K, CC α), MRL dimension via a separate script, plus rank-aware metrics (NDCG@K, MRR@K, Recall@K). What the eval does not check despite being re-index-free: BM25/keyword, reduced top_k variation (production clamp to [12,12]), statistical significance tests, latency tracking. What the eval does not check because it needs re-indexing: chunking config, dense embedding model, sparse embedding model, schema changes. Important: the eval runs on `test_db` (7 reference papers, RAG-internal methodology material), production runs on the live collections in `rag`. Eval statements must be re-validated by extending the DB — see `process-docs/eval_suite/status_2026-05-10.md` for the extension path.

---

## Salvage from `dev/server_management/DOCS.md`

**A_constellation_profile.py prerequisites:**
- All llama-server model files present (`models/Qwen3-Embedding-8B-Q8_0.gguf`, etc.)
- `rag-cli server stop` clean state (or let `ensure_constellation` handle cleanup)
- `test_db` collection indexed in `rag_test` (only if using DB-backed retrieval; not required for this script)

**Constellations profiled (8 total):**

| Name | Servers |
|---|---|
| `embedding-8b-solo` | embedding-8b |
| `embedding-0.6b-solo` | embedding-0.6b |
| `embedding-8b+splade` | embedding-8b, splade |
| `embedding-8b+reranker-0.6b` | embedding-8b, reranker-0.6b |
| `embedding-8b+reranker-0.6b+splade` | embedding-8b, reranker-0.6b, splade |
| `embedding-8b+reranker-8b` | embedding-8b, reranker-8b |
| `embedding-8b+reranker-8b+splade` | embedding-8b, reranker-8b, splade |
| `embedding-0.6b+reranker-8b` | embedding-0.6b, reranker-8b |

**VRAM measurement:** Parses `Metal buffer size = X MiB` lines from each server's llama startup log (path from `~/.rag-locks/server-port-*.json` state files). Sums across all active constellation servers. `system_profiler SPDisplaysDataType` is sampled additionally as best-effort total GPU snapshot; may not expose per-process breakdown on Apple Silicon.

**CLI flags:**

| Flag | Description |
|---|---|
| `--constellation NAME` | Profile a single named constellation |
| `--all` | Profile all 8 constellations in sequence; writes one combined report |

Per-constellation: VRAM (Metal log + system_profiler), cold query stats (N=5), warm query stats (N=50), timeout count. Final comparison table:
| Constellation | VRAM (GB) | Cold p50 (ms) | Warm p50 (ms) | Warm p95 (ms) | Timeouts/50 |

**Usage:**
```bash
./venv/bin/python dev/server_management/A_constellation_profile.py --constellation embedding-8b-solo
./venv/bin/python dev/server_management/A_constellation_profile.py --all > /tmp/profile_run.log 2>&1
tail -f /tmp/profile_run.log
```

**Implementation notes:**
- Uses `ensure_constellation()` from `src.rag.server_manager` via subprocess (dev/ convention: no src/ imports directly)
- Rerank batch: 50 synthetic documents (no DB); simulates real batch size without retrieval
- Timeouts contribute their wall-clock time to latency stats (conservative — actual server latency including queueing)
- DO NOT execute this script during a worker session — run in next session on clean state

**B_real_smell.py prerequisites:**
- All llama-server model files present
- `test_db` collection indexed in `rag_test` — queries come from `dev/retrieval/queries_test_db.json`
- Imports `p1_retriever`/`p2_embedder`/`p3_sparse_embedder` from `dev/retrieval/` and `dev/indexing/` via `sys.path` insert (dev/ convention: no src/ imports directly, except `ensure_constellation` via subprocess)

**Constellations profiled (6, `C1`-`C6`):** embedding-8b solo (dense) → +splade (hybrid/cc) → +reranker-0.6b (dense+rerank-0.6b) → +reranker-8b (dense+rerank-8b) → +splade+reranker-0.6b (cc+rerank-0.6b, hybrid+rerank-0.6b) → +splade+reranker-8b (cc+rerank-8b, hybrid+rerank-8b).

**VRAM measurement:** same Metal-log-parsing approach as `A_constellation_profile.py`.

**Output:** `md/smell_<timestamp>.md` — per-constellation VRAM + per-mode query latency table (cold query 1, warm queries 2-3, mean warm), plus a final cross-constellation summary table.

**Usage:**
```bash
./venv/bin/python -u dev/server_management/B_real_smell.py 2>&1 | tee /tmp/smell_real.log
```

**Implementation notes:**
- `HEALTH_POLL_TIMEOUT=180s`, `RERANK_TIMEOUT=300s` (reranker-8b with real chunks can be slow)
- URL globals in `p1_retriever`/`p2_embedder`/`p3_sparse_embedder` are monkey-patched per constellation to hit the dynamically-allocated ports

---

## Salvage from `src/rag/DOCS.md`

**Gotchas section**, cut in the milestone-2 rewrite (no place in Role/Public Interface/Flow/Modules/State):

- **splade_server.py has no Python import callers** — appears as dead code in any import grep but is the subprocess target launched by `server_manager.py`. Do not delete.
- **server_lock.py has no Python import callers** — verify dead code status before removing; may be planned for future concurrent-request serialization.
- **retriever.py re-exports format_results / format_collections / format_documents** from `formatting.py`. `cli.py` imports these from `src.rag.retriever`, not `src.rag.formatting`. Keep the import in retriever.py's INFRASTRUCTURE or cli.py breaks.
- **DEFAULT_QUERY_PREFIX** lives in `search_primitives.py`, not retriever.py — it moved with `embed_query()` during the retriever split refactor.
- **error_log.py** is called by server_utils.py, server_lifecycle.py, watchdog.py, and server_cli.py (previously only server_manager.py — update any grepping for callers accordingly).

---

# Comment and Docstring Salvage

One heading per source file, in triage-table order. Only files with at least one relocated
item appear below; files where everything was covered elsewhere are omitted.

## Salvage from `src/rag/server_lifecycle.py`

Comments (originally at the given line numbers):

- L124: `# Name collision check — must come before port resolution`
- L163: `# Resolve a class-name (embedding / reranker / splade) to the default variant preset name.`
- L164: `# Returns the input unchanged if not a class name; falls back to first variant in insertion order.`
- L175: `# Start all default servers (one per class); non-default variants must be started by name.`
- L176: `# Returns name → 'started'|'already_running'|'error: ...'`
- L190: `# Stop ALL servers (both default and non-default), regardless of whether they're running.`
- L191: `# Returns name → 'stopped'|'not_running'`
- L202: `# Yield (path, state) for every server-port state file that parses cleanly; skips corrupt/missing files`
- L212: `# Raise ValueError if name is a preset name or already claimed by a live arbitrary server`
- L226: `# Return the running label if port already has a healthy managed server; else clear its stale state file`
- L241: `# Return http://localhost:{port} for a running server matching name.`
- L242: `# Match strategy:`
- L243: `#   1. Exact match wins (e.g. find_server_url("embedding-8b")).`
- L244: `#   2. Class-prefix fallback for legacy callers: find_server_url("embedding")`
- L245: `#      → returns the FIRST running variant in SERVERS insertion order`
- L246: `#      (i.e. the default variant if it's running, else next).`
- L247: `# Client modules (embedder.py / reranker.py / sparse_embedder.py) call with`
- L248: `# class-name strings — the prefix path keeps them working without changes`
- L249: `# when SERVERS holds multiple variants per class.`
- L261: `# 1. Exact match`
- L265: `# 2. Class-prefix fallback: iterate variants in SERVERS insertion order,`
- L266: `#    return first one that's running.`
- L275: `# Check if a server responds; state-file-only — no state file means not running.`
- L276: `# Accepts preset name OR class name (embedding / reranker / splade).`
- L284: `# Popen the launch cmd, write the state file, then block on _wait_for_health`
- L308: `# Health-poll wait loop: polls until /health responds, rewrites state file with actual PID`
- L309: `# if it differs from proc.pid, logs success; unlinks state file on any exception.`
- L334: `# Mapping: llama-server mode → CLI flag. Modes not in this dict use llama-server's`
- L335: `# default behavior (no mode flag) — that's the text-generation case.`
- L342: `# Build llama-server cmd for a given model, port, mode, and extra flags`
- L351: `# Build uvicorn cmd for a given app and port`


---

## Salvage from `src/rag/server_utils.py`

Comments (originally at the given line numbers):

- L38: `# Insertion order matters: when client calls find_server_url("embedding") and`
- L39: `# multiple variants are running, the FIRST matching entry in iteration order`
- L40: `# wins. Keep the canonical default for each class FIRST.`
- L41: `#`
- L42: `# default=True → started by `rag-cli server start` without args + by ensure_ready`
- L43: `#                for search/index workflows. Non-default variants are visible as`
- L44: `#                presets but only start when explicitly named.`
- L112: `# Preset names — arbitrary starts may not collide with these`
- L115: `# Map llama-server mode → external class name used by find_server_url() prefix-match.`
- L116: `# Modes that match their class name (embedding, splade) need no entry here.`
- L122: `# Map class-name (embedding / reranker / splade / generator) → list of preset variant`
- L123: `# names, in default-first order. Used by find_server_url() prefix-match for backward`
- L124: `# compatibility with client calls find_server_url("embedding") etc.`
- L128: `# splade/embedding class names match their mode already; keep insertion order = default first`
- L133: `# Find the first PID listening on a port; returns None if port is free`
- L178: `# SIGTERM → wait → SIGKILL a server described by its state dict; unlinks state file.`
- L179: `# caller + reason are LIFECYCLE EVIDENCE: every kill of a managed process must leave`
- L180: `# a trail in error_log (server-name, port, pid, kill-method, who-asked, why).`
- L213: `# Return True if the process is alive (os.kill(pid, 0) succeeds)`
- L260: `# Bump state-file mtime to register activity; no-op if file was just unlinked (race: watchdog)`
- L268: `# Remove state file for a port; safe if never written or already gone.`
- L269: `# caller + reason are LIFECYCLE EVIDENCE — every state-file removal logged`
- L270: `# so any future "where did my server go?" investigation has a starting point.`


---

## Salvage from `src/rag/db.py`

Comments (originally at the given line numbers):

- L24: `# Quick probe: is Postgres accepting connections? Short timeout, no side effects.`
- L109: `# Validate that collection exists in database`
- L130: `# Query all collections with chunk counts. filter: case-insensitive substring match on name.`
- L150: `# Query all documents in a collection with chunk counts`
- L173: `# Query indexing progress per document in a collection.`
- L174: `# Returns rows of {"document", "done", "total"} where:`
- L175: `#   done  = chunks currently in the documents table for this (collection, document)`
- L176: `#   total = expected chunk count (from the per-row total_chunks column)`
- L177: `# A document with done < total is in progress; done == total is fully indexed.`
- L178: `# Documents that haven't started indexing won't appear.`
- L197: `# Fetch chunks for a contiguous range`


---

## Salvage from `src/rag/sync.py`

**module docstring** (originally lines 2-37):
```
"""Project doc indexing — manifest-driven sync with hash-based change detection.

Each project that wants its docs indexed places a `.rag-docs.json` at its root.

Single-collection format (legacy, still supported):

    {
      "collection": "Trading_internal",
      "include": [
        "process-docs/*.md",
        "concepts/*.md",
        "strategies/**/*.md",
        "CLAUDE.md"
      ]
    }

Multi-collection format:

    {
      "collections": [
        {"name": "Trading_internal", "include": ["process-docs/*.md", "CLAUDE.md"]},
        {"name": "Trading_archive",  "include": ["archive/**/*.md"]}
      ]
    }

Detection: presence of "collections" key → multi-collection. Else: single-collection.

`sync_docs_workflow(project_root)` reads the manifest, expands the globs,
hashes every matched file, diffs against the `indexed_files` table in
postgres, and performs only the necessary add/update/remove operations.
Unchanged files are skipped — no embedder calls.

Return value:
  Single-collection: flat dict with collection, added, updated, removed, unchanged, total_chunks_indexed.
  Multi-collection:  dict keyed by collection name, each value is the per-collection flat dict.
"""
```

**FunctionDef `sync_docs_workflow` docstring** (originally lines 76-84):
```
    """Sync project docs into RAG collection(s) per `.rag-docs.json` manifest.

    Single-collection manifest → returns flat result dict (backward-compatible):
        {"collection": str, "added": [...], "updated": [...],
         "removed": [...], "unchanged": [...], "total_chunks_indexed": int}

    Multi-collection manifest → returns dict keyed by collection name:
        {"col_a": {flat result dict}, "col_b": {flat result dict}, ...}
    """
```

**FunctionDef `expand_globs` docstring** (originally lines 259-264):
```
    """Return {relative_path_str: absolute_Path} for every .md file matched.

    Files matched by multiple patterns are de-duplicated via the relative-path key.
    Only `.md` files are kept. Paths whose components include any entry from
    GLOB_EXCLUDE_DIRS, or that lie under `.claude/worktrees/`, are discarded.
    """
```

Comments (originally at the given line numbers):

- L107: `# Single-collection (legacy) path`
- L136: `# Embedder + SPLADE only needed when we have new content to embed.`
- L137: `# Removed-only runs are pure DB deletes — no GPU cost.`
- L179: `# Index each queued relative path, registering its hash; returns total chunks indexed`
- L217: `# Multi-collection format`
- L233: `# Single-collection format (legacy)`
- L275: `# Compute SHA256 of file content`
- L280: `# Ensure the indexed_files tracking table exists`
- L295: `# Fetch stored hashes for a collection`
- L305: `# Upsert (collection, document) → sha256 entry`
- L317: `# Remove tracker row for a removed file`
- L327: `# Chunk + embed + store a single file. Replaces existing chunks for that document.`
- L340: `# Always clear existing chunks first (handles updated AND empty-now cases)`


---

## Salvage from `eval/scripts/validate_pass_c.py`

Comments (originally at the given line numbers):

- L16: `# Anti-lookup gate (2026-08-06 batch01 diagnosis): needs phrased as bare artifact lookups`
- L17: `# ("a researcher wants the definition of X") violate R6's case-match need level. The`
- L18: `# batch01 failure mode; Bollerslev summaries carry zero hits.`
- L26: `# Validate a Pass C theme-summary output against its Pass B themes`
- L54: `# Load and parse the input JSON, failing loudly on missing file or bad JSON`
- L65: `# Verify top-level and per-summary required keys are present`
- L82: `# Verify exactly one summary per Pass B theme, matching theme_ids`
- L105: `# Verify field+information_need+sub_concepts+answer_type together fall in the 60-90 word budget`
- L119: `# Verify sub_concepts has 3-5 entries`
- L141: `# Verify no document-structure references appear in the summary text`
- L155: `# Verify primary_concept is present and exactly matches one entry of sub_concepts`
- L179: `# Extract the leading clause of a sentence: up to the first ", and/but/or" or sentence-ending punctuation`
- L185: `# Verify information_need's first clause carries the primary_concept via stemmed token overlap.`
- L186: `# Concept-level, not verbatim (2026-08-06): requiring EVERY concept token forced verbatim`
- L187: `# primary_concept embedding (documented in the Pass C batch01 completion entry), which fed the`
- L188: `# Pass D paraphrase collapse. A majority of concept tokens in the leading clause suffices.`
- L200: `# Anti-lookup gate: reject information_need phrased as a bare artifact lookup (R6 case-match level)`


---

## Salvage from `src/rag/server_manager.py`

Comments (originally at the given line numbers):

- L29: `# Ensure server(s) for a name, class-name, or operation are running, starting if needed.`
- L30: `# Class-name calls (e.g. ensure_ready("embedding")) ensure the default variant.`
- L32: `# Direct preset name`
- L40: `# Class name → default variant`
- L43: `# If ANY variant of this class is already healthy, we're done.`
- L48: `# Otherwise start the default variant (after exclusivity stop).`
- L54: `# Operation-based lookup — only consider DEFAULT variants per class.`
- L67: `# Skip if any variant of this class is already healthy.`
- L109: `# Return names of all preset servers with a live state file and alive PID.`


---

## Salvage from `dev/rag-chunking/test_overlap_dedup.py`

Comments (originally at the given line numbers):

- L42: `# Build chunk dicts in the same shape fetch_chunk_range returns`
- L47: `# Long single-paragraph source (no blank lines) so the chunker relies on`
- L48: `# sentence/word separators, matching production markdown prose at chunk boundaries`


---

## Salvage from `dev/server_management/A_constellation_profile.py`

Comments (originally at the given line numbers):

- L39: `# All constellations to profile; order matches task spec`
- L53: `# seconds for ensure_constellation subprocess`
- L54: `# seconds to confirm health after constellation setup`
- L55: `# pause between constellations when running --all`
- L60: `# Profile one constellation end-to-end; returns result dict for report.`
- L104: `# Identify the constellation's server list and its embedding/reranker preset names`
- L112: `# Ensure the constellation is running and healthy; returns an error string, or None on success.`
- L126: `# Run cold + warm query batches and compute their latency stats.`
- L162: `# Poll /health for every server in the constellation until all respond 200 or timeout.`
- L187: `# Read state files to find URL for a named preset server.`
- L200: `# Report title, metadata, and separator`
- L212: `# Render one constellation's VRAM + cold/warm query section`
- L244: `# Render the final cross-constellation comparison table`
- L266: `# Write per-constellation sections + comparison table to output_path.`


---

## Salvage from `dev/rag-chunking/A_overlap_match_probe.py`

Comments (originally at the given line numbers):

- L66: `# Collapse whitespace runs to a single space; return normalized text + map from`
- L67: `# normalized index back to the original-text index (mapping[-1] == len(text))`


---

## Salvage from `dev/retrieval/A_mrl_sweep.py`

Comments (originally at the given line numbers):

- L68: `# Verify dense embedding server is reachable before starting`
- L80: `# Verify SPLADE server is reachable before starting`
- L92: `# Load query list from queries_rag_mcp_test.json`
- L99: `# Open psycopg2 connection to rag_test with pgvector registered`
- L112: `# Fetch all document rows with embeddings for a collection`
- L132: `# Embed all queries at full model dimension (4096d), return as numpy arrays`
- L139: `# Fetch SPLADE sparse top-CANDIDATES results for each query (dimension-independent)`
- L148: `# Truncate a vector to dim and L2-normalize`
- L157: `# Fuse dense and sparse candidate lists using Reciprocal Rank Fusion`
- L174: `# Evaluate all queries at a single MRL dimension, return dense and hybrid results`
- L216: `# Check which expected documents appear in hits`
- L225: `# Check which expected snippets appear as substrings in any hit's content`
- L238: `# Compute aggregate metrics from per-query results list`
- L264: `# Build summary table with one row per (dimension, mode) pair`
- L283: `# Build by-query-type breakdown table (type x dimension x mode)`
- L305: `# Build per-query breakdown for queries where any metric differs across dims or modes`
- L355: `# Write final MD report to md/`


---

## Salvage from `eval/scripts/validate_pass_b.py`

Comments (originally at the given line numbers):

- L22: `# Validate a Pass B theme-formation output against its Pass A blocks and source document`
- L54: `# Load and parse the input JSON, failing loudly on missing file or bad JSON`
- L65: `# Load the source markdown, failing loudly on missing file`
- L74: `# Verify top-level and per-theme/resplit/soft-member required keys are present`
- L113: `# Verify every theme span lies within [1, total_lines]`
- L126: `# Verify spans within one theme never overlap each other`
- L140: `# Verify theme spans never intersect a Pass A trash span`
- L154: `# Verify each resplit's new boundaries sit on blank lines and reconstruct the original block's range`
- L182: `# Verify every non-trash Pass A block is covered by theme spans or explicitly listed as unassigned`
- L252: `# Anti-section-echo gate: assignable blocks per theme must not collapse toward 1:1`
- L265: `# Zero-tolerance gate: no theme may be a standalone proof (theorem statement + proof = ONE theme per R7)`


---

## Salvage from `src/rag/indexer.py`

Comments (originally at the given line numbers):

- L31: `# Index from chunks.json (pre-chunked, LLM-cleaned)`
- L133: `# Load chunks from JSON file`
- L188: `# Delete all chunks for a collection`
- L197: `# Check if a document has a complete chunk set in the documents table.`
- L198: `# Complete means COUNT(*) > 0 AND COUNT(*) == MAX(total_chunks) — every`
- L199: `# expected chunk-row is present. Used by workflow.py index-dir / index-file`
- L200: `# to detect documents that were indexed before indexed_files tracking`
- L201: `# existed (adopt-on-complete pattern: register hash without re-embed).`
- L254: `# Format sparse vector for pgvector sparsevec type: '{idx1:val1,idx2:val2}/dimensions'`


---

## Salvage from `src/rag/server_cli.py`

Comments (originally at the given line numbers):

- L21: `# Handle 'workflow.py server' / 'rag-cli server' subcommand`
- L172: `# Resolve log_path via state file (Box-aware: dynamic ports in log name).`
- L251: `# Print table of all box-managed servers from state files`
- L260: `# Scan state files, build row dicts (name, mode, port, pid, model, idle, status)`
- L286: `# Compute column widths, print header and one row per server`
- L308: `# Format idle seconds as 'Xm YYs' (< 1h) or 'Xh YYm' (>= 1h)`
- L318: `# Get value of --flag from an args list; returns None if not found`


---

## Salvage from `eval/scripts/validate_pass_d.py`

Comments (originally at the given line numbers):

- L11: `# Anti-paraphrase ceiling (2026-08-06 batch01 diagnosis): batch01 natural_questions were the`
- L12: `# summary's information_need with a question mark. Under THIS script's stemmed tokenization`
- L13: `# the Bollerslev calibration spans 0.50-0.78 (16 nq+fs queries) while batch01 sits at median`
- L14: `# 0.92 with 94% above 0.80. Ceiling 0.80 admits the full calibration range and rejects the`
- L15: `# copy-through failure mode. Applied to natural_question and field_sentence; keyword_bag is`
- L16: `# exempt (it is BUILT from the summary's term pool, overlap is its design).`
- L21: `# Validate a Pass D query-authoring output against its Pass C summaries`
- L46: `# Load and parse the input JSON, failing loudly on missing file or bad JSON`
- L57: `# Verify top-level and per-query required keys are present, and format is one of the three allowed`
- L77: `# Verify each Pass C theme has exactly 3 entries covering all three formats, no unknown theme_ids`
- L115: `# Extract the leading clause of a sentence: up to the first ", and/but/or" or sentence-ending punctuation`
- L121: `# R16b: verify the query leads with the theme's primary_concept, per format`
- L125: `# already reported by check_theme_format_completeness`
- L144: `# Anti-paraphrase gate: query token-overlap with the information_need must stay under the ceiling`


---

## Salvage from `src/rag/lock.py`

Comments (originally at the given line numbers):

- L86: `# Filesystem race during cleanup (file already removed, perm change)`
- L87: `# is non-fatal — process is exiting the lock context regardless.`


---

## Salvage from `dev/server_management/constellation_measure.py`

Comments (originally at the given line numbers):

- L16: `# seconds per request before counting as timeout`
- L17: `# brief pause between warm queries (avoid burst)`
- L19: `# 50 moderately-sized test documents — realistic rerank batch without DB access.`
- L20: `# Each ~280 chars (≈70 tokens), simulating retrieved paragraph chunks.`
- L34: `# Sum all MTL0 Metal buffer sizes from llama startup logs for the given preset names.`
- L35: `# Matches all three MTL0 allocation lines (model weights + KV cache + compute scratch),`
- L36: `# which together equal the total Metal GPU allocation announced by llama_params_fit_impl.`
- L37: `# CPU buffer lines (CPU_Mapped, CPU output, CPU compute) are excluded — GPU only.`
- L62: `# Total in-use GPU memory snapshot via system_profiler; best-effort on Apple Silicon.`
- L63: `# Returns MiB or None if system_profiler doesn't expose VRAM usage on this hardware.`
- L80: `# Run n queries (embed + optional rerank); returns (latencies_ms, timeout_count).`
- L81: `# Timeouts still contribute their wall-clock time to latencies for conservative stats.`
- L123: `# Compute percentile stats from a latency list (ms).`


---

## Salvage from `eval/scripts/validate_pass_a.py`

Comments (originally at the given line numbers):

- L13: `# Granularity gates (2026-08-06 batch01 diagnosis): the heading-grep shortcut produced`
- L14: `# median block sizes of 48-56 lines and 1.5-2.1 blocks/100 lines vs. the Bollerslev`
- L15: `# calibration's median 8 and 8.5/100 (clean batch01 docs sat at 4.0-6.8/100). The gates`
- L16: `# mechanically expose heading-only segmentation; legitimately large single-argument`
- L17: `# proof blocks pass because the gate is on the MEDIAN, not the max.`
- L23: `# Validate a Pass A segmentation output against its source document`
- L44: `# Load and parse the input JSON, failing loudly on missing file or bad JSON`
- L55: `# Load the source markdown, failing loudly on missing file`
- L64: `# Verify top-level and per-item required keys are present`
- L88: `# Verify every trash entry's type is in the R4 taxonomy`
- L100: `# Verify blocks+trash spans are 1-indexed, non-overlapping, in order, and cover every source line exactly once`
- L131: `# Granularity gate: median block size and blocks-per-100-lines must sit in the calibration corridor`


---

## Salvage from `dev/indexing/p4_db.py`

Comments (originally at the given line numbers):

- L73: `# Format sparse vector for pgvector sparsevec type: '{idx1:val1,...}/dimensions'`


---

## Salvage from `dev/server_management/B_real_smell.py`

Comments (originally at the given line numbers):

- L35: `# noqa: E402 (after sys.path setup)`
- L36: `# noqa: E402 (for URL patching after constellation switch)`
- L37: `# noqa: E402`
- L43: `# seconds`
- L44: `# seconds — reranker-8b with real chunks can be slow`
- L46: `# Constellations in switch-verification order`
- L99: `# Ensure + health-poll + measure one constellation across all its modes; returns result dict for report.`


---

## Salvage from `dev/retrieval/eval_report.py`

Comments (originally at the given line numbers):

- L10: `# Format rank list as compact string like "Rank 1, 2, 5" or "-"`
- L17: `# Build config table lines for report header`
- L32: `# Render one query's result section (document match, snippet match, rank metrics)`
- L76: `# Write MD evaluation report to md/`
- L116: `# Accumulate per-query and per-type stats for the summary section`
- L162: `# Build the aggregate metrics table lines for the summary section`
- L191: `# Build the by-query-type breakdown table lines for the summary section`
- L209: `# Build summary section with aggregate metrics`
- L220: `# Write sweep comparison MD report with all swept values + baseline fixed params`


---

## Salvage from `eval/scripts/audit_leakage.py`

Comments (originally at the given line numbers):

- L15: `# Report n-gram overlap between each theme's summary and its source passages, for human leakage review`
- L32: `# Load and parse the input JSON, failing loudly on missing file or bad JSON`
- L43: `# Load the source markdown, failing loudly on missing file`
- L52: `# Concatenate the raw text of a theme's source line spans`
- L60: `# Concatenate a summary's textual fields into one string`
- L68: `# Tokenize to lowercase words, dropping stopwords`
- L73: `# Build the set of n-grams shared between passage text and summary text`
- L80: `# Build the set of n-gram strings from a token list`
- L85: `# Print the leakage-candidate report for one theme`


---

## Salvage from `cli.py`

Comments (originally at the given line numbers):

- L242: `# Assemble the read_document anchor-range header + content text`


---

## Salvage from `dev/retrieval/eval_cross_report.py`

Comments (originally at the given line numbers):

- L8: `# Render one param1×param2 matrix table (header row + separator + one row per value1)`
- L19: `# Find best cell by snippet_recall, tie-break NDCG`
- L25: `# Report title, metadata, and the "## Primary" section heading`
- L44: `# Primary snippet-recall matrix + best-cell callout line`
- L56: `# The five secondary metric matrices (NDCG, MRR, Recall@K, Doc Recall, Latency)`
- L76: `# Winner callout section`
- L95: `# Narrative notes highlighting notable jumps across the top_k dimension (only when param2 is top_k)`
- L110: `# Write cross-product sweep comparison MD: primary snippet_recall matrix + secondary metric matrices`


---

## Salvage from `dev/retrieval/eval_metrics.py`

Comments (originally at the given line numbers):

- L7: `# Check which expected documents were found and at which ranks (diagnostic)`
- L16: `# Check which expected_chunks identifying_quotes appear as substrings in any hit's content`
- L30: `# Compute NDCG@K with binary relevance (rel=1 if (hit.document, hit.chunk_index) in expected_set)`
- L31: `# DCG@k = Σ (2^rel_i - 1) / log2(i+1), IDCG = DCG of perfect ranking using total_relevant`
- L39: `# Compute MRR@K: 1/rank of first relevant hit in top K, 0 if none`
- L47: `# Compute Recall@K: expected_chunks retrieved in top K / total expected_chunks`
- L55: `# Bundle NDCG@K, MRR@K, Recall@K using expected_chunks as binary ground truth`
- L67: `# Compute average doc recall, snippet recall, rank metrics, and latency across all query results`


---

## Salvage from `dev/retrieval/eval_runner.py`

Comments (originally at the given line numbers):

- L19: `# Load query objects from JSON file`
- L35: `# Resolve queries file path: explicit --queries path or auto-derive from collection name`
- L43: `# Assert each expected_chunks identifying_quote is a substring of its chunk content in the active collection`
- L69: `# Rerank results using a cross-encoder at an explicit URL (avoids p1_retriever's hardcoded port).`
- L88: `# Dispatch the non-rerank modes to their p1_retriever call`
- L110: `# Dispatch the six rerank modes: fetch first-stage candidates, then rerank at the resolved URL`
- L133: `# dense+rerank-8b`
- L139: `# Run a single query with full config; returns (hits, latency_ms)`


---

## Salvage from `dev/retrieval/p1_retriever.py`

Comments (originally at the given line numbers):

- L58: `# Execute BM25 query against PostgreSQL full-text search index`


---

## Salvage from `dev/retrieval/A_retrieval_eval.py`

Comments (originally at the given line numbers):

- L24: `# starts servers + patches dynamic-port URLs`
- L44: `# restrict_values applies to whichever param is "mode"`
- L48: `# For non-mode sweeps, do upfront server check; for mode sweeps, constellation is managed per-iteration.`
- L57: `# results[(v1, v2)] = (avg_doc, avg_snip, avg_ndcg, avg_mrr, avg_recall_k, mean_latency_ms)`
- L88: `# starts servers + patches dynamic-port URLs`
- L113: `# Run every query for one config, building the per-query result dicts (hits, matches, rank metrics)`
- L131: `# Parse key=val override strings into a dict`


---

## Salvage from `dev/retrieval/eval_constellation.py`

Comments (originally at the given line numbers):

- L27: `# mode → required server presets (used by _ensure_constellation_for_mode)`
- L45: `# Check required servers are healthy based on modes`
- L48: `# dense embedding needed for all except sparse/bm25`
- L68: `# Ensure the correct server constellation is running for a mode (subprocess, dev convention).`
- L69: `# Idempotent: healthy servers are left alone; only missing/wrong servers are changed.`
- L84: `# Patch module-level URL globals in p2/p3/p1 to reflect dynamic ports from ~/.rag-locks state files.`
- L115: `# Read ~/.rag-locks state files to find the URL for a named preset server.`


---

## Salvage from `src/rag/chunker.py`

Comments (originally at the given line numbers):

- L33: `# Load file content`
- L72: `# Get overlap text aligned to word boundary`
- L106: `# Add metadata to chunks`


---

## Salvage from `src/rag/formatting.py`

Comments (originally at the given line numbers):

- L41: `# Format indexing-progress list for display.`
- L42: `# Input rows: {"document", "done", "total"}.`
- L43: `# done == total → fully indexed; done < total → in progress.`


---

## Salvage from `src/rag/index_cmd.py`

Comments (originally at the given line numbers):

- L122: `# Chunk + index each queued file, registering its hash; returns total chunks indexed`


---

## Salvage from `eval/scripts/filter_spans_only.py`

Comments (originally at the given line numbers):

- L24: `# Load and parse the input JSON, failing loudly on missing file or bad JSON`
- L35: `# Verify document/themes keys and every theme's id/spans are present`
- L75: `# Write the filtered JSON to the output path`


---

## Salvage from `dev/indexing/A_index_collection.py`

Comments (originally at the given line numbers):

- L22: `# full stored dimension; MRL truncation (1024d) is retrieval-time only`
- L97: `# Render the summary table + errors section`


---

## Salvage from `dev/indexing/p1_chunker.py`

Comments (originally at the given line numbers):

- L45: `# Recursively split text using hierarchical separators`
- L69: `# Get overlap text aligned to word boundary`
- L80: `# Merge small splits into chunks with overlap`


---

## Salvage from `src/rag/error_log.py`

Comments (originally at the given line numbers):

- L34: `# Return all entries from the start of today in local time`
- L46: `# Return all error entries from the JSONL file`


---

## Salvage from `src/rag/watchdog.py`

Comments (originally at the given line numbers):

- L48: `# Per-tick: purge orphans, then idle-stop any server whose log hasn't been touched > IDLE_TIMEOUT`


---

## Salvage from `dev/retrieval/A_retrieval_sandbox.py`

Comments (originally at the given line numbers):

- L39: `# Check required servers are healthy based on modes`
- L58: `# Load queries list from JSON file`
- L72: `# Run a single query through all requested modes`
- L98: `# Write MD report to md/`


---

## Salvage from `dev/chunker/A_quote_coverage.py`

Comments (originally at the given line numbers):

- L10: `# noqa: E402 — sys.path must be set first`
- L63: `# Index chunks by chunk_index for O(1) lookup`
- L66: `# Single-chunk verbatim match (across all chunks in the doc)`
- L76: `# Boundary-split match: concat adjacent pairs (chunk_i + chunk_{i+1})`


---

## Salvage from `src/rag/embedder.py`

Comments (originally at the given line numbers):

- L54: `# Truncate text to approximate max tokens`


---

## Salvage from `src/rag/server_lock.py`

**ClassDef `acquire` docstring** (originally lines 18-27):
```
    """Per-server flock context manager. Raises ServerBusyError immediately if server is busy.

    Usage:
        try:
            with server_lock.acquire("embedding"):
                response = httpx.post(...)
        except server_lock.ServerBusyError as e:
            error_log.write("embedding", "busy", str(e), caller_pid=os.getpid())
            raise
    """
```

Comments (originally at the given line numbers):

- L61: `# Raise ServerBusyError with holder PID, cmd, started_at from sibling JSON`
- L72: `# Write data atomically via tmp+rename (mirrors lock.py pattern)`


---

## Salvage from `dev/indexing/p5_indexer.py`

Comments (originally at the given line numbers):

- L81: `# Embed texts with dense and sparse in parallel`


---

## Salvage from `dev/retrieval/eval_config.py`

Comments (originally at the given line numbers):

- L27: `# Modes where score_threshold is not meaningful (score scale not comparable to cosine)`
- L32: `# Modes where query_prefix has no effect (no dense embedding step)`


---

## Salvage from `src/rag/splade_server.py`

Comments (originally at the given line numbers):

- L53: `# Encode texts into sparse vectors with indices and float values`
