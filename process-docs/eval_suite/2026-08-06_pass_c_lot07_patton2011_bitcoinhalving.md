# Pass C Theme Summaries — lot07: Patton2011VolatilityForecastImperfectProxies, BitcoinHalvingCycleVolatilityMSGARCH (2026-08-06)

Fresh-worker Pass C over two documents' Pass B spans (spans-only input at
`/tmp/pass_c_inputs/<doc>.spans.json` — no need sentences or labels, need derived
fresh from each theme's passage text via line spans into the source `.md`, no read
of any pass_b file). HARD STOP honored this session: read both spans files and
source passages, reported a per-document per-theme plan (primary_concept + need
gist + sub_concepts) in chat, and went idle until the orchestrator's explicit "Go"
before writing any deliverable JSON.

## Patton2011VolatilityForecastImperfectProxies.md (8 themes)

Output: `eval/queries/pass_c_runs/Patton2011VolatilityForecastImperfectProxies.pass_c.json`
— 8 summaries, word budget 61-75 (of the 60-90 range).

Themes trace: the robust-loss-function definition and the necessary condition for a
noisy-proxy ranking to match the true-variance ranking (t01), the standard menu of
loss functions (MSE, QLIKE, MAE and their variants) evaluated for bias when the
squared return is the proxy (t02), realized volatility and the intraday range as
more efficient alternative proxies and how fast distortion shrinks with sampling
frequency (t03), the general necessary-and-sufficient functional form for robust
loss functions and its derivation from the forecast-optimality condition (t04), the
uniqueness of MSE and QLIKE among loss functions restricted to depend only on the
(standardized) forecast error (t05), the homogeneous-and-robust subset invariant to
rescaling of units and its one-parameter family (t06), the empirical application
comparing two volatility forecasting models via a Diebold-Mariano test across
several proxy/loss-shape choices (t07), and the general latent-variable-forecasting
motivation bracketing the paper (unobservable-variable forecast evaluation, with
volatility as the leading case) (t08).

t01 and t04 share the primary_concept "robust loss function" but differ in
situation: t01 is the definition + necessary condition (does a candidate loss
function preserve ranking), t04 is the constructive derivation of the entire
necessary-and-sufficient class (proof-heavy span, framed as "under what conditions
does the guarantee hold, derived how" per the anti-lookup NEED LEVEL rule rather
than "wants the proof of X").

## BitcoinHalvingCycleVolatilityMSGARCH.md (16 themes)

Output: `eval/queries/pass_c_runs/BitcoinHalvingCycleVolatilityMSGARCH.pass_c.json`
— 16 summaries, word budget 60-73.

Themes trace: the halving-cycle bull/bear/stagnation structure (t01), the
correlation condition linking halving-driven price independence to safe-haven/hedge
classification (t02), institutional/industrial adoption context (t03), value-at-risk
sensitivity to ignored regime changes (t04), the Bitcoin-vs-gold safe-haven/hedge
debate (t05), the daily-return dataset and sample-period split (t06), the
quantile-threshold hedge regression specification (t07), its threshold
regime-switching extension (t08), the Markov-switching GARCH/GJR model
specification and estimation (t09), out-of-sample VaR backtesting via coverage
tests (t10), descriptive statistics and stationarity testing of the return series
(t11), empirical hedge-effectiveness results across pre/post-crash periods (t12),
asset-correlation shifts with the stock market (t13), the regime-change test setup
over the full Bitcoin price history (t14), regime persistence and goodness-of-fit
across fitted specifications (t15), and the interpretation of what the estimated
regimes actually track — volatility level versus halving-cycle stage (t16).

"safe haven asset" (t02, t05) and "regime change" (t14, t16) are each reused as
primary_concept across two themes; situations were kept distinct per the pipeline
rule (t02 = correlation condition as classification test; t05 = Bitcoin-vs-gold
literature debate; t14 = test setup over the full sample; t16 = interpreting what
the fitted regimes correspond to).

## Validator mechanics reconfirmed / newly learned this session

- **Leading-clause extraction is comma-conjunction-based, not sentence-based**:
  `leading_clause` truncates `information_need` at the first `, and/but/or` or
  `.`/`;`, not at the end of the first full sentence. Two draft summaries
  (Patton t08 "latent variable forecasting", Bitcoin t01 "Bitcoin halving cycle")
  had the primary_concept's content words placed AFTER an early `, and`/`, or`
  break (e.g. a parenthetical list "inflation, GDP growth, or default probability
  forecasting" truncated the scanned clause before "latent variable" ever
  appeared). Fix: front-load the exact primary_concept phrase into the sentence
  before any list/parenthetical that contains a bare `, and/or/but`. Caught by
  running `validate_pass_c.py`, not by static re-reading — the failure message
  reports the exact truncated clause the validator scanned, which made the fix
  immediate.
- **Digits and hyphens in concept slots**: kept `field`/`primary_concept`/
  `sub_concepts` fully hyphen-free per this session's explicit instruction (e.g.
  "Diebold Mariano test" not "Diebold-Mariano test", "regime specific
  coefficients" not "regime-specific"), while `information_need` prose was also
  written hyphen-free throughout (not just where required) to avoid any risk of
  tripping the structure-reference literal-token scan on a stray compound.
- **Zero digits anywhere** — number words ("two regime", "single regime") were
  used freely for structural/cardinality description; no numerals appeared in
  either output, so the "digits banned except model-order parentheticals in
  sub_concepts" exception was never exercised in this lot.
- **Both documents passed `validate_pass_c` on the second run** — the two
  leading-clause failures above were the only validator failures; all other
  checks (primary_concept membership, word budget, digit/hyphen/structure-ban
  scans, lookup-phrasing ban) passed on the first attempt for all 24 summaries
  combined.
