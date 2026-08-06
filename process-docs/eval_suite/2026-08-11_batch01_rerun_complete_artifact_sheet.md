# Batch01 Re-run Complete: Artifact Sheet and Calibration Comparison (2026-08-11)

Full four-pass re-run of the 20 batch01 papers under the hardened prompts and content-gated
validators (per the 2026-08-06 diagnosis and fix program). All passes executed by
claude-sonnet-5 workers in KB-budgeted lots (150 KB source per Pass A/B lot; Pass C lots
2 docs; Pass D lots 3-6 docs since input is summaries only), each lot plan-gated (report
plan → orchestrator Go → implement → validator → review → merge). Framed as of 2026-08-11.

## End state

- Pass A: 21/21 artifacts pass the hardened validator (granularity gates: median block
  ≤ 25 lines, ≥ 4 blocks/100 lines). 1700 blocks total (old batch01 stand: ~490).
- Pass B: 21/21 pass (blocks/theme floor 2.0, zero proof-labeled themes). 274 themes,
  b/t median 6.1 (old batch01: 1.47), 129 distributed themes.
- Pass C: 21/21 pass (anti-lookup gate, concept-level head anchoring, digit/structure
  bans). 274 summaries, zero lookup-phrasings.
- Pass D: 21/21 pass (0.80 stemmed overlap ceiling, head-concept lead, format
  completeness). 822 queries (274 x 3 formats).
- Leakage audit (3-gram, summaries vs passages): overwhelmingly generic field
  collocations; 13 candidate phrases flagged for the human review gate (narrative-shaped
  sequences, e.g. "slowly decaying exponentially weighted moving averages",
  "investor attention more timely") — listed in `/tmp` audit output at run time,
  reproducible via `eval/scripts/audit_leakage.py` per document.

## Headline metrics vs old batch01

| Metric | old batch01 | re-run |
|---|---|---|
| Blocks/theme median | 1.47 | 6.1 |
| Proof-labeled themes | 10 | 0 |
| Docs with zero distributed themes | 10/20 | 1/20 (Hamilton — structurally justified: no appendix, inline footnotes) |
| Pass C lookup-phrasings | 11/254 explicit + widespread soft form | 0/274 |
| Query overlap vs information_need (nq+fs, stemmed) | median 0.92, 94% > 0.80 | median 0.56, max 0.78 |
| Pass D coverage | 17/20 docs | 21/21 docs |
| Model provenance | absent | `model` field in all 84 artifacts |

Bollerslev1986GARCH (calibration): b/t 5.62, overlap median 0.61/max 0.78 — the re-run
docs bracket the calibration values on both metrics.

## Process characteristics of the re-run

- KB budgeting held: no worker death, no mid-lot method degradation across 11 Pass A lots,
  11 Pass B lots, 10 Pass C lots, 5 Pass D lots.
- Plan gates caught real errors pre-write in most lots: proof-splitting intent (A lot 6),
  section-echo risk, recap-need themes (B lot 1), lookup phrasings, over-ceiling drafts
  (D lots 2/3/5 — e.g. StaricaGranger t03 nq at 0.84 caught and rewritten to 0.40 before
  any file existed).
- Two HARD-STOP violations occurred (A lot 1 before the gate wording was hardened;
  C lot 6 with a rationalization) — both logged in the respective lot recap entries;
  gate wording was tightened twice in response and held afterward.
- Validator mechanics discovered during the run and encoded into lot prompts: literal
  primary_concept prefix for keyword_bag (incl. connective words), irregular-plural stem
  mismatches, Oxford-comma clause-break truncation, hyphen handling (compound modifiers
  hyphen-free; intrinsic names keep hyphens), "cross section" tripping the
  structure-reference token scan.

## Deferred / open for the review gate

- The 13 flagged leakage candidates need the human review call (semantic judgment whether
  any is distinctive passage phrasing rather than field collocation).
- The "cross section" structure-ban false positive is a validator refinement candidate.
- Ground-truth qrels construction (theme spans → chunk-level GT against the frozen test
  corpus) and the corpus freeze itself remain the next milestones toward the sweep; corpus
  state is to be recorded in the collections metadata at test-DB indexing time (user
  decision, this session).
- Books (18 corpus docs > 150 KB) deliberately deferred; capacity evidence recorded in the
  2026-08-06 diagnosis entry.

## Sources

- `eval/queries/pass_{a,b,c,d}_runs/` (84 artifacts, all with `model` field)
- `eval/queries/pass_a_runs/batch01_archive/` etc. (the discarded first batch01, for diff)
- `eval/scripts/validate_pass_{a,b,c,d}.py`, `audit_leakage.py` (content-gated state)
- `eval/queries/prompts/` (hardened prompt revisions)
- per-lot process-docs entries in this area (2026-08-06 .. 2026-08-11)
