# Pass B Theme Formation — lot11: Cont2001EmpiricalPropertiesAssetReturns, Chou2005CARRConditionalAutoregressiveRange, StaricaGranger2005NonstationaritiesStockReturns (2026-08-07)

Fresh-worker Pass B over three documents' Pass A output, run one after the other. All
three are empirical-finance papers dense with figure/table captions interrupting running
prose, which surfaced a distinct distributed-theme trigger not centered on this batch's
prior lots: caption trash (not theorem/appendix separation) splitting one continuous
argument into non-adjacent spans.

## Cont2001EmpiricalPropertiesAssetReturns.md (71 blocks, 11 trash spans)

Output: `eval/queries/pass_b_runs/Cont2001EmpiricalPropertiesAssetReturns.pass_b.json`
— 15 themes, 0 resplits, 2 unassigned blocks, 69/71 assignable blocks covered —
4.6 blocks/theme (below the Bollerslev1986GARCH calibration anchor of 5.6, above the
validator's 2.0 floor).

5 of 15 themes are distributed (t03-t07), all for the same reason: a Pass-A-trashed
figure/table caption sits mid-block-run inside one continuous argument (e.g. Figure 1's
caption splitting the stationarity/ergodicity/finite-sample discussion; Figure 3+4's
captions splitting Mandelbrot's sample-moment tail-index method; Table 2's caption
splitting the EVT estimation narrative). This is structurally distinct from the
theorem+appendix-proof pattern seen in prior lots — here the paper has no appendix, so
R7b's "expect distributed themes in any paper with an appendix" anchor does not directly
apply, but the underlying R7 principle (a theme resuming after a digression is one
coherence unit) still fires whenever captions interrupt prose.

Split-test applied: the section-5.2 "volatility clustering & nonlinear dependence"
Pass-A grouping was split into t08 (power-transform ACF measures: C2, Calpha,
Ding-Granger power-law decay — "how strong/persistent is clustering, which power
captures it best") and t09 (leverage effect + r=sigma*epsilon decomposition — "what
asymmetric signature exists and how is it formalized into the GARCH/SV factorization
used downstream"), on the grounds these are two self-standing single-search questions
with no realistic single query needing their union. t03 (stationarity + ergodicity +
finite-sample-properties, Section 3's three subsections) was kept merged: a cumulative
validity-checklist a practitioner runs through before trusting return-based inference,
not three independent searches.

Unassigned: b070 (explicit self-referential recap, "In the preceding sections we have
tried to present..."), b071 (forward-looking open-questions list touching several
different resolved themes — volatility forecasting, risk management, trading strategy,
portfolio risk — at once, recap-shaped preview rather than one answerable need).

## Chou2005CARRConditionalAutoregressiveRange.md (61 blocks, 11 trash spans)

Output: `eval/queries/pass_b_runs/Chou2005CARRConditionalAutoregressiveRange.pass_b.json`
— 10 themes, 0 resplits, 3 unassigned blocks, 58/61 assignable blocks covered —
5.8 blocks/theme, at the Bollerslev1986GARCH calibration anchor.

6 of 10 themes are distributed (t04-t06, t08-t10), driven by the same caption-trash
mechanism as Cont2001 plus one distinct pattern: eq. 11 (the forecast-encompassing
regression) is introduced in the running text *before* Table 5 (Mincer-Zarnowitz
single-regressor results) is presented, even though eq. 11's actual results table
(Table 6) appears only after Table 5. This produced a symmetric pair of interposed
themes — t08 (MZ/Table 5) and t09 (encompassing/Table 6) each split around the other's
material — rather than a single interposed-caption gap.

Split-test applied: t05 (ECARR results) vs t06 (WCARR/Weibull results) — split, distinct
distributional hypotheses under test with a clear textual pivot ("the empirical
distribution test results indicate clear rejection of the hypothesized exponential
distribution... we now turn to Table 3 for the Weibull specification"). t08 (MZ
regression) vs t09 (encompassing regression) — split, different regression
specifications answering different questions (individual predictive power vs relative
information content / dominance). t01 (SV milestone + range-estimator history +
ARCH/GARCH review + CARR's stated gap/contribution) — kept merged, one literature-
positioning need ("how does CARR relate to and improve on competing volatility-modeling
traditions").

Unassigned: b001, b002 — generic "volatility modeling matters to research/policy/market
stability" motivational preamble (derivatives market growth, Barings/Orange
County/LTCM), no actionable technical content and not resolved by any one specific later
section, so neither merged as a distributed span nor treated as content. b057 — a
section-3 wrap-up sentence synthesizing RMSE/MAE (Table 4), Mincer-Zarnowitz (Table 5),
and encompassing (Table 6) findings into one "ECARR is sharper" takeaway — recap-shaped
across three already-covered themes.

## StaricaGranger2005NonstationaritiesStockReturns.md (60 blocks, 4 trash spans)

Output: `eval/queries/pass_b_runs/StaricaGranger2005NonstationaritiesStockReturns.pass_b.json`
— 8 themes, 0 resplits, 0 unassigned blocks, 60/60 assignable blocks covered —
7.5 blocks/theme, above the Bollerslev1986GARCH calibration anchor.

Section 5 (Conclusions) was pre-excluded as Pass A trash (near-verbatim restatement of
the abstract), leaving no post-hoc unassigned-recap decision to make for this document.

3 of 8 themes are distributed. t02 (homogeneity-interval concept + KS-functional
decision procedure) and t03 (periodogram/Kiefer-Muller/Theorem 2.1 theory) are mutually
interposed — t03's dense theoretical build-up is threaded through by t02's single
procedural block (b017), the reverse of the caption-trash pattern seen in the other two
lot11 documents: here the interposing content is itself a real theme, not trash. t08 is
the textbook intro-poses/section-resolves pattern: the introduction (lines 41-44)
explicitly frames the LM-vs-SM forecasting-model choice as a question the paper's
"second half" will settle, and Section 4 (lines 227-313) is exactly that resolution —
joined as one distributed theme per the established precedent rather than left as
recap-shaped preview, since it previews exactly ONE later section, not several.

Split-test applied: Section 3 "Data analysis" (originally one Pass-A-adjacent run of 29
blocks, b024-b052) was split 4 ways — t04 (ARMA(1,1) local test, white-noise finding
within intervals), t05 (piecewise mean/variance model + long-run regime findings
1928-2000), t06 (extension to absolute returns + post-1953 simplified model), t07
(robustness: constant-sigma check, 1987 crash exception, t-statistic alternative test)
— each a self-standing single-search question with no realistic query needing all four
at once. t03 (periodogram definitions vs the Theorem 2.1 statement itself) was
considered for a further split and kept merged: a bare periodogram/spectral-density
definition is never its own search (fails the standalone-search test), it only matters
in service of the asymptotic result it builds toward.

## Verification performed

`eval/scripts/validate_pass_b.py` run against each document's Pass A JSON and source
markdown: schema, span-bounds, intra-theme overlap, trash-disjointness, resplit-boundary
(n/a all three docs, zero resplits), full block-coverage, soft-member containment (n/a,
zero soft members used in this lot), the 2.0 blocks/theme floor, and the zero-tolerance
proof-label gate. All three passed on the first attempt:
`OK validate_pass_b: 15 themes, 0 resplits, 2 unassigned blocks` (Cont2001),
`OK validate_pass_b: 10 themes, 0 resplits, 3 unassigned blocks` (Chou2005),
`OK validate_pass_b: 8 themes, 0 resplits, 0 unassigned blocks` (StaricaGranger2005).
Opus reviewed the pre-write plan, corrected the invalid t08a/t08b id format to the
required sequential t01-t15 scheme for Cont2001, and explicitly endorsed the
content — the volatility-clustering/leverage split, the ECARR/WCARR and MZ/encompassing
splits with their interposition-driven distributed spans, the StaricaGranger Section-3
four-way split, and the intro-poses/Section-4-resolves distributed theme — before Go.
Not verified: no semantic/LLM cross-check of theme-need wording quality beyond the
reasoning recorded per theme above; no soft-membership use was attempted in this lot
(unlike lot10) since no cross-theme shared-lemma pattern was present in these three
documents.
