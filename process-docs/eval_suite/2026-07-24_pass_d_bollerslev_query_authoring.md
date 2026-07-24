# Pass D Query Authoring Run: Bollerslev1986GARCH, 8 Themes / 24 Queries (2026-07-24)

First execution of Pass D (`eval/queries/query_prompt_pass_d.md`, R16-R20) against a real Pass C
output — `eval/queries/pass_c_runs/Bollerslev1986GARCH.pass_c.json` (8 theme summaries, GARCH
paper). Worker had summaries only, no document/segmentation/prior-pass access, isolating the
"query author who never saw the answering passages" role the rule specifies.

## Output

`eval/queries/pass_d_runs/Bollerslev1986GARCH.pass_d.json` — 24 entries (8 themes t01-t08 x 3
formats: keyword_bag, natural_question, field_sentence), each combining 2+ of the theme's
sub_concepts per R16's multi-concept requirement.

## R16 term-addition audit

Per theme, checked whether any term beyond the summary's field/sub_concepts vocabulary was
introduced, and whether it was field-owned (allowed) vs. an invented specific (disallowed):

- 6 of 8 themes needed zero additions — summary vocabulary alone sufficed for all 3 formats.
- t03: added "normal distribution" as the implicit comparison baseline for "leptokurtosis" —
  the term is definitionally entailed by leptokurtosis itself (heavier-than-normal tails), not
  a new claim.
- t05: added "GARCH errors" as shorthand for the summary's "regression model whose error
  variance follows a volatility process" — justified because the whole source document's model
  class is GARCH; kept as generic shorthand, no concrete parameter or condition attached.

No theme required a concrete value, named theorem, or specific empirical result (R18)
anywhere across the 24 queries — field_sentence entries assert THAT a condition/result of the
stated answer_type exists (e.g. "requires a bound on its parameters" for t03's moment
existence condition) without stating what the bound is.

## Format-length calibration (R17/R19)

keyword_bag entries measured 8-11 words across all 8 themes (target 6-12) — no compression or
padding needed. natural_question entries ranged 19-37 words, all single grammatical questions
(compound "and"-joined clauses count as one sentence per the rule's own compound example in
R17). field_sentence entries ranged 27-40 words, 1 sentence each (several compound with
semicolon-equivalent "and"/"but" joins, still within the 1-2 sentence cap) — none needed
splitting to 2 sentences.

Opus flagged before writing that t05 and t08 keyword_bag drafts might sit near the 12-word cap
once every listed sub_concept term was included; actual count came in at 11 and 9 words
respectively, so no trimming was required in practice — the concern did not materialize for
this document, but the check-before-write step is worth keeping for summaries with denser
sub_concept lists (5+ multi-word terms).

## Validation approach

Throwaway script at `/tmp/validate_pass_d.py` (not repo-persisted per dev/ convention — no
regression value beyond this one pass run): parses the JSON, asserts document field, exactly
24 entries, theme_ids t01-t08 each with all 3 formats present, per-format field checks
(keyword_bag 6-12 words + no `?`; natural_question exactly one `?` + single-sentence split;
field_sentence no `?` + 1-2 sentence split via regex sentence splitter). All 24 entries passed
on first run — no rework needed.

## Process note

Worker plan-then-Go flow (per Worker Rules) surfaced the term-addition table and draft
examples before any file was written, so the R16/R18 audit above was reviewed by Opus prior to
commit rather than after. No deviations between the reported plan and the committed output.
