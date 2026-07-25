# delete_workflow leaves indexed_files orphans (2026-06-03)

## Problem

`rag-cli delete --collection X` removes a collection's chunks from the `documents` table but leaves its `indexed_files` manifest rows behind. The manifest then claims "X indexed (hash Z)" while the embeddings are gone. The incremental sync (`_sync_one_collection` → `get_db_hashes`) compares on-disk file hashes against the stale manifest, finds them unchanged, and SKIPS re-indexing → a deleted-then-reindexed collection comes back EMPTY (0 chunks).

## Discovery

Surfaced 2026-06-03 while building gh-cli `index_releases` (per-repo RAG indexing with a clean-before-index "janitor": `rag-cli delete --collection` + `rmtree(doc_dir)` + rewrite MDs + `workflow.py index-dir`). First index of a repo works (fresh collection). The SECOND run (janitor deletes, then reindexes) reported "New chunks added: 0" and left the collection empty — the manifest survived the delete and the sync skipped every MD as "unchanged".

## Measurement (2026-06-03, prod DB `rag` @ localhost:5433)

986 / 2270 `indexed_files` rows orphaned (43%, no matching chunks in `documents`), across 13 collections:

| Collection | manifest | orphaned |
|---|---|---|
| reddit_meta_probe | 342 | 342 |
| searxng-cli-reference | 193 | 166 |
| github_releases__anthropics__claude-code | 100 | 100 |
| monitor-cc-reference | 177 | 89 |
| Monitor_reference | 88 | 88 |
| Monitor_CC-features | 43 | 43 |
| Monitor_CC-meta | 40 | 40 |
| searxng-meta | 27 | 27 |
| Trafilatura_Reference | 25 | 25 |
| RAG-meta | 20 | 20 |
| reddit-cli-posts | 51 | 19 |
| searxng-features | 19 | 19 |
| RAG-features | 8 | 8 |

Clean collections (gh-cli-docs/issues/reference, monitor-cc-docs, trading-*, rag-cli-*, reddit-cli-docs, searxng-cli-docs) have 0 orphans — never partial-deleted.

## Root Cause

`delete_workflow()` → `delete_chunks(conn, collection, document)` in `src/rag/indexer.py` only runs `DELETE FROM documents WHERE collection=...`. The `indexed_files` table (`src/rag/sync.py`: schema `collection/document/sha256/last_indexed_at`; managed by `upsert_hash` / `delete_indexed_file`) is never touched on a collection or document delete.

## Recommendation

1. **~~Function fix — IMPLEMENTED (commit e1b2b4b):~~** `delete_workflow()` in `src/rag/indexer.py` now calls `delete_manifest_rows()` (new helper) immediately after `delete_chunks()`, on the same connection. `delete_manifest_rows()` mirrors `delete_chunks()` WHERE logic exactly — collection-wide when only `--collection` given, per-document when `--document` given — but targets `indexed_files` instead of `documents`. Both tables are cleared atomically on every delete. Delete-then-reindex (e.g. the gh-cli `index_releases` janitor) now works correctly.

2. **One-time reconciliation (clear the existing 986 orphans) — DONE (2026-06-04):**
   ```sql
   DELETE FROM indexed_files i
   WHERE NOT EXISTS (
     SELECT 1 FROM documents d
     WHERE d.collection = i.collection AND d.document = i.document
   );
   ```
   Executed 2026-06-04. Result: `DELETE 986`. Final orphan count: 0. Total manifest rows after: 1385.

   Note: an empty source MD (0 chunks but a manifest row) would be a false-positive "orphan" — harmless (re-processed as 0 chunks on next sync).

## Operational cleanup executed (2026-06-04)

Performed alongside the reconciliation on prod DB `rag` @ localhost:5433:

- **`github_issues` deleted:** 3 chunks removed from `documents`, 0 manifest rows (already clean), disk dir `data/documents/github_issues/` removed (6 files).
- **`wise2627-reference` removed:** empty dir `data/documents/wise2627-reference/` deleted.
- **`github_releases__anthropics__claude-code` renamed:** disk dir renamed to `data/documents/github_releases/` (100 files), re-indexed as collection `github_releases` → 215 chunks across 100 documents.
- **Reconciliation:** `DELETE FROM indexed_files WHERE NOT EXISTS (SELECT 1 FROM documents …)` → deleted 986 orphan rows. Final orphan count: 0.
- **Survive-list intact:** all 16 surviving collections verified (gh-cli-discussions/docs/issues/reference, monitor-cc-docs/reference, rag-cli-docs/reference, reddit-cli-docs/posts/reference, searxng-cli-docs/reference, trading-docs/reference, github_releases).

## Downstream dependency

gh-cli `index_releases` (`src/github/index_releases.py`) is functionally BLOCKED on fix #1: its clean-before-index janitor calls `rag-cli delete --collection` and then re-indexes — which only works once the delete also clears the manifest. Until then, `index_releases` populates a collection on first run but empties it on every subsequent run.

## Code refs

- `delete_workflow()`, `delete_chunks()`, `delete_collection()` — `src/rag/indexer.py`
- `_sync_one_collection()`, `get_db_hashes()`, `upsert_hash()`, `delete_indexed_file()`, `indexed_files` table DDL — `src/rag/sync.py`
- Consumer that exposed it — gh-cli `index_releases_workflow` janitor
