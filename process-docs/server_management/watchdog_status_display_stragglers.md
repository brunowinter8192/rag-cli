# Idle Source — rag-cli Display Stragglers (2026-06-12)

The original state-file-mtime switch claimed (Cross-Project Symmetry) that the idle source was now "consistent across the watchdog stop path (RAG) and the display path (Monitor_CC)". That claim was incomplete: it covered the RAG watchdog + Monitor_CC's GPU pane but missed rag-cli's **own** two idle displays, which kept reading the log mtime — the exact `/health`-polluted source the theme set out to abandon.

## The Two Stragglers

| Site | Old source | Consumer |
|---|---|---|
| `status.py` `_log_idle_seconds(log_path)` → `_server_status()` | `log_path.stat().st_mtime` | `rag-cli status` (`last_used` field) |
| `server_cli.py` `_cli_list()` | `log_path.stat().st_mtime` | `rag-cli server status` / `server list` (IDLE column) |

Meanwhile the watchdog (`watchdog.py:_watchdog_tick`) and Monitor_CC's GPU pane (`_state_file_idle`) already keyed off the state-file mtime. So for any uvicorn-logged server (SPLADE logs its own `/health` probes), `rag-cli status` would show a perpetually-fresh idle that never grew — directly contradicting the watchdog's state-file-based stop decision. Same divergence class the theme exists to eliminate: two derivations of one value, debugging-hostile when they disagree.

## Consolidation

Both display sites moved to the state-file mtime — the single canonical idle source across all consumers:

- `status.py`: new `_state_file_idle(port)` → `time.time() - (TIMESTAMP_DIR / f"server-port-{port}.json").stat().st_mtime` (mirrors Monitor_CC's helper of the same name). `_server_status()` calls it via `info["port"]` (already carried by `box_status()`). Dead helpers `_state_log_paths()` + `_log_idle_seconds()` removed; now-unused `json` and `Path` imports removed.
- `server_cli.py`: `_cli_list()` uses `sf.stat().st_mtime` — the state-file `Path` already held by the `for sf in state_files` loop (mirrors `watchdog.py:_watchdog_tick`). The dead `log_path = Path(...)` line removed. Note: `log_path` reads in `_action_status` / `_action_tail` are for log *content* (tail), not idle — left untouched.

## Outcome

Four idle consumers now key off the same state-file mtime, never the log: watchdog stop-path, Monitor_CC GPU pane, `rag-cli status`, `rag-cli server list`. The earlier Cross-Project-Symmetry consistency claim is now actually complete.

The box/server architecture doc was corrected in the same pass: two stale "log mtime" references removed (the LOG_DIR paragraph no longer claims watchdog idle-stop keys off log mtime; the GPU-pane line now reads state-file mtime).
