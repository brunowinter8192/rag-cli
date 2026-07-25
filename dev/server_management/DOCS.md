# dev/server_management/ — Server Constellation Profile Suite

Measurement scripts for GPU server constellation performance profiling on M4 Pro.
No pipeline modules (`pN_`); analysis scripts only.

All scripts run from project root:
```bash
./venv/bin/python dev/server_management/<script>.py [args]
```

---

## A_constellation_profile.py

**Purpose:** Measure VRAM footprint, cold/warm query latency, and timeout rate for each
predefined server constellation. Produces a comparison table used to decide cross-class
`exclusive_with` values in `SERVERS` (e.g., whether `reranker-8b` must auto-stop `embedding-8b`).

**Prerequisites:**
- All llama-server model files present (`models/Qwen3-Embedding-8B-Q8_0.gguf`, etc.)
- `rag-cli server stop` clean state (or let `ensure_constellation` handle cleanup)
- `test_db` collection indexed in `rag_test` (only if using DB-backed retrieval; not required for this script — test query is fixed, rerank batch is synthetic)

**Constellations profiled (8 total):**

| Name | Servers |
|---|---|
| `embedding-8b-solo` | embedding-8b |
| `embedding-0.6b-solo` | embedding-0.6b |
| `embedding-8b+splade` | embedding-8b, splade |
| `embedding-8b+reranker-0.6b` | embedding-8b, reranker-0.6b |
| `embedding-8b+reranker-0.6b+splade` | embedding-8b, reranker-0.6b, splade |
| `embedding-8b+reranker-8b` | embedding-8b, reranker-8b |
| `embedding-8b+reranker-8b+splade` | embedding-8b, reranker-8b, splade |
| `embedding-0.6b+reranker-8b` | embedding-0.6b, reranker-8b |

**VRAM measurement:** Parses `Metal buffer size = X MiB` lines from each server's llama
startup log (path from `~/.rag-locks/server-port-*.json` state files). Sums across all
active constellation servers. `system_profiler SPDisplaysDataType` is sampled additionally
as best-effort total GPU snapshot; may not expose per-process breakdown on Apple Silicon.

**CLI flags:**

| Flag | Description |
|---|---|
| `--constellation NAME` | Profile a single named constellation |
| `--all` | Profile all 8 constellations in sequence; writes one combined report |

**Output:** `md/profile_<timestamp>.md`

Per-constellation: VRAM (Metal log + system_profiler), cold query stats (N=5),
warm query stats (N=50), timeout count. Final comparison table:

| Constellation | VRAM (GB) | Cold p50 (ms) | Warm p50 (ms) | Warm p95 (ms) | Timeouts/50 |

**Usage:**
```bash
# Single constellation
./venv/bin/python dev/server_management/A_constellation_profile.py \
    --constellation embedding-8b-solo

# All constellations (sequential, ~2-4h total depending on hardware)
./venv/bin/python dev/server_management/A_constellation_profile.py --all > /tmp/profile_run.log 2>&1
tail -f /tmp/profile_run.log
```

**Implementation notes:**
- Uses `ensure_constellation()` from `src.rag.server_manager` via subprocess (dev/ convention: no src/ imports directly)
- Rerank batch: 50 synthetic documents (no DB); simulates real batch size without retrieval
- Timeouts contribute their wall-clock time to latency stats (conservative — actual server latency including queueing)
- DO NOT execute this script during a worker session — run in next session on clean state

---

## B_real_smell.py

**Purpose:** Real-data smell test across all 6 server constellations (`C1`-`C6`) — runs the first
3 `test_db` queries per retrieval mode, measuring VRAM + cold/warm latency with actual retrieved
chunks (not synthetic docs) for realistic rerank load.

**Prerequisites:**
- All llama-server model files present
- `test_db` collection indexed in `rag_test` — queries come from `dev/retrieval/queries_test_db.json`
- Imports `p1_retriever`/`p2_embedder`/`p3_sparse_embedder` from `dev/retrieval/` and `dev/indexing/` via `sys.path` insert (dev/ convention: no src/ imports directly, except `ensure_constellation` via subprocess)

**Constellations profiled (6, `C1`-`C6`):** embedding-8b solo (dense) → +splade (hybrid/cc) →
+reranker-0.6b (dense+rerank-0.6b) → +reranker-8b (dense+rerank-8b) → +splade+reranker-0.6b
(cc+rerank-0.6b, hybrid+rerank-0.6b) → +splade+reranker-8b (cc+rerank-8b, hybrid+rerank-8b).

**VRAM measurement:** same Metal-log-parsing approach as `A_constellation_profile.py`.

**Output:** `md/smell_<timestamp>.md` — per-constellation VRAM + per-mode query latency table
(cold query 1, warm queries 2-3, mean warm), plus a final cross-constellation summary table.

**Usage:**
```bash
./venv/bin/python -u dev/server_management/B_real_smell.py 2>&1 | tee /tmp/smell_real.log
```

**Implementation notes:**
- `HEALTH_POLL_TIMEOUT=180s`, `RERANK_TIMEOUT=300s` (reranker-8b with real chunks can be slow)
- URL globals in `p1_retriever`/`p2_embedder`/`p3_sparse_embedder` are monkey-patched per constellation to hit the dynamically-allocated ports
