# Pass C Theme Summaries — lot04: Engle1982ARCHInflation, ChuStinchcombeWhite1996MonitoringStructuralChange (2026-08-08)

Fresh-worker Pass C over two documents' Pass B spans (spans-only input, no need
sentences or labels — need derived fresh from each theme's passage text via line
spans into the source `.md`). Both documents are proof-heavy (theorem/lemma/corollary
structure), unlike the applied-estimator lots before it — this session's main open
question was how the anti-lookup case-match framing holds up against dense theoretical
content, not just empirical-method themes.

## Engle1982ARCHInflation.md (14 themes)

Output: `eval/queries/pass_c_runs/Engle1982ARCHInflation.pass_c.json` — 14
summaries, word budget 60-75 (of the 60-90 range), `validate_pass_c` OK on first run.

Themes trace the paper's structure: motivation and formal ARCH specification versus
exogenous-variable and bilinear heteroscedasticity (t01), cross-domain motivating
examples — forecasting, portfolio theory, misspecification (t02), likelihood-function
and information-matrix derivation (t03), moment-existence conditions for a first-order
process (t04), covariance-stationarity conditions and alternative variance functional
forms for the general-order process (t05), symmetry/regularity conditions (t06),
block-diagonality of the information matrix separating mean and variance estimation
(t07), the scoring-algorithm estimation procedure (t08), relative efficiency of maximum
likelihood over ordinary least squares (t09), the Lagrange-multiplier test for the
effect (t10), the applied inflation price-equation setup (t11), variance-function order
selection for the inflation model (t12), empirical maximum-likelihood-versus-ordinary-
least-squares coefficient comparison (t13), and outlier-diagnostic evaluation of the
fitted forecast variances (t14).

Three theme pairs share closely related concepts and were deliberately differentiated
by situation rather than by anchor-term substitution: t01 ("autoregressive conditional
heteroscedasticity", definitional/comparative framing) vs t02 ("heteroscedasticity",
cross-domain motivation framing); t09 ("relative efficiency of maximum likelihood
estimation", theoretical efficiency-gain derivation) vs t13 ("maximum likelihood versus
ordinary least squares", empirical fitted-coefficient comparison); t04 ("moment
existence conditions", first-order process) vs t05 ("covariance stationarity
conditions", general-order process plus alternative functional forms).

## ChuStinchcombeWhite1996MonitoringStructuralChange.md (15 themes)

Output:
`eval/queries/pass_c_runs/ChuStinchcombeWhite1996MonitoringStructuralChange.pass_c.json`
— 15 summaries, word budget 70-81, `validate_pass_c` OK on first run.

Themes trace: motivation — why repeated retrospective break tests inflate type-one
error under the law of iterated logarithm (t01), the general monitoring-scheme
framework — detector, threshold, stopping time (t02), the CUSUM procedure and its
practical boundary choice (t03), regularity conditions on the monitoring boundary
underlying the invariance-principle extension (t04), convergence in distribution of
hitting times under a functional central limit theorem (t05), the core boundary-
crossing-probability approximation theorem (t06), the fluctuation-monitoring procedure
converging to a Brownian bridge (t07), consistency of fluctuation monitoring under a
permanent parameter shift (t08), calibration of the historical window length in the
univariate special case (t09), the boundary's relation to Wald sequential testing and
its optimality limits (t10), classification within the partially-sequential two-sample
testing literature (t11), simulated empirical-size validation (t12), simulated
detection-delay/average-run-length performance (t13), sensitivity of detection delay to
break-point timing and the underlying growing-variance tradeoff (t14), and the
break-point location procedure via the maximum likelihood-ratio statistic (t15).

Four themes (t04, t05, t06, t08) are pure theorem/lemma/proof spans; each was framed as
"under what conditions does the guarantee hold, derived how" per the proof-heavy-span
guidance carried over from the review-round feedback on prior lots, rather than as an
artifact-lookup ("wants the proof of Lemma X").

## Validator mechanics reconfirmed this session

- **Word budget**: two of 29 total drafts (Engle t04, t06) landed 3-4 words short on
  the first pass — fixed by extending information_need with an additional clause
  drawn directly from the passage's own derivation logic (e.g. adding "why the odd
  moments vanish by symmetry" to t04) rather than padding sub_concepts. All other
  27 drafts cleared the 60-90 band on the first pass, given upfront word-count
  simulation against the validator's own `count_words` before writing the
  deliverable files.
- **Primary-concept anchoring** (`check_primary_concept_leads_need`): zero failures
  this round — every information_need was drafted with the primary_concept phrase
  placed verbatim at the start of the first clause (before any ", and/but/or" or
  sentence break), which trivially satisfies the majority-stem-overlap check and
  sidesteps the synonym-substitution failure mode identified in the lot03 session.
- **Digit-free discipline applied proactively**: word-numbers ("first-order",
  "general-order") used freely since the digit ban only targets literal numeral
  characters, not spelled-out ordinals; no numeric results, chi-square statistics,
  table coefficients, or simulation sample sizes (m = 25/50/100/..., a-squared
  thresholds) from either source document leaked into any field.
- **Abbreviation-consistency correction (review-round feedback)**: reviewer flagged
  that sub_concepts may use field abbreviations (MLE, LM test, FCLT) but the
  primary_concept and the information_need's first clause must stay spelled-out
  where the primary_concept itself is spelled out, to keep the stem-match check
  meaningful rather than accidentally passing on an acronym-only overlap. Both
  drafts already used fully spelled-out primary_concept values and first clauses
  throughout (no abbreviations had been introduced), so no edit was required —
  verified programmatically by scanning every (primary_concept, sub_concepts) pair
  for acronym-only entries before the final write.
- **Hyphen guidance (review-round feedback)**: reviewer also flagged
  "detection-delay sensitivity" (t14, doc2) as a candidate hyphenated term-merge;
  the drafted primary_concept was already "sensitivity of detection delay to break
  timing" (unhyphenated, spelled out) — the hyphenated form only appeared in an
  informal planning-table abbreviation shown to the reviewer, not in the actual
  JSON value, so again no source edit was required.
- **R13 private-model-label / author-citation removal**: Engle's own citations
  (McNees, Klein, Khan, Friedman, Lucas) generalized to "ad hoc variance proxies" /
  "macroeconomic theory"; Chu-Stinchcombe-White's citations (Segen and Sanderson,
  Switzer, Robbins, Nikiforov, Basseville, Wald) and internal symbol labels
  (Ẑn, Q^m_n) generalized to "monitoring boundary" / "fluctuation monitoring
  procedure"; neither paper coins a private model acronym analogous to Corsi's
  "HAR-RV" from the lot03 session, so no acronym-rewrite case arose here.

Iteration pattern: both documents converged in one validator round each — all
mechanical checks (digits, structure-reference words, primary_concept membership,
primary_concept anchoring, lookup phrasing, sub_concepts count, word budget) were
pre-checked programmatically against the validator's own check functions before the
deliverable files were written, so the actual `validate_pass_c.py` invocation against
each Pass B file passed on the first and only run for both documents.
