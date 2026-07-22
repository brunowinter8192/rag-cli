# Retrieval-Eval Methodology — Anti-Leakage Redesign (2026-07-22)

## Context

As of 2026-07-22: building two new frozen, timestamped test corpora to replace the small 7-paper `test_db` — one **docs** collection (from the trading project's `.rag-docs.json` docs) and one **reference** collection (from the 93 trading-reference papers), mirroring the two production RAG usage types. Both source collections are moving targets, so each frozen test collection is a dated snapshot. Before authoring a single query, the query-construction methodology is redesigned to remove a bias baked into the prior (~2026-05) approach. The eval is **retrieval-only** (Qwen3-Embedding-8B dense + reranker, no generation, no SPLADE in the prod path).

## The flaw in "relevance-by-construction"

Prior approach: a worker read each source MD and formulated queries from the text just read; this was framed as a feature ("relevance by construction — an input datum, not an estimation problem; no LLM-judge needed"). It conflates two separable things:

- **Legitimate:** knowing which chunk is the gold label. That is a valid, cheap ground-truth datum.
- **Poison:** authoring the query while looking at the passage wording. The query vocabulary then overlaps the passage → the eval measures lexical overlap the author injected, not semantic retrieval. A pure-lexical BM25 aces such queries; the 8B dense embedding's actual strength — bridging synonyms/paraphrase — is never exercised. This is precisely why the prior eval "ignored semantic search."

The gold-label half is kept; the query-authored-from-the-passage half is discarded.

## Three-level model (the concrete failure mode)

- **L1** natural information need — "what colour is the large property by the church in the town centre"
- **L2** the RAG query derived from it — "property colour near church"
- **L3** the corpus fact — "the villa is yellow; the house beside it is brown; …"

Bias enters when **L2 is written from L3 instead of from L1**. Reading L3 first ("the villa is yellow") steers the author to phrase L2 with the passage's own tokens ("villa", "yellow"), guaranteeing a lexical hit. Correct order: **L1 → L2**, then verify an L3 gold chunk exists — never L3 → L2.

## Anti-leakage protocol (grounded in the indexed papers)

- **Cranfield separation** — information need and relevance judgment are two separate steps. BEIR operationalises this as the `corpus / queries / qrels` triple: queries live independently of the passages, relevance is a separate judgment layer.
- **RAGAS precedent (WikiEval construction):** questions were LLM-generated with an explicit anti-leakage instruction — *"Do not use phrases like 'provided context' in the question"* — then judged by **two** annotators (agreement ~95% faithfulness/context-relevance, ~90% answer-relevance; disagreements resolved by discussion). Confirms: generate the need first, judge relevance second, and suppress passage-echoing phrasing.
- **Paraphrase-gap discipline:** deliberately make L2 vocabulary disjoint from L3 wording (ask "Anwesen", when the passage says "Villa"). A query that shares no content word with its gold chunk is the one that actually tests the embedding.
- **Blind-split for a two-person team (user + Claude):** one party fixes L1 from a topic prompt without the target wording; the gold chunk(s) are located only afterward. Simulates the annotator/author separation without crowdsourcing.

## Trap: do NOT reuse ARES's retrieval-filter on the eval gold set

ARES generates synthetic queries from passages, then **filters out any query that fails to retrieve its own source passage as the top result** (a technique from Dai et al. 2022). That is deliberate for building **judge-training** data — it keeps only queries the retriever already answers. Applying the same filter to an **eval gold set is circular**: it manufactures ~100% recall by construction and deletes exactly the failures the eval exists to surface. Our gold set keeps hard queries, including ones the current prod config misses — those misses are the signal, not noise to be filtered away.

## Hard negatives / discrimination

A gold set that only rewards finding the one gold chunk, with no distractors present in the corpus, is too easy to discriminate configs. Both large corpora already contain near-duplicate material (survey papers restating each other; multiple trading papers on the same concept), which supplies natural hard negatives. Two grounded distractor patterns to lean on when curating:

- **ARES strong negatives:** passages from the **same document** as the gold chunk (topically adjacent, lexically similar, not the answer).
- **RAGAS context-relevance distractors:** related-but-less-relevant material (they injected Wikipedia back-link sentences). The equivalent here: a second paper's tangential mention of the same term.

## Metric

- **Primary: nDCG@10.** BEIR's rationale (adopted): Precision/Recall are rank-unaware; MRR/MAP are binary-only and fail under graded relevance; **nDCG balances precision- and recall-oriented tasks and handles both binary and graded relevance**. BEIR computes nDCG@10 via the official TREC eval tool — same cutoff we already cap retrieval at (top_k=12, so @10 is fully covered).
- **Secondary:** Recall@k (absolute coverage plausibility), MRR (first-gold-hit position).
- **Graded relevance (upgrade over the prior binary scheme):** `rel=2` exact gold chunk, `rel=1` same-document other chunk, `rel=0` else. nDCG's graded form (`DCG@k = Σ (2^rel_i − 1)/log2(i+1)`) consumes this directly and distinguishes "perfect hit" from "right document, wrong chunk".
- **Retrieval-only scope:** because there is no generation step, RAGAS's answer-faithfulness and answer-relevance metrics do **not** apply; only its **Context Relevance** is retrieval-side. Do not import generation metrics into a pure-retrieval sweep.

## Why this must precede the sweep

The planned config sweep (SPLADE on/off, 8B parameters, reranker on/off) scores configs against the gold set. If the gold set carries injected lexical overlap, the sweep ranks configs by how well they exploit that overlap — a BM25-flattering artefact — not by retrieval quality. An unbiased, paraphrase-gapped gold set with hard negatives is the precondition for the sweep to mean anything. Index the frozen corpora at the richest setting first (SPLADE populated, max 8B token budget) so downstream configs can be **subset** without re-indexing where the parameter is subsettable (candidate count, sparse-branch drop, context truncation); chunk boundaries and embedding dimension remain re-index-only.

## Sources

Indexed in `rag-cli-reference`:
- `ARES_Automated_RAG_Evaluation` — synthetic query generation, the retrieve-your-passage filter (training-data only), strong/weak negatives, PPI confidence intervals
- `RAGAS_Evaluation_Framework` — anti-leakage generation prompt, two-annotator relevance judgment, context-relevance distractor construction, reference-free metric triple
- `BEIR_Zero_Shot_IR_Benchmark` — nDCG@10 rationale, `corpus/queries/qrels` standard
- `RAG_Evaluation_Survey_2025` — metric formulas (Recall@k, MRR, nDCG@k, MAP)
- `Lost_In_The_Middle_Long_Contexts` — position effect (mid-context relevance is used less; matters for rerank ordering)
- `MTEB_Massive_Text_Embedding_Benchmark` — embedding-model comparison methodology for the 8B parameter sweep
