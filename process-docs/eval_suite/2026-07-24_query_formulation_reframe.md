# Query Formulation Reframed: Spec Is a Hypothesis, Format Is a Measured Dimension (2026-07-24)

Course correction on the query spec pinned 2026-07-23, triggered by the user's Grundsatzfrage: "have we been formulating correctly at all?" Framed as of 2026-07-24.

## The correction: "match the user" does not apply — our users are rule-driven

Classic IR must mirror an exogenous query distribution (millions of external users). Our queries are written by an LLM under rules WE set; the measured 53-query distribution (median 9 words, ~70% multi-concept keyword bags) is the artifact of the previous un-examined habit, not a law of nature. Pinning it as THE spec canonizes the status quo without ever asking whether it is good.

What stays exogenous: the NEED distribution (multi-concept, field-terminology-heavy information needs arise from the work itself). Designable: the FORM (keyword bag vs natural question vs answer-like sentence). The measurement remains valid as a need distribution; it is no longer a form prescription.

## Three-layer model of a query's path

1. **Formulation** (Claude writes the search text, under rules) — ours to design.
2. **Transformation** (the SYSTEM may rewrite/augment the text before embedding) — ours to design; currently EMPTY in prod.
3. **Matching** (Qwen3 embeds, vector compare, rerank) — frozen training; we only select (model, chunk size, top-k, reranker) via the config sweep.

Code finding (2026-07-24, grep over `src/rag/embedder.py`, `retriever.py`, `search_primitives.py`): NO instruction prefix anywhere — prod embeds the naked query although Qwen3-Embedding is instruction-aware ("{Instruction} {Query}" input format, per its §2) and was trained with task instructions. An unused, zero-latency, deterministic lever.

## LLM-in-layer-2 rejected; the HyDE idea migrates to layer 1

HyDE (Gao 2023) / Query2doc (Wang 2023) put an LLM generation in layer 2 (hypothetical answer-document embedded instead of / appended to the query). Rejected for prod: seconds of latency per search, non-determinism mid-pipeline, and the benefit is layer-1-dependent AND corpus-register-dependent — the pseudo-document must imitate the TARGET corpus register (academic math prose for reference vs process notation for docs); a generic prompt is either corpus-tuned or consistently mediocre.

Key move: in classic IR layer 2 exists because layer 1 is a human typing 3 keywords. In our stack layer 1 IS an LLM under our rules — the HyDE mechanism ("embed answer-like field prose, not a keyword list") becomes a FORMULATION RULE at zero latency. What remains in layer 2 is the non-LLM tool only: the instruction prefix (string concatenation, collection→task-string lookup table).

## Corpus-dependence resolved: the collection is a KNOWN parameter

The search command takes the collection as an argument → per-corpus tuning in layer 1 is a static branch in the rule, not fuzzy guessing. Two collection TYPES per the canonical project layout:
- **docs** — register known BY CONSTRUCTION (our own writing rules produce the corpus; both ends of the match are designable, query rule and doc-writing rule can share canonical vocabulary).
- **reference** — genre prior only (academic prose, varying math density; foreign authors — only the eval can answer).
Transfer expectation: docs-winner transfers project-wide (same generation rules everywhere); reference-winner transfers at genre level, spot-check on divergent corpora.

## Eval design consequence: format sweep on shared regions

Region-graded GT hangs on the NEED, not the phrasing → K query variants per need cost zero extra grading. Sweep grid: layer-1 formats {keyword bag (incumbent), natural question, answer-like field sentence (HyDE-derived)} × layer-2 {naked, instruction prefix} = 6 cells, all prod-viable, no LLM in the pipeline. Run per corpus (docs + reference test corpora), report per format per corpus. Winner becomes the rule; if winners diverge per corpus → collection branch in the rule; if a single rule is preferred → best worst-case across corpora, consistency as an explicit criterion. UQV100 (Bailey 2016) is the methodological anchor: same need, many formulations, measured variance (10,835 queries / 100 topics, 5,764 distinct variants).

## Literature procured + indexed this session (rag-cli-reference, query batch)

Gao2023HydeZeroShotDenseRetrieval, Wang2023Query2docQueryExpansionLlm, Su2023InstructorInstructionFinetunedEmbeddings, Asai2022TartTaskAwareRetrievalInstructions, Weller2024FollowirInstructionFollowingRetrieval, Bailey2016Uqv100QueryVariability. (BEIR + Qwen3_Embedding were already indexed and ground layer 3 / the instruction-awareness finding.)

Deferred candidate: Bendersky & Croft 2008 (key concepts in verbose queries) — the counter-hypothesis to answer-like long forms; fetch if the format sweep needs a fourth candidate. Qwen3-Embedding HuggingFace model card (vendor guidance on instruction use) — cheap, not yet fetched.

## Sources

- Code: `src/rag/embedder.py`, `src/rag/retriever.py`, `src/rag/search_primitives.py` (naked-query finding).
- Real query distribution: `monitor-cc/src/logs/dual_log/*.jsonl` (53 distinct queries, measured 2026-07-23).
- `rag-cli-reference`: the six query-batch docs above + BEIR_Zero_Shot_IR_Benchmark, Qwen3_Embedding.
