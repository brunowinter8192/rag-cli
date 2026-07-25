# Pass C Theme Summary Rerun — Bollerslev1986GARCH.md (2026-07-25)

Rewrote `eval/queries/pass_c_runs/Bollerslev1986GARCH.pass_c.json` from scratch against a
revised set of 8 Pass B theme spans (independent Pass B rerun, different grouping than the
2026-07-24 run) and an updated `eval/queries/prompts/summary_prompt_pass_c.md` (prompts moved
under `prompts/`; R12 gained a `primary_concept` slot plus an ordering rule requiring
information_need's first clause to carry the primary component). No prior summary was reused
where spans differed — each theme's need was re-derived fresh from the passages.

## Regrouping vs. the prior (2026-07-24) run

- t01 narrowed to intro-only (model definition split out); t02 now merges what were
  previously two themes (model definition + full stationarity proof) into one.
- t03 narrowed to moment-existence-theorem-plus-proof only; kurtosis/leptokurtosis moved out
  to a merged t04 (mean/median lag + kurtosis, previously two separate themes).
- t05 (ACF/PACF) now absorbs the order-specific fourth-moment footnote (GARCH(1,2)/(2,1))
  that the prior run had grouped with the moment-existence theme instead.
- t06 (MLE), t07 (LM test) unchanged in span from the prior run.
- t08 (empirical example) now owns the full mean/median-lag empirical sentence contiguously,
  where the prior run had split it between the lag theme and the empirical theme.

## primary_concept selections

Two judgment calls beyond the mechanical cases (theme dominated by one clear topic):
- t04 (kurtosis vs. mean/median lag): kurtosis picked on content-share — roughly 26 of the
  32 span lines are moment/kurtosis derivation vs. ~6 for the lag formula.
- t08 (model comparison vs. inflation rate / diagnostics): model comparison picked as the
  organizing question the theme's diagnostics (residual autocorrelation, kurtosis/skewness,
  forecast-interval width) all serve, rather than any single diagnostic being primary.

## Ordering-rule compliance fixes

Two summaries initially failed the "information_need leads with primary_concept" check on a
literal-overlap validation pass:
- t02: first clause paraphrased the primary concept as "a generalized conditionally
  heteroskedastic process" instead of naming it — reworded to state "the GARCH process"
  explicitly near the sentence start.
- t06: primary_concept "maximum likelihood estimation" did not token-match the hyphenated
  "maximum-likelihood estimator" in the drafted sentence — reworded to the unhyphenated form.

## Word-budget iteration

First draft: t01 under band (57 words) — the primary-concept phrase "lag structure" also sat
past the sentence's first 10 words, so the same edit fixed both the budget and the ordering
requirement by restructuring the sentence to open with the lag-structure clause and adding a
non-negativity-constraint clause. After the ordering-rule fixes, four more summaries (t03, t04,
t07, t08) were still under the 60-word floor (46-59 words) — fixed by adding one indicative
clause per summary and, for t03, one additional sub_concept ("ARCH process", legitimate given
the passage's explicit ARCH(1)-special-case comparison). Final counts: 66, 65, 61, 69, 67, 60,
64, 62 words across t01-t08, all within the 60-90 band.

## Verification performed

A throwaway python script (`/tmp/validate_pass_c_bollerslev_v2.py`, not committed) checked:
JSON schema shape; exactly 8 entries with theme_ids t01-t08; word count (field +
information_need + sub_concepts + answer_type) within 60-90 per summary; no digits outside
GARCH(1,1)-style sub_concept parentheticals; no document-structure references; 3-5
sub_concepts per theme; `primary_concept` present and a member of `sub_concepts`; the
information_need's first ~10 words token-overlap the primary_concept's words. All checks
passed. Not verified: no downstream check that the summaries seed effective multi-concept
queries (out of Pass C's scope per R15) and no cross-check against a second independent Pass C
run on the same spans.
