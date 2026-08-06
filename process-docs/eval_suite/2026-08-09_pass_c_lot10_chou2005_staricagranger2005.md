# Pass C — lot10: Chou2005CARR, StaricaGranger2005NonstationaritiesStockReturns

Worker session producing Pass C theme summaries for 2 documents (10 + 8 themes) from
spans-only Pass B input, per `eval/queries/prompts/summary_prompt_pass_c.md`. Both
validated OK via `validate_pass_c.py` on first attempt (word budgets 72-88 words per
summary, no re-run needed).

## Orchestrator corrections applied mid-session

Two adjustments from Opus review, applied before finalizing (not caught by the validator
itself — the validator checks schema/budget/theme-id cross-reference, not slash-merges or
hyphen-anchor alignment):

1. **Slash-merged sub_concept slots are a single hook, not two.** Chou t01 originally had
   `"ARCH/GARCH"` as one sub_concepts entry — collapses two distinct field terms into one
   query-author hook, defeating the "3-5 named field terms" intent. Fixed to `"GARCH"`
   alone (ARCH is subsumed by GARCH generically for this theme's content). General rule
   going forward: never slash-merge two field terms into one sub_concepts slot; either
   drop to the more general term or use two separate slots.

2. **Primary_concept anchor must match verbatim when the primary IS a hyphenated intrinsic
   name.** R12's ordering rule requires the first information_need clause's content words
   to match primary_concept (inflection-tolerant). For most primary_concepts (multi-word
   generic phrases) approximate/stemmed matching suffices. But when primary_concept is
   itself an intrinsic proper-noun method name that keeps its hyphen (Mincer-Zarnowitz,
   Newey-West, Cramer-von Mises, Ljung-Box, Kiefer-Müller), the first clause must reproduce
   the identical hyphenated form — a de-hyphenated or reworded variant risks failing
   stemmed-anchor matching in the query-author's downstream reading. Applied to Chou t08
   (primary = "Mincer-Zarnowitz regression"): first clause opens with that exact string.

## Anti-lookup framing patterns used

Two theme spans in this lot were proof/theorem-heavy (Chou t03: QMLE consistency under
misspecified exponential density; Starica t03: integrated periodogram asymptotic Gaussian
limit / Theorem 2.1). Both framed per the documented pattern: "under what conditions does
X hold, how is it derived" rather than "wants the proof/theorem of X" — confirms this
framing generalizes cleanly across two unrelated math-heavy themes in different documents.

## R13 practitioner-test notes

Author-named estimators kept as field-adopted terms despite bearing a person's name (same
logic as Newey-West, Cramer-von Mises already established in prior lots): "Parkinson
volatility estimator" (Chou t01) — citation year dropped, estimator name kept since it is
standard range-based-volatility terminology, not paper-private phrasing.

Paper-private acronyms dropped even though they read like standard terms: Starica-Granger's
own "SM" (shifts-in-mean model) and "LM" (long-memory/FARIMA model) labels are the paper's
internal shorthand, not field nomenclature — rewritten as plain descriptive phrases
("shifts in mean model", "long memory model") instead of carrying the symbols forward.

## Compound-modifier hyphenation

Continued the hyphen-free-compound-modifier convention from prior lots (e.g. "out of
sample forecast evaluation", "root mean squared error", "heteroskedasticity autocorrelation
consistent standard errors", "quasi maximum likelihood estimation") while preserving
hyphens on all intrinsic proper-noun names. No validator rejection encountered for either
choice in this lot — consistent with the established convention, not a new finding.
