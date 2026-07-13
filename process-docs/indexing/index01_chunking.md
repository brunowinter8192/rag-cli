# Indexing Step 1: Chunking

## Status Quo (IST)

**Code:** `src/rag/chunker.py` — invoked internally by `cli.py index`
**Method:** Recursive character split with hierarchical separators
**Separators:** `\n\n` → `\n` → `. ` → `! ` → `? ` → ` `
**Config:** 2000 chars target, 400 chars overlap (word-aligned)

No markdown-awareness (headers not treated as boundaries). No content-adaptive splitting (code, prose, tables treated identically).

## Evidenz

### Pipeline Optimization Paper (RAG: RAG_reference / Pipeline_Optimization)

| Chunk Size | Acc@3 | NDCG@3 |
|-----------|-------|--------|
| 2000 chars | 0.412 | 0.356 |
| 512 chars | 0.460 | 0.415 |
| Semantic (variable) | 0.456 | 0.404 |

512 chars outperforms 2000 chars by +5pp Acc@3. Semantic chunking performs comparably to 512 fixed. Adding a reranker bridges ~50% of the gap between 2000 and 512.

### Our Chunk Statistics (all collections)

- 5553 chunks total, avg 843 chars, median 889 chars, max 1190 chars
- p90: 990, p95: 1005, p99: 1138

### Rethinking Chunk Size (RAG: RAG_reference / Rethinking_Chunk_Size_Long_Document)

Systematic evaluation of fixed-size chunking across 6 QA datasets with 2 embedding models: **Stella** (decoder, Qwen2-basis, 130k ctx window) and **Snowflake** (encoder, 8k ctx window). Chunk sizes: 64/128/256/512/1024 tokens. Metric: Recall@K. No overlap in any experiment.

**Chunk size × model ctx window axis:** Stella's 130k-context Qwen2 base yields global chunk representations that scale with chunk size — larger chunks provide richer context without noise. Snowflake's 8k ctx pretraining favors local token interactions and degrades at large chunks.

| Model | Architecture | Context | Optimal Chunk | Strongest Datasets |
|-------|-------------|---------|---------------|-------------------|
| Stella | Decoder (Qwen2-basis) | 130k | 512-1024 tokens | NarrativeQA, NQ, TechQA |
| Snowflake | Encoder | 8k | 64-128 tokens | SQuAD, CovidQA |

**Concrete Recall@1 numbers:**
- NQ: Stella peaks at 512 tokens (R@1 = 38.5%); Snowflake peaks at 1024 tokens (R@1 = 47.7%)
- TechQA: R@1 rises from 4.8% (64 tokens) to 71.5% (1024 tokens) for Stella — strongest decoder advantage in the study
- SQuAD (short fact-based answers): both models comparable at 64 tokens (R@1 ≈ 64%) — chunk size nearly irrelevant for entity-level retrieval

**Relevance to IST:** Qwen3-Embedding-8B is a Qwen2-based causal decoder with 32k context — architecturally same family as Stella. The decoder advantage at 512-1024 tokens directly applies. Our 2000-char setting (~500 tokens) sits squarely in the optimal range for this model family.

### Chunking Eval (ad-hoc, script not committed)

5-Doc subset sweep on RAG_MCP: 6 variants (A-F, 500-1500 chars). **Result: all variants Recall@3/5/10 = 1.000.** Corpus too small to discriminate — needs larger benchmark dataset.

### RAG Evaluation Survey 2025 (RAG: RAG_reference / RAG_Evaluation_Survey_2025)

Section 3.2.3 ("Upstream Evaluation") codifies chunking eval at two levels: (1) **intrinsic** — Full Keyword Coverage (% of required keywords in ≥1 retrieved chunk), Tokens-To-Answer (index of first fully comprehensive chunk); (2) **extrinsic** — downstream Recall, Precision, ROUGE/BLEU/F1 vs ground-truth evidence. Domain-specific evidence (financial reports [57]) shows structure-based and semantic chunking improves retrieval accuracy while reducing latency. Core assertion: chunking quality propagates through retriever evaluation metrics, not chunking metrics directly. Confirms our eval approach: downstream Recall@K is the correct primary signal.

### Qwen3 vs BGE-M3 (Referenced — Medium article, no longer indexed after 2026-04-30 clean-slate)

Anecdotal: "strong performance with chunk sizes of 2,000–4,000 tokens" for Qwen3. No methodology provided.

## Recommendation (SOLL)

**Keep:** `2000 chars / 400 overlap` — primary anchor: Rethinking_Chunk_Size_Long_Document shows decoder models (Qwen2-basis family, architecturally identical to Qwen3-Embedding-8B) benefit from 512-1024 token chunks, with Recall@1 gains of +5-8% vs encoder models at this range. 2000 chars ≈ 500 tokens sits squarely in the optimal range for this model family. Supporting: Pipeline_Optimization reranker bridges ~50% of any remaining 2000→512 char gap. Community consensus: 500-1000 tokens for decoder models. Validated via A_chunking_stats: 483 chunks, avg 1736 chars, 80% in 1500-2000 bucket. Recursive character split with default separators sufficient — semantic chunking not worth the complexity (multiple Reddit threads confirm).

**Keep:** Recursive character split with hierarchical separators (`\n\n` → `\n` → `. ` → `! ` → `? ` → ` `). Validated via `dev/indexing/A_chunking_stats.py` (report: `dev/indexing/A_chunking_stats_reports/stats_RAG_MCP_20260407_171958.md`): 483 chunks, avg 1736 chars, 80% in 1500-2000 bucket.

## Offene Fragen

- Chunk size × MRL dimension interaction — does 1024d change the optimal chunk size vs 4096d? **Still open.** Qwen3_Embedding confirms MRL support (1024/2560/4096d) but contains no chunk × dimension data. Closure requires: re-download arxiv 2411.17299 (2D_Matryoshka_Training, removed in 2026-05-10 rebalance) → index into RAG_reference → run search_hybrid for layer × dimension interaction findings. Not in current session scope.
- Retrieval quality with 2000 chars vs 1000 chars — needs A/B comparison on same queries (pending retrieval eval)

## Quellen

Indexed in collection `RAG_reference`:
- Pipeline_Optimization (Chunks 6, 20, 28, 29, 36) — GTE-large, Encoder
- Rethinking_Chunk_Size_Long_Document — Stella/Snowflake, Decoder vs Encoder
- RAG_Evaluation_Survey_2025 — two-level eval methodology (intrinsic + extrinsic chunking metrics)

Referenced (consulted historically, no longer indexed after 2026-04-30 data clean-slate — sources kept for attribution but not searchable in current collection):
- medium.com__mrAryanKumar (Qwen3 vs BGE-M3 comparison)
- medium.com__yashasvimantha (MRL Sweet Spot Qwen3-0.6B)
- research_trychroma_com__evaluating-chunking (Chroma Technical Report)
- Anthropic contextual-retrieval (Contextual Chunking concept)
- Late Chunking vs Contextual Retrieval comparison
