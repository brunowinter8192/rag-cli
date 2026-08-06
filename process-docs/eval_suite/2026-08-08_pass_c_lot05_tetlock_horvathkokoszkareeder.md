# Pass C Theme Summaries — lot05: Tetlock2007GivingContentInvestorSentiment, HorvathKokoszkaReeder2013MeanFunctionalTimeSeriesTwoSample (2026-08-08)

Fresh-worker Pass C over two documents' Pass B spans (spans-only input, no need
sentences or labels — need derived fresh from each theme's passage text via line
spans into the source `.md`). The two documents contrast sharply in register: Tetlock
is a fully applied empirical-finance paper (VAR regressions, robustness checks, a
trading-strategy backtest, no theorems), while Horvath-Kokoszka-Reeder is proof-heavy
functional-time-series theory (four of fifteen themes are theorem statements with
accompanying proof spans pulled in from the paper's separate proofs section).

## Tetlock2007GivingContentInvestorSentiment.md (15 themes)

Output: `eval/queries/pass_c_runs/Tetlock2007GivingContentInvestorSentiment.pass_c.json`
— 15 summaries, word budget 62-77 (of the 60-90 range). First `validate_pass_c` run
failed on five themes (t03, t05, t07, t11, t12) landing 55-59 words, 1-5 words short;
fixed by extending each information_need with one additional qualifying clause drawn
from the same passage (e.g. t05 added "bid ask bounce" as a named microstructure
source already present in the text), not by padding sub_concepts. Second run: OK.

Themes trace the paper's argument: background precedent linking media/communication
content to market activity (t01), the noise-trader/arbitrageur theoretical framework
and its rival information-based and stale-information accounts (t02), the General
Inquirer dictionary-based content-analysis methodology including word-sense
disambiguation (t03), principal-components extraction of the pessimism factor and its
year-by-year stability (t04), the VAR control-variable specification (t05), the core
Granger-causality return-forecasting test (t06), the reverse-direction feedback-trading
test (t07), the volume-forecasting test distinguishing transaction-cost from
liquidity/noise-disagreement accounts (t08), the small-cap-concentration test via the
size premium (t09), timing-window robustness checks (t10), the bull-market-era
structural-break test (t11), the semiparametric/lowess nonlinearity check (t12), the
trading-strategy profitability-net-of-costs assessment (t13), the factor-decomposition
validation of the pessimism proxy against its constituent word categories (t14), and
the risk-return-tradeoff alternative explanation via conditional volatility (t15).

Deliberate primary_concept fix mid-session: t09's initial draft used the paper's own
"small-minus-big factor" phrasing as primary_concept; on review this was judged too
close to the paper-specific Fama-French label rather than the general field concept a
practitioner would search on, so primary_concept was changed to "size premium" with
"SMB factor" demoted to a sub_concept hook only.

## HorvathKokoszkaReeder2013MeanFunctionalTimeSeriesTwoSample.md (15 themes)

Output:
`eval/queries/pass_c_runs/HorvathKokoszkaReeder2013MeanFunctionalTimeSeriesTwoSample.pass_c.json`
— 15 summaries, word budget 61-79. First `validate_pass_c` run failed on three themes
(t04, t06, t10) landing 54-59 words; fixed the same way, by extending
information_need with one additional passage-grounded clause (e.g. t06 added
"conditions on the smoothing bandwidth and the underlying dependence structure").
Second run: OK.

Themes trace: the functional-time-series data structure and its temporal-dependence
scope (t01), the long-run-variance estimation problem for dependent curves and its
positioning against prior two-sample covariance-operator work (t02), the weak
dependence condition (m-dependent approximation) and its proof for a general nonlinear
moving-average error sequence (t03), the central limit theorem for the dependent
functional sample mean (t04), the kernel/bandwidth construction of the long-run
covariance kernel estimator (t05), the consistency proof for that estimator (t06), the
two-sample mean-equality test statistic and its asymptotic null/alternative
distribution (t07), eigenfunction-based dimension reduction for a computable test
statistic (t08), the exact asymptotic null distributions of the two competing test
statistics (t09), the test-consistency condition against the alternative (t10), the
numerical implementation via basis expansion and a finite matrix eigenvalue problem
(t11), the finite-sample size/power simulation study (t12), the independent-curve-
sample (medfly) empirical application (t13), the dependent-financial-curve
(Eurodollar term-structure) empirical application (t14), and the practical guidance on
choosing between the two test statistics and the dimension-reduction parameter (t15).

Four themes (t03, t04, t06, t09) are proof-bearing theorem spans (each theme's line
spans pull in both the theorem statement from the main text and its proof from the
paper's separate proofs section at the end of the document); each was framed as
"under what conditions does the guarantee hold, derived/proved how" rather than an
artifact-lookup ("wants the proof of Theorem X"), and all theorem/lemma numeric labels
(Theorem 2.1, 3.3, etc.) and internal symbols were generalized away (e.g. "central
limit theorem", "consistency", "asymptotic null distribution").

Primary_concept collision avoided deliberately for t13/t14: both are real-data
"apply the test" themes: differentiated by primary_concept naming the data regime
itself (independent curve samples vs dependent financial curve data) rather than by
a shared "empirical application" concept, so the two summaries remain distinguishable
to a query author who never sees which dataset is biological vs financial.

## Validator mechanics reconfirmed this session

- **Word budget**: 8 of 30 total drafts (5 in Tetlock, 3 in Horvath-Kokoszka-Reeder)
  landed 1-5 words under the 60-90 band on the first pass; the initial per-theme word
  counts had been hand-estimated rather than machine-counted before writing, unlike
  the lot04 session's proactive `count_words` simulation — the fix pattern (extend
  information_need with a passage-grounded clause) matched lot04's approach exactly.
- **Hyphen-free field-term normalization**: applied broadly across both documents on
  reviewer instruction — "long run variance", "long run covariance kernel", "bid ask
  spread", "look ahead bias", "risk return tradeoff", "heteroskedasticity robust
  standard errors", "Karhunen Loeve expansion", "two sample" (mean testing / problem)
  all written hyphen-free; intrinsic-hyphen terms (m-dependent approximation,
  chi-square distribution, P-value stability) were kept hyphenated only inside
  sub_concepts, never as a primary_concept or in an information_need's first clause.
- **Primary_concept re-labeling**: two cases where the first drafted primary_concept
  echoed the source paper's own named-factor phrasing too closely (Tetlock's
  "small-minus-big factor") were caught and generalized to the underlying field
  concept ("size premium") before the deliverable was finalized — corroborates the
  lot04 finding that reviewer-driven terminology passes catch author-phrasing leakage
  that a single-pass R13 self-check can miss.
- **Structure-reference and digit bans**: no numeral characters, table/section/
  appendix references, or theorem/equation numeric labels leaked into any of the 30
  summaries; both documents' heavy numeric-results content (Tetlock's basis-point
  coefficients and p-values; Horvath-Kokoszka-Reeder's simulation power tables and
  P-value tables) was excluded by framing answer_type/information_need around the
  kind of test or condition, never the reported magnitude.

Iteration pattern: both documents required exactly one validator-failure round (word
budget only — no digit, structure-reference, lookup-phrasing, or primary_concept-
membership failures on either run) before `validate_pass_c.py` passed OK against both
Pass B files.
