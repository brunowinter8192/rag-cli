# Pass B Theme Formation — lot07: Tetlock2007GivingContentInvestorSentiment, HorvathKokoszkaReeder2013MeanFunctionalTimeSeriesTwoSample (2026-08-06)

Fresh-worker Pass B over two documents' Pass A output, run one after the other.

## Tetlock2007GivingContentInvestorSentiment.md (70 blocks, 3 trash spans)

Output: `eval/queries/pass_b_runs/Tetlock2007GivingContentInvestorSentiment.pass_b.json`
— 15 themes, 0 resplits, 4 unassigned blocks, 66/70 assignable blocks covered —
4.4 blocks/theme (below the Bollerslev1986GARCH calibration anchor of 5.6, above the 2.0
floor; several genuinely thin-but-standalone needs pull the average down).

Themes track the paper's empirical arc: motivation/data-source/prior-literature,
the competing sentiment/information/stale-information theoretical framework, GI
content-analysis tool mechanics (distributed with the Appendix), PCA factor construction
and stability, the VAR specification, the core Dow-return predictability result, reverse
causality (returns forecasting future pessimism), volume predictability, SMB/small-stock
predictability, one merged timing-robustness theme spanning Tables VI-VIII, subperiod
stability, nonlinearity (semiparametric), economic significance/trading-strategy
profitability, GI-category (Negative/Weak) robustness, and a standalone risk-premium
alternative-explanation theme. 2 of 15 themes are distributed: the intro (split only by an
excluded navigation-meta trash span) and the GI-mechanics theme (methodology intro merged
with the Appendix's category examples/limitations, per R7).

Split-test applied: prior-literature review (b005) was split from the formal
noise-trader/liquidity-trader theoretical framework (b006-011) — different searches
("what has prior work found" vs "what does the model predict"). GI-category
interpretability (b061-063) was split from the risk-premium alternative-explanation test
(b064) — different searches, and the latter (t15) is a single 1-block theme; confirmed
before writing that b064's own prose is a complete, self-contained "unreported test" with
its own result (conditional volatility of the Dow is higher, not lower, when pessimism is
high) and no associated table living elsewhere, so it earns its own theme rather than
attaching to t14. Tables VI/VII/VIII (Dow-return, volume, and SMB timing-robustness) were
considered for a 2- or 3-way split by dependent variable but kept as one 10-block theme —
one realistic question ("does the predictability survive a delayed measurement window?")
spans all three, and splitting further would approach the section-echo failure mode.

Unassigned: b056 (Section III summary — pure recap of t06/t08/t09/t11), and b065/b066/b067
(Conclusions — pure recap of t06/t08/t09/t10/t13/t14/t15, no standalone claim per the
established recap precedent).

## HorvathKokoszkaReeder2013MeanFunctionalTimeSeriesTwoSample.md (75 blocks, 5 trash spans)

Output: `eval/queries/pass_b_runs/HorvathKokoszkaReeder2013MeanFunctionalTimeSeriesTwoSample.pass_b.json`
— 15 themes, 0 resplits, 4 unassigned blocks, 71/75 assignable blocks covered —
4.7 blocks/theme (close to the Bollerslev1986GARCH calibration anchor of 5.6).

This document is the R7b showcase the rule set was written for: five of the paper's six
theorems (2.1, 2.2, 3.1/3.2 jointly, 3.3, 3.4) each pair a Section 2/3 statement with a
distant Section 5/6 proof as ONE theme — the exact failure mode the batch01 diagnosis
found (standalone "Proof of Theorem N" themes, zero distributed themes) does not recur
here. Non-theorem themes: intro/motivation, the weak-dependence (L2-m-approximability)
condition, the two-sample setup (location models/hypotheses/U_N,M), constructing the
implementable U(1)/U(2) statistics, estimating the covariance kernel d(t,s), the numerical
implementation algorithm, the simulation study, the medfly application, the Eurodollar
application (distributed around an intervening recap paragraph), and practical
statistic/dimension-p guidance. 6 of 15 themes are distributed in total.

Split-test applied: constructing U(1)/U(2) from empirical eigenprojections (b031-034),
their null distribution (Theorem 3.3, b035-036), and their behavior under the alternative
(Theorem 3.4, b037-038) were kept as three separate themes rather than merged into one
"test statistics" theme — a practitioner computing a p-value needs only the null-law
theme, not the power-theory theme; genuinely independent searches. b021 and b027 (each a
single transition sentence with no content of its own — "Theorem 2.2 is proven in Section
5", "we state two results...") were left unassigned rather than folded into an adjacent
theme, matching the transition-block precedent. b067/b068 (statistic choice and
dimension-p guidance) were kept merged — one "how do I use this test in practice" need.

Unassigned: b021, b027 (content-free transitions), and b064/b066 — a general Section 4.4
recap paragraph split by an intervening Table 4.4, restating a point ("formal tests detect
differences invisible to visual inspection") already made in the simulation study (t12);
b065 (the table itself, containing the actual Eurodollar samples-3-vs-4 p-values) stays in
t14 as a second, non-adjacent span.

## Verification performed

`eval/scripts/validate_pass_b.py` run against each document's Pass A JSON and source
markdown: schema, span-bounds, intra-theme overlap, trash-disjointness, resplit-boundary
(n/a both docs, zero resplits), full block-coverage, soft-member containment (n/a, no soft
members in either document), the 2.0 blocks/theme floor, and the zero-tolerance proof-label
gate all passed on the first attempt (no fix-and-rerun cycle needed) —
`OK validate_pass_b: 15 themes, 0 resplits, 4 unassigned blocks` for both documents.
Opus reviewed and approved the pre-write plan before the JSON was written, flagging one
specific check (confirm t15/b064 in Tetlock genuinely carries standalone test content
rather than just naming a result documented elsewhere) — verified as described above.
Not verified: no semantic/LLM cross-check of theme-need wording quality beyond the
reasoning recorded per theme above.
