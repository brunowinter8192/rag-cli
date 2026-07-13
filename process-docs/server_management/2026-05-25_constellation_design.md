# Server Management — Constellation Design (2026-05-25)

## Pain (Discovery Path)

`--sweep-cross mode top_k` with 11 modes on test_db was meant to compare cc+rerank-8b vs cc+rerank-0.6b vs dense+rerank-{0.6b,8b}. Actual result: 6 of 11 modes ran cleanly (all no-rerank modes plus dense+rerank-0.6b at 97% snippet_recall — best clean data point), 5 of 11 modes (all rerank variants except dense+rerank-0.6b) returned 0% snippet_recall consistently.

Log analysis showed two separate failure modes that combined to produce this picture:

**Mode A — httpx timeouts in the eval client:** reranker-8b processing received 50 candidate pairs per query, server-side tasks started queuing (in the log: cancel events for task_ids 4747-4795, only ONE successful response at the end). Eval-side httpx default timeout of 300s expired, eval cancelled the connection, server cancelled the task. Cascaded across all 50 pairs of every query. Due to GPU memory pressure (see memory analysis below), per-query latencies were dramatically higher than the theoretically calculated ~10s.

**Mode B — watchdog killed servers mid-stress:** `IDLE_TIMEOUT=3600s` in `src/rag/server_utils.py:26`. Watchdog checks state-file mtime in `~/.rag-locks/server-port-{N}.json`. Mtime is only updated via `_touch_state_file(port)` — and this call happened in client modules AFTER a successful httpx response, not BEFORE the request. Failing requests didn't bump the mtime. The sweep took ~57min total, of which ~9min productive activity on reranker-0.6b (configs 26-30 dense+rerank-0.6b), then silence while the rerank-8b modes failed. Watchdog calculated reranker-0.6b idle > 60min and killed it — from mode cc+rerank-0.6b (config 36) onward the errors were "Connection refused" instead of "timed out", because the server was actually gone.

## Root Cause Analysis

### Memory Math on M4 Pro 48GB

Estimated VRAM footprints (from llama_memory_breakdown_print + model sizes):

| Server | Model Weights | KV-Cache (4 slots × 32k ctx) | Compute Buffer | Total |
|---|---|---|---|---|
| embedding-8b | 7.7 GB | 0 (2k ctx, 1 slot) | ~500 MB | ~9 GB |
| reranker-0.6b | 600 MB | ~3.6 GB | ~600 MB | ~5 GB (vs ~1 GB without KV) |
| reranker-8b | 7.7 GB | ~4.6 GB | ~2.9 GB | ~15 GB (vs ~9 GB without KV) |
| splade | ~500 MB | 0 | ~100 MB | ~600 MB |
| generator-4b | ~4 GB | ~2 GB | ~1 GB | ~7 GB |

Metal VRAM slice on M4 Pro: ~36 GB out of the 48 GB unified memory. Concurrent run of embedding-8b + reranker-8b + splade + reranker-0.6b (which actually happened intermittently during the sweep): ~9 + 15 + 0.6 + 5 = ~30 GB. Already 83% of the Metal budget, plus OS, plus Postgres, plus compute temporaries allocated additionally at runtime. Effect: memory-bus stalls, Metal context-switching between processes (Metal does not parallelize across processes, only within), catastrophic slowdown.

Per-query latency expected under this memory-pressure situation: not the ~10s the model needs in isolation, but rather 60-90s — just under the 300s timeout but with fluctuations that regularly exceed it.

### Why -np 4 was the main problem for the reranker

llama-server default is `n_parallel = 4` (no explicit `-np` flag sets -np = 4). Each parallel slot allocates its own KV-cache on the configured `-c 32768` context. A single reranker-8b server thus costs ~4.6 GB KV-cache ADDITIONALLY to the ~7.7 GB model weights. With `-np 1` the KV-cache would drop to a quarter (~1.1 GB), total VRAM footprint from 15 GB down to ~9 GB — fits the memory budget much better.

The rerank workloads in this pipeline arrive sequentially from the eval orchestrator anyway (50-pair batch per query, one query after another). Parallel slots on the reranker thus bring no throughput gain — they are pure memory waste. Setting `-np 1` is the only sensible configuration for this use case.

## Design Discussion (four options, decided direction)

### Options discussed

**A — Class-exclusivity alone.** Exactly one variant runs per class. ensure_ready("reranker-8b") stops reranker-0.6b beforehand. Does NOT address cross-class memory conflicts (embedding-8b + reranker-8b remain startable in parallel).

**B — Configurable `exclusive_with` per preset.** Each preset carries a list of other conflict-causing presets. Data-driven via the config dict, readable in a single file. ensure_ready walks the list before start and stops all conflicts automatically.

**C — Memory budget with LRU eviction.** Each preset has a `memory_gb` annotation, global budget (~30 GB), ensure_ready stops the LRU server if starting a new one would exceed budget. Smart, robust against future preset additions, more code complexity.

**D — Explicit profile mode.** User/code actively switches profiles (`rag-cli profile use rerank-8b-eval`). Maximally explicit, forces every caller to set the profile.

### Decided: B + idle-detection fix + `-np 1`

Rationale for B: the `exclusive_with` field is declarative, anyone can read in the config file which combinations are incompatible and why. Cross-class exclusivity becomes OPTIONAL — e.g. `reranker-8b.exclusive_with: ["reranker-0.6b", "embedding-8b"]` if measurements show the constellation is broken. Callers need to know nothing. Maintainable.

Rationale for the idle-detection fix (highest priority): `_touch_state_file` must happen BEFORE the httpx post, not after success. That way every incoming request counts as "server alive", even if it times out. Watchdog can no longer falsely kill during stress phases. Simple 3-file change in client modules, very large impact on robustness.

Rationale for `-np 1` on both reranker presets: no throughput loss for this sequential workload, drastically reduced memory footprint, primary single-lever win.

Options A, C, D rejected: A solves only half the problem. C is overkill for 6 static presets (no dynamic preset registration). D too invasive for the existing callers in embedder/sparse_embedder/reranker.

### Cross-class exclusivity: PENDING on measurement data

We DELIBERATELY do not enter any cross-class `exclusive_with` entries before we have empirical data. Instead, a dev measurement script is written that systematically activates every meaningful constellation and measures VRAM + latency + stability. Data will show:

- Which constellations are stable at acceptable latency
- Where cross-class exclusivity is needed (e.g. "when reranker-8b starts, stop embedding-8b automatically")
- Where per-mode swaps are worthwhile vs. parallel permanence (load time vs. latency improvement)

Only AFTER data will the `exclusive_with` lists be finalized.

## Per-Mode Swap vs Per-Query Swap (Sub-Discussion)

In theory, server swaps could happen per QUERY — before each rerank-8b call: embedding-8b out, reranker-8b in, run rerank, reranker-8b out, embedding-8b in for the next query. Totally deterministic, never more than one large model in VRAM.

Practical problem: GGUF loading for 8B models takes 5-10s. Per-query swap means 10-20s pure load latency per query, plus the actual inference. For a 17-query sweep that would be 200-400s just for swapping.

Per-mode swap is the right granularity: at the start of the sweep for "cc+rerank-8b", swap embedding-8b → reranker-8b once, then run all 85 queries of the mode phase (17 × 5 top_k) without further swaps. Switch to the next mode → one swap. Swap cost amortizes over 85 queries = negligible.

**Implication:** the eval orchestrator (or a wrapping pre-flight script) should decide before each mode which servers are needed and swap accordingly. ensure_ready with exclusive_with does this automatically when the caller requests the right server. A fixed constellation can be hardcoded per production query path (e.g. embedding-8b + splade + chosen reranker), server-manager keeps it stable.

## Measurement Plan — what the profile-script data must answer

Constellations the script in `dev/server_management/A_constellation_profile.py` will profile:

1. embedding-8b-solo
2. embedding-0.6b-solo
3. embedding-8b + splade
4. embedding-8b + reranker-0.6b
5. embedding-8b + reranker-0.6b + splade (full production default constellation)
6. embedding-8b + reranker-8b (THE question — does it even work?)
7. embedding-8b + reranker-8b + splade (full constellation with 8B reranker)
8. embedding-0.6b + reranker-8b (fallback if 8B+8B doesn't work — smaller embedding plus large rerank)

Measured per constellation:
- VRAM footprint after all server loads (state-stable after 30s warm-up)
- Cold-query latency (first 5 queries after server start — capture warmup cost)
- Warm-query latency (50 sequential queries — mean, p50, p95, p99, max)
- Stability (timeout count, latency drift over the 50 queries — does latency grow monotonically?)

Empirical decision basis to be derived from the data:
- If embedding-8b + reranker-8b has stable acceptable latency (p95 < 30s e.g.) → running reranker-8b in parallel is OK, no cross-class exclusive_with needed, eval can sweep normally
- If embedding-8b + reranker-8b is unstable / has timeouts → cross-class exclusive_with forces a swap, eval must swap per-mode
- If embedding-0.6b + reranker-8b runs cleanly → this is a viable sweep constellation for 8B-reranker comparisons
- If reranker-8b already performs poorly solo → hardware limit, reranker-8b is not practical on M4 Pro 48GB and should drop out of production options

## What This Session Does NOT Do

- Script is written but NOT executed. Empirical profiling = next fresh session.
- Eval sweep not restarted. Sweep waits on profile data for constellation choice.
- Cross-class `exclusive_with` entries not set. Only after data.
- Production code in `cli.py` / `retriever.py` not adjusted. Hardfix worker for top_k=12 / cc+rerank-mode comes LATER, after eval re-run with a clear winning config.

## Next Session — Workflow

1. Run `./venv/bin/python dev/server_management/A_constellation_profile.py --all` — produces `dev/server_management/md/profile_*.md`
2. Read report, decide:
   - Which constellations are stable → eval-ready
   - Do we need cross-class `exclusive_with` entries → add if yes
   - Should `-c` be reduced further on the rerankers (32k → 8k or 4k) for an even smaller footprint
3. Sequential eval sweeps with the chosen constellation per mode group (server swap between mode groups). Re-run the 5 failed modes on test_db. If the 8B reranker runs stably, also extend to test_db_2 + test_db_3.
4. After a clean sweep: hardcode winning (mode, top_k) in retriever.py + cli.py + tool-use.md

## Sources

- `process-docs/architecture/box_architecture.md` — server-architecture state, updated during this session by the worker
- `process-docs/eval_suite/methodology_clarification_2026-05-24.md` — eval methodology baseline (binary relevance, snippet_recall primary)
- `process-docs/eval_suite/2026-05-24_phase_a_queries_sample.md` — query schema with chunk_index + identifying_quote
- `dev/retrieval/md/cross_mode_top_k_test_db_20260525_004613.md` — original test_db sweep (7 modes, before schema extension)
- `dev/retrieval/md/cross_mode_top_k_test_db_20260525_022544.md` — the partially-failed 11-mode sweep that triggered this discussion
- Server-manager logs: `~/.rag-locks/logs/server_manager.log` (watchdog events), `~/.rag-locks/logs/llama-port-{N}.log` (per-server llama activity, incl. memory_breakdown_print on exit)
- RAG_reference collection: no direct sources for this topic (RAG-specific hardware eval, no paper covers this)
