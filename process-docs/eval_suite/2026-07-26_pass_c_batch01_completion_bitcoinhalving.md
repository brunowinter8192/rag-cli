# Pass C Batch01 Completion — BitcoinHalvingCycleVolatilityMSGARCH (2026-07-26)

Closed out batch01's Pass C run: a predecessor worker produced summaries for 19 of 20
documents before hitting its context limit; this session wrote the 15-theme summary for the
remaining document, `data/documents/trading-reference/BitcoinHalvingCycleVolatilityMSGARCH.md`,
against `eval/queries/prompts/summary_prompt_pass_c.md` (R11-R15). Input was the spans-only
filter output (`/tmp/pass_c_inputs/BitcoinHalvingCycleVolatilityMSGARCH.spans.json`), no Pass
B need sentences/labels — summary content was derived fresh from the raw passage text at each
span's line range. Output: `eval/queries/pass_c_runs/BitcoinHalvingCycleVolatilityMSGARCH.pass_c.json`,
15 summaries, `validate_pass_c.py` clean on first content pass after four rounds of fixes (see
below). batch01's Pass C phase is now 20/20 complete.

## Theme-to-content mapping

- t01: intro — halving-cycle stage definition (bull/bear/stagnation) + recurring event
  sequence + institutional/industrial adoption context.
- t02: implications section — regime-change motivation for Bitcoin volatility, VaR
  sensitivity, prior regime-switching GARCH findings, altcoin interdependence.
- t03: stated study objectives (safe-haven/hedge test + regime-change test) and scope vs.
  two prior studies.
- t04: literature — gold's non-uniform safe-haven effect across markets/crises.
- t05: literature — empirical hedge/safe-haven findings for gold and Bitcoin across studies.
- t06: literature — GARCH volatility-forecasting extensions (ML hybrids, multicollinearity
  fix), regime-aware VaR motivation.
- t07: dataset construction (assets, sources, sample split around the COVID crash).
- t08: Baur-McDermott safe-haven/hedge regression framework + quantile-dummy specification +
  classification table.
- t09: MSGARCH model specification, expected-duration formula, GARCH/GJR variance equations,
  estimation (MLE, AIC/BIC) and VaR-backtesting setup.
- t10: results-section roadmap (thin span, 8 lines — see Gotcha below).
- t11: descriptive statistics / stationarity for the 5-asset pre-COVID dataset.
- t12: safe-haven/hedge empirical results, pre- vs. post-crash, tied to correlation shift.
- t13: descriptive statistics / stationarity for the extended Bitcoin-only regime dataset.
- t14: in-sample/out-of-sample regime-switching vs. single-regime model comparison
  (goodness-of-fit, persistence, VaR backtest pass/fail).
- t15: conclusions — practical implications + future-research recommendations.

## `validate_pass_c.py`'s leading-clause check is a literal stemmed-token match, not semantic

`check_primary_concept_leads_need` extracts the leading clause as everything before the FIRST
`", and/but/or"` or sentence-ending punctuation, then requires every stemmed token of
`primary_concept` to appear (stemmed) somewhere in that clause — pure token-set membership,
no ordering, no true "lead" position check beyond the clause boundary. Four rounds of
validator failures on this document, all one pattern: writing a paraphrased opening ("A
researcher wants to know why X suggest the presence of Y" for primary_concept "regime
changes") fails because "regimes" stems to `regim` while "changes" (the primary_concept's own
word) stems to `chang` via `-es` suffix stripping — but a differently-inflected clause word
("regimes" vs. "regime") can silently stem to a different token than expected. The reliable
fix is not clever paraphrase but embedding the primary_concept phrase VERBATIM (matching
inflection) inside the leading clause. Also caught: `answer_type: "section overview"` fails
`check_no_structure_references` (bans `section`) even though it's the answer_type slot, not
the summary prose — the banned-word scan runs over field+information_need+sub_concepts+
answer_type combined, not just information_need.

## Gotcha: thin spans force a light-but-honest summary, not a padded one

t10 (`line_start: 244, line_end: 251`) is an 8-line results-section roadmap sentence with no
independent findings of its own. R12's ~60-90 word budget still applies uniformly — met it by
folding in the roadmap's own content (which findings the two results subsections ground: safe
haven/hedge vs. regime change, each anchored by its own descriptive-statistics pass) rather
than inventing findings the span doesn't contain.
