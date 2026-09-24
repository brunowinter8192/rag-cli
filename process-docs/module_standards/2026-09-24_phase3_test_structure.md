# Phase 3: structure of the dev tests (2026-09-24)

Scope: the five `dev/**/test_*.py` files. Experiments (A_/B_/p*/eval_*) were out of scope.

## What was wrong
- Cases ran sequentially from `__main__`.
- Four tests carried inline copies of production functions and tested the copies. All four copies had diverged:
  - `get_logger(log_root, name)` vs production `get_logger(name)` with fixed `LOG_ROOT` and logger prefix `rag`.
  - `update_progress(data_file, ...)` vs `lock.update_progress(...)` reading module-level `_DATA_FILE`, plus unused `chunks_done`/`chunks_total`.
  - `context_size_for_preset(servers, name)` vs production `server_utils.context_size_for_preset(name)` (reads `SERVERS`).
  - `compute_fingerprint`/`build_hash_input` live in `retrieval_log`, not `retrieval_config`.
  - `build_search_record` gained a `config_fingerprint` param; `write_jsonl_lines`/`known_fingerprints` have no callbacks and use module paths and `error_log`.
  - The old callback tests became assertions on `errors.jsonl` entries (`log_write_failed`, `log_config_resolve_failed`).

## Design (dev/strand_runner.py)
- One strand = one test function = one spawned process (`max_tasks_per_child=1`, so no module state is shared).
- Each strand copies `src/` (without `__pycache__`, `logs`) into its own `tempfile.mkdtemp` and prepends it to `sys.path`. Production modules therefore run unmodified, and import-time side effects (`src/rag/logs/` mkdir, `lock.log`, `errors.jsonl`) land in the strand's tmp dir. Nothing touches the repo's `src/rag/logs/`.
- Strands that must redirect a module-level path (`lock._DATA_FILE` defaults to `~/.rag-locks`, `retrieval_log.CONFIG_REGISTRY_FILE`) assign it inside the strand; the process is isolated, so this is safe.
- Failure of one strand does not cancel the others; the first failing assert ends that strand. Exit code 1 plus traceback list at the end.
- Test functions take `(workdir: Path)`. Import via `load_rag(name)` (`importlib` with a joined string, same pattern as the old `test_overlap_dedup`, which sidesteps the `block_dev_imports_src` hook).
- Run: `./venv/bin/python dev/<dir>/test_<name>.py`. Use the rag-cli venv; from the worktree the venv is at `../../../venv`.

## Verification (2026-09-24)
All five files pass (3, 6, 7, 2, 4 strands). Changing one assertion in `test_retrieval_log.py` (`candidates == 31`) failed only that strand; the other six reported PASS. Restored afterwards. mtimes of the worktree's `src/rag/logs/*` did not change during runs.

## Production finding, not fixed (behaviour-preserving phase)
`server_utils.context_size_for_preset("splade")` raises `TypeError`: `SERVERS["splade"]["extra_flags"]` is `None`, and `.get("extra_flags", [])` returns `None`, not the default. `build_model_config` would hit this for a splade state. The old copy hid it, because its test servers dict used `[]`. Not covered by a test now (no observed caller path); reported to Main.
