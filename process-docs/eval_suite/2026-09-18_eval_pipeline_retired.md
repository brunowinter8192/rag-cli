# The Four-Pass Eval Pipeline Is Retired (2026-09-18)

User decision, taken after walking the whole pipeline end to end in one session. The synthetic
query-generation pipeline under `eval/` is no longer pursued. The tree moved to
`dev/eval_suite/`; nothing was deleted. This entry is the stop sign for the eval_suite area and
states why, so a successor does not restart the machine by accident.

## What existed at the moment of retirement

Four LLM passes over the paper corpus, each run by a blind worker that knew nothing about its
neighbour passes:

- Pass A cut a document into contiguous blocks at blank lines and classified non-content as trash.
- Pass B grouped blocks into themes, a theme being the all-and-only answer set of ONE realistic
  practitioner question, allowed to span non-adjacent regions (statement plus appendix proof).
- Pass C wrote one neutral, indicative summary per theme, describing the NEED without letting
  the passage's wording through.
- Pass D authored three query formats per theme from the summary alone, never having seen a passage.

Completed state, all validators green:

| Stage | Result |
|---|---|
| Documents through the full chain | 21 (20 batch01 papers plus Bollerslev1986GARCH as calibration) |
| Pass A blocks | 1700 |
| Pass B themes | 274 |
| Pass C summaries | 274 |
| Pass D queries | 822 (274 themes x 3 formats) |

Never completed, and this matters: **no ground truth was ever built.** The corpus was never
frozen, no test DB was ever indexed, and the qrels step — mapping theme line-spans onto
chunk indices — was never started. 822 queries existed with no machine-checkable answer set
behind them. The pipeline stopped exactly one step before the thing that would have made it an
evaluation. A human review of 13 flagged leakage candidates was also still outstanding.

## Why it is retired

The pipeline's entire reason for existing was anti-leakage. If a query is written while looking
at the passage it should retrieve, it inherits that passage's distinctive phrasing, and the
evaluation then measures which retrieval configuration best exploits that injected lexical
overlap — a BM25-flattering artefact, not retrieval quality. Four passes of worker blindness,
mechanical input filtering and a stemmed-overlap ceiling exist to prevent exactly that.

A real query captured from production has this property for free. It is written from an
information need BEFORE any result is seen, blind to corpus wording, because the person or
agent issuing it does not yet know what the corpus says. The eval_suite area recorded this
itself on 2026-07-23, as a finding about the measured query log, while simultaneously planning
the synthetic pipeline. The observation and the plan contradicted each other, and the
contradiction went unnoticed for two months.

The second reason is proportionality. The synthetic route consumed many sessions across roughly
two months, produced a discarded first batch, a full re-run under hardened prompts, a prompt
overhaul, and still had corpus freeze plus qrels ahead of it. Real logging was one worker.

## What changed on the same day that made this possible

Before 2026-09-18 the query log was effectively unusable:

- The `logging.info` line in `retriever.py` truncated the query to 50 characters, and the
  measured real query has a median of 9 words, so the informative tail was cut off.
- Neither the collection nor the `--document`/`--exclude` filters were recorded.
- Nothing at all about the result was recorded.
- The lines did not even land where the documentation claimed. Several modules called
  `logging.basicConfig` at import time, only the first call configures the root logger, and the
  winner varies per process. The search lines had been landing in
  `~/.rag-locks/logs/server_manager.log` for two months.

That was repaired the same day, see the infra area. Retrieval logging now writes one JSONL
record per `search` carrying the full untruncated query, the collection, both filters, the dense
candidate count, the wall-clock duration and every returned hit with rank, document, chunk index
and reranker score. A content sidecar stores the full chunk text of every hit, joined by a
search id, so a later re-chunk that shifts every chunk index cannot silently invalidate a
historic record. `expand_chunks` is logged the same way, which means the entry point AND the
expansion that follows it are both visible.

Verified in production on 2026-09-18 at 19:24 local: query `chunk boundary overlap
deduplication` on `rag-cli-docs` with `--exclude 'process-docs/%'`, 30 candidates, 3703 ms,
12 hits, the top three scores 0.999557 / 0.980821 / 0.835526 matching the printed output
exactly, sidecar 19.5 KB for that single search.

## The honest gap, and the shape of the replacement

A log gives queries and results. It does not give the CORRECT result. There is no absolute
metric without a notion of right, and that is a real loss compared to what the pipeline
intended to deliver.

It is smaller than it sounds, because a configuration decision is a COMPARISON, not an absolute
measurement. The replacement shape:

- Replay the same real query under two configurations.
- Only the DIFFERENCE between the two hit lists needs a judgment call, not all 12 hits.
- Objective signals need no judgment at all. 55 of the 851 historic invocations returned zero
  candidates — unambiguous failures. A query immediately followed by a rephrased variant of
  itself is a failure signal too, and the records carry timestamps.

Two measured facts constrain any metric built on this, both predating the retirement:

- The result count is a constant 12 and the `score > 0` filter is dead, because the reranker
  emits a sigmoid-like value that is never zero. A deliberately off-domain query (quantum
  entanglement, photosynthesis) against the trading papers still returned 12 hits, with scores
  from 0.0067 down to 0.00048. The count in a log line therefore carries no information about
  success; only the stored results and scores do. This is precisely why the result had to be
  logged and not just the query.
- Generic-vocabulary queries pull legitimately relevant material the author did not intend.
  A ground truth of the form "the one intended region" would score correct behaviour as failure.

## The question this retirement does NOT answer

A searcher arrives from one of two directions: knowing the corpus vocabulary, or knowing only
their own problem. These stress different machinery — lexical matching serves the first, the
embedding and reranker must bridge for the second. Choosing a configuration on evidence from
one direction alone can produce a correct number and a wrong decision.

Measured evidence, 53 distinct real queries: median 9 words, roughly 70 percent dense
multi-concept bags of field terminology, natural questions a ~10 percent minority. Every
observed query sat in the corpus vocabulary. The problem-only direction was never observed.

Hypothesis, explicitly unproven: those queries came from agents that had already read project
documentation within the same session, so knowing the vocabulary may be a selection effect of
where the log was taken rather than evidence that the other direction does not occur.

The synthetic pipeline would not have answered this either. Its Pass C practitioner test
deliberately KEEPS field terminology, and Pass D builds every query from the summary's
sub-concepts, so all 822 queries sit in the corpus vocabulary by construction. Both routes
measure the same single direction. The full retrieval log is the first instrument that can
actually detect the other one, if it exists.

## Where the artifacts went, and what to do before reviving anything

Everything moved byte for byte to `dev/eval_suite/` — the four pass prompts and `injection.md`,
the 84 run artifacts across the four pass directories, the discarded first batch under the
`batch01_archive` subdirectories, and the validator and audit scripts.

Anyone considering a revival should first answer one question with data rather than reasoning:
does the accumulated retrieval log contain enough distinct real queries to discriminate between
configurations? The literature reference point is roughly 100 to 150 labelled examples before
systems can be reliably told apart. 794 distinct queries already existed in the old lean log
over two months, so the answer is likely yes, and reviving a synthetic generator to manufacture
what is already arriving for free would repeat the mistake this entry records.
