# Pass C (theme summaries) — lot08: InclanTiao1994, AueGabrysHorvathKokoszka2009

As of 2026-08-06, Pass C was run on 2 documents (17 + 8 themes) producing
`eval/queries/pass_c_runs/InclanTiao1994CumulativeSumsSquaresVariance.pass_c.json` and
`eval/queries/pass_c_runs/AueGabrysHorvathKokoszka2009ChangePointMeanFunction.pass_c.json`.
Both validated OK against `eval/scripts/validate_pass_c.py` (17/17 and 8/8 summaries respectively).
Model: claude-sonnet-5.

## Theme-to-concept mapping approach

Both source documents are proof-heavy statistics papers (variance change-point detection via
cumulative sums of squares; change-point estimation in functional-data mean functions). Several
Pass B themes cover the same underlying statistical object from different angles (e.g. the
centered cumulative-sum statistic appears across definition, F-test/LR relationship, expected-value
derivation, and asymptotic-distribution-proof themes). Rather than inventing a distinct
primary_concept per theme, reused primary_concepts (`likelihood ratio test`, `detection
performance`, `limit distribution`) were kept where the underlying concept was genuinely the same,
with the information_need's first clause carrying the differentiating SITUATION (single vs two
change points; fixed-size vs shrinking/local-alternative change; existence-testing vs
number-of-changes framing). This matches the "same primary_concept across themes" allowance in the
Pass C rules, provided the situation differs.

## Proof-heavy spans

For theme spans that are pure derivations/proofs (Appendix A/B in InclanTiao1994; Theorem 2.1/2.2
proof sections and Appendix A/B verification in AueGabrysHorvathKokoszka2009), the need was framed
as "under what conditions does the guarantee hold, derived how" rather than "wants the proof/theorem
of X" — the latter phrasing is validator-banned as a bare artifact lookup. This framing was applied
consistently to 5 of the 25 themes across both documents (t07, t08 in InclanTiao1994; t04, t05, t06
in AueGabrysHorvathKokoszka2009).

## Terminology decisions (R13 practitioner test)

Kept as field-owned despite paper origin: `ICSS algorithm` — coined by this paper but adopted as
standard vocabulary in the variance change-point literature since 1994, confirmed via explicit
user guidance during this session. Also kept: `Brownian bridge`, `F test`, `likelihood ratio test`,
`posterior odds ratio`, `masking effect`, `functional principal component analysis`, `local
alternative`, `Donsker`-style convergence reasoning (rephrased, see below).

Dropped/rephrased: the summary originally named "Donsker's theorem" explicitly as the derivation
tool for the Brownian-bridge convergence result (InclanTiao1994 t08) — replaced with the generic
field term "functional central limit theorem argument" to avoid naming a specific external citation
as if it were the paper's own labeled result, keeping the need at the case-match altitude rather
than a named-artifact reference.

## Validator failure and fix (first-clause anchor check)

First validation pass on InclanTiao1994 failed on 2 of 17 themes: t06 (`ICSS algorithm`) and t11
(`simulation study design`). Both needs opened with a paraphrase of the concept ("an iterative
procedure that isolates...", "a controlled comparison...") without the primary_concept's literal
content words appearing before the first ", and" clause break — the validator's mechanical scan for
concept-anchoring failed even though the paraphrase was semantically equivalent. Fix: reworded both
leading clauses to open with the primary_concept phrase itself ("A practitioner wants an ICSS
algorithm..." / "A practitioner wants a simulation study design...") followed by the
situation-specific elaboration. Re-run passed. Lesson for future lots: when primary_concept is a
multi-word named artifact/method (algorithm name, procedure name), lead the need with that exact
phrase rather than a description of it, even though the general R12 guidance only requires
"majority of content words, inflection-tolerant" — the validator's break-position check is stricter
in practice for compound-noun primary_concepts.

## Word-budget observations

All 25 summaries landed in the 62-81 word range (target 60-90), computed as
field + information_need + sub_concepts + answer_type. No digits appear in any slot; no hyphenated
compounds were used where a hyphen-free form was available (`change point`, `single change`,
`second order expansion`, `eigen decomposition` all written as separate words per prior-lot
validator guidance).
