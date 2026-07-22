# search_hybrid → search Rename + Dead Retrieval Code Removal

## Scope (2026-07-23)

Mechanical cleanup, no behavior change to the live search path. Two parts, one commit (`d5e0757`).

**Dead code removed** (each verified zero-caller via `grep` across the repo before deletion — no alias, no deprecation shim):
- `src/rag/sparse_embedder.py` (60 LOC, whole module) — SPLADE client, unused since `backfill_splade_workflow` was removed in an earlier pass; the only other `sparse_embedder` hits in the repo were `dev/indexing/p3_sparse_embedder.py` (an unrelated, standalone dev-local copy) and a code comment in `server_lifecycle.py`.
- `search_workflow()` in `src/rag/retriever.py` — pure-dense, no-rerank workflow; `cli.py` never imported it (it imported `search_hybrid_workflow`), so it had no production caller.
- `bm25_search()` + `_bm25_query()` in `src/rag/search_primitives.py` — PostgreSQL full-text search primitives; no caller in `src/`. (`dev/retrieval/p1_retriever.py` has its own local `_bm25_query`, a distinct file — not a caller of the src/ version.)

**Rename** — `search_hybrid` → `search`, hard rename, no backward-compat alias:
- `cli.py`: subcommand name (`add_parser`, help text), `_READ_ONLY_CMDS` entry, dispatch dict key, `_cmd_search_hybrid` → `_cmd_search`, import.
- `src/rag/retriever.py`: `search_hybrid_workflow` → `search_workflow` — this name was free precisely because the dead `search_workflow()` above was deleted first.
- `DOCS.md` (root) + `src/rag/DOCS.md`: all `search_hybrid` mentions updated; DOCS.md caller/purpose text for the deleted module and functions cleaned up in the same pass (`sparse_embedder.py` module section removed, `search_primitives.py`/`retriever.py` purpose+LOC updated, stale `sparse_embedder` caller mentions removed from `server_manager.py`/`server_lifecycle.py` doc entries).
- `process-docs/` intentionally NOT touched — write-once, `search_hybrid` still appears in prior entries as the accurate name at the time they were written.

## Rationale — why "hybrid" was a misnomer

The command name `search_hybrid` predates a 2026-05-26 change (see `process-docs/retrieval/retrieval03_fusion.md`) that deleted `fusion.py` (`cc_fusion`, `rrf_fusion`) and made the workflow unconditionally dense-vector-search + cross-encoder rerank — no sparse/BM25 component, no fusion step, no `rerank` toggle. From that point on, "hybrid" no longer described the architecture: there was nothing being combined. The name survived only because renaming it wasn't in scope of the fusion-removal work.

This pass closes that gap: the prod search path is dense+rerank, and the command is now named `search` — no architectural implication of a sparse or fusion component that no longer exists. The SPLADE server preset in `server_lifecycle.py` was deliberately left untouched (kept for manual/dev use), and `splade_server.py` remains the live subprocess target for it — only the unused `sparse_embedder.py` HTTP *client* was dead.

## Verification

- `grep -n "search_hybrid" cli.py src/rag/*.py DOCS.md src/rag/DOCS.md` → zero matches.
- `py_compile` clean on `cli.py`, `src/rag/retriever.py`, `src/rag/search_primitives.py`.
- `python cli.py search --help` — argparse surface resolves correctly (query, collection, `--document`, `--exclude`).
- `python cli.py --help` — subcommand list shows `search`, not `search_hybrid`.
