# Retrieval Step 1: Query Embedding

## Status Quo (IST)

**Code:** `src/rag/search_primitives.py:embed_query()` (imported by `retriever.py`)
**Dense:** Same model as indexing (Qwen3-Embedding-8B), with instruct prefix
**Sparse:** Same model as indexing (SPLADE++), no prefix
**Prefix:** `Instruct: Given a search query, retrieve relevant passages that answer the query\nQuery: `

Query embedding is asymmetric: documents are embedded without prefix, queries with prefix. This is the Qwen3 model card's recommended approach for retrieval.

## Evidenz

No isolated evaluation of query embedding quality. Query embedding is tested implicitly through all retrieval evaluations.

## Recommendation (SOLL)

Pending — no isolated query embedding evaluation.

## Offene Fragen

- HyDE: Generate hypothetical answer, embed that instead of raw query. Claimed benefit when user terminology differs from document terminology. Cost: 1 LLM call per query.
- Query expansion: Decompose complex queries into sub-queries. Cost: 1 LLM call per query.
- Multi-query: Generate N query variants, retrieve for each, merge results.
- All above add latency (LLM call) — worth it only if retrieval quality is insufficient.

## Quellen

- HyDE implementation: Zilliz (Milvus), Haystack (deepset)
- Anthropic contextual-retrieval (query processing context)
- Qwen3-Embedding Model Card (instruct prefix format)
