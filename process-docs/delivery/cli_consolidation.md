# CLI Consolidation: workflow.py Retirement

## Problem / Kontext

Two CLIs existed in parallel:
- `cli.py` — agent-facing retrieval (`search_hybrid`, `list_collections`, `list_documents`, `read_document`); wrapped by `rag-cli`
- `workflow.py` — human-triggered pipeline (`index-dir`, `index-file`, `index-json`, `chunk`, `backfill-splade`, `delete`, `server`, `search`)

The split was leaky: `delete` and `server` existed in both; `search` was in `workflow.py` but not `cli.py`; the agent had no delete capability while the human CLI had a redundant search. As `cli.py` absorbed operational subcommands (`delete`, `update_docs`, `server`), the boundary became arbitrary — `workflow.py`'s indexing was the only meaningfully exclusive functionality.

Immediate trigger: fixing the `indexed_files` orphan bug required adding `delete_manifest_rows()` to `delete_workflow()`. The fix review exposed the full surface drift and prompted consolidation.

## Entscheidungen + Begründung

### Eine CLI: cli.py mit 10 Subcommands

`workflow.py` retired completely; `cli.py` absorbs all pipeline operations. Single entry point is discoverable and avoids split-brain where the same logical operation (`delete`, `server`) had two partially divergent implementations. The lock wrapper in `cli.py main()` already covered all subcommands — `workflow.py` re-implemented lock acquisition independently for its own commands.

### index/delete-Symmetrie

Both `index` and `delete` take `--collection X [--document D]`, with `--collection` required. `--document` without `--collection` raises `ValueError`/argparse error. The two commands are inverse operations over the same `(collection, document)` noun space — matching signature makes the pairing explicit.

`index-dir` + `index-file` collapsed into one `index` subcommand: `--document` absent → collection-wide path (all `.md` in `data/documents/<collection>/`); `--document D.md` → single-file path. Eliminates redundant directory-vs-file branching at the CLI surface; the branch lives internally. Heartbeat daemon thread spawned only in the collection-wide path (single-file is seconds; collection-wide can run minutes — `status` reports stale heartbeat at >60s).

### Kanonischer Pfad: data/documents/\<collection\>/

`index` binds to `RAG_ROOT / "data" / "documents" / collection` — no arbitrary `--input` flag. The collection name IS the directory component. Consistent with `delete` (which also operates on `data/documents/<collection>/`) and makes the collection↔directory relationship non-configurable. Files outside this tree cannot be indexed via `index`; `update_docs` handles arbitrary project paths via `.rag-docs.json`.

### Source-Removal als Default auf Delete

`--remove-source` flag dropped. Source removal is now unconditional: `delete --collection X` removes the collection directory; `delete --collection X --document D` removes `D.md` + `D.json` sidecar. The flag was a footgun — deleting chunks while leaving source on disk produced an inconsistent state where re-indexing via `index` would find the files, hash-check them, find them "new" (no manifest row), and re-index, but leaving the impression that a clean delete had happened. Unconditional removal keeps the collection-level invariant: after `delete`, neither chunks nor source nor manifest rows exist.

Per-document delete now correctly removes the `.json` chunk sidecar (`md_path.with_suffix('.json')`) — the previous `raw/` candidate was dead (no `raw/` subdirectories exist in any collection).

### Agent-facing vs. Wrapper-only Split

`server`, `progress`, `status` exposed in `cli.py` (visible in the project) but classified as wrapper-only / not agent-facing:
- `server`: GPU server lifecycle is operational. An agent calling `server start` creates uncontrolled side-effects; the human operator triggers this before sessions.
- `progress`: polling-only, designed for human observation during a running `index`. Wiring this to an agent would provoke polling loops.
- `status`: observability tool for humans diagnosing a stuck lock or unhealthy server. An agent has no action to take on the output.

`delete` and `index` are classified agent-facing: the agent directly manages its own knowledge base (index a new release, delete a stale collection before re-indexing). Both are guarded by the global lock so concurrent invocations fail fast with `rag busy`.

### Subcommands nicht migriert (entfernt)

| Entfernt | Begründung |
|---|---|
| `chunk` (standalone) | Chunking is internal to `index` (md → chunks → index). No standalone chunk-without-index use case remains. |
| `index-json` | Pre-chunked JSON path had no remaining caller after `chunk` removal. |
| `search` (dense-only) | `search_hybrid` (dense + cross-encoder reranker) is the prod retrieval path. Dense-only is strictly worse; no agent use case. |
| `backfill-splade` | SPLADE out of prod indexing path. `sparse_embedding` stays NULL for new chunks; backfill had one caller (`workflow.py`). |
| `--remove-source` flag | See above — unconditional removal is the correct invariant. |

**Dead-code closure in `indexer.py`:** removing `backfill_splade_workflow()` made `fetch_null_sparse()`, `update_sparse()`, and `from .sparse_embedder import sparse_embed_workflow` dead. All removed in the same commit. `sparse_embedder.py` module stays (subprocess target could be reused if SPLADE backfill returns), but its `Called by` in DOCS.md is now flagged `[] (DEAD CODE)`.

### Multi-Model-Varianten-Switching aus Regeln entfernt

Previous rules exposed model variant switching (`embedding-8b` vs `embedding-0.6b`) as an agent concern. Removed: retrieval is fixed on `embedder-8b` + reranker (both verified on production corpus); indexing is `8b`-only. The agent calls `search_hybrid` and gets the best available result. Variant switching is an operational decision for the human operator via `cli.py server start <preset>`.

## Outcome

| Artefakt | Änderung |
|---|---|
| `cli.py` | +10 subcommands (7 agent-facing, 3 wrapper-only); `_write_chunks_json` migrated from `workflow.py` |
| `workflow.py` | Deleted |
| `start.sh` | `workflow.py server start` → `cli.py server start` |
| `src/rag/indexer.py` | `delete_manifest_rows()` added; `backfill_splade_workflow()` + `fetch_null_sparse()` + `update_sparse()` + dead import removed; LOC 304 → 250 |
| `decisions/delivery01_mcp_tools.md` | IST updated to consolidated 10-subcommand surface |
| `src/rag/DOCS.md` | All `workflow.py` caller refs updated; `sparse_embedder.py` flagged dead |
