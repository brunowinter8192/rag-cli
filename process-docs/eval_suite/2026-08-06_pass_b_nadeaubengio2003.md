# Pass B Theme Formation — NadeauBengio2003InferenceGeneralizationError.md (2026-08-06)

Fresh-worker Pass B over the 113-block, 6-trash-span Pass A output for
`data/documents/trading-reference/NadeauBengio2003InferenceGeneralizationError.md` (915
lines) — output written to
`eval/queries/pass_b_runs/NadeauBengio2003InferenceGeneralizationError.pass_b.json`: 15
themes, 0 resplits, 3 unassigned blocks, 2 soft-membership blocks, 110/113 assignable blocks
covered — 7.33 blocks/theme (above the Bollerslev1986GARCH calibration anchor of 5.6, above
the validator's 2.0 floor).

## Theme grouping

This is a long, methods-dense stats paper (7 competing significance-test procedures, 3
simulation benchmark problems, 3 appendix sub-sections, 17 footnotes) — 2.5x the block count
of the Bollerslev1986GARCH calibration run. Themes cluster around seven realistic
practitioner needs: (1) the danger of ignoring training-set variability, (2) formal
CV-estimator definitions, (3) the sigma-decomposition variance theory, (4) the
no-unbiased-estimator impossibility result, (5) two constructed variance estimators, (6) a
liberal/conservative diagnostic + comparison table over all seven inference procedures split
into (7) established and (8) newly-proposed methods, (9-12) three simulation-benchmark setups
plus their shared design/CI-methodology framing, (13) the empirical size/power comparison,
and (14-15) the J and M tuning-parameter choices. Seven inference methods and three benchmark
problems each split into separate themes rather than one "Section 4" / one "Section 5" theme
— each method-family and each problem-type answers a distinct single-search question, and no
realistic query needs their union (R6 split test).

## Distributed themes (R7) — two categories

Twelve of fifteen themes are distributed. Most are trash-gap or footnote-placement artifacts
rather than genuine multi-need distribution:
- J-choice and M-choice themes: fragmented into 3 spans each by embedded figure-image trash
  blocks (lines 709-716, 724-731, 741-746) and, for the M-choice theme, by the Section 6
  heading/recap paragraph sitting physically between the M-recommendation text and Figure
  13's caption.
- The three simulation-problem themes (regression/Gaussian-classification/letter-recognition):
  each split by the adjacent problem's setup/table sitting between otherwise-contiguous
  blocks of the same problem.
- Six themes (variance theory, two-estimators, framework+table, established tests, proposed
  tests, simulation design) absorb one or more of the paper's 17 endnotes as trailing distant
  spans — the notes section physically sits at the document tail, so any note elaborating an
  earlier method or proof necessarily produces a distributed theme. This is the R7b pattern
  generalized beyond theorem+proof to claim+footnote.

One theme is genuine R7b theorem+proof distribution: the variance-structure theme merges
Lemma 1/2, the sigma0-3 covariance definitions, Var[mu_hat_J] (eq. 8), Propositions 1-3, and
Conjecture 1 (Section 2, contiguous) with Lemma 2's proof (Appendix A.1) and Proposition 2's
n2-monotonicity proof (Appendix A.2) — an 18-block theme, deliberately not split further
because every piece supports one question ("how does the repeated-CV estimator's variance
behave, and can it be unbiasedly estimated").

## Split decision on the introduction (user-directed, mid-task)

Initial draft bundled the paper's motivation paragraph (why ignoring training-set variability
inflates false claims) with the CV-estimator's formal notation/definition into one 11-block
introduction theme. User challenge against R6's split test: does one question need both the
motivational argument and the full notation-heavy formal setup? Re-examination: no —
"why do naive CV significance tests overestimate significance" is answerable without the
loss-function/index-set formalism, and "how is the repeated CV point-estimate formally
defined" needs none of the motivational framing. Split into a 2-block "danger of liberal
tests" theme and a 10-block "generalization-error and CV-estimator definitions" theme (the
latter absorbing a Section-6 CV-variant scope caveat as a third distributed span — same
"what does this estimator cover" question as the Section-1 scope material).

## Conclusion section — recap vs. genuine content (user-directed, mid-task)

Initial draft folded the entire Section 6 conclusion (4 blocks) into a "paper recap and
recommended parameters" theme. User challenge: R5's precision half rules out recap content —
does the conclusion contain any need not already answered elsewhere? Content-diffed each
conclusion block against already-assigned themes: the opening paragraph restates the
motivation theme's danger argument verbatim; the theoretical-contribution paragraph restates
the no-unbiased-estimator and two-estimators themes; the simulation-results sentence restates
the size/power-comparison theme; and even the seemingly-actionable "J around 15, M between 5
and 10, conservative-Z-vs-corrected-resampled-t" recommendation sentence turned out to
near-verbatim restate content already present in the J-choice and M-choice themes (the
procedure-choice guidance is a direct duplicate of a sentence already in the J-choice theme).
Net: the entire conclusion-recap "theme" was dropped and its four blocks moved to
`unassigned`, each with its own duplication-source reasoning — only the genuinely
non-duplicated CV-variant scope sentence (last conclusion paragraph, about overlapping vs.
disjoint test sets) survived, relocated as a distributed span of the CV-estimator-definitions
theme instead of staying in a standalone conclusion theme.

A secondary finding during this pass: the validator's `check_block_coverage` ties
`unassigned` status to the whole Pass A block id, not to individual resplit sub-spans — a
resplit block cannot have one half covered by a theme and the other half unassigned in the
same submission. This constrained the conclusion-recap resolution to an all-or-nothing
per-block choice (no partial resplit-then-unassign), which is what led to diffing the
recommendation sentence's content rather than mechanically splitting it at its blank line.

## Verification performed

`eval/scripts/validate_pass_b.py` run against the Pass A JSON and the source markdown:
schema, span-bounds, intra-theme overlap, trash-disjointness, resplit-boundary (n/a, zero
resplits), full block-coverage (all 113 Pass A blocks either covered by exactly one theme's
spans or listed in `unassigned`), soft-member containment, the 2.0 blocks/theme floor, and
the zero-tolerance proof-label gate all passed: `OK validate_pass_b: 15 themes, 0 resplits, 3
unassigned blocks`. Not verified: no semantic/LLM cross-check of theme-need wording quality
beyond the reasoning recorded per theme above and the two user-directed corrections.
