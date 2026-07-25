# Pass D Re-run: R16b Primary-Concept Lead, Revised Bollerslev Summaries (2026-07-25)

Second Pass D execution on `Bollerslev1986GARCH.md`, triggered by two upstream changes merged
from `integration` (`d80b772..709fe3f`, fast-forward, clean): prompts moved to
`eval/queries/prompts/`, and Pass C summaries were rewritten (`pass_c_runs/Bollerslev1986GARCH.pass_c.json`)
following a Pass B re-run — new `primary_concept` field per theme, reworded `information_need`,
some `sub_concepts` sets changed (e.g. t01 reframed as background-motivation, t05 gained
`moment existence condition`). Output fully overwritten from scratch (24 queries, 8 themes x 3
formats) — no reuse of the prior run's query text, since the summaries changed substantively.

## New rule: R16b (mechanical primary_concept lead)

`query_prompt_pass_d.md` added R16b: every query's keyword_bag opens literally with the
summary's `primary_concept`; natural_question and field_sentence make it the grammatical
subject. Framed explicitly as mechanical execution, not re-ranking — "the weighting decision
was made in the summary pass ... your job is to execute it."

## Validation caught a real defect: object vs. concept as subject

Extended `/tmp/validate_pass_d.py` with a head-concept check (leading-clause substring match
against `pass_c.json`'s `primary_concept`, tolerant of the head-noun's own inflection). First
run failed on t06: the natural_question opened with "the maximum likelihood **estimator**"
(the resulting object) rather than "maximum likelihood **estimation**" (the summary's
`primary_concept`, the method). Fixed by rephrasing the subject to the literal primary_concept
phrase ("How is maximum likelihood estimation ... carried out ..., and shown to yield an
asymptotically normal estimator?"). This is the mechanical-rule failure mode R16b is meant to
catch: a fluent paraphrase that silently swaps the head concept for a closely related noun.

## R16 term-addition audit (unchanged pattern from the first run)

- t01, t02, t03, t07, t08: no additions beyond summary vocabulary.
- t04: "normal distribution" — implicit comparison baseline entailed by "leptokurtosis" itself.
- t05: "GARCH" — the summary's `information_need` still says "this class of volatility models"
  (deictic, unusable standalone); resolved by naming the field-owned model class directly,
  consistent with the user-flagged fix from the first Pass D run on this document (t06 "GARCH
  errors" fix, same pattern applied proactively here rather than waiting to be told).
- t06: "GARCH errors" — shorthand for "regression model whose error variance follows a
  volatility process," same justification as the first run.

No concrete parameter values, named theorems, or specific empirical results were introduced in
any field_sentence (R18) — e.g. t07's field_sentence names "a corresponding number of degrees
of freedom" without a concrete count, t03's names a "generalization" of the ARCH existence
condition without stating the bound.

## Validation approach

`/tmp/validate_pass_d.py` (throwaway, not repo-persisted): parses both `pass_d.json` and
`pass_c.json`, cross-checks 24 entries / t01-t08 / 3 formats each, per-format length and
syntax (keyword_bag 9-11 words this run, single-sentence question/field-sentence splits, no
stray `?`), plus the new head-concept check against each theme's `primary_concept`. One
failure on first run (t06, described above), pass on second run after the one-line fix.

## Process note

Same plan-then-Go worker flow: per-theme primary_concept/sub_concept table and R16 addition
table reported before any file write; Opus confirmed the t05 "GARCH" resolution matched the
prior round's user-flagged fix before authorizing the write.
