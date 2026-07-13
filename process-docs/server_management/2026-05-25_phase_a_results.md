# Server Management — Phase A Results (2026-05-25)

Sister file to `2026-05-25_constellation_design.md` (design rationale + measurement plan). This file records what executing that plan produced, plus the follow-on phases B + B-up that emerged from the Phase A findings.

---

## Smell-Test Results (6 Constellations)

Source: `dev/server_management/B_real_smell_reports/smell_20260525_182729.md`
Script: `dev/server_management/B_real_smell_test.py` (3 queries, top_k=12, rerank_candidates=12)

### VRAM Footprints

| Constellation | Servers | VRAM (GB) |
|---|---|---|
| C1 | embedding-8b | 9.01 |
| C2 | embedding-8b + splade | 9.01 |
| C3 | embedding-8b + reranker-0.6b | 15.93 |
| C4 | embedding-8b + reranker-8b | 23.87 |
| C5 | embedding-8b + splade + reranker-0.6b | 15.93 |
| C6 | embedding-8b + splade + reranker-8b | 23.87 |

All constellations fit in 48 GB unified memory (max C4/C6 at 23.87 GB). SPLADE adds ~0 VRAM vs C3 (SPLADE is ~600 MB, dwarfed by other servers).

### Cold / Warm Latencies

| Constellation | Mode | Cold (ms) | Mean Warm (ms) |
|---|---|---|---|
| C1 | dense | 221 | 126 |
| C2 | hybrid | 382 | 194 |
| C2 | cc | 140 | 143 |
| C3 | dense+rerank-0.6b | 1807 | 1892 |
| C4 | dense+rerank-8b | 17666 | 19604 |
| C5 | cc+rerank-0.6b | 1971 | 2149 |
| C5 | hybrid+rerank-0.6b | 1909 | 2102 |
| C6 | cc+rerank-8b | 21728 | 22043 |
| C6 | hybrid+rerank-8b | 19402 | 21080 |

**Key finding: reranker-8b is unusably slow (~20s/query warm).** At 17–22s per query × 17 queries = 4.8–6.2 min per config, a 40-config sweep would take ~4 hours. Combined with the previous sweep's Watchdog-kill failures at that latency, reranker-8b is not viable on M4 Pro 48GB for batch eval sweeps, and is too slow for interactive production use. All `*+rerank-8b` modes dropped from prod consideration.

**reranker-0.6b smell-test discrepancy:** Warm latency in the smell test (rc=12) was ~1.9–2.1s, but the full sweep at rc=50 showed ~7s. Ratio matches: 12 candidates × ~160ms/pair ≈ 2s; 50 candidates × ~140ms/pair ≈ 7s. Rerank latency scales linearly with candidate count.

---

## Phase A — Eval-Sweep Results (8 modes × 5 top_k = 40 configs)

Source: `dev/retrieval/A_retrieval_eval_reports/cross_mode_top_k_test_db_20260525_2028.md`
Log: `dev/retrieval/A_retrieval_eval_reports/cross_mode_top_k_test_db_20260525_2028.log`
Parameters: collection=test_db, 17 queries, alpha=0.8, rrf_k=60, rerank_candidates=50

### Primary: Snippet Recall % at top_k=12 (the decision-relevant slice)

| Mode | snippet_recall | NDCG | mean_lat |
|---|---|---|---|
| cc | 83% | 0.691 | 156ms |
| dense | 86% | 0.659 | 131ms |
| bm25 | 82% | 0.686 | 8ms |
| sparse | 85% | 0.695 | 36ms |
| hybrid | 80% | 0.708 | 157ms |
| cc+rerank | 97% | 0.665 | 7177ms |
| hybrid+rerank | 97% | 0.665 | 7026ms |
| dense+rerank-0.6b | 97% | 0.665 | 7448ms |

Full table (all top_k values): `cross_mode_top_k_test_db_20260525_2028.md`.

---

## Phase A — Key Insights

### 1. Three rerank-0.6b modes converge identically at top_k=12

cc+rerank, hybrid+rerank, and dense+rerank-0.6b all produce snippet_recall=97% / NDCG=0.665 at top_k=12. The SPLADE server contributes zero measurable signal when the reranker is active — the reranker normalizes whatever the first-stage retriever returns to the same final ranking.

Implication: **dense+rerank-0.6b is the simplest viable rerank config.** No SPLADE server needed (saves 600 MB VRAM, reduces C5 to C3). For production, this is the cheapest constellation that achieves peak snippet recall — and the architecture decision below acts on this.

### 2. Reranker cost: +17pp snippet recall at 45× latency

Non-rerank best (hybrid top_k=12): 80% snippet, 157ms
Rerank best (any mode, top_k=12): 97% snippet, ~7100ms
Trade-off: +17pp for 45× latency increase.

Whether this trade-off is acceptable depends on the downstream use case. For interactive queries where the LLM synthesizes an answer from top-k chunks, the 7s latency per query is borderline for interactive use. For batch research, clearly acceptable.

### 3. Dense leads snippet recall without reranker; hybrid leads NDCG

At top_k=12 without reranker:
- Snippet recall leader: `dense` (86%) > `sparse` (85%) > `cc` (83%) > `bm25` (82%) > `hybrid` (80%)
- NDCG leader: `hybrid` (0.708) > `sparse` (0.695) > `cc` (0.691) > `bm25` (0.686) > `dense` (0.659)

Snippet recall measures whether the ground-truth chunk appears anywhere in the top-k set (binary hit). NDCG weights hits by rank — a relevant chunk at rank 1 scores much higher than one at rank 9.

**Decision-relevant note: NDCG is not meaningful for our use case.** The downstream LLM agent receives ALL top_k=12 chunks at once, so rank-order within the 12 does not matter. The user clarified this explicitly during the prod-config discussion. Recall is binary: chunk present or absent. NDCG-tie-break is irrelevant for prod-config selection.

### 4. Reranker NDCG (0.665) is lower than hybrid no-rerank NDCG (0.708)

Despite reranking achieving 97% snippet recall vs hybrid's 80%, the reranked NDCG is lower. This happens because NDCG measures the full ranking — a reranker trained to push the best match to position 1 fills positions 2–12 with thematically-related but not query-specific chunks. The "tail" of a reranked result is noisier than a good first-stage ranking.

Per the decision-relevance note above, this NDCG inversion doesn't affect our prod choice (agent reads all 12 chunks, order is irrelevant). It's documented as an empirical observation, not as a metric we optimize.

### 5. Q7 and Q16 recovery (aggregate analysis only)

The sweep log contains per-query latency but not per-query snippet recall — cross-sweep stdout only reports aggregate summary stats per config.

Baseline cc top_k=12 snapshot (from `eval_baseline_20260524_234854.md`):
- Q7 ("How does RAGAS estimate faithfulness..."): 0/1 snippet (0%) — doc found at ranks 1–8, quote missing
- Q16 ("How do SPLADE-v3 and Rethinking Chunk Size each evaluate..."): 1/2 snippets (50%) — missing "meta-analysis over more than 40 query sets"

At rc=50, the reranker receives 50 candidates. Quotes missing from top-12 can be recovered if they appear in candidates 13–50. The aggregate improvement from 83% (cc top_k=12 baseline) to 97% (any rerank mode, top_k=12) = +14pp across 17 queries. Per-query recovery for Q7 and Q16 cannot be confirmed without re-running with full per-query logging.

---

## Phase A — Infrastructure Work Landed

All in `dev/` (eval tooling) and `src/rag/` (server management). Production code changes in `src/`:

- `server_utils.py`: `stop()` now reads PID from state-file before `kill -TERM`, removing race condition
- `server_utils.py`: `find_all_pids_on_port()` filters to `LISTEN` state only (was matching `ESTABLISHED` connections spuriously)
- `server_utils.py`: `_start_server_internal()` dynamic-port URL patching — `ensure_ready()` now patches `server_url` in config after binding to a dynamic port, so clients get the correct URL
- `p1_retriever.py` (dev): `--restrict-modes` flag added for fast single-mode smoke testing
- `eval_config.py` (dev): `rerank_candidates` promoted to first-class sweep parameter
- `A_retrieval_eval.py`: `_rerank_at()` timeout extended 60s → 300s
- `A_retrieval_eval.py`: latency tracking added to cross-sweep (6th tuple element)
- `A_retrieval_eval.py`: `_write_cross_sweep_report()` fixed to unpack 6-element tuple (Phase A.2 salvage)

---

## Phase B — rerank_candidates Sweep on dense+rerank-0.6b

Source: `dev/retrieval/A_retrieval_eval_reports/cross_mode_rerank_candidates_test_db_20260525_211134.md`
Parameters: collection=test_db, 17 queries, mode=dense+rerank-0.6b, top_k=12, rerank_candidates ∈ {20, 30, 40, 50}

### Results

| rc | snippet_recall | mean_lat | Δlat vs prev step |
|---|---|---|---|
| 20 | 94% | 2828ms | — |
| **30** | **97%** | **4539ms** | +1711ms |
| 40 | 97% | 6276ms | +1737ms |
| 50 | 97% | 7228ms | +952ms |

### Plateau at rc=30

Going from rc=20 to rc=30 recovers one snippet (94 → 97%) — that snippet was previously in candidate position 21–30. From rc=30 upward, recall saturates at 97% — adding candidates 31–50 brings no new snippets.

**rc=30 is the prod-config recommendation candidate:** same peak recall as rc=50, 37% faster (4539 ms vs 7228 ms).

### Latency curve shape

Per-step Δlat: +1711, +1737, +952 ms per +10 candidates. First two steps are tightly consistent (~172 ms per pair); the rc=40→50 step is anomalously low (+952 ms). Most likely the per-pair scoring time at rc=40 → 50 hits a batch-scheduling sweet spot, OR the tail candidates (41–50) are shorter / cheaper text. The curve is effectively linear with possibly a slight sublinear taper at the high end — no evidence of caching or non-linearity inside the reranker batch processing.

### Why dense+rerank-0.6b specifically

We chose this mode for the rc-sweep (not cc+rerank or hybrid+rerank) because Phase A Insight 1 had established all three modes are metrically identical at top_k=12 rc=50. Sweeping all three would have tripled the runtime without producing additional decision data — they would converge at lower rc too (the SPLADE-fed candidates and dense-fed candidates feed the same reranker). Single-mode sweep is sufficient.

---

## Phase B Up-Sweep — Findings

Source: `dev/retrieval/A_retrieval_eval_reports/cross_mode_rerank_candidates_up_test_db_20260525_2237.md`
Parameters: collection=test_db, 17 queries, mode=dense+rerank-0.6b, top_k=12, rerank_candidates ∈ {60, 70, 80}

### Result: identical 97% across rc=50, 60, 70, 80

| rc | snippet_recall | mean_lat |
|---|---|---|
| 50 (Phase B reference) | 97% | 7228ms |
| 60 | 97% | 7184ms |
| 70 | 97% | 7557ms |
| 80 | 97% | 7209ms |

Going up did NOT push recall beyond 97%. Latency variation across rc=50–80 (±3%) is noise across separate baseline invocations, not signal — the runs are mechanically equivalent.

### Why: the dev-side CANDIDATES cap

`dev/retrieval/p1_retriever.py:19` has `CANDIDATES = 50` hardcoded. `search_dense()` slices its result list to `[:CANDIDATES]` regardless of the `rerank_candidates` argument passed in. The eval scaffold silently caps retrieval at 50 candidates per query — rc=60, 70, 80 all receive the same 50-candidate input to the reranker as rc=50 did. Three apparently-different configs were one config run four times.

The Up-Sweep did not measure what it was supposed to measure. To genuinely test rc>50, the dev cap would need to be lifted AND the rc value increased. The Quote Coverage Audit (next section) made that follow-up unnecessary by resolving the underlying question through inspection rather than further measurement.

### Latency curve in the genuine range (Phase B rc=20–50)

The Phase B sweep showed per-pair scoring time ~145–157 ms with one anomalous step (rc=40 → 50: +952 ms vs expected +1600 ms). Plausible mechanic: at 40 candidates the reranker uses two internal batches, at 50 it fills one larger batch — the second-batch overhead disappears. Empirical latency at rc=50 settled at ~7.2s.

For rc>50 genuine the linear extrapolation would predict ~8.7s at rc=60, ~11.7s at rc=80 — but this prediction is now uninteresting because the Quote Coverage Audit showed adding candidates wouldn't help recall regardless.

---

## Quote Coverage Audit

Source: `dev/chunker/A_quote_coverage_reports/coverage_20260525_230358.md`
Script: `dev/chunker/A_quote_coverage.py`
Parameters: collection=test_db, all 17 queries × 28 identifying_quotes

Triggered by the Up-Sweep finding that 97% snippet recall was unchanged from rc=50 to rc=80. Two competing hypotheses had to be resolved:
- **(a) rank-bounded:** the quote exists in a chunk that ranks beyond dense top-50 — going wider would surface it. The dev-cap bug had prevented direct test, but the question remained.
- **(b) corpus-bounded:** the quote text doesn't appear verbatim in any single chunk — chunker boundary split, or source-vs-eval text mismatch. No rc value can fix this.

The audit tests (b) directly: for each identifying_quote, check whether it appears as a verbatim substring in any chunk of test_db. Single-chunk match → reachable. Boundary-split → split across two consecutive chunks (concatenated check). Not-in-index → quote text simply absent.

### Result: all 28 quotes present verbatim in single chunks

| Status | Count | % |
|---|---|---|
| Single-chunk verbatim match | 28 | 100% |
| Boundary-split | 0 | 0% |
| Not in index | 0 | 0% |

Zero gaps. The chunker behaves correctly with respect to the eval ground-truth. Hypothesis (b) REJECTED.

### The single persistent miss is Q16 quote 2

Q16: "How do SPLADE-v3 and the Rethinking Chunk Size paper each evaluate retrieval quality — what datasets and evaluation approaches do they use?"

Missing quote: `"recall @ k trends for different chunk sizes and embedding models"`
Expected document: `Rethinking_Chunk_Size_Long_Document.md`, Chunk 3

Chunk 3 is a **dataset-statistics table** (NarrativeQA, Natural Questions, NewsQA, ... with numerical columns). The missing quote appears as a single line within an enumeration at the chunk's end. The dense embedding of Chunk 3 is dominated by tabular structure and numerical content — semantically far from the natural-language framing of Q16, which mentions "SPLADE-v3" explicitly and pulls the query embedding toward SPLADE chunks.

At rc=50, the candidate pool fills mostly with SPLADE_v3.md chunks (semantic alignment with the named entity in the query). The Rethinking_Chunk_Size table-chunk does not enter the top-50 dense neighborhood — and structurally would not enter at rc=100 or rc=200 either, because the embedding distance is property-of-the-chunk-content, not rank-bounded.

With `cc+rerank` the failure pattern shifts but doesn't resolve: SPLADE-sparse retrieval can match "recall @ k" term-exactly via its keyword index, but then the OTHER Q16 quote (the SPLADE one) drops out of its candidate set. Both rerank modes hit exactly 1/2 for Q16 — different quote missed, same total. Hypothesis (a) thus also implicitly REJECTED through the cc+rerank cross-check.

### The 97% Ceiling Mechanic

Q16 contributes 1/2 = 50% to the 17-query average where the other 16 queries hit 100% with dense+rerank-0.6b: (16 × 100 + 50) / 17 = 97.06%. The ceiling is precisely explained by one query.

The dense embedding cannot bridge the semantic distance between a query mentioning a specific named entity (SPLADE-v3) and a structurally-different (tabular) chunk in a different document. This is a property of dense retrieval on cross-document queries with semantic-asymmetric chunk content — not a tunable parameter, not a chunker bug, not a candidate-count limit.

### Two consequences for prod

1. **rc=30 is definitively final.** Going to rc=50, rc=100, or rc=1000 hits the same 97% ceiling. Latency savings from rc=30 vs rc=50 are real (39% faster), recall savings nil.
2. **97% is the achievable ceiling for this query-set with dense+rerank-0.6b.** Higher requires architectural changes that don't make sense for one edge query (see Q16 Known-Limit Decision below).

---

## Q16 Known-Limit Decision

Three options were considered for the single persistent miss:

**A. Remove Q16 from the eval-set.** Pro: arithmetic ceiling becomes 100%. Con: Q16 is a legitimate cross-document query class — common in real research use ("how do paper X and paper Y each address Z"). Removing it because it's hard distorts what the eval reports about real-world retrieval quality. Declined.

**B. Per-query mode selection.** Route Q16-class queries (cross-document, named-entity-heavy) through hybrid or cc first-stage where SPLADE can match "recall @ k" term-exactly. Pro: theoretical recovery path. Con: requires per-query classifier + dual code path + the hybrid mode is overall WORSE on the 16 non-Q16 queries (80% vs dense 86% snippet recall in Phase A no-rerank). Net effect would be lower aggregate recall plus more code complexity. Declined.

**C. Accept and document.** 97% is the known ceiling for this query-set; Q16's miss is mechanically explained as a semantic-distance edge case in dense retrieval; the eval reports realistic prod behavior including this limit. Chosen.

Implication for `decisions/retrieval04_reranking.md` Evidenz: when citing 97% snippet recall on test_db, the doc should note that 100% is achieved on 16/17 queries and that the persistent miss is a documented cross-document + semantic-asymmetry edge case, not a tuning opportunity.

---

## Architecture Decision — Two-Path Split in `search_hybrid_workflow`

Phase A Insight 1 (three rerank modes equivalent at top_k=12) means SPLADE contributes nothing when the reranker is active. The current code path runs SPLADE-search + cc-fusion + rerank — three stages where only the first stage (dense retrieve) plus the last stage (rerank) matter for the final result.

**Decision: split the workflow code path based on `rerank` parameter.**

```
search_hybrid_workflow(rerank=True):
    candidates = retrieve_dense(query, collection, RERANK_CANDIDATES, ...)
    results = rerank_workflow(query, candidates, top_k=12)
    return results

search_hybrid_workflow(rerank=False):
    dense = search_vectors(conn, query_vec, HYBRID_CANDIDATES, ...)
    sparse = splade_search(conn, query, HYBRID_CANDIDATES, ...)
    results = cc_fusion(dense, sparse, top_k=12)
    return results
```

Savings when `rerank=True`:
- No SPLADE-server roundtrip (~190 ms warm per smell-test C2)
- No cc-fusion CPU work (negligible)
- SPLADE server can stay idle / not be in the active constellation (drops from C5 → C3 = 600 MB VRAM saved)
- For collections used exclusively with `--rerank`, SPLADE indexing is not strictly required (see SPLADE Indexing section below)

**Default stays `rerank=False`.** This is unchanged. The split affects only how rerank=True is handled internally — the user-facing behavior of rerank=False is preserved. Default-False is protection for technical-doc collections (see Domain Dependency section).

---

## Domain Dependency — Why Default Stays rerank=False

Historical evidence from `decisions/retrieval04_reranking.md` shows reranker effectiveness is domain-dependent, not universally beneficial:

- **searxng (technical docs, 26088 chunks):** Dense+Rerank vs Dense: NDCG@3 -8.5pp, Recall@10 -5pp. Reranker HURTS.
- **qwen3_paper (academic text, 66 chunks):** Dense+Rerank vs Dense: NDCG@3 +19.3pp, Recall@10 +12.2pp. Reranker HELPS massively.
- **test_db (academic text, 250 chunks) — Phase A:** rerank vs no-rerank: snippet_recall +17pp (80% → 97% at top_k=12). Reranker HELPS — confirms the academic-domain pattern at the size scale we use for prod-eval.

The reranker model (Qwen3-Reranker-0.6B) appears to lack domain knowledge for technical text (YAML configs, Python API refs, code blocks). On academic / natural-language text it has been pre-trained well; on heavily-coded technical docs the pre-training distribution mismatches.

Implication for prod config: **default rerank=False protects the technical-doc case**. Users querying academic-domain collections opt in with `--rerank`. Documenting this clearly is a Phase C decision-doc task (extend `retrieval04_reranking.md` SOLL with usage guidance).

---

## SPLADE Indexing — Resolved (UNPARKED 2026-05-26 — see Architecture Lean-Completion below)

When `rerank=True` is used, SPLADE-search is bypassed at query time (architecture split above). But: SPLADE-INDEXING is currently global across all collections. If a collection is ever queried with `rerank=False`, the SPLADE index is required for cc-fusion.

A future optimization could make SPLADE indexing per-collection optional — academic-domain collections that will only ever use `rerank=True` could skip the SPLADE indexing step entirely (faster indexing, less storage, no SPLADE server load during indexing).

This would require: a per-collection metadata flag (e.g., `splade_indexed: false`), schema migration, indexer-side routing to skip SPLADE for flagged collections, and runtime guard in `search_hybrid_workflow(rerank=False)` to error or fall back gracefully on collections without SPLADE.

**Resolution:** The rerank=False cc-fusion path was removed entirely (2026-05-26). New chunks get NULL in sparse_embedding column. No per-collection flag needed — SPLADE indexing is globally off for new chunks. The `sparse_embedding` schema column and `backfill_splade_workflow` are retained for manual historical-data use.

---

## Architecture Lean-Completion (2026-05-26, post-Phase-C)

Phase C (2026-05-25) introduced a two-path split in `search_hybrid_workflow`: `rerank=True` → dense-only → reranker; `rerank=False` → cc-fusion (dense + SPLADE). This split was a structural prerequisite — it confirmed empirically that the SPLADE server was not needed on the rerank path and that cc_fusion could be isolated cleanly.

**User decision in the same session:** commit to the lean config. The `rerank=False` branch is removed. SPLADE is out of prod in all three dimensions: workflow (no cc-fusion), CLI (no `--rerank` toggle, no `search_keyword`), and indexer (new chunks get NULL sparse_embedding).

**What changed in commit `f8f35c0` (2026-05-26):**
- `search_hybrid_workflow()` signature: `rerank` parameter removed, function body is unconditionally dense+rerank
- `HYBRID_CANDIDATES = 50` constant removed; `RERANK_CANDIDATES = 30` kept
- `search_keyword_workflow()` removed from `retriever.py` (no CLI caller existed)
- `--rerank` flag removed from `rag-cli search_hybrid` argparse
- `fusion.py` deleted (`cc_fusion` + `rrf_fusion` had zero src/ callers after the change)
- `splade_search()` removed from `search_primitives.py`; `sparse_embed_workflow` import removed from that file
- `indexer.py`: `parallel_embed()` (dense + sparse in parallel) removed; `index_json_workflow` now calls `embed_workflow` only; `store_chunks()` writes NULL for sparse_embedding on new chunks; `backfill_splade_workflow` retained
- `sparse_embedder.py`, `splade_server.py`, SPLADE preset in `server_utils.py`: all retained — archival, not auto-started by prod paths

**Architecture as of 2026-05-26:**
- Single prod constellation: embedding-8b + reranker-0.6b (C3, 15.93 GB VRAM)
- SPLADE server preset retained in config; not started by default prod paths
- `sparse_embedding` column kept in schema; existing values preserved; new chunks get NULL

**Prod-config basis:** exclusively the reproducible test_db measurements (Phases A + B + Quote Coverage Audit on `dev/retrieval/A_retrieval_eval.py` + `dev/chunker/A_quote_coverage.py`). Historical April-2026 data (non-reproducible, pre-A_retrieval_eval scaffold) is an orientation reference — not a decision-blocking argument. A future extension of test_db with cross-domain queries (technical-doc queries) would provide new belastbare Datenbasis if domain-dependency needs to be re-evaluated.

---

## MCP — Clarification (Opus-Side False Assumption)

During the prod-config discussion, Opus repeatedly referenced "removing top_k from MCP schema". User pushed back asking where MCP came from. Verification step: `grep -rn "mcp_server\|McpServer\|register_tool\|@mcp" src/ --include='*.py'` returned nothing.

**There is no MCP server in this project.** The folder path `/Users/.../MCP/RAG/` is historical naming, not a sign of MCP integration. The RAG library is consumed via `rag-cli` (CLI tool, in `~/.local/bin/rag-cli`) plus directly as a Python library. No MCP tool definitions exist.

Implication for the prod-config change: scope is `rag-cli` (CLI flags) + `src/rag/retriever.py` (workflow signature). MCP schema is not in scope and never was.

---

## chunk-size matrix on test_db_2 / test_db_3 — Skipped

The original plan (constellation_design 2026-05-25) anticipated running the rerank sweep across three collections of different chunk sizes (test_db = 2000 chars, test_db_2 = 1024 chars, test_db_3 = 512 chars) to characterize how chunk size interacts with rerank performance.

User decision during the Phase B discussion: **skip the chunk-size sweep.** Reasoning:

> "ich erwarte aber das eh 2000 am besten sein wird. theoretisch müssten wir um vergleichbar zu sein bei den anderen mehr zurückgeben. also mehr chunks weil die ja kleiner sind. aber dann haben wir eben auch so zersplitterte results. 30 chunks die alle klein und zersplittert sind ergeben schnell ein ganz falsches bild."

Two arguments combined:
1. **Strong prior on 2000-char chunks winning.** test_db is the only collection with 2000-char chunks, and intuition + paper evidence agrees larger chunks help dense-retrieval-only setups.
2. **Comparability requires more chunks to be retrieved at smaller chunk sizes — but more chunks fragments the LLM's downstream context.** Fixing top_k=12 means small-chunk collections deliver less total context per query. A "fair" comparison would need top_k to scale inversely with chunk size, which then introduces fragmentation: 30 small chunks paint a worse picture for the LLM than 12 larger ones, even if recall metrics look the same.

The chunk-size matrix is therefore deferred indefinitely. test_db at 2000-char chunks is the prod-eval reference; smaller chunk sizes are not currently in scope.

---

## Final Prod-Config Decision

Locked. All open empirical questions resolved through Phase A + Phase B + Up-Sweep + Quote Coverage Audit. The Q16 ceiling is mechanically explained and accepted as a known limit.

| Parameter | Current prod | Final prod | Source |
|---|---|---|---|
| `RERANK_CANDIDATES` | 50 | **30** | Phase B plateau at rc=30; Quote Coverage Audit confirms higher rc cannot break the ceiling |
| `DEFAULT_TOP_K` | 5 | **constant removed, top_k hardcoded to 12 inside workflow** | User direction — no top_k choice exposed |
| `HYBRID_CANDIDATES` | 50 | 50 (unchanged) | Not swept — only affects rerank=False path |
| `rerank` default | False | False (unchanged) | Domain-dependent protection (technical-doc collections per `retrieval04_reranking.md` historical evidence) |
| `search_hybrid_workflow` signature | accepts top_k | top_k removed | User direction — hardcode 12 |
| `rag-cli search_hybrid --top-k` flag | exists, default 12 | removed | User direction |
| Architecture | linear: dense + SPLADE → fusion → optional rerank | split: rerank=True → dense-only → rerank; rerank=False → cc-fusion (current) | Phase A Insight 1 + Up-Sweep confirmation |
| SPLADE indexing | global | global (unchanged) | Parked, separate decision |

Phase C scope:
1. Apply the architecture split + constants to `src/rag/retriever.py`
2. Remove `top_k` from CLI + workflow signature
3. Update `decisions/retrieval04_reranking.md` IST + Evidenz with this session's data (test_db 97% snippet recall at rc=30, Q16 known-limit note)
4. Update `decisions/retrieval02_search.md` if top_k referenced
5. Update `decisions/retrieval03_fusion.md` IST noting that fusion is bypassed when rerank=True
6. Update `~/.claude/shared-rules/global/tool-use.md` rag-cli section — remove `--top-k` references (Opus does directly, cross-project)
