# RAG — Root Modules

## Documentation Tree

- [src/rag/DOCS.md](src/rag/DOCS.md) — RAG pipeline modules (retrieval, indexing, embedding, server lifecycle)
- [dev/DOCS.md](dev/DOCS.md) — Development & evaluation scripts

---

## cli.py

**Purpose:** Unified CLI entry point — retrieval subcommands consumed by the `agent-rag-search` Skill via the `rag-cli` wrapper (`~/.local/bin/rag-cli` in PATH), plus human-triggered pipeline operations (index, delete, server, update_docs).
**Input:** Subcommand + positional args (query, collection, filters, options).
**Output:** Stdout — formatted search results, document content, progress messages, or deletion counts.

| Subcommand | Description |
|---|---|
| `search_hybrid` | Dense retrieval + cross-encoder reranking; top_k=12 fixed (always-rerank, no toggle) |
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

**Lock model:** The global advisory flock (`~/.rag-locks/rag.lock`, `src/rag/lock.py:acquire`) is acquired only by **write commands**: `index`, `update_docs`, `delete`. All read commands (`search_hybrid`, `list_collections`, `list_documents`, `progress`, `read_document`) and lifecycle commands (`status`, `server`) are **lock-exempt** — they run concurrently with each other and with a running write. Safety: Postgres MVCC means readers see consistent committed snapshots; GPU servers serialise concurrent inference internally. Commands that hold the lock write a `kind` field: `kind="index"` for `{"index", "update_docs"}` (embedding ops), `kind="query"` for `delete`. External consumers (e.g. Monitor_CC menubar) gate on `kind` to detect active indexing without parsing command names.

**Usage (via `rag-cli` wrapper — retrieval):**
```bash
rag-cli list_collections
rag-cli list_documents my_collection
rag-cli search_hybrid "transformer attention" my_collection
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

---

## start.sh

**Purpose:** Start PostgreSQL and all GPU servers via `cli.py server start`.
**Input:** None (no arguments). Requires GGUF model files under `models/`.
**Output:** Running PostgreSQL + all GPU servers (embedding port 8081, reranker 8082, SPLADE 8083).

**Usage:**
```bash
./start.sh
```
