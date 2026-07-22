# Region-Based, Expansion-Aware Retrieval Eval (2026-07-22)

## Context

Same-session continuation of the anti-leakage query-construction redesign. As the discussion deepened, the **unit of evaluation** itself shifted — from "did retrieval return the one gold chunk" to "did retrieval surface the right REGION as a broad, graded entry point." This entry records that reframe, the construction recipes distilled from the indexed papers, the scale evidence, and community-grounded findings on the context problem. The two frozen test corpora (docs + reference) were NOT built this session — only the methodology was settled and the eval-methodology reference papers were ingested (see Open Items).

## Terminology (fixed)

- **Corpus / test-DB** — the indexed documents (the searchable haystack). Two planned: a `docs` collection (trading project's `.rag-docs.json` docs) and a `reference` collection (93 trading-reference papers).
- **Query-Set** — the list of test queries (the L2 level).
- **Ground Truth (qrels)** — per query, which chunks are relevant and at what grade.
- **Eval-Set** — Query-Set + Ground Truth together.

## The reframe: unit of relevance is the REGION, not the chunk

Production reality drives this. Real flow: hit a problem → RAG search → see candidate chunks → tell the agent to expand the chunks it leans on (`read_document ±N`) → answer sharpens, redirects, or is discarded. Often not the single chunk but the surrounding ones carry the answer — **context makes the music**. Therefore good retrieval is NOT "one query returns exactly the one answer chunk." It is: return a broad, well-graded set that surfaces the right region(s), from which cheap expansion reaches the rest. Consequences:

- **Per-chunk query construction is wrong.** A query is built from a THEME that spans a region (say ~30 chunks, of which ~10 answer the specific need), not from one chunk.
- **Trivial single-chunk-answerable queries are excluded** — they don't reflect prod, where the entry-point-then-expand pattern dominates.
- **Not "one chunk wins" but a gradation.** The eval rewards ranking core above context above irrelevant.

## Graded, multi-chunk region ground truth

Per query, annotate contiguous relevant regions (may span multiple documents) with a grade: **core = 2** (chunks answering the specific pain, ~10), **context = 1** (surrounding region, the ~20 that give perspective / are expansion targets), **rest = 0**. This is exactly the graded + multi-relevant input nDCG consumes.

## Metrics — three, not one

- **Graded nDCG@10 (primary).** BEIR's rationale (adopted): Precision/Recall are rank-unaware; MRR looks only at the first hit (worthless when 30 chunks matter); MAP is binary-only. nDCG sums graded relevance with a positional log-discount, normalized to the ideal ordering — the only common metric that is graded + multi-relevant + rank-aware simultaneously. BEIR computes nDCG@10 via the official TREC tool; our retrieval cap is top_k=12 so @10 is covered. BEIR's corpora reach Avg-relevant-docs/query of 493.5 (TREC-COVID), proving nDCG handles heavily-multi-relevant queries.
- **Region-Recall (breadth).** Did top-k enter each relevant region at least once? Measures the "broad perspective" the agent needs to decide what to expand.
- **Expansion-Coverage (prod fidelity, our own — no paper has it).** Simulate `read_document ±N` around each top-k hit; does the expanded context reach the core chunks? This is the retrieve→expand two-stage flow that IS our architecture and that no standard IR metric models. A neighbor of a core chunk retrieved in top-k is a prod success because expansion reaches the core.

## Query design

- **Theme-first**, targeting a region, non-trivial. Reduces leakage as a side effect (you look at a theme, not one chunk's wording).
- **Process, not surface.** The query originates from an abstracted information need, blind to the passage wording. Overlap that then arises is natural and wanted; overlap injected by reading-then-copying is the poison. Paraphrase-gap is therefore NOT forced zero-overlap on every query — it is one query TYPE among several, at a prod-representative rate.
- **Type labels + prod distribution.** Label each query (keyword / natural-question / paraphrase / multi-hop-cross-document) and report per type. This is the scientific payoff: it reveals whether dense+rerank wins only on paraphrase queries while BM25 would suffice on keyword ones. Rough target mix ~30% keyword, ~40% natural, ~20% paraphrase, ~10% multi-hop.
- **Drift-robust anchoring.** Human input = MD name + line range; the script resolves it to a verbatim identifying quote → chunk_index by substring, so it survives re-chunking (the lesson already embedded in the old `identifying_quote` scheme).

## How the papers actually construct an eval (three archetypes)

- **BEIR — reuse existing human-judged datasets, build no new queries.** 18 English datasets, 9 task types, deliberately mixed annotation sources (crowd-workers / experts / community feedback) to average out annotation bias. Standard `corpus / queries / qrels` format. Query counts 49–13,145 per dataset; Avg-relevant-docs/query 1.0–493.5; mostly binary, some 3/5-level graded. Negatives sometimes sampled (SCIDOCS: per query 5 relevant + 25 random uncited papers).
- **RAGAS — synthetic LLM generation + 2-annotator validation (WikiEval).** 50 Wikipedia pages on events since 2022 (so parametric memory can't shortcut → forces real retrieval), recent-edit-prioritized. ChatGPT generates one question/page under a 6-rule prompt; rule 6 is the anti-leakage guard ("do not use phrases like 'provided context' in the question"). Two annotators judge 3 dimensions (agreement ~95% faithfulness/context-relevance, ~90% answer-relevance). Distractors built deliberately (back-link sentences = related-but-less-relevant).
- **ARES — synthetic at scale + tiny human set + PPI.** FLAN-T5 XXL generates query+answer per passage from 5 few-shot in-domain examples. Strong negatives = passages from the SAME document (or BM25 top-10 similar); weak negatives = random unrelated passages. ~150+ human-labeled validation datapoints for prediction-powered inference (confidence intervals on the ranking).

**Trap (flagged):** ARES filters generated queries by "keeps only those that retrieve their source passage top-1." That is deliberate for JUDGE-TRAINING data. Applying it to an eval gold set is circular — it manufactures ~100% recall and deletes exactly the failures the eval must surface. Our gold set keeps hard queries the current config misses.

## Scale evidence

ARES's Kendall's-Tau table (correlation between true and measured RAG-system ranking vs number of labeled datapoints): at 50 labels tau ≈ 0.44 (noise), at 150 tau ≈ 0.72–0.83, at 300–400 tau ≈ 0.89–1.0. **Below ~100–150 labeled examples systems cannot be reliably distinguished.** Caveat: in ARES that count is the PPI human-validation-set size (they use LLM judges); our setup has no judges, relevance is a direct label, so each query IS a labeled datapoint. The ~100–150 floor therefore transfers by analogy, not as a hard constant. This is the quantified reason the prior 17-query set was too small — it had nothing to do with the metric, everything with sample size. **Hypothesis (unproven):** region-graded queries carry far more signal per query (nDCG over ~30 graded items vs one binary hit), so 30–50 rich queries may match the discriminative power of 100+ thin ones.

## Community grounding — the context problem is universal (Reddit, 2026-07-22)

Indexed r/Rag, r/LocalLLaMA, r/LangChain, r/LlamaIndex, r/vectordatabase into `reddit-cli-posts`. Findings:

- **Our `read_document ±N` is a named standard pattern.** u/334578theo (r/LlamaIndex): "for each chunk your retriever pulls in, grab the before and after chunk … pass everything to a reranker." That is Sentence-Window / Parent-Document (small-to-big) retrieval; we do it agent-driven at query time.
- **Consensus against both extremes.** Whole-document embedding is rejected (lossy single-vector compression, accuracy drops); fixed tiny chunks ("just 512 tokens") called "mostly wrong" for cutting structure. Community guideline ~1024–2048 tokens/chunk — where our 2000-char chunks sit.
- **Named solutions:** Parent-Document / small-to-big; Sentence-Window (= read_document); structure-aware / hierarchical chunking with section-header metadata; RAPTOR (cluster + tree-summarize, multi-level retrieval).
- **Directly supports our design:** "query complexity should determine retrieval level — broad questions stay at paragraph level, precise stuff needs sentence-level" (r/LocalLLaMA) validates per-type queries. "By chunking you might divide information that has to stay together … parent retrieval with whole sections could help" (u/k-en, r/Rag) independently restates "context makes the music." Practitioners built Lost-in-the-Middle positional-sweep benchmarks — the position effect is measured, not theoretical.

## Open thread — "never index whole documents" as a read_document enforcer

Insight worth pursuing: never indexing full documents (only meaningful excerpts / bookmarks) would ENFORCE the read_document pattern — if the agent knows RAG never holds the full context, only the entry point, it is structurally pushed to expand. Upsides: more accurate (less noise per vector), lower embedding latency (index less). Open problem: **how do you know what to index?** Selecting excerpts screams manual work — a no-go at scale, especially for process-docs and 1000+ page books. No solution yet; candidate directions (structure-aware auto-selection, hierarchical summaries à la RAPTOR) not evaluated. Thematically overlaps indexing/chunking, not only eval.

## Open Items (not executed this session)

- **Corpus freeze NOT done.** The two timestamped test collections (docs from `/Users/.../ai/trading` via `.rag-docs.json`; reference from `data/documents/trading-reference`, 93 papers) were never built. Old `data/documents/test_db` (7 papers) not deleted, its vectors not dropped. Index at richest setting first (SPLADE populated, max 8B token budget) so downstream configs can be subset without re-indexing where subsettable; chunk boundaries + embedding dimension stay re-index-only.
- **`eval/` root folder NOT created.** Decided: `eval/queries/` for Query-Set + Ground-Truth artifacts, `eval/suite/` for the harness — deliberately separate from `dev/` (which dilutes). Process reasoning stays in `process-docs/eval_suite/`; artifacts go in `eval/`.
- **Config sweep pending** (SPLADE on/off, 8B params, reranker on/off) — requires the unbiased region-graded eval-set first; only then does the sweep mean anything. Goal: confirm whether the current prod config (dense 8B + reranker-0.6b, no SPLADE) holds → baseline. Follow-up sessions: new-model research, advanced RAG tactics.
- **Tooling hooks** captured as separate issues (read_document full-read enforcement; persisted-output head/tail — undecided).

## Sources

- `rag-cli-reference`: ARES_Automated_RAG_Evaluation, RAGAS_Evaluation_Framework, BEIR_Zero_Shot_IR_Benchmark, RAG_Evaluation_Survey_2025, Lost_In_The_Middle_Long_Contexts, MTEB_Massive_Text_Embedding_Benchmark
- `reddit-cli-posts`: 25 posts indexed 2026-07-22 from r/Rag, r/LocalLLaMA, r/LangChain, r/LlamaIndex, r/vectordatabase (query "chunking long documents context retrieval")
- `trading-reference` corpus (93 papers) — chunk 88 of AdvancesInFinancialMachineLearningLopezDePrado2018 used as the worked triple-barrier query example
