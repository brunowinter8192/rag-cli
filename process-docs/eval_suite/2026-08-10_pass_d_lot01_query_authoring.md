# Pass D Query Authoring — Lot01 (3 Documents, 54 Themes / 162 Queries) (2026-08-10)

Applied `eval/queries/prompts/query_prompt_pass_d.md` (R16-R20) to three Pass C summary sets:
`NadeauBengio2003InferenceGeneralizationError` (15 themes), `HansenLundeNason2011ModelConfidenceSet`
(23 themes), `AndersenBollerslevDieboldLabys2003ModelingForecastingRealizedVolatility` (16 themes).
Output: `eval/queries/pass_d_runs/<doc>.pass_d.json` per document, 45/69/48 queries respectively —
`validate_pass_d.py` OK on all three on the committed content.

## Method: import the validator's own functions for iterative drafting, run the CLI as the final gate

Rather than hand-tracing `check_head_concept`/`check_overlap_ceiling` per draft, imported
`validate_pass_d.py` as a module (`importlib.util`) and ran its `stem`/`WORD_PATTERN`/
`check_head_concept`/`check_overlap_ceiling` directly against draft query dicts held in memory,
iterating until every theme's 3 formats passed, before writing any deliverable file. This closed
the loop between "the rule text" and "the actual regex/stemming behavior" — several drafts that
read as compliant by eye failed mechanically (see failure classes below) and would not have been
caught by inspection alone. The real `eval/scripts/validate_pass_d.py` CLI was still run per
document as the final gate after the files were written; the in-memory pass is a drafting aid, not
a substitute for it.

## Guardrail: 0.72 rewrite-trigger below the 0.80 formal ceiling

Orchestrator instruction for this run: treat any natural_question/field_sentence overlap above
0.72 (not the formal 0.80 ceiling) as a rewrite trigger during authoring, so nothing ships near the
edge. Final max overlaps: doc1 0.710 (t14 nq), doc2 0.719 (t04 nq), doc3 0.704 (t11 nq) — all
comfortably under the 0.72 trigger and the formal 0.80 ceiling with margin.

## Recurring mechanical failure classes hit while drafting (all fixed before commit)

- **keyword_bag head-concept mismatch on multi-word primary_concept.** When `primary_concept`
  contains stopwords ("of", "and", "for", "versus"), the keyword_bag's first N tokens must match
  it VERBATIM including those stopwords (e.g. "monotonicity **of** cross-validation estimator
  variance", "set **of** superior objects", "empirical size **and** power comparison") — dropping
  the stopword for a terser-reading bag fails `check_head_concept` even though the phrase reads
  fine to a human.
- **natural_question/field_sentence head-concept mismatch from paraphrasing the concept phrase
  itself.** Reformulating the primary_concept's own wording (e.g. "relation to existing..." →
  "relate to existing...", "no-change benchmark definition..." → "standard...") breaks the
  stemmed-substring match even when a human reader would call it the same concept — the concept
  phrase must appear verbatim (or stem-identical) somewhere in the leading clause, independent of
  how the REST of the query is reformulated.
- **keyword_bag word-count overflow (13-15 words) from a long primary_concept plus 3+ sub_concepts.**
  Themes whose primary_concept itself runs 5-8 words (e.g. "model confidence set versus superior
  predictive ability tests") leave little of the 6-12 budget for sub_concepts; the fix was
  dropping to 2 sub_concepts rather than 3-4, not shortening the concept phrase.
- **Near-ceiling overlap from need-sentence structural mirroring**, even when vocabulary looked
  reformulated. All instances above 0.72 were fixed by changing STRUCTURE (rhetorical framing —
  "X sounds appealing, but does it..." / "would I expect... or does it come down to...") rather
  than swapping individual words, which is what actually breaks stemmed n-token overlap with the
  need sentence's clause shape.

## Angle differentiation for consecutive theory themes sharing vocabulary (doc3 t03/t04/t05)

Three adjacent themes in the volatility paper (semimartingale decomposition, quadratic variation,
normal mixture distribution) share dense continuous-time-asset-pricing vocabulary
(no-arbitrage, martingale, continuous-time price process) across their `sub_concepts`. Each is
independently gated by its own `primary_concept`, so mechanical validation alone would not force
distinct queries. Differentiated by the ANGLE of the underlying question rather than by term
substitution: t03 = existence conditions (under what no-arbitrage condition does the decomposition
hold), t04 = estimator/proxy equivalence (when does quadratic variation equal the conditional
covariance matrix), t05 = distributional consequence (what return-distribution form follows from
the volatility path). This produced visibly distinct queries despite the shared field vocabulary.

## R16 field-owned additions beyond summary vocabulary (audit)

Kept minimal and traceable to terms already implied by each theme's `information_need`:
- doc1 t02/t10/t11: "K-fold", "leave-one-out", "Gaussian data-generating setup" — named or
  directly implied in the need sentence, not invented.
- doc2 t15/t20: "cointegration rank" (named in the need), "AIC or BIC" (standard instances of
  "information-criterion-type likelihood measures" from the need).
- doc3 t04/t09: "asymmetric" (standard field qualifier for leverage effect), "currency pair"
  (field-owned synonym for exchange-rate series).
No invented concrete conditions, values, or named results beyond what each summary supports.
