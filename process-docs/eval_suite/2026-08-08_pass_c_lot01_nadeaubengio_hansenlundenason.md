# Pass C Theme Summaries — lot01: NadeauBengio2003InferenceGeneralizationError, HansenLundeNason2011ModelConfidenceSet (2026-08-08)

Fresh-worker Pass C over two documents' Pass B spans (spans-only input, no need
sentences or labels — need derived fresh from each theme's passage text via line
spans into the source `.md`).

## NadeauBengio2003InferenceGeneralizationError.md (15 themes)

Output: `eval/queries/pass_c_runs/NadeauBengio2003InferenceGeneralizationError.pass_c.json`
— 15 summaries, word budget 60-67 (of the 60-90 range), `validate_pass_c` OK.

Themes trace the paper's structure: motivation (t01), CV-estimator formal setup
(t02), the Lemma-1/Lemma-2 covariance-structure derivation (t03), variance
monotonicity in n1/n2/J (t04), the non-existence-of-unbiased-estimator result
(t05), the liberal/conservative inference framework (t06), the three pre-existing
tests — t-test, resampled t-test, Dietterich's paired cv test (t07), the two new
conservative procedures (t08), simulation-study design (t09), the three simulated
problem families — regression/Gaussian-classification/letter-recognition (t10-t12),
empirical size/power comparison (t13), and the J and M parameter-choice
recommendations (t14-t15).

## HansenLundeNason2011ModelConfidenceSet.md (23 themes)

Output: `eval/queries/pass_c_runs/HansenLundeNason2011ModelConfidenceSet.pass_c.json`
— 23 summaries, word budget 61-82, `validate_pass_c` OK.

Themes trace: MCS concept intro (t01), the two empirical applications reconciled
against the general theory — inflation no-change-benchmark discrepancy (t02) and
Taylor-rule regression selection (t03), the formal M* definition (t04), the MCS
algorithm and Theorem 1 (t05), the informativeness-adaptive FWE-bound property
(t06), sequential-testing Type-I-error safety plus the singleton-M* Corollary 1
(t07), test/elimination-rule coherency — Theorem 2 and Definition 3 (t08), MCS
p-values — definition and worked table (t09), MCS p-value interpretation and
Theorem 3 (t10), bootstrap assumptions and the quadratic-form test (t11), that
test's high-dimensional limitation and the closed-testing motivation for
t-statistic tests (t12), the T_max/T_R statistics with Proposition 1/Lemma 2/
Theorem 4 (t13), nested-model bootstrap caveats plus parameter-uncertainty
extensions (t14), relation to trace-tests/multiple-comparisons-with-best/
step-down procedures (t15), relation to SPA tests and other sequential
model-selection literature (t16), the Bayesian-interpretation section (t17),
the two Monte Carlo simulation designs (t18-t19), the in-sample regression
simulation (t20), and the two empirical applications in full — inflation
forecast setup/subsample results/factor-combination results (t21-t23) plus the
Taylor-rule results (already covered by t03's distributed span).

## Validator mechanics discovered this session

`validate_pass_c.py`'s `check_primary_concept_leads_need` stems each word by
stripping non-alphanumerics THEN checking suffixes — so a hyphenated compound
written as one token (`"Taylor-rule"`, `"model-comparison"`) collapses to a
single merged stem (`"taylorr"`, `"modelco"`) that no longer separately matches
`"taylor"` or `"rule"`/`"model"`/`"compari"` from the primary_concept. Writing
compounds as separate space-delimited words (`"Taylor rule"`) fixes this. Also:
`check_no_stray_digits` bans digits everywhere in field/information_need/
answer_type and in sub_concepts outside a `(n,n)`-style parenthetical — so a
field-standard numeric method name like Dietterich's 5x2cv had to be referenced
digit-free ("Dietterich cross-validation test") rather than dropped from
sub_concepts, per R13's practitioner-test (the method itself is field
vocabulary; only its numeral had to go). `leading_clause` breaks at the first
`.`, `;`, or `, and/but/or` — long primary_concept phrases (5+ content words)
are hard to fully embed before a natural clause break tempts an early "and/or";
shortening the primary_concept to 2-3 content words (e.g. "familywise error
rate control" instead of "...under sequential elimination") made anchoring
reliable without fighting the clause-break regex.

Iteration pattern: draft all summaries as case-match needs first (R6/R12),
run the validator, then fix only the specific reported failures (word-budget
gaps closed with a trailing clause; anchoring failures fixed by de-hyphenating
or shortening primary_concept) rather than rewriting whole batches — both
documents converged in two validator-fix rounds each.
