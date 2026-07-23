# Prod-Retrieval Characterization + Query-Construction Findings (2026-07-23)

Snapshot of what was established this session by reading `src/rag/` and running live probes against the `trading-reference` and `rag-cli-docs` collections. Settled facts are separated from the still-open design at the end. All figures are as-of-2026-07-23 measurements, not standing guarantees.

## 1. The prod search path is dense + rerank — NOT hybrid, NOT threshold-gated

`retriever.py:search_workflow` (renamed from `search_hybrid_workflow` this session) does, in order:
1. `embed_query` (Qwen3 instruct prefix) → `search_vectors(RERANK_CANDIDATES=30)`: pure dense cosine, top 30 candidates, no score cutoff at this stage.
2. `rerank_workflow(query, candidates, 12)`: cross-encoder rerank → `ranked[:12]`.
3. `results = [r for r in results if r['score'] > 0]`.

No SPLADE, no BM25, no CC/RRF fusion in the prod path (the fusion machinery lives only in `dev/retrieval/`). The displayed `score` is the reranker's `relevance_score` (`reranker.py:rerank_workflow`, `round(...,6)`).

**The result count is effectively a constant 12, not relevance-driven.**
- Hard cap 12 (`ranked[:top_k]`). Candidate pool 30 (competition, not output size). Fewer than 12 only when the collection/filter holds <12 chunks.
- The `score > 0` filter is dead in practice: the reranker emits a sigmoid-like [0,1] value, never ≤0. Live probe: a pure off-domain query (`"quantum entanglement photosynthesis chlorophyll membrane spin coherence"`) against the trading papers STILL returned 12 results, scores 0.0067 → 0.00048 — all positive. A garbage query gets the same 12 slots as a perfect one; only the magnitude differs.
- There is no relevance threshold in prod. `score_threshold` exists only in `dev/retrieval/eval_config.py`, cosine-modes only.

## 2. Score behavior — good absolute indicator, poor fine-rank signal at the top

The reranker score is informative ACROSS the relevance range (0.0005 nonsense → ~1.0 on-topic), but SATURATES within the top when many chunks are strongly relevant. Evidence:
- HAR-family queries on `trading-reference`: top-8 all 0.997–1.000 (many equally-relevant chunks) → no fine discrimination in the head.
- `"connection pooling lock"` on `rag-cli-docs`: 0.985 → 0.047 across the 12 → clearly discriminative.

**Metric consequence:** nDCG must consume the GT grades, never the system score. The score can order and can gate on/off-domain, but it is not a graded relevance signal.

**Candidate product lever (open):** an off-domain query currently dumps 12 near-zero-score junk chunks into context; a `score_threshold` (e.g. drop < ~0.1) would cut the nonsense tail cleanly. Belongs as a swept parameter in the new eval — "how many to return / return nothing below X", not only "which chunks".

**Prod ≠ old dev-eval baseline:** `dev/retrieval/eval_config.py` BASELINE was `mode="cc"` (convex-combination fusion, no rerank) — it never matched the prod dense+rerank path. The new eval must target the actual prod config.

## 3. Real query distribution (proxy dual_log, 53 distinct queries)

Extracted real `search`/`search_hybrid` invocations from `monitor-cc/src/logs/dual_log/*.jsonl` (6629 invocations, 53 distinct). Word count: min 1, median 9, mean 8.7, max 14; 45% fall in 11–15 words, only 13% ≤3 words.

Dominant pattern: **dense multi-concept keyword bags**, not natural questions — e.g. `"measurement error covariance not restricted to diagonal correlated errors banding assumption"`, `"per-node lambda correction global lambda break location instability 2022-07 2020-08 trim fraction"`. Several distinct sub-needs concatenated into one query. The natural-question type (what RAGAS/ARES generate) is a ~10% minority, mostly in consumer domains.

**Two consequences:**
- Building the eval on paper-style natural questions would measure a query type that is ~10% of reality. The prior planned 30%-keyword/40%-natural mix does not match the measured ~70% dense-multi-concept reality.
- Real logged queries are need-first BY CONSTRUCTION (written from the info-need before results are seen, blind to corpus wording) → they are the anti-leakage gold standard the passage→query paper recipes structurally cannot produce.

**Decision (this session):** do NOT reuse exact prod queries (overfit / re-scoring already-served queries). Instead distill a query SPEC from the measured distribution and pin it as a production rule so eval↔prod stay identical by construction. Spec: 9–12 words, technical terminology, no question form, multi-concept, need-first. Expected answer breadth ~3–4 relevant chunks, which MAY be distributed across a document (not one contiguous block).

## 4. What the eval papers prescribe for query construction

`rag-cli-reference` (ARES, RAGAS, BEIR) converge on ONE dominant recipe: LLM-generates-query-FROM-passage + few-shot/rule prompt + hard negatives + small human validation.
- RAGAS WikiEval: one question/page under a 6-rule prompt (rule: non-trivial info; only anti-leakage guard is "no 'provided context' phrasing"); 2-annotator validation; distractors from back-link sentences.
- ARES: FLAN-T5 query+answer per passage from 5 few-shot examples; strong negatives = same-document / BM25-neighbor passages, weak = random.
- BEIR: build no new queries — reuse existing human-judged datasets.

**Key gap:** every recipe is passage→query, which injects exactly the lexical overlap prior methodology named the poison; RAGAS's guard is weak, and ARES actively FILTERS for queries that retrieve their own passage (a trap when applied to an eval gold set — it manufactures ~100% recall and deletes the failures the eval must surface). The papers give a usable prompt scaffold + negatives/distractor construction, but NOT the need-first origination — that remains our own contribution, more rigorous than the papers on the leakage axis.

## 5. Index-all vs selective indexing — decided: index-all

Considered the Reddit "never index whole documents, only excerpts, expand as mandatory follow-up" pattern (would structurally enforce `read_document`, less noise per vector). Rejected for this system: the collections grow daily, so selective indexing forces a daily "what to index / what not" maintenance decision — untenable at scale. Selective indexing is the better approach only for a frozen corpus known to stay fixed. Kept: index everything, expand on demand.

Because the production consumer is an agent that then does `read_document ±N`, retrieval's job is the ENTRY POINT, not the final answer. Graded region GT (core=2 = exact-answer chunks, context=1 = surrounding region) yields both readouts from one dataset — an "exact-answer" view (nDCG on core only) and an "entry-point" view (region-recall + expansion-coverage) — so the answer-vs-entrypoint framing need not be pre-chosen, only measured.

## 6. Expansion mechanics

Expansion is pauschal on the most-relevant chunk, NOT triggered by detected incompleteness — the whole point of `read_document` is that assumed completeness is the trap (the agent believes a chunk is complete though it never saw the neighbors). So the expansion-coverage metric's pauschal simulation is correct, not an overestimate. But expansion bridges only the LOCAL neighborhood (`±N` around one hit); for distributed relevance (multiple clusters) the retrieval must surface each cluster independently — expansion does not teleport across a document.

## 7. Live exploratory run (directional, not a baseline)

A worker authored 7 HAR-family region-queries (Corsi2009 HAR-RV, BollerslevPattonQuaedvlieg2016 HARQ, AndersenBollerslevDieboldLabys2003 RV) to spec; run live against `trading-reference`. Because the author read the passages first, this run carries mild construction leakage — directional discussion material, NOT the frozen baseline.

Findings:
- Specific-vocabulary queries → high single-paper precision (Q1/Q2/Q4/Q5: top-8 essentially all the intended paper).
- Generic-vocabulary query (Q3, `"out-of-sample RMSE MAE forecast comparison multiple horizons volatility models"`) pulled Chou2005 (CARR) at ranks 2–4 — unintended by the author but legitimately relevant. This is the BEIR "holes" problem made concrete: GT cannot be "intended paper only"; generic terms give corpus-wide relevance.
- Multi-hop is fragile. Q7 (meant to need Corsi + HARQ) returned only HARQ, because the HARQ paper restates the HAR notation → self-contained. Formulating a query as cross-document does NOT create cross-document relevance; the content structure decides. Real multi-hop needs a topic genuinely split across papers with no single-paper superset.
- Relevant chunks are distributed (e.g. Q1: ch0 + ch10–21), confirming the ~3–4-distributed answer shape and the entry-point framing.

## 8. Corpus garbage stays in — as a real-world negative

The `trading-reference` corpus contains LaTeX/OCR conversion-artifact chunks (e.g. Engle1982 chunks that are `\text{chi}\quad…` repeated). Decision: do NOT run a special cleanup pass before freezing test corpora. The garbage is real — conversion artifacts that slipped through — and a good retrieval must not surface it. Keeping it makes "does retrieval avoid the garbage?" a measurable signal; the lever is retrieval quality, not a hand-cleaned corpus.

## Still open (explicitly NOT decided this session)

- Query-authoring process: full human need-first (highest fidelity, expensive) vs a "theme-fed LLM" middle path (feed the LLM a theme/summary of the region, not the verbatim passage, to keep automation while cutting leakage). Both leave region-graded GT as the manual step.
- Metric refinements and whether `score_threshold` becomes a swept parameter and/or a prod feature.
- The idea of returning MORE than 12 (or unbounded) and gating purely via a score ceiling — requires a trustworthy score AND the ~100-query set with results+scores first.

## Sources

- Code: `src/rag/retriever.py` (`search_workflow`), `src/rag/reranker.py`, `src/rag/search_primitives.py` (`search_vectors`), `dev/retrieval/eval_config.py`.
- `rag-cli-reference`: ARES_Automated_RAG_Evaluation, RAGAS_Evaluation_Framework, BEIR_Zero_Shot_IR_Benchmark.
- Proxy logs: `monitor-cc/src/logs/dual_log/*.jsonl` (real query extraction).
- `reddit-cli-posts` (context-problem / chunking discussions).
