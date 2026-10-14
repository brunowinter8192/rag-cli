# Multi-Query Search Strategy (2026-09-16)

## Decision

Callers stop issuing one query and reading 12 results. They issue four queries and read three results each.

The total number of chunks a caller ends up reading stays roughly the same. What changes is how many distinct regions of the vector space produced them.

## Why

A single query is a single point in the vector space. Everything it can return lies in one neighbourhood of that point. Widening `top_k` does not leave that neighbourhood, it only walks further down the same ranked list. Results 4 through 12 of a single query are therefore the weakest members of one neighbourhood, not members of other neighbourhoods.

Four differently phrased queries produce four points. Each returns the strongest members of its own neighbourhood. Coverage of the corpus goes up, and the average quality of what the caller reads goes up as well, because rank 1-3 beats rank 4-12 in every list.

This reasoning is training knowledge about dense retrieval, carried over from the Multi-Query and RAG-Fusion literature. It has not been measured against this project's eval suite as of 2026-09-16.

## How the four queries must differ

The four queries are siblings, not refinements.

- Each carries ONE concept. An embedding of two concepts lands at their midpoint, where typically no chunk lives.
- Each is phrased as a declarative statement in the vocabulary of the corpus, the way the answer itself would read. A question and its answer do not sit next to each other in the vector space.
- None of them is derived from the hits of another. Rewriting a query out of the vocabulary of its own hits is classical relevance feedback: it raises precision and lowers recall. For a coverage pass that is the wrong direction.

Worked example. The subject is why worker spawns fail intermittently.

Good set of four:
1. `worker spawn fails when the worktree branch already exists`
2. `tmux session name collides with an existing session`
3. `worker process exits before the prompt file is read`
4. `spawn returns success but the pane stays empty`

Bad single query covering the same ground:
- `why do worker spawns sometimes fail and what are the causes` — two concepts plus four meta-words (`why`, `sometimes`, `what`, `causes`) that appear in no chunk and drag the vector away from the corpus.

## Known obstacle in the current code

`search_hybrid_workflow()` in `src/rag/retriever.py` hardcodes `top_k = 12` and its signature accepts no `top_k` parameter. A caller cannot ask for three results as of 2026-09-16.

Two consequences follow, and both are unresolved:

- Reading only the first three of twelve returned results gets the intended coverage benefit, but the reranker still scores all `RERANK_CANDIDATES = 30` candidates per query. Four queries therefore cost roughly four times the rerank latency, which is about 18 seconds at the measured ~4.5s per query.
- Making `top_k` a parameter reduces what is returned but not what is reranked. The latency stays the same unless `RERANK_CANDIDATES` is lowered alongside it, and the rc=30 plateau is a measured result that should not be disturbed without a fresh measurement.

Whichever route is taken, the latency of a four-query pass is the number to watch, not the recall.

## What a successor should do first

Do not implement the parameter before measuring the premise. The premise is that four queries at three results cover more relevant chunks than one query at twelve. That is a recall question, and `dev/retrieval/A_retrieval_eval.py` already measures recall against `test_db`.

The measurement needs a query set where each entry is four sibling phrasings of one information need, scored against the union of their top-3 lists. If that union does not beat the single-query top-12 baseline on snippet recall, the decision above is wrong and should be reverted rather than shipped.
