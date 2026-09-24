# Phase 4 step 2: DOCS.md format (2026-09-24)

## What changed
- New DOCS.md in `dev/error_log/`, `dev/infra/`, `dev/lock_progress/`, `dev/eval_suite/scripts/`. Their module entries moved out of `dev/DOCS.md` and `dev/eval_suite/DOCS.md` (the latter keeps Role/Flow/State and points to `scripts/DOCS.md`).
- `src/DOCS.md` rewritten into the format (src/ only holds an empty `__init__.py` plus `rag/`).
- `src/rag/DOCS.md`: all Purpose lines cut to 25 words or less, every function and constant reference removed (Flow, Reads, Writes, Called by, State). The State table rows were shortened to owner/state/reads/writes without function names.
- `dev/DOCS.md`, `dev/rag-chunking/DOCS.md`, `dev/indexing/DOCS.md`, `dev/retrieval/DOCS.md`, root `DOCS.md`: function/constant references removed.
- `scripts/docs_drift_whitelist.txt` deleted (the directory is gone with it; the tool has no whitelist mechanism any more).

## Verification
`docs-drift-check` from the worktree root: 0 Rule-Violation, 0 LOC-Drift, 1 Path-Drift (the known `queries/pass_` false positive). A script confirmed no Purpose line above 25 words in any DOCS.md.
Environment note: a worktree has no `venv/`, so `dev/chunker/DOCS.md` and `dev/rag-chunking/DOCS.md` report `./venv/bin/python` as NOT FOUND. That is a worktree artefact, not a docs defect. I verified with a temporary `venv` symlink to the main checkout's venv, then removed it.
I did not re-read every source module in full for this pass; the existing claims were kept and only shortened or de-identified. Claims were not re-verified against code.

## Salvage from src/rag/DOCS.md
Substance cut from the file that exists nowhere else (verbatim):

- retrieval_log.py Reads: "A missing file is the normal first-run case and stays silent (`FileNotFoundError` caught separately); any other read failure (corrupt, unreadable) is traced via `code="log_config_resolve_failed"`, not swallowed — an empty result is still returned so the search proceeds, at the cost of one duplicate registry entry."
- retrieval_log.py Writes: "A write that raises for any reason never propagates — reported via `error_log.write(..., code="log_write_failed")`; a config-resolution or registry-read failure is reported separately via `code="log_config_resolve_failed"`; both fall back to `stderr` only if the `error_log` write itself also fails."
- retriever.py Writes: "There is no plain-text `retriever.log`; its previous two `logging.info` lines (query truncated to 50 chars, no collection/filters/results recorded) are superseded entirely by the structured `search.jsonl` / `expand.jsonl` records."
- reranker.py: "Defines `RERANK_INSTRUCTION = None`, documenting that no reranker instruction is sent today."
- server_utils.py: "Contains the SERVERS preset dict (no `default_port` — ports are fully dynamic), all path constants, `_CLASS_MAP` ... Dependency root — no imports from other server sub-modules. `LOG_DIR` here is `~/.rag-locks/logs/` — a *different* concern from `log_setup.LOG_ROOT`: it is the subprocess-stdout redirect target for llama-server/uvicorn processes (consumed by server_lifecycle.py), not Python `logging` output. `context_size_for_preset` reads `SERVERS[preset]["extra_flags"]` — the launch command, i.e. launch *intent*; it does not verify what context size the running process actually honors (no `/props` call, by design — see retrieval_config.py)."
- server_lifecycle.py: "`status()` and `check_health()` are state-file-only — no state file means not running. Provides `find_server_state`/`find_server_url` (the latter now a thin wrapper over the former)."
- splade_server.py: "`src/rag/logs/splade_server.log` — distinct from `~/.rag-locks/logs/splade_server.log`, which is this process's own stdout, redirected by the launching `server_lifecycle.py._launch`, not written by this module." Also: served on port 8083, `MAX_ACTIVE_DIMS = 256`.
- lock.py: "`acquire` runs an auto-heartbeat daemon thread so long-running operations don't need to call `heartbeat()` explicitly." Lock scope: "`acquire` is called **only** by write commands (`index`, `update_docs`, `delete`). Read commands (`search`, `list_collections`, `list_documents`, `progress`, `expand_chunks`) are fully lock-free."
- error_log.py: "O_APPEND write is POSIX-atomic for writes under PIPE_BUF, no locking needed. Defines `ERROR_CODES` (frozenset of 6 genuine anomaly codes) to separate lifecycle noise from real failures."
- Flow, retrieval: candidate pool is 30 (`RERANK_CANDIDATES=30`).
- Flow, logging: "no module calls `logging.basicConfig` anymore."
- State table, config_registry.jsonl: "Membership checked by reading the whole file — no lock; a fresh process per CLI call rules out an in-process cache, so two concurrent searches under a new config can each append an identical duplicate line. Harmless, not prevented — the read path stays lock-free." Fingerprint fields: embedding preset/model/path/quantization/context_size/vector_dimension, query prefix, truncation limit, reranker preset/model/path/quantization/context_size/instruction, candidate count requested.
- State table, expand.jsonl: "No `config_fingerprint` — `expand_chunks_workflow` touches no model."
- State table, server-port-{N}.json fields: pid, port, model_path, model_name, mode, log_path, start_time, name.
- server_lock.py stays flagged as DEAD CODE (no importers) in its Called by line.

## Salvage from dev/retrieval/DOCS.md, dev/indexing/DOCS.md, DOCS.md
Only identifier names were cut; no substance lost. Env overrides for the servers are `EMBEDDING_URL`, `SPLADE_URL`, `RERANKER_URL`. `eval_config.py` holds `BASELINE`, `SWEEP_RANGES`, `THRESHOLD_IGNORED_MODES`, `PREFIX_NOOP_MODES`. The root lock is acquired in `cli.py:main()`.
