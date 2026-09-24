# RAG — Root Modules

## Role
Project root — the CLI entry point and the server-bootstrap shell script. Touch this when changing the CLI subcommand surface or startup sequence; actual pipeline logic lives in `src/rag/`.

## Public Interface
No `__init__.py` — `cli.py` is invoked directly or via the `rag-cli` wrapper (`~/.local/bin/rag-cli`); `start.sh` is invoked directly.

## Flow
`cli.py` parses a subcommand → acquires the global lock for write commands only → dispatches into `src/rag/retriever.py`, `index_cmd.py`, `indexer.py`, `sync.py`, `server_cli.py`, or `status.py` → prints formatted output to stdout. `start.sh` starts PostgreSQL then calls `cli.py server start` for all GPU servers.

## Modules

### cli.py (314 LOC)

**Purpose:** Unified CLI entry point — retrieval subcommands for the `agent-rag-search` Skill via the `rag-cli` wrapper, plus human-triggered pipeline operations (index, delete, server, update_docs).
**Reads:** CLI args; delegates all data reads to `src/rag/` sub-modules.
**Writes:** stdout (formatted results); delegates all data writes to `src/rag/` sub-modules; `~/.rag-locks/rag.lock` (write commands only).
**Called by:** `rag-cli` wrapper (`~/.local/bin/rag-cli`); run directly for pipeline operations.
**Calls out:** `src.rag.retriever`, `src.rag.index_cmd`, `src.rag.indexer`, `src.rag.sync`, `src.rag.server_cli`, `src.rag.status`, `src.rag.lock` (intra-package, some lazy-imported); httpx.

---

### start.sh (14 LOC)

**Purpose:** Start PostgreSQL and all GPU servers via `cli.py server start`.
**Reads:** nothing (no arguments); requires GGUF model files under `models/`.
**Writes:** nothing directly — spawns PostgreSQL and GPU server processes.
**Called by:** run directly by the operator.
**Calls out:** `cli.py` (subprocess).

---

## State
`~/.rag-locks/rag.lock` / `rag.flock` — global write-command mutex, owned by `src/rag/lock.py`, acquired by `cli.py` only for `index`/`update_docs`/`delete`. Full documentation for the pipeline package lives in `src/rag/DOCS.md`; dev scripts in `dev/DOCS.md`.
