# Pass D Query Authoring — Lot05 (6 Documents, 74 Themes / 222 Queries) (2026-08-11)

Applied `eval/queries/prompts/query_prompt_pass_d.md` (R16-R20) to six Pass C summary sets:
`InclanTiao1994CumulativeSumsSquaresVariance` (17 themes), `AueGabrysHorvathKokoszka2009ChangePointMeanFunction`
(8), `Cont2001EmpiricalPropertiesAssetReturns` (15), `Chou2005CARRConditionalAutoregressiveRange` (10),
`StaricaGranger2005NonstationaritiesStockReturns` (8), `BitcoinHalvingCycleVolatilityMSGARCH` (16).
Output: `eval/queries/pass_d_runs/<doc>.pass_d.json` per document, 51/24/45/30/24/48 queries respectively —
`validate_pass_d.py` OK on all six on the committed content.

## Method: local re-implementation of the validator's stem/overlap logic, checked pre-write

Same approach as lot01-lot04: copied `stem()`, `leading_clause()`, `head_ok()`/`check_head_concept`, and
the overlap ratio into a `/tmp` helper mirroring `eval/scripts/validate_pass_d.py` exactly, ran every
draft through it — 12 sample themes (2 per document) shown to the orchestrator before Go, then the
full 222-query set after Go — before writing any deliverable file. Ran the real
`eval/scripts/validate_pass_d.py` CLI per document as the final gate — all six printed OK.

## Two new mechanical gotchas in the validator's stemming/clause logic (not seen in lot01-lot04)

**Irregular-plural stem mismatch.** `stem()` strips regular suffixes (`-s`, `-es`, `-ies`, `-ing`, `-ed`)
but has no irregular-form table. When a `primary_concept` noun appears in a query with a different
inflection than the concept string uses, the stems diverge and `check_head_concept` fails even though
a human reader sees the same concept: `"value"` → `value` vs `"values"` → `valu` (the `-es` rule fires
on `values` because its last two characters happen to be `es`); `"cycle"` → `cycle` vs `"cycles"` → `cycl`
(same `-es` trap); `"spectrum"` → `spectru` vs `"spectra"` (irregular plural, no suffix rule touches it)
→ `spectra` — completely different stem, not even a plural mismatch bug, since `spectra` doesn't share a
root with `spectru` at all; `"change"` → `change` vs `"changes"` → `chang`. Symptom caught by the local
`head_ok()` helper, not by eyeballing: `InclanTiao1994` t04 (`asymptotic critical value`),
`Cont2001` t14 (`singularity spectrum`), `BitcoinHalvingCycle` t01 (`Bitcoin halving cycle`) and t16
(`regime change`) all failed on first draft for this reason. Fix: reuse the exact singular/plural
surface form of the `primary_concept` string verbatim at the head of `natural_question`/`field_sentence`,
never an inflected variant, even when the inflected form reads more naturally.

**Oxford-comma list truncates the leading clause before the concept is captured.** `CLAUSE_BREAK` matches
`,\s*(?:and|but|or)\s+` anywhere in the string, not just at a top-level clause boundary — a serial-comma
list inside the sentence (`"bull, bear, and stagnation phases"`) contains exactly this pattern
(`", and stagnation"`) and truncates `leading_clause()` mid-list. If the `primary_concept` phrase sits
after that truncation point, `check_head_concept` never sees it. Caught on `BitcoinHalvingCycle` t01
(`Bitcoin halving cycle`): the draft opened with the concept correctly, but a later serial-comma list
in the same sentence combined with a plural mismatch (see above) to produce the failure; fixed by
dropping the Oxford comma (`"bull, bear and stagnation"`) and switching to the concept's exact singular
form. General rule adopted for the rest of the lot: place `primary_concept` as the literal opening
words of `natural_question`/`field_sentence` (`"The <primary_concept> ..."`), which trivially survives
both gotchas since the concept precedes any possible clause-break trigger.

## Guardrail: 0.72 rewrite-trigger below the 0.80 formal ceiling

First full-batch pass produced 21 overlap violations above 0.72 across the six documents (7 of them
above the 0.80 hard ceiling): `InclanTiao1994` t15 fs 0.78, t08 fs 0.74, t13 fs 0.73, t17 nq 0.73, t04
nq/fs head-fail (inflection bug, not overlap); `AueGabrysHorvathKokoszka2009` t04 fs 0.72, t08 nq 0.78;
`Cont2001` t06 fs 0.75; `Chou2005` t03 fs 0.78, t07 nq 0.80 (at the hard ceiling); `StaricaGranger2005`
t03 nq 0.84 / fs 0.83, t05 fs 0.74, t06 fs 0.83; `BitcoinHalvingCycle` t08 nq 0.77, t12 fs 0.76, t13
nq 0.74 / fs 0.73 (also head-fail from an inserted article breaking contiguity), t14 nq 0.74. Root
cause matched prior lots: drafts followed the `information_need` sentence's own clause order and term
clusters too closely, especially for summaries whose need sentence is already dense and short on
alternative phrasing (e.g. `StaricaGranger2005` t03's integrated-periodogram need, `Chou2005` t07's
forecast-evaluation need). Rewrote all 21 with situational framing and angle-shifted phrasing; final
per-document maxima: InclanTiao1994 0.66, AueGabryshorvathKokoszka2009 0.62, Cont2001 0.69, Chou2005
0.66, StaricaGranger2005 0.66, BitcoinHalvingCycle 0.72 (Chou2005CARR t07 fs, left as-is since under
the 0.80 ceiling and rewriting further risked losing field register) — all comfortably under the 0.80
ceiling, most under the 0.72 self-trigger.

## R16 field-owned additions beyond summary vocabulary (audit)

None beyond standard field terminology already implied by each theme's `sub_concepts` — no invented
concrete conditions, values, or named results added to any of the 222 queries.

## Angle differentiation for identical-primary_concept themes (five pairs, all resolved)

- `InclanTiao1994` t03/t10 (`likelihood ratio test`): t03 kept to single-change derivation/F-test
  relation register; t10 to sequential multi-change testing with extreme-value standardization.
  t13/t14 (`detection performance`): t13 to the one-change scenario; t14 to the two-change
  configuration/ordering scenario.
- `AueGabrysHorvathKokoszka2009` t04/t05 (`limit distribution`): t04 fixed-size (non-vanishing) shift;
  t05 local/vanishing alternative with a shrinkage-rate condition.
- `Cont2001` t14/t15 (`singularity spectrum`): t14 derivation via multifractal formalism and moment
  scaling; t15 cross-asset universality vs. finite-sample-artifact question.
- `BitcoinHalvingCycle` t02/t05 (`safe haven asset`): t02 Bitcoin's own halving-driven correlation
  condition; t05 Bitcoin-vs-gold comparative diversification question. t14/t16 (`regime change`): t14
  test-setup/groundwork register; t16 interpretation of what the detected regimes correspond to.

Verified by direct diff of each pair's three drafts before Go — no cross-theme phrase collision.
