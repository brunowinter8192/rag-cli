# Pass C Theme Summary Run — Bollerslev1986GARCH.md (2026-07-24)

Applied `eval/queries/summary_prompt_pass_c.md` (R11-R15) to the 8 Pass B theme spans for
`data/documents/trading-reference/Bollerslev1986GARCH.md` (528 lines). Input was spans only
(no Pass B need sentences/labels), per the pipeline's leakage-prevention design — Pass C read
each span's raw passage text directly from the document. Output:
`eval/queries/pass_c_runs/Bollerslev1986GARCH.pass_c.json` — 8 summaries, one per theme,
each with field / information_need / sub_concepts / answer_type.

## Theme-to-content mapping

- t01: intro + section-2 GARCH(p,q) definition, stationarity setup, ARCH(infinity)/ARMA-in-eps^2
  representation.
- t02: stationarity condition statement + full appendix proof of the stationarity theorem.
- t03: GARCH(1,1) moment theorem, higher-order moment conditions (incl. GARCH(1,2)/(2,1)
  footnote), kurtosis, appendix proof.
- t04: mean-lag / median-lag formulas + their empirical values later in the document.
- t05: maximum-likelihood derivation — score, information matrix, BHHH iteration, asymptotic
  normality.
- t06: ACF/PACF theory for the squared process, Yule-Walker analogue, sample identification.
- t07: Lagrange-multiplier test derivation, singularity/non-identification of the general test.
- t08: empirical example — AR(4)/ARCH diagnostics, GARCH(1,1) vs ARCH(8) comparison, kurtosis/
  skewness, forecast-interval discussion.

## R13 practitioner-test calls

Kept as field-standard (a practitioner would type these unprompted): GARCH process, ARCH
process, wide-sense stationarity, conditional variance equation, kurtosis, leptokurtosis,
GARCH(1,1) process, mean lag / median lag, persistence, long memory, maximum likelihood
estimation, score function, information matrix, asymptotic normality, BHHH algorithm,
autocorrelation/partial autocorrelation function, Yule-Walker equations, model identification,
Lagrange multiplier test, chi-square distribution, degrees of freedom, inflation rate, model
comparison, forecast interval, volatility clustering.

Dropped as author phrasing / not a hook a cold searcher would use: "adaptive learning
mechanism" (t01, t04 candidate — interpretive gloss unique to this paper's framing, not a
term the field reaches for), "recursive moment formula" (t03 candidate — names the paper's
derivation mechanics, not a search-relevant concept), "asymptotic independence of mean and
variance estimates" (t05 candidate — states the paper's specific result rather than acting as
a term hook), document-structure references ("Theorem 1", "Theorem 2") excluded throughout
per R14.

## Correction mid-task: initial GARCH omission

First draft omitted the bare term "GARCH" itself from t01/t02 sub_concepts, reasoning it was
implied by "GARCH process" already sitting in other slots — flagged by reviewer as exactly the
over-neutralization failure R13 exists to prevent (documented precedent: batch01 stripped
"GARCH" to "generalized conditional-variance model"). Corrected by adding "GARCH process" to
both t01 and t02 sub_concepts, dropping the weakest existing term in each 5-slot budget
("moving average representation" from t01, "coefficient restriction" from t02) to stay within
the 3-5 term cap.

## Word-budget iteration

First draft: 5 of 8 summaries landed under the 60-90 word floor (47-58 words), because
information_need sentences stayed too terse. Fixed by adding one indicative clause per
under-budget summary — framing WHY the need matters (e.g., "since heavier-than-normal tails
matter for assessing risk", "useful for comparing how quickly different fitted models forget
past shocks") without stating the passage's actual answer content. Final counts: 60, 67, 63,
61, 60, 63, 64, 65 words across t01-t08, all within band.

## Verification performed

A throwaway python script (`/tmp/validate_pass_c_bollerslev.py`, not committed) checked: JSON
parses and matches the schema; exactly 8 entries with theme_ids t01-t08; word count (field +
information_need + sub_concepts + answer_type combined) within 60-90 per summary; no digits in
field/information_need/answer_type, with GARCH(1,1)-style parenthetical digits in sub_concepts
exempted; no document-structure references ("section", "appendix", "paper", "author") in any
slot; 3-5 sub_concepts per theme. All checks passed. Not verified: no downstream check that the
summaries actually seed effective multi-concept queries (out of Pass C's scope per R15) and no
cross-check against a second independent Pass C run.
