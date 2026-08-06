# Pass B Theme Formation — lot06: Engle1982ARCHInflation, ChuStinchcombeWhite1996MonitoringStructuralChange (2026-08-06)

Fresh-worker Pass B over two documents' Pass A output, run one after the other.

## Engle1982ARCHInflation.md (62 blocks, 5 trash spans)

Output: `eval/queries/pass_b_runs/Engle1982ARCHInflation.pass_b.json`
— 14 themes, 0 resplits, 1 unassigned block, 61/62 assignable blocks covered —
4.36 blocks/theme (below the Bollerslev1986GARCH calibration anchor of 5.6, but well above
the 2.0 floor; the paper's short motivation/results paragraphs naturally block finer).

Themes track the paper's arc: ARCH formulation vs. alternative heteroscedasticity models,
motivating applications, the general likelihood derivation, three theorem+proof pairs
(first-order moment existence/fat tails, general stationarity + alternative functional
forms, symmetry/regularity + Theorem 3), the regression-model ML theory culminating in
Theorem 4's block-diagonality result, the scoring-algorithm implementation, MLE-vs-OLS
efficiency, the LM test for ARCH effects, and four empirical-application themes for the UK
inflation study. 4 of 14 themes are distributed, all theorem/lemma-statement + appendix-proof
merges per R7b.

Split-test applied: the empirical application (§9, originally one 15-block candidate
covering price-equation spec, ARCH-order selection, ML-vs-OLS results, and
variance/outlier findings) was split 4-way — baseline spec+diagnostics, ARCH(4)
declining-weight model selection, ML tables I/II/III comparison, and variance/outlier
results each answer an independently-searchable question, and no realistic single question
needs their union. t01 (8 blocks: 4 alternative-heteroscedasticity examples + ARCH
definition + regression formalization) was considered for splitting the straw-man examples
out but kept merged — none of the individual alternative-model examples is ever searched
standalone (R6 test 2), all four serve one "why is ARCH formulated this way" need. t07
(regression ML theory, 8 blocks including Theorem 4) was considered splitting off the
OLS-consistency paragraph (b027) but kept merged — too short/context-dependent to stand
alone.

Soft membership: symmetry/regularity definitions (b023, b024; home theme t06, verifying
Theorem 3) also serve t07 (Theorem 4 explicitly requires the model be "symmetric and
regular" and reuses both conditions in its proof).

Unassigned: b057, the closing sentence of §9 ("this example illustrates ARCH's
usefulness...") — pure recap of results already covered by t13/t14, no standalone need
(R5 precision precedent).

## ChuStinchcombeWhite1996MonitoringStructuralChange.md (86 blocks, 5 trash spans)

Output: `eval/queries/pass_b_runs/ChuStinchcombeWhite1996MonitoringStructuralChange.pass_b.json`
— 15 themes, 0 resplits, 1 unassigned block, 85/86 assignable blocks covered —
5.67 blocks/theme (close to the Bollerslev1986GARCH calibration anchor of 5.6).

Themes: intro/motivation for real-time monitoring, the shared regression-stability
framework, CUSUM construction+calibration, the regular-boundary-function/Lemma 3.1-3.2
machinery, the FCLT boundary-crossing convergence theorems (3.3/3.4), computing crossing
probabilities via Theorem A + the two closed-form boundaries (7)/(8), FL detector
construction+Corollary 3.6, FL's power-one consistency (Theorem 3.7), the univariate FL
specialization/choice-of-m, FL's relation to Wald's SPRT and the optimality question,
FL's relation to Switzer's partially-sequential two-sample tests, and four Monte Carlo
simulation themes (empirical size, detection-timing/ARL-MRL, late-break robustness, and
break-point-location). 8 of 15 themes are distributed: six are theorem/lemma/corollary
statement + appendix-proof merges (R7b), one splits only on an intervening trash span
(navigation metadata), and one (FL-vs-Wald-SPRT-optimality) merges the §3.4 Discussion's
optimality analysis with the §5 Concluding Remarks' restatement of the same unresolved
open question — the intro-poses/conclusion-echoes pattern applied to an unresolved rather
than a resolved question.

Split-test applied twice, both matching the discipline the batch01 diagnosis found missing:
- §3.4 Discussion (originally one 7-block candidate) was split 3-way into univariate
  specialization/choice-of-m, Wald-SPRT-optimality relation, and the Switzer
  partially-sequential-two-sample-test relation — three independently searchable
  questions, confirmed by re-reading each sub-paragraph's citations and claims separately.
  The Switzer theme (t11) is only 1 block but passes the standalone-search test — it is a
  substantive citation-backed technical point (why Switzer's stopping rule doesn't fit the
  paper's costless-sampling-under-null assumption), not a bare formula/fact.
- §4 Simulations (originally one 11-block candidate) was split 4-way into empirical size,
  detection-timing (ARL/MRL), late-break robustness/boundary-growth tradeoff, and
  break-point-location estimation. t14 (late-break robustness) is thin (2 blocks, 4 lines
  total split across the document by an intervening Table III) but passes the
  standalone-search test as a real, distinct robustness question ("why is detection slower
  for late breaks") separate from the ARL/MRL headline result and from break-point
  estimation.
- Two merge candidates were considered and kept: CUSUM detector-definition (§2.2) +
  Corollary 3.5 application (§3.2), and FL detector construction (§3.3) + Corollary 3.6 —
  in both cases implementing the procedure requires both halves (construction and the final
  calibrated formula), so no realistic single question separates them.

Soft membership: boundary functions (7)/(8) (b038; home theme t06, computing crossing
probabilities via Theorem A) also serve t03 (CUSUM/Corollary 3.5) and t07
(FL/Corollary 3.6), since both corollaries reuse the identical closed-form boundary.

Unassigned: b078, the Concluding Remarks' opening paragraph — pure recap of the two already-
covered monitoring procedures, no standalone need.

## Verification performed

`eval/scripts/validate_pass_b.py` run against each document's Pass A JSON and source
markdown: schema, span-bounds, intra-theme overlap, trash-disjointness, resplit-boundary
(n/a both docs, zero resplits), full block-coverage, soft-member containment, the 2.0
blocks/theme floor, and the zero-tolerance proof-label gate all passed on the first attempt
(no fix-and-rerun cycle needed) —
`OK validate_pass_b: 14 themes, 0 resplits, 1 unassigned blocks` (Engle1982) and
`OK validate_pass_b: 15 themes, 0 resplits, 1 unassigned blocks` (ChuStinchcombeWhite1996).
Not verified: no semantic/LLM cross-check of theme-need wording quality beyond the reasoning
recorded per theme above; Opus reviewed and approved the pre-write plan (two adjustments:
Doc2 theme ids renumbered to the t01-t15 schema pattern, and the FL-vs-Wald-SPRT
distributed_justification made to explicitly name the intro-poses/conclusion-restates
pattern) before the JSON was written.
