# Pass B Theme Formation — lot05: AlizadehBrandtDiebold2002RangeBasedStochasticVolatility, Corsi2009SimpleLongMemoryRealizedVolatility (2026-08-06)

Fresh-worker Pass B over two documents' Pass A output, run one after the other.

## AlizadehBrandtDiebold2002RangeBasedStochasticVolatility.md (117 blocks, 9 trash spans)

Output: `eval/queries/pass_b_runs/AlizadehBrandtDiebold2002RangeBasedStochasticVolatility.pass_b.json`
— 17 themes, 0 resplits, 1 unassigned block, 116/117 assignable blocks covered —
6.82 blocks/theme (above the Bollerslev1986GARCH calibration anchor of 5.6).

Themes track the paper's own methodological arc: intro motivation, continuous-time model +
discretization, state-space QMLE, absolute-return-proxy properties, log-range-proxy
properties, microstructure-noise robustness, the Monte Carlo study (design, parameter
accuracy, extraction accuracy), the exchange-rate empirical application (data,
one-factor-model misspecification, two-factor-model fit, empirical normality check), and the
two-factor interpretation/long-memory-links discussion. 6 of 17 themes are distributed: the
microstructure-robustness theme spans Section II.F's theoretical argument and Section III.C's
page-distant systematic Monte Carlo confirmation (canonical intro-poses/later-resolves
pattern); the one-factor/Table-V themes are mutually interleaved because a section heading's
cut-off sentence resumes only after an interposed table; three others are split purely by
interposed trash (footnotes, figure-caption stubs).

Split-test applied to the largest candidate (t08, MC parameter-estimation section, 17
blocks): considered separating "baseline T=1000/N=1000 comparison" from "sensitivity to
trading frequency N and sample size T". Rejected — the mechanism paragraph explaining the
normality-vs-information-content decomposition cross-references both Table II and Table III,
and Table II itself already embeds the N-sensitivity panels, so no clean block boundary
exists without duplicating table blocks across spans; a realistic single question ("is
range-based QMLE reliable enough to adopt") wants both baseline and robustness evidence
together. Kept as one theme.

Soft memberships: Table I (b022, home in the absolute-return-proxy theme) and the
range-history intro sentence (b006, home in the intro theme) both also serve the log-range
theme; Table VI's data block (b089, home in the one-factor theme, since its numbers are first
cited there) also serves the two-factor theme, since the table reports both models' columns.

### Recap-precedent consistency check (user-directed)

User flagged that Corsi's conclusion (see below) was kept as *content* at Pass A on the
grounds that it carries standalone claims, and asked to verify the Pass-B unassigned call
against theme coverage before finalizing. Re-read both documents' final "future research"
paragraphs against this document's already-assigned themes: Alizadeh b116
("consensus emerging for two-factor SV models", literature-context) is fully recap of
t13/t15 — stayed unassigned. Alizadeh b117 (multivariate range-based extensions + open
range-vs-realized-volatility comparison pointer) contains a genuinely new, un-restated
direction (the whole paper is univariate) — promoted to a standalone single-block theme
(t17) rather than left unassigned, applying the same standard used on the Corsi document for
consistency across the lot even though the user's directive named Corsi specifically.

## Corsi2009SimpleLongMemoryRealizedVolatility.md (67 blocks, 6 trash spans)

Output: `eval/queries/pass_b_runs/Corsi2009SimpleLongMemoryRealizedVolatility.pass_b.json`
— 8 themes, 0 resplits, 1 unassigned block, 66/67 assignable blocks covered —
8.25 blocks/theme.

Themes: intro motivation (why GARCH/SV and ARFIMA fail the stylized facts), the HAR-RV
model (notation + Heterogeneous Market Hypothesis motivation + cascade derivation, merged
into one theme — see split-test note below), simulation validation against stylized facts
(merged, see below), empirical data/RV-methodology, in-sample HAR(3) OLS estimation +
goodness-of-fit, in-sample forecast performance, out-of-sample forecast performance, and a
promoted extensibility theme (below). 3 of 8 themes are distributed, all via interposed
footnotes/figure captions/trash image placeholders splitting otherwise-continuous prose.

Split-test applied to two merge candidates:
- t02 (notation + motivation + derivation, 19 blocks): considered separating the economic
  rationale (Heterogeneous Market Hypothesis) from the mathematical derivation. Rejected —
  the notation section is not a standalone search (formula-only, R6 test 2) and flows
  directly into the equations it is used in; a practitioner realistically searches
  "what is HAR-RV and why is it built this way" as one query. Kept merged, single contiguous
  span.
- t03 (simulation validation, 17 blocks): considered separating by stylized fact (kurtosis,
  persistence, self-similarity). Rejected — the abstract itself bundles all three as one
  finding, and the setup/calibration blocks are shared infrastructure for all three,
  requiring duplication to split cleanly. Kept merged.

### Recap-precedent consistency check (user-directed)

Initial draft left both conclusion blocks (b066 recap paragraph, b067 extensibility pointer)
unassigned under the pure-recap-conclusion precedent. User challenge: verify whether the
extensibility/tradeoff content is actually covered elsewhere before defaulting to unassigned.
Re-check: b066's claims (long-memory reproduction, parsimony, HAR-vs-ARFIMA
accuracy-vs-simplicity tradeoff) are all restatements already covered by t02/t03/t07 (the
tradeoff specifically by b065 inside t07) — stayed unassigned. b067 (extending HAR-RV with
separately-measured jump components and leverage effects, citing Andersen et al. 2007 and
Corsi/Pirino/Renò 2008) introduces content not present anywhere else in the paper — promoted
to a standalone single-block theme (t08) instead of left unassigned.

## Verification performed

`eval/scripts/validate_pass_b.py` run against each document's Pass A JSON and source
markdown: schema, span-bounds, intra-theme overlap, trash-disjointness, resplit-boundary
(n/a both docs, zero resplits), full block-coverage, soft-member containment, the 2.0
blocks/theme floor, and the zero-tolerance proof-label gate all passed —
`OK validate_pass_b: 17 themes, 0 resplits, 1 unassigned blocks` (doc1) and
`OK validate_pass_b: 8 themes, 0 resplits, 1 unassigned blocks` (doc2), both after the
recap-precedent fix. Not verified: no semantic/LLM cross-check of theme-need wording quality
beyond the reasoning recorded per theme above and the two user-directed corrections.
