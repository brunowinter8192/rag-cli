# Batch01 Failure Diagnosis, KB Worker Budget, Model Provenance (2026-08-06)

Diagnosis of the first 20-paper batch (run 2026-07-26..28 through the four-pass chain),
concluded from artifact measurement + the batch run entries. Outcome: all 20 batch01
artifact sets archived to `eval/queries/pass_*_runs/batch01_archive/` pending a full
re-run; only the Bollerslev1986GARCH calibration set remains live. All batch01 and
Bollerslev runs used claude-sonnet-5 workers. Framed as of 2026-08-06.

## Headline numbers (batch01 vs. Bollerslev calibration)

| Metric | Bollerslev | batch01 (20 papers) |
|---|---|---|
| Blocks/theme ratio | 5.62 | median 1.47 (min 1.07) |
| Median Pass A block size (worst docs) | 8 lines | 48-56 lines (max block 314) |
| Docs with ZERO distributed themes | 0/1 | 10/20 |
| Docs with zero soft memberships | — | 19/20 |
| Proof-only themes (violate theorem+proof merge precedent) | 0 | 10 |
| natural_question token-overlap with information_need | median 0.60 | median 0.90 (198/214 queries > 0.8) |
| Pass D coverage | 3/3 formats | 17/20 docs (3 never ran) |

## The failure chain — one defect per pass, each feeding the next

1. **Pass A under-segmented via a documented mid-batch method switch.** The worker
   processed the first ~5 documents line-by-line (the validated Bollerslev method,
   cumulative ~396 KB), then switched to a heading-grep shortcut ("too slow at batch
   scale") for the remaining ~15 — boundaries only at the paper's own headings, R2
   (subject-shift cut) effectively suspended. The switch was throughput pressure, NOT
   context exhaustion: it happened at ~400 KB of a run that later reached ~1.4 MB.
2. **Pass B echoed sections instead of forming themes.** On coarse blocks the split
   test had nothing to work with: theme lists mirror the papers' tables of contents,
   half the docs have no distributed theme at all, and 10 standalone proof themes
   contradict the Bollerslev precedent (theorem statement + appendix proof = ONE
   distributed theme per R7). The 2026-07-28 audit fixed two patterns
   (conclusion-recap, setup/result splits) but explicitly left proof merging and the
   granularity root cause out of scope.
3. **Pass C wrote lookup needs on themes too fine to carry a case-match need.** R6's
   meta level ("does this methodology fit my case") degraded to "a researcher wants
   the definition/theorem/proof of X" — 11/254 needs explicitly lookup-phrased, the
   softer form widespread. A 28-line theme cannot seed a case-match need.
4. **Pass D paraphrased the summaries.** natural_question token-overlap with the
   information_need: batch01 median 0.90 vs. Bollerslev 0.60 — the queries are the
   summary's need sentence with a question mark. The anti-leakage chain against the
   PASSAGE held; the three formats collapsed into one. Contributing factor: the
   validator's literal head-concept check rewarded verbatim primary_concept embedding
   (documented in the Pass C completion entry), pushing toward uniformity.
5. **Validators checked structure only.** Schema, span bounds, trash disjointness,
   coverage — all passed while every content property above failed. The only content
   check that ever fired (head-concept lead) made the paraphrase problem worse.

## Capacity findings (the KB question)

Document sizes in batch01 span 38-140 KB (factor 3.7) — batching by document COUNT is
blind; the unit is KB of source text.

- Hard context death: Pass C worker died after 19 docs / ~1425 KB source read (plus
  summaries written; effective context load estimated 2-3x source KB). Pass D worker
  died at 17 docs. The three missing Pass D artifacts were never backfilled.
- Care threshold: quality degradation (the Pass A method switch) began at ~400 KB
  cumulative — far below the context ceiling. The binding constraint is worker CARE
  under a large remaining backlog, not raw context capacity.
- Position analysis of Pass C lookup-phrasing shows late clustering (positions 14-17,
  cumulative 1.0-1.3 MB) — weak evidence (11 cases, confounded with document type),
  but nothing suggests trustworthy work beyond ~1 MB.

**Decision: 150 KB source text per worker lot** (user-approved). Margins: ~9.5x to
observed death (1425 KB), ~2.6x to observed care threshold (~400 KB), and with 3x
overhead a lot stays under ~450 KB effective load — inside the observed-clean range.
For the 20-paper re-run this yields 11 lots of 2-3 docs (first-fit-decreasing packing,
lots 115-150 KB). A batch stays 20 docs per review gate; internally it is KB-packed.
Raise the budget only after the re-run's first lot is measured under hardened
validators.

## Fix program (user-approved)

1. Lot size 150 KB, hard; no worker ever gets the full batch again.
2. Pass A prompt: line-by-line reading mandated, heading-grep explicitly banned;
   validator gains a granularity gate (median block size + blocks/100 lines in the
   Bollerslev corridor) that mechanically exposes the shortcut.
3. Pass B prompt: explicit theorem+proof merge rule; validator gains proof-label lens
   (zero tolerance), blocks/theme band, distributed-theme expectation for papers with
   appendices.
4. Pass C prompt: lookup-phrasing ban ("wants the definition/theorem/proof of");
   R6's case-match framing becomes a formulation requirement in R12; validator checks
   the banned patterns.
5. Pass D: anti-paraphrase gate — token-overlap ceiling of natural_question vs.
   information_need (~0.75, calibrated on Bollerslev's 0.44-0.72 range), in prompt
   and validator.
6. Head-concept check relaxed to concept level so it stops forcing verbatim embedding
   (which would undercut fix 5).

## Model provenance (new requirement)

- Every pass output JSON carries a mandatory `model` field (validators enforce);
  batch01 + Bollerslev artifacts predate this and were all claude-sonnet-5.
- Each run's process-docs entry records model + lot composition.
- Planned experiment (deferred): an identical run with claude-opus-5 workers once the
  sonnet-5 re-run under hardened gates exists as baseline.

## Books (forward note, not this session)

18 corpus documents exceed 150 KB (top: Hamilton1994TimeSeriesAnalysis at 2532 KB —
1.7x the load that killed the Pass C worker). A book is not runnable whole for ANY
pass; the batching plan's open question (Pass A unit: whole vs. per-chapter) is
therefore settled by capacity: per-chapter, bundled into ~150 KB units, with GLOBAL
line numbers into the original file (span anchoring must survive), and a Pass B
extension for cross-chapter themes (the book analogue of statement+appendix-proof).
Needs its own design round before the first book run.

## Sources

- `eval/queries/pass_*_runs/batch01_archive/` (the diagnosed artifacts)
- `eval/queries/pass_*_runs/Bollerslev1986GARCH.pass_*.json` (calibration reference)
- `eval/scripts/validate_pass_*.py` (structural-only state at diagnosis time)
- `data/documents/trading-reference/` (99 files as of this date; source sizes)
