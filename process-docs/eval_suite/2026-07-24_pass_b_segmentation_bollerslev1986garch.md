# Pass B Theme Formation Run — Bollerslev1986GARCH.md (2026-07-24)

Applied `eval/queries/segmentation_prompt_pass_b.md` (R5-R10) to the 45-block Pass A output
for `data/documents/trading-reference/Bollerslev1986GARCH.md` (528 lines). Run by a fresh
worker with no Pass A segmentation history in context, per the pipeline's cross-model-check
design. Output: `eval/queries/pass_b_runs/Bollerslev1986GARCH.pass_b.json` — 8 themes, 0
resplits, 1 unassigned block, 2 soft-membership blocks.

## Split test (R6-3) firings

Two cases where section-adjacent blocks were kept as separate themes rather than merged:
- Model definition (background + section 2 formal spec) vs. the wide-sense stationarity
  theorem + its appendix proof — "what is GARCH" and "under what condition is it stationary,
  proven how" read as two distinct single-search questions even though Theorem 1's statement
  physically sits inside the definition section.
- GARCH(1,1) moment-existence (Theorem 2, kurtosis, its appendix proof) vs. mean/median lag
  of the conditional variance equation — adjacent in section 3, but "when do higher moments
  exist" and "how long is the memory of the variance equation" are separate practitioner
  questions.

One candidate rejected: the BHHH iterative algorithm block contains an internal blank line
that could separate "algorithm mechanics" from "asymptotic consistency/normality of the
estimator" — kept as one estimation theme since a practitioner asking "how do you estimate
GARCH by ML" wants both the procedure and its justification together.

## Distributed themes (R7)

Four of the eight themes are non-adjacent, each justified by the same pattern the rule
anticipates (method section + appendix, or method + empirical application):
- Stationarity theorem statement (section 2) + full proof (Appendix A.1, itself fragmented
  into three spans by two single-character conversion-residue trash lines from the PDF OCR).
- Moment-existence theorem (section 3) + a footnote generalizing the fourth-moment condition
  to GARCH(1,2)/GARCH(2,1) (section 4) + proof (Appendix A.2).
- Mean/median lag formulas (section 3) + their empirical comparison across three fitted
  models (section 7).
- ACF/PACF diagnostic discussion (section 4), interrupted mid-section by the fourth-moment
  footnote above, which belongs to the moment-existence theme instead.

## Soft membership (R8)

- The stationarity theorem statement is core to the stationarity theme but also serves as
  contextual overview content inside the model-definition theme — flagged in both
  directions.
- One Pass A block (median-lag formula, 145-152) textually straddles two needs: it ends
  mid-paragraph with a fourth-moment-existence clause that sets up the moment-existence
  theme's kurtosis formulas. No blank line separates the two clauses (checked against the
  source), so R9 forbids a resplit here — resolved via soft membership instead, assigning
  the block to both the lag theme and the moment-existence theme.

## Unassigned content

One Pass A block (the paper's roadmap-by-section sentence, 2 lines) was left unassigned:
it is purely navigational meta-text about the paper's own structure, not itself an answer to
any realistic practitioner search question, so including it in a theme would violate the
"only" (precision) half of R5.

## Trash-driven span fragmentation (not a thematic signal)

Two themes reach four spans not because of genuine thematic distribution but because Pass A
trash (OCR conversion-residue characters, figure-caption stubs) sits inside what would
otherwise be one contiguous region: the stationarity-proof theme (Appendix A.1) and the
empirical-example theme (section 7, three figure captions plus the lag-comparison sentence
carved out for the separate lag theme). Distinguishing this from genuine R7 distribution
matters for reading the region count against the "~3-4 regions per need" calibration anchor.

## Verification performed

A throwaway python script (validate_pass_b_bollerslev.py) checked: JSON schema shape;
every span within 1-528; no span overlap within a single theme; every theme span disjoint
from all 9 Pass A trash spans; every one of the 44 assignable Pass A blocks contained in at
least one theme's spans (or explicitly the one unassigned block); soft-membership blocks
detected as multi-theme by the coverage check matched the two flagged in the output JSON.
Not verified: no semantic/LLM cross-check beyond the reasoning recorded per theme above —
this is a single fresh-worker pass, not adjudicated against a second Pass B run.
