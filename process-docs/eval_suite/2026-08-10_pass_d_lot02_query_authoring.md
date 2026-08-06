# Pass D Query Authoring — Lot02 (4 Documents, 40 Themes / 120 Queries) (2026-08-10)

Applied `eval/queries/prompts/query_prompt_pass_d.md` (R16-R20) to four Pass C summary sets:
`DaEngelbergGao2011InSearchOfAttention` (7 themes), `AlizadehBrandtDiebold2002RangeBasedStochasticVolatility`
(17 themes), `Corsi2009SimpleLongMemoryRealizedVolatility` (8 themes), `BengioGrandvalet2004KFoldCVVariance`
(8 themes). Output: `eval/queries/pass_d_runs/<doc>.pass_d.json` per document, 21/51/24/24 queries
respectively — `validate_pass_d.py` OK on all four on the committed content.

## Method: local re-implementation of the validator's stem/overlap logic, checked pre-write

Rather than importing `validate_pass_d.py` as a module, replicated `stem()`, `leading_clause()`,
`check_head_concept`'s substring logic, and the overlap ratio in a standalone `/tmp` script and ran
every draft through it before writing any deliverable file, then ran the real
`eval/scripts/validate_pass_d.py` CLI per document as the final gate. Both approaches (import vs.
re-implement) converge on the same mechanical checks; re-implementation was chosen here to keep the
pre-flight report (shown to the orchestrator before the Go) self-contained without touching the
worktree's script files.

## Guardrail: 0.72 rewrite-trigger below the 0.80 formal ceiling

Per-orchestrator-approved plan, treated any natural_question/field_sentence overlap above 0.72 as a
rewrite trigger, reserving the formal 0.80 ceiling as the hard fail line. One theme (Bengio t08)
drafted at 0.818 — over the hard ceiling — during pre-flight; five more (Corsi t01 nq 0.792,
Alizadeh t07/t09/t10/t16 nq at 0.735-0.788) sat above the 0.72 trigger. All six were rewritten
before commit; final maxima per document: Da 0.655 (t01 fs), Alizadeh 0.741→0.556 (t09, post-fix;
doc max ended at t16 fs 0.724), Corsi 0.694 (t03 fs, post t01/t08 fixes), Bengio 0.686 (t04 fs,
post t04/t08 fixes) — all comfortably under the 0.80 ceiling with the 0.72 trigger holding except
one field_sentence in each of Alizadeh (t16, 0.724) and Corsi (t03, 0.694) left marginally above/at
trigger by design tradeoff against further rewrites, both still well inside the formal 0.80 ceiling.

## Mechanical failure classes hit while drafting (all fixed before commit)

- **keyword_bag head-concept mismatch on multi-word primary_concept with connectives.** Concepts
  like "SVI and individual investor trading" or "change in SVI and future stock returns" require
  the keyword_bag's leading tokens to include "and"/"in" verbatim — an initial draft that dropped
  the connective for a terser-reading bag ("SVI individual investor trading...") failed
  `check_head_concept` even though it reads naturally; fixed by keeping the full literal concept
  phrase as the bag's prefix.
- **Apostrophe-s tokenization mismatch.** `WORD_PATTERN` (`[A-Za-z][A-Za-z\-']*`) captures
  possessives as one token ("range's" → stemmed "rang", not "range"), so a natural_question
  written as "the price range's noise is..." silently breaks the head-concept substring match
  against the unmodified concept token "range". Fixed by rephrasing to avoid possessive-'s directly
  after a concept noun ("the price range carries less measurement noise" instead).
- **Near-ceiling overlap from need-sentence structural mirroring.** All instances above 0.72 were
  reduced by changing rhetorical STRUCTURE and swapping in synonymous field phrasing (e.g. "does
  the choice of X change Y, and does the gap shrink/widen as..." reworded to "what would a good ...
  design look like ... in terms of picking realistic parameters and sweeping over..."), not by
  word-for-word synonym substitution alone — surface synonym swaps left overlap nearly unchanged
  because the stemmed clause SHAPE was still identical to the need sentence.

## Angle differentiation for a 17-theme document with a dense shared-vocabulary cluster

Alizadeh has three themes with the identical `primary_concept` "price range" (t05, t11, t17) plus
a wider cluster (t01/t04/t08/t09/t14/t15) all touching `volatility proxy`/`measurement error`/
`quasi maximum likelihood`. Differentiated by angle rather than term substitution: t05 = analytical
derivation under a Brownian-motion assumption (theory, ex-ante efficiency), t11 = empirical
cross-currency comparison via autocorrelation (applied, ex-post persistence), t17 = open research
directions (multivariate extension, comparison to realized volatility). Similarly t01 (efficiency
loss from a noisy proxy, motivation-level) vs. t08 (finite-sample bias/RMSE as sample size and
intraday frequency vary, empirical-comparison-level) share "quasi maximum likelihood estimation"
vocabulary but ask structurally different questions.

## R16 field-owned additions beyond summary vocabulary (audit)

Kept minimal and traceable to terms already implied by each theme's `information_need` or
`sub_concepts`:
- Da t06: "small cap" as a standard field synonym for "market capitalization" (from sub_concepts).
- Alizadeh t02: "daily data" as the implied empirical unit for "discrete time approximation ...
  suitable for empirical estimation" (not named in the need, but the paper's data frequency is
  domain-standard for this literature).
- Alizadeh t07: "realistic process parameters" for "parameterize the data generating process"
  (need's own phrase, restated).
No invented concrete conditions, values, or named results beyond what each summary supports.
