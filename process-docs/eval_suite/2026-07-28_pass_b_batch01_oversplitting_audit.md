# Pass B batch01 over-splitting audit (20 papers)

Dated: 2026-07-28

## Trigger

Batch01's 20 Pass B artifacts showed a blocks/theme ratio of ~1.0-1.3 vs. the Bollerslev1986GARCH
calibration run's 5.6 (8 themes / 45 blocks). A review pass on a Hamilton1989 sample confirmed two
systematic over-splitting patterns rather than legitimate fine structure. This session ran a
targeted two-lens audit of all 20 batch01 Pass B artifacts (not Bollerslev) against both patterns
and fixed every document where a lens fired.

## The two lenses

1. **Conclusion-recap themes violating R5/R6.** A "Conclusions" theme whose need reads as "compact
   summary of the paper's contribution" and whose span recaps topics already covered by earlier
   themes is R4 `abstract_summary` trash that Pass A missed; Pass B cannot reclassify trash, so the
   fix is theme removal + `unassigned` entry (reason: `conclusion-recap, missed abstract_summary
   trash`), not a resplit.
2. **Setup/result splits of one need (R6-3).** Two adjacent themes where one is a method's setup
   (recursion, algorithm, simulation design, empirical setup) and the next is that same method's
   result/answer/table are one theme when a realistic single question needs both halves together
   (Bollerslev precedent: BHHH mechanics + asymptotic justification merged into one estimation
   theme). Fix: merge spans, one need sentence covering both halves.

## Lens-1 decision method: content-graded, not label-graded

Every "Conclusions"/"Concluding remarks" themed span across the 20 documents was read in full and
graded on two axes: (a) does it recap topics already established as their own themes, and (b) does
it carry a genuine standalone, quantified, or actionable claim not stated elsewhere. Label alone was
not a reliable signal — several themes explicitly needed as "compact summary of the paper's
contribution" (near-verbatim trash phrasing) were confirmed trash by content; others labeled
identically carried real content and were kept.

12 of 20 documents fired: AlizadehBrandtDiebold2002, BaiPerron2003, BengioGrandvalet2004, Chou2005,
ChuStinchcombeWhite1996, Cont2001, DaEngelbergGao2011, Hamilton1989 (the confirmed calibration
case), HansenLundeNason2011, NadeauBengio2003, Patton2011, StaricaGranger2005.

8 of 20 kept their conclusion theme, on content grounds:
- **AndersenBollerslevDieboldLabys2003** (t13, "Conclusions and future research directions"): the
  final future-research paragraph derives a specific, actionable Cholesky-factor parameterization
  for guaranteeing positive-definite multivariate realized-covariance forecasts — a genuine
  technical proposal, not a recap or a vague pointer list.
- **BitcoinHalvingCycleVolatilityMSGARCH** (t15): contains explicit practitioner-actionable
  recommendations not stated elsewhere ("investors should not invest in Bitcoin for hedge
  properties"; "the Markov-switching model remains recommended over single-regime counterparts")
  and a causal synthesis (regime changes tied to volatility dynamics, not halving-cycle stages)
  distinct from the earlier regime-analysis-mechanics theme.
- **Corsi2009** (t08): the opening paragraph is a genuine HAR-vs-ARFIMA practical-adoption tradeoff
  (simplicity/robustness on a moving window vs. cutoff-choice sensitivity) — a real "should I use
  HAR or ARFIMA" decision need, not a recap.
- **Tetlock2007** (t17): buried in an otherwise-recap conclusion is a specific quantified takeaway —
  a hypothetical zero-cost sentiment trading strategy yielding 7.3%/year, with an implementation-cost
  caveat — not present in any other theme.
- Chou2005's *separate* "Future research extensions" theme (t14, kept) vs. its "Forecast-comparison
  conclusion and CARR summary" theme (t13, fired): the predecessor had already split these two;
  the future-research half introduces genuinely new topics (robust range measures, joint
  price-range models) while the bottom-line-takeaway half purely recapped already-established
  results. This pairing showed the two content types can coexist in one document under different
  themes, reinforcing that the grading has to be per-span, not per-document.
- Engle1982ARCHInflation, HorvathKokoszkaReeder2013 never had a conclusion-shaped theme (both end
  in proofs/appendices) — nothing to grade.

## Lens-2 discovery method

Scanned all adjacent theme-label pairs for the setup→result/example shape (design/setup/definition
immediately followed by results/procedure/worked-example on the *same* method), then read the
underlying source span for every candidate before deciding. Two shapes were explicitly excluded
after inspection, both confirmed via source reading rather than assumed:

- **One-to-many shared setup, kept separate.** AndersenBollerslevDieboldLabys2003's "forecast
  evaluation setup" theme feeds two horizon-specific result themes (1-day, 10-day); Tetlock2007's
  VAR-design theme feeds four separate regression-result themes; NadeauBengio2003's simulation-design
  theme feeds three separate guidance themes (sizes/powers, choice of J, choice of M). A setup shared
  by multiple independently-searchable results mirrors Bollerslev's own kept-separate
  method-vs-application split (MLE theory theme stays distinct from the empirical application
  theme) rather than its BHHH-merge precedent — so these were left untouched.
- **Distinct methodological caveat, not a setup/result pair.** Cont2001's t09 (volatility-clustering
  evidence) and t10 ("How reliable are ACFs?") looked pair-shaped by label but t10 is a
  self-standing caveat about a widely-used tool (sample ACF reliability under heavy tails) that a
  practitioner could search independently of the volatility-clustering finding it happens to sit
  next to — kept separate.

10 of 20 documents fired: Hamilton1989 (t06/t07, the confirmed calibration case), Chou2005
(t09/t10, OOS forecast-eval setup + RMSE/MAE results), BaiPerron2003 (t02/t03, triangular-matrix
SSR concept + the DP algorithm it enables — genuinely one continuous method exposition, not a
theorem/proof pair), Corsi2009 (t05/t06, in-sample HAR(3) estimation + its own forecast-accuracy
diagnostics — mirrors Bollerslev's single all-inclusive empirical-case theme), InclanTiao1994
(t06/t07, the ICSS algorithm + a worked simulated-series walkthrough that explains the algorithm's
Step 3 in action — pedagogically inseparable from the algorithm itself), HansenLundeNason2011
(t06/t07, KLIC/effective-d.o.f. theory + the bootstrap procedure needed to actually compute it),
ChuStinchcombeWhite1996 (t12/t13, simulation design + the empirical size/first-hitting results it
produces), Patton2011 (t10/t11, IBM empirical setup + DMW ranking results), BengioGrandvalet2004
(t07/t08, bare notation setup that fails the standalone-search test on its own + the covariance-
structure lemma it exists only to support), AueGabrysHorvathKokoszka2009 (t04/t05, change-point
estimator definition + its own limit-distribution theorems — the source section is itself titled
as one topic, "Change-point estimator and its limit distribution").

## Explicitly out of scope, considered and rejected

Formal theorem-statement/proof splits in math-heavy appendices (e.g. AueGabrysHorvathKokoszka2009's
proof-of-Theorem-2.1/2.2 themes sitting far from their theorem statements) were considered against
the Bollerslev precedent (which *does* merge theorem+proof via distributed spans) but deliberately
left untouched: the audit's lens-2 definition, as given, is about a practitioner's realistic-need
setup→payoff split (recursion→answer, algorithm→worked-example, design→result), not a general
theorem/proof merging pass across the corpus. Extending to appendix-proof merging would be a
broader re-formation of the distributed-theme structure beyond the two named lenses.

## Outcome

15 of 20 batch01 artifacts changed (one or both lenses fired); 5 needed no change. Every changed
artifact was re-validated with `validate_pass_b.py` against its Pass A blocks and source document
(schema, span-bounds, trash-disjointness, block-coverage) — this is structural verification only,
not semantic re-confirmation of the keep/fire calls themselves. Blocks/theme ratio after the audit
still sits well below Bollerslev's 5.6 calibration across most documents; the audit targeted the two
confirmed patterns only and was explicitly not a from-scratch re-formation, so residual fine-grained
splitting (beyond these two lenses) was left as-is per scope.
