# Batching Plan: 20-Paper Increments, Books Individually (2026-07-25)

Scaling decision after the Bollerslev1986GARCH end-to-end validation (Pass A-D chain run,
revised, re-run, and reviewed). Framed as of 2026-07-25.

## State the plan builds on

The full formulation chain was validated on one document: Pass A (45 blocks) → Pass B
(8 themes, independently replicated — theme cores reproduce; variance sits in granularity
calls at theorem-adjacent boundaries) → Pass C (8 summaries, primary_concept slot) →
Pass D (24 queries, 3 formats, primary_concept lead). Leakage audit on the summaries came
back clean (3 n-gram candidates over 8 summaries, all generic field collocations). User
review of the full artifact sheet passed.

## Decided: papers in 20-doc increments, review gate between batches

- Next step: ONE batch of 20 documents from `data/documents/trading-reference/` — PAPERS
  only — through the full chain, then a review of the same shape as the Bollerslev review
  (artifact sheet + leakage audit) before the next batch.
- Continue in 20-doc increments with a review gate after each; no full-corpus run without
  passing gates. Rationale: a prompt-level defect scales into every batched document —
  the increment caps the blast radius (the t01/t02 attribution drift was caught on ONE
  document and cost two rerun passes; at 60 documents it would have cost a re-batch).

## Books: individually, never batched

User decision: books are processed ONE AT A TIME, each as its own run — they are too large
for batching. The Pass A unit for a book (whole vs per-chapter) remains undecided; not
needed for the paper batches and deferred until the first book is attempted.

## Operational notes for the batch runs

- The Pass B → Pass C spans-only filter is now a committed script
  (`eval/scripts/filter_spans_only.py`, whitelist-asserted down to span keys) — no more
  ad-hoc filtering; the anti-leakage boundary is mechanical.
- One worker per pass step; worker context budget is the limiting factor for how many
  documents one worker can carry through a single pass — to be sized empirically in the
  first batch.
- Fresh-worker requirements unchanged: Pass B fresh (no Pass A history), Pass D never
  sees passages; Pass C reads passages by design.

## Sources

- `eval/queries/prompts/` (the four pass prompts, revision state as of this date)
- `eval/scripts/filter_spans_only.py`
- `eval/queries/pass_b_runs/`, `pass_c_runs/`, `pass_d_runs/` (Bollerslev validation artifacts)
