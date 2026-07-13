# llama.cpp rebuild — rpath relocation (2026-06-02)

## Problem

`rag-cli update_docs` and all hybrid search failed with `RuntimeError: Failed to start embedding-8b on port 8081 after 90s` (raised in `server_lifecycle.py:_wait_for_health`). NOT a timeout/model-load issue — `llama-server` died within milliseconds of launch.

## Root Cause

Project was moved `ClaudeCode/MCP/RAG/` → `ClaudeCode/cli/rag-cli/` (naming_unification) WITHOUT rebuilding llama.cpp. The `llama-server` binary AND every dylib (`libmtmd`, `libllama`, `libggml*`, `libggml-metal`) carry a single absolute baked `LC_RPATH` = `/Users/.../ClaudeCode/MCP/RAG/llama.cpp/build/bin` — the OLD path, now gone. dyld cannot resolve any `@rpath/lib*.dylib` → binary aborts on launch → `/health` never responds → `_wait_for_health` polls 90× @1s and raises.

**Evidence:**
- `~/.rag-locks/logs/llama-port-8081.log`: `dyld: Library not loaded: @rpath/libmtmd.0.dylib … tried '.../MCP/RAG/llama.cpp/build/bin/libmtmd.0.dylib' (no such file)`
- `otool -l <binary>`: single `LC_RPATH` → old `MCP/RAG` path. Same for `libmtmd.0.0.638.dylib`, `libllama.0.dylib`, `libggml-metal.0.dylib`.
- Libs physically present at NEW `cli/rag-cli/llama.cpp/build/bin/` (the rpath just doesn't point there).
- The naming_unification `execution_log.md` had already flagged this as a deferred "embedding-8b didn't start in 90s" item — this session resolved it.

## Fix (user choice: full rebuild over surgical patch)

Backed up old `build/` → `build.stale.<ts>` (since removed), then fresh configure + build from the new location:
```
cmake -S llama.cpp -B llama.cpp/build -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_SHARED_LIBS=ON -DGGML_METAL=ON -DGGML_METAL_EMBED_LIBRARY=ON \
  -DGGML_ACCELERATE=ON -DGGML_BLAS=ON -DGGML_BLAS_VENDOR=Apple
cmake --build llama.cpp/build --target llama-server -j<ncpu>
```
Original build flags recovered from the stale `CMakeCache.txt`. A plain `cmake --build` on the old build dir would NOT have fixed it — `CMakeCache.txt` carried the stale absolute `*_SOURCE_DIR`/`*_BINARY_DIR` paths, so a fresh configure was required.

**Verified:** new binary `LC_RPATH` = `cli/rag-cli/llama.cpp/build/bin`, zero `MCP/RAG` refs (`otool -l`), `--version` launches Metal cleanly. `embedding-8b` starts healthy on 8081; `update_docs` ran and indexed 6 previously-deferred OldThemes into `monitor-cc-docs`.

## Caveat / move-proofing

A rebuild re-bakes an ABSOLUTE rpath → this breaks identically on any future relocation. The move-proof alternative (NOT taken, user preferred rebuild): `install_name_tool -add_rpath @loader_path <binary + dylibs>` makes each image find its siblings relative to itself, surviving moves.

## Sources

- `src/rag/server_lifecycle.py` — `start()` (Popen + state-file), `_wait_for_health()` (90s poll → RuntimeError)
- `src/rag/server_utils.py` — `SERVERS["embedding-8b"]` (timeout 90, default_port 8081)
- `~/.rag-locks/logs/llama-port-<port>.log` — llama-server stdout/stderr (dyld error lands here)
- `decisions/OldThemes/naming_unification/execution_log.md` (rag-cli + monitor-cc) — original deferred-item note
