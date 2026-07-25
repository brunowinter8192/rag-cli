# Graph RAG — Session Conclusion (2026-05-26)

## Context

Opened for discussion. In the 2026-05-24 scoping, two directions were distinguished: A (project visualization as a graph) vs B (graph-augmented retrieval / classic GraphRAG paradigm). First indication at the time: A primary, B optional later. This session made a decision on both directions.

## What Direction B (Graph-Augmented Retrieval) concretely is

Beyond the scoping doc's short description, refined further:

**Indexing phase.** Every chunk is run through an LLM with the prompt "extract entities and relations". Output: typed entities (e.g. `Reranker`/Component, `Qwen3-Reranker-0.6B`/Model, `snippet recall 97%`/Metric) plus relations (`(Reranker)-[USES_MODEL]->(Qwen3-Reranker-0.6B)`, `(retrieval-reranking-record)-[CITES]->(Qwen3-Paper)`). Entities + relations land in a graph DB (Neo4j, in-memory NetworkX, or simpler: JSON/SQLite with an edge table). The vector DB remains in parallel.

**Query phase.** Two paths simultaneously: (1) classic vector search on chunks, (2) entity extraction from the query plus graph traversal from matched entities to N-hop neighbors. Both hit sets are merged, deduplicated, ranked → top-K to the LLM.

**What it buys.** Multi-hop queries ("which process records about X also cite source Y"), compositional queries, abstract topic questions — answers that aren't reliably reachable purely semantically in embedding space because the connection is structural (`CITES`, `USES_MODEL`, `SUPERSEDES`), not semantic.

**What it costs.** LLM call per chunk at indexing time (scales linearly), graph DB as an additional storage layer, entity-extraction prompt tuning, traversal logic plus merging with vector hits. Implementation effort: several days. Maintenance on every `update_docs` run: new chunks must be extracted.

## User objection: B is visualizable

Previously implicitly assumed B = invisible (internal data structure only). Counter-point: the internally built knowledge graph IS visualizable — as a Mermaid diagram, as a 3D force-directed graph, however rendered. Technically correct. The force-directed-graph image shown (presumably Obsidian-vault style, pink nodes = documents, blue nodes = high-connectivity hubs, light-blue cluster = selected node + neighbors) would in principle be just as renderable from B's entity graph as from A's code-symbol graph.

In practice, though, A and B operate at different layers of the project: A operates at file level (modules, process docs, historical entries as nodes), B operates at entity level (extracted terms/concepts as nodes). Both visualizations would be possible simultaneously but show different topologies.

## Decision: both directions deferred

**Core argument against B: maintainability for constantly growing project docs.**

GraphRAG paradigms (Microsoft GraphRAG, LightRAG, nano-graphrag) are designed for **fixed data corpora** — scientific paper collections, knowledge bases, static documentation corpora. Indexing is expensive once, then the graph stands. For an actively developed project with process-docs that change every session, the cost calculation tips:

- Every doc change requires re-running entity extraction → ongoing LLM cost
- Entity-extraction errors in a single doc edit propagate into the graph → distorted retrieval results on future queries
- Conceptual overhead when writing: every new doc forces the implicit question "how does this relate to X, Y, Z" for relations to stay complete — otherwise the next multi-hop query won't find what it should
- Corrections to the graph (e.g. when an entity was extracted incorrectly) are expensive and not trivially visible — the graph is not the primary artifact one maintains

**B fits fixed corpora, not living project docs.** If the RAG project ever reaches a state where it grows less actively and is used more as a knowledge archive, B becomes more plausible. Currently it's the exact opposite — project docs change per session.

**Direction A (visualization) is appealing but not a primary lever right now.** The force-directed-graph image would give orientation, yes. But at the current project size (~10 src/ modules, ~30 process-docs files) textual navigation via RAG + DOCS.md + source inventory is functional. The graph would supplement, not replace, this non-essential gap.

## What remains: refine the current system

Explicit user direction: "test the current system in production further before adding another new feature — better to refine and improve it now." The structural levers visible here:

- **Indexing setup:** chunker configuration (chunk size, overlap), document-format-aware splitting if the corpora demand it
- **Retrieval setup:** dense+rerank has been the sole prod path since `f8f35c0` (2026-05-26). RERANK_CANDIDATES=30 fixed (Phase B plateau)
- **Models:** Qwen3-Embedder-8B + Qwen3-Reranker-0.6B as the current set. Where real leverage remains, it hangs more on model updates / model comparisons than on architecture changes

Assessment at the time: "I see little leverage that wouldn't add complexity." That's a valid description of the state at the time. RAG-system complexity is not what was limiting retrieval quality then — the important trade-offs (rerank vs no-rerank, fusion vs dense-only, top_k=12) were measured through and settled. What remains is eval extension (grow test_db, cross-domain queries) and model observation.

## Status

Both directions (A + B) deferred, as a marker for "later, when the project grows substantially larger OR stops growing actively" — either shifts the cost calculation against the situation at the time.

Reopen triggers would be:
1. Project grows to a volume where textual navigation no longer suffices (~50+ modules + ~100+ process-docs entries)
2. Project moves into maintenance mode (docs no longer constantly change) — then B's indexing cost calculation becomes viable
3. Compositional queries become a pain point ("which process records about X also cite source Y") — vector search alone no longer delivers

Until then: no action.

## Sources

- Microsoft GraphRAG, HKUDS/LightRAG, gusye1234/nano-graphrag — the three canonical B implementations; not yet indexed in RAG_reference
