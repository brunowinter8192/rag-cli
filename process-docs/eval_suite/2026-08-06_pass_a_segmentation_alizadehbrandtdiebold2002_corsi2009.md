# Pass A Segmentation Run — AlizadehBrandtDiebold2002 + Corsi2009 (2026-08-06)

Applied `eval/queries/prompts/segmentation_prompt_pass_a.md` (R1-R4, R3b) to two
`data/documents/trading-reference/` papers, one after the other:

- `AlizadehBrandtDiebold2002RangeBasedStochasticVolatility.md` (729 lines, range-based
  stochastic volatility estimation: continuous-time model, discretization, QMLE derivation,
  Monte Carlo comparisons, five-currency two-factor empirical results) →
  `eval/queries/pass_a_runs/AlizadehBrandtDiebold2002RangeBasedStochasticVolatility.pass_a.json`
  — 117 blocks, 9 trash spans. `OK validate_pass_a: 117 blocks, 9 trash spans, 729 lines
  covered` (median block size 2 lines, 16.05 blocks/100 lines).
- `Corsi2009SimpleLongMemoryRealizedVolatility.md` (341 lines — see line-count discrepancy
  note below — HAR-RV cascade model derivation, simulation, empirical HAR(3) estimation and
  forecasting) →
  `eval/queries/pass_a_runs/Corsi2009SimpleLongMemoryRealizedVolatility.pass_a.json`
  — 67 blocks, 6 trash spans. `OK validate_pass_a: 67 blocks, 6 trash spans, 341 lines
  covered` (median block size 2 lines, 19.65 blocks/100 lines).

## Discovery: task-header line count vs actual file line count can disagree — always verify with `splitlines()`

The task prompt described Corsi2009 as "340 lines" and embedded exactly 340 numbered lines of
text (cut off mid-word, "Leverage eff", at the visible end). The actual source file has 341
lines: `wc -l` reports 340 because the file has no trailing newline after its final line
("Received July 7, 2008; revised December 31, 2008; accepted January 14, 2009."), so `wc -l`
(which counts `\n` characters) undercounts by one. The validator loads the source via
`f.read().splitlines()`, which correctly yields 341 lines regardless of trailing newline —
confirmed directly with a `python3` one-liner before writing the JSON. Segmenting against the
340-line mental model would have left line 341 uncovered and failed the validator's coverage
check. Lesson: when a source total-line count matters for span coverage, verify it with
`splitlines()` (or equivalent), not `wc -l` and not the task-embedded line numbers alone — a
missing trailing newline is a silent off-by-one trap.

## Method: reconstruct from the embedded/task text, then re-verify tricky spans against the real file

Built the full ordered (line_start, subject-or-trash-type) sequence from the task-embedded
numbered text first (both documents fully read, no heading-grep shortcut — every blank line
judged for subject-shift per R2/R3b). Given the density of mid-sentence PDF-pagination splits
in both papers, re-read the actual source files directly (`Read` with offset/limit) for every
region where a footnote, table, or figure was suspected of floating mid-sentence, to eliminate
transcription risk before committing to line numbers — all spot-checks matched the
task-embedded text exactly except for the Corsi2009 total-line discrepancy above. Final
line_end values were computed mechanically as `next_span.line_start - 1` (last span end = last
document line) rather than hand-counted, avoiding manual coverage-arithmetic drift.

## Object-interposed mid-sentence splits (footnote/table/figure floats), several per document

Both papers are PDF conversions where footnotes, tables, and figures routinely float to a
column break in the middle of a running sentence. Per the prompt's page-break guidance, a bare
blank line splitting one sentence is merged into a single block (no footnote/table/figure
object in between) — e.g. AlizadehBrandtDiebold2002 L188-191 ("...highest and" / blank /
"lowest log prices...") and Corsi2009 L23-25 ("...simple additive model" / blank / "defined as
the sum of..."). When an actual object (footnote text, or a whole Table/Figure with its own
caption+data) sits between the two half-sentences, it cannot be skipped over by a single
contiguous span — the object gets its own block, and the two half-sentences become two
separate block entries (matching subject labels, not fabricated as topic shifts):
- AlizadehBrandtDiebold2002: L160/172 (Table I interposed between "...with origin" / "x_0=0
  and constant diffusion..."), L520/544 (Table V interposed mid-"absolute return-based"),
  L628/654 (footnote 26 + Table VIII interposed mid-"which cap-/-tures only the sum...").
- Corsi2009: L88/95 (footnote 6 continuation + a second footnote interposed mid-"...in this
  simplified case) with" / "the daily integrated volatility"), L222/238 (Table 3 interposed
  mid-"market component weights, that is,"), L269/273 (Figure 8 caption interposed mid-"moving
  window" / "of 1000 observations"), L303/327 (Figure 9's orphan panel labels + full caption
  interposed mid-"The reason is that the AR(1) and AR(3) models" / "have a memory...").

## Caption content-vs-stub calls

Applied the rule literally: a caption carrying parameters, model equations, or "how to read
the panel" instructions is CONTENT; only orphan labels with zero standalone content are
`caption_stub`. In both documents nearly every full figure/table caption qualified as CONTENT
(even one-liners specifying panel order, e.g. Corsi2009 Fig 1 "actual (top) and simulated
(bottom)"). `caption_stub` was reserved strictly for bare series/model-name labels with no
sentence at all:
- AlizadehBrandtDiebold2002: Figure 3's pre-caption panel labels (L408-416, "QML with
  Absolute Return" / "QML with Range" / "Exact ML with Absolute Return"), bare axis-label
  lines before Figs 4/5 (L492-493, L496-497), and Figure 6's "Histogram"/"QQ Plot" panel
  labels (L680-696).
- Corsi2009: Figure 9's pre-caption block (L305-324) — a run of bare "AR(3)" / "USD/CHF" /
  "ARFIMA(5,d,0)" / "HAR(3)" / "S&P500" / "T-Bond" labels with no prose, immediately followed
  by the actual substantive Figure 9 caption (L325-326, kept as content).

## Conclusion trash-vs-content split, consistent with prior precedent

Both papers' final sections were split rather than blanket-classified: pure-recap paragraphs
went to `abstract_summary`, paragraphs carrying a standalone claim not stated elsewhere stayed
CONTENT.
- AlizadehBrandtDiebold2002 §V: L721-726 (two paragraphs restating the two-factor result and
  the range's Gaussian/efficiency properties — pure recap) → `abstract_summary`. L727-729
  (forward-looking claims: a cross-asset two-factor consensus emerging, and specific future
  directions — multivariate range extensions, comparison to realized volatility,
  microstructure-robust filtering) → kept as two CONTENT blocks.
- Corsi2009 §4: L335-338 (HAR-RV summary + forecasting-performance recap vs ARFIMA) and
  L339 (extensibility: additional regressors, jump measures, leverage effects, nonlinear
  extensions, Vector-HAR) were BOTH kept as CONTENT — confirmed correct by the orchestrator
  mid-task, since L339's extensibility discussion states specific proposed extensions not
  made elsewhere in the paper, the same standalone-claim test applied to L727-729 above.

## Large-block justifications (R3b same-object carve-out)

Only in AlizadehBrandtDiebold2002: Table II (L286-337, 52 lines) and Table III (L352-402, 51
lines) each kept as one block — a single Monte Carlo results table spanning multiple N-trades
panels (A/B/C) of the same experiment, panel-to-panel being elaboration of the same object per
R2, not a subject shift. No block in either document's final segmentation exceeds these two.
Corsi2009 has no block over 22 lines.

## Verification performed

Structural only: `validate_pass_a.py` run against both produced JSONs and their source
documents — schema check, trash-type whitelist, full coverage (729 lines / 341 lines
respectively) with no gaps or overlaps, and the granularity corridor, all passing in one run
each. Not verified: no independent semantic cross-check of individual subject-shift judgments
beyond the reasoning recorded above — that is Pass B's territory if a block turns out to
straddle two topics.
