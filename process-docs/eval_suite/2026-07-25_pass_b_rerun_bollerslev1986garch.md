# Pass B Theme Formation Rerun — Bollerslev1986GARCH.md (2026-07-25)

Second independent Pass B pass over the same 45-block Pass A output for
`data/documents/trading-reference/Bollerslev1986GARCH.md` (528 lines), run by a fresh worker
with no Pass A or prior Pass B history in context — output overwrote
`eval/queries/pass_b_runs/Bollerslev1986GARCH.pass_b.json`: 8 themes, 0 resplits, 1 unassigned
block, 2 soft-membership blocks.

## Theme grouping

Sections map close to 1:1 with themes except section 3 (GARCH(1,1)), which splits on R6's
split test into a moment-existence theme (Theorem 2 + appendix proof) and a separate
lag/kurtosis-diagnostics theme (mean lag, median lag, fourth-moment/kurtosis formulas) — "is
my fitted model's k-th moment finite" and "what do the lag/kurtosis numbers say about
persistence and tail shape" read as two distinct single-search questions with no realistic
question needing their union.

## Distributed themes (R7)

Five of eight themes ended up non-adjacent, but three of those five are trash-gap artifacts
(figure captions, an author-acknowledgment footnote, OCR conversion-residue characters
sitting between otherwise-contiguous Pass A blocks) rather than genuine thematic
distribution:
- Introduction/motivation theme: split only by the acknowledgment footnote (lines 18-19).
- GARCH(1,1) lag-diagnostics theme: split only by the Fig. 1 caption stub.
- Empirical-example theme (four spans): split only by the Fig. 2/3/4 caption stubs.

Two are genuine R7 distribution — theorem statement (body) + formal proof (appendix), which
happen to also be trash-fragmented internally:
- GARCH(p,q) definition/stationarity theme: Theorem 1 statement (section 2) + Appendix A.1
  proof, the proof itself broken into three spans by two conversion-residue trash lines.
- GARCH(1,1) moment-existence theme: Theorem 2 statement (section 3) + Appendix A.2 proof.

## Soft membership (R8)

- The ARMA-type representation block (eq. 6-7, presented as an alternative GARCH
  parameterization in the definition section) is core to the definition/stationarity theme,
  but the paper explicitly reuses it ("It follows then immediately from (6) and (7)...") to
  derive the autocorrelation recursion in the ACF/PACF section — flagged as also relevant to
  that theme.
- A footnote generalizing the fourth-moment-existence condition to GARCH(1,2)/GARCH(2,1) is
  physically anchored in the ACF/PACF section (elaborating that section's finite-fourth-moment
  assumption) but conceptually extends the GARCH(1,1) moment-existence theorem — flagged as
  also relevant to that theme.

## Unassigned content — user-directed correction

Initial draft included the paper's section-by-section roadmap sentence (2 lines) inside the
introduction/motivation theme on the reasoning that it forms one continuous orientation
narrative with the surrounding motivation text. User correction: a roadmap sentence is purely
navigational meta-text about the paper's own structure, answers no practitioner information
need, and its inclusion violates R5's "only" (precision) half regardless of narrative
adjacency — moved to unassigned with that reasoning, theme span shortened accordingly. Net
effect: distinguishes "textually adjacent to a real need" from "itself part of the answer set"
as the operative test for R5 precision, not narrative continuity.

## Verification performed

A throwaway Python script (`/tmp/validate_pass_b.py`, not retained) checked: JSON parses;
every span within 1-528; no span overlap within a single theme; every theme span disjoint
from all 9 Pass A trash spans; every one of the 44 assignable Pass A blocks contained in
exactly one theme's spans, with the 45th (roadmap sentence) confirmed present only in the
unassigned list; soft-membership blocks confirmed to lie within their home theme's own spans.
No resplits were needed this run, so the blank-line boundary check (R9) had no cases to
verify beyond confirming the `resplits` array is empty. Not verified: no semantic/LLM
cross-check of theme-need quality beyond the reasoning recorded per theme above.
