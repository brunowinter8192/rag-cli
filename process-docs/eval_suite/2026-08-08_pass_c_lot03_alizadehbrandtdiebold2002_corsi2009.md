# Pass C Theme Summaries — lot03: AlizadehBrandtDiebold2002RangeBasedStochasticVolatility, Corsi2009SimpleLongMemoryRealizedVolatility (2026-08-08)

Fresh-worker Pass C over two documents' Pass B spans (spans-only input, no need
sentences or labels — need derived fresh from each theme's passage text via line
spans into the source `.md`).

## AlizadehBrandtDiebold2002RangeBasedStochasticVolatility.md (17 themes)

Output: `eval/queries/pass_c_runs/AlizadehBrandtDiebold2002RangeBasedStochasticVolatility.pass_c.json`
— 17 summaries, word budget 60-70 (of the 60-90 range), `validate_pass_c` OK.

Themes trace the paper's structure: motivation for range-based estimation over
Gaussian QMLE with return proxies (t01), the continuous-time SV diffusion and
its AR(1) discretization (t02), the state-space/Kalman-filter QMLE setup
(t03), non-Gaussian properties of log absolute/squared returns as proxies
(t04), efficiency and near-normality of the log range proxy (t05), robustness
of the range to microstructure noise / bid-ask bounce vs realized volatility
(t06), Monte Carlo design (t07), finite-sample bias/RMSE comparison across
estimators (t08), Kalman-filter latent-volatility extraction accuracy (t09),
futures-vs-spot data-construction rationale (t10), empirical
persistence/autocorrelation comparison of proxies across five currencies
(t11), one-factor model fit and residual diagnostics (t12), two-factor model
and the persistence-parameter derivation linking one- and two-factor
estimates (t13), empirical verification of log-range normality (t14),
measurement-error masking of a second volatility factor (t15), structural
two-factor vs reduced-form fractionally-integrated long memory (t16), and
closing research directions — multivariate extension, comparison to realized
volatility (t17).

Same primary_concept anchored three different themes at different situations
by design (t01 vs t08: "Gaussian quasi maximum likelihood estimation" as
motivation-for-the-problem vs quantified finite-sample performance evidence;
t05 vs t11 vs t17: "price range" as analytical efficiency derivation vs
empirical cross-currency persistence comparison vs forward-looking extension
directions) — differentiation carried entirely by the information_need's
situational framing, per explicit review-round instruction, not by varying
the anchor term.

## Corsi2009SimpleLongMemoryRealizedVolatility.md (8 themes)

Output: `eval/queries/pass_c_runs/Corsi2009SimpleLongMemoryRealizedVolatility.pass_c.json`
— 8 summaries, word budget 60-69, `validate_pass_c` OK.

Themes trace: motivation — why short-memory GARCH/SV fail the persistence and
multiscaling stylized facts, alternative to fractional integration (t01), the
additive volatility-cascade derivation into a single autoregressive
specification (t02), simulation-based validation against real exchange-rate
stylized facts (t03), realized-volatility construction from tick data with
microstructure-noise handling and multi-horizon aggregation (t04), OLS
estimation with Newey-West correction and restriction testing against an
unrestricted higher-order autoregressive alternative (t05), in-sample
one-day-ahead forecast evaluation via a Mincer-Zarnowitz-style regression
(t06), out-of-sample multi-horizon forecast comparison against short-memory
and fractionally-integrated benchmarks (t07), and closing model extensions —
jump component, leverage effect, nonlinear transition, multivariate
generalization (t08).

## Validator mechanics reconfirmed this session

- **Word budget**: three of 25 total drafts (doc1 t06, t12; doc2 t08) landed
  1-2 words short on the first pass — fixed by appending a short trailing
  qualifier to information_need rather than padding sub_concepts (e.g. "...one
  estimator clearly dominates the other in practice").
- **Primary-concept anchoring** (`check_primary_concept_leads_need`): one
  failure this round — doc1 t14, primary_concept "log range" was not written
  into information_need's opening clause (drafted as "...theoretical near
  normal distribution of a volatility proxy...", generic paraphrase rather
  than the literal anchor term). Fixed by rewriting the clause to start "the
  log range's theoretical near normal distribution actually holds
  empirically...". Confirms the lot02-session finding: a synonym substitution
  for the anchor term (here "volatility proxy" standing in for "log range")
  does not satisfy the stem-match check even when contextually unambiguous.
- **Digit-free / no-hyphen-merge discipline applied proactively at draft
  time** (informed by lot01/lot02 prior sessions, so zero iteration needed on
  these this round): "HAR(3)", "AR(22)", "ARFIMA(5,d,0)" spelled out
  digit-free ("heterogeneous autoregressive model", "higher order
  autoregressive alternative", "ARFIMA"); proper-name and compound hyphens
  dropped (Ornstein Uhlenbeck process, Newey West correction, Mincer
  Zarnowitz regression, cash and carry relationship, bid ask bounce, quasi
  maximum likelihood estimation, F test, self similarity, long memory, short
  memory, out of sample, two factor / single factor).
- **R13 private-model-label removal**: Corsi's own coined name "HAR-RV"
  rephrased throughout as "heterogeneous autoregressive model" /
  "volatility cascade" (analogous to lot02's VAR-RV/VAR-ABS/AR-RV rewrites) —
  the practitioner test still rejects a paper's internal acronym for its own
  proposed model even where the acronym later became field-standard
  terminology, since a cold searcher approaching the passage fresh would not
  yet have that label.
- **primary_concept practitioner-test correction mid-session**: Corsi t08 was
  initially drafted with primary_concept "model extension" (fails R13 — not a
  term a practitioner types) and corrected to "jump component" (a real,
  field-owned search term) before the validator pass, per explicit review
  feedback; sub_concepts trimmed to 4 (below the "leverage effect", "nonlinear
  transition", "multivariate model" set) once "model extension" was dropped
  entirely rather than kept as a secondary sub_concept.

Iteration pattern: both documents converged in one validator round each after
the anchoring and word-budget fixes above (doc1: two failures, both fixed in
a single edit pass; doc2: passed on first validator run).
