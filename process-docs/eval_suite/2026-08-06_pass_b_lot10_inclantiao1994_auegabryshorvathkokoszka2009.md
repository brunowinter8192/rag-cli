# Pass B Theme Formation — lot10: InclanTiao1994CumulativeSumsSquaresVariance, AueGabrysHorvathKokoszka2009ChangePointMeanFunction (2026-08-06)

Fresh-worker Pass B over two documents' Pass A output, run one after the other. Both are
change-point-detection papers with substantial appendix proof sections, making them a
direct R7b test case (theorem + appendix proof = one distributed theme; no standalone
proof themes).

## InclanTiao1994CumulativeSumsSquaresVariance.md (85 blocks, 9 trash spans)

Output: `eval/queries/pass_b_runs/InclanTiao1994CumulativeSumsSquaresVariance.pass_b.json`
— 17 themes, 0 resplits, 1 unassigned block, 84/85 assignable blocks covered —
4.94 blocks/theme (below the Bollerslev1986GARCH calibration anchor of 5.6, well above
the validator's 2.0 floor).

Themes track the paper's structure: prior-literature survey; Dk statistic definition
+ visual behavior (distributed around Figure 1's trashed captions); Dk's relation to
the F-test and likelihood-ratio test (distributed around Table 1/Figure 2, kept merged
after a split-test check — both jointly ground "why Dk is a valid change detector",
neither stands alone as a real search); critical values/quantiles of max|Dk| (Table 1 +
Section 2.3's empirical-vs-asymptotic validation, distributed around the intervening
Theorem 1 material); expected-Dk shape under one change (distributed, absorbing the
forward-referenced Figure 2); masking effect + the ICSS algorithm itself, merged into
one 4-span distributed theme after a split-test check — masking-cause and
algorithm-mechanics were considered for separation but kept merged since the ICSS
algorithm's entire purpose is solving masking, so no realistic query searches the cause
without the fix; a standalone Appendix-A theme for the Taylor-expansion derivation of
approximate E[Dk] across all three change scenarios (treated as its own "derivation"
need rather than forced into either the one-change or two-change body theme, with
cross-links back to those themes via soft membership); Theorem 1 (Brownian-bridge
convergence) merged with its Appendix B proof per R7b; the IBM real-data example;
the LR-based and Bayesian posterior-odds decision procedures (each distributed around
interposed tables); Table 4/5 empirical results (each distributed, paired with its own
Section 4.2/4.3 discussion); the k* sampling-distribution precision theme (Tables 6+7);
AR(1)-residual robustness; and the CPU-time cost-comparison theme.

Split-test applied: t03 (F-test-relation vs likelihood-ratio-derivation) — kept merged,
one "statistical grounding of Dk" question. t06 (masking-cause vs ICSS-mechanics) —
kept merged, see above.

Soft membership: Appendix A's per-case formulas cross-linked to the body themes they
underlie — b072 (homogeneous-variance case, E[Dk]~=0) also_in the Dk-definition theme
(t02, whose opening claim it derives); b073/b074 (one-change case, eq. A.6) also_in the
single-change-shape theme (t05); b075/b076 (two-change case, eq. A.7/A.8) also_in the
masking/ICSS theme (t06). This kept Appendix A as one coherent derivation unit (avoiding
fragmenting it across three themes' primary spans) while still surfacing its relevance
to each consuming body section for retrieval.

Unassigned: b043, Section 4.1's intro paragraph, previews both the LR-based decision
strategy (t10) and the Bayesian posterior-odds procedure (t12) — recap-shaped preview
spanning two different themes' resolved content.

## AueGabrysHorvathKokoszka2009ChangePointMeanFunction.md (47 blocks, 5 trash spans)

Output: `eval/queries/pass_b_runs/AueGabrysHorvathKokoszka2009ChangePointMeanFunction.pass_b.json`
— 8 themes, 0 resplits, 1 unassigned block, 46/47 assignable blocks covered —
5.75 blocks/theme, matching the Bollerslev1986GARCH calibration anchor of 5.6.

This is a pure-theory paper (functional-data change-point estimator, two limit
theorems, all proofs relegated to Section 4 + two verification appendices) and is
precisely the batch01-failure shape the R7b rule targets: naive per-section
segmentation would have produced standalone "Proof of Theorem 2.1" / "Proof of
Theorem 2.2" / "Appendix A" / "Appendix B" themes (four of batch01's ten banned
standalone-proof themes were this exact pattern). Instead: Theorem 2.1 (constant-size
change) is one 5-span distributed theme covering the statement, the shared
criterion-decomposition setup (Section 4.1), its two-lemma proof (Section 4.2), and
Appendix A's verification lemmas, which the proof explicitly invokes ("It is shown in
the Appendix that this deterministic part is the dominating term"). Theorem 2.2
(vanishing-size change) is a parallel 3-span distributed theme covering the statement +
rate condition, its Section 4.3 proof, and Appendix B's verification lemmas (same
explicit invocation pattern). The Section 4.1 criterion-decomposition blocks
(b027/b028/b030-b033) are used verbatim by both theorems' proofs — assigned primary to
Theorem 2.1's theme (introduced there first, "we proceed with the proof of Theorem 2.1
in the next subsection") and soft-flagged also_in Theorem 2.2's theme, the correct R8
use for genuine cross-theorem lemma reuse rather than duplicating spans.

Remaining themes: the functional mean-shift model + covariance eigenstructure setup;
the pre-existing Berkes et al. test statistic + its limit theorem (background, no proof
merge needed — the proof lives in the cited external paper, not this one); the
change-point estimator definition + its behavior-under-the-alternative setup (kept
merged after a split-test check — Proposition 2.1, the KA decomposition, and the PC
scores are prerequisite machinery consumed by both theorems, never searched standalone);
a genuinely standalone single-block theme for the estimator's consistency-failure
condition (b019: the full claim — inconsistency when the change is orthogonal to the
leading eigenspace, plus the large-d impracticality caveat — lives entirely inside one
block, meeting the single-block-theme legitimacy bar); and two finite-sample-validation
themes (Table 1 for the constant-size case; density-plot Figures 1/2 for the
vanishing-size case, distributed around a caption-trash gap and Figure 2's caption,
which floats into Section 4's proof text due to page-layout, non-adjacent to the rest
of the simulation discussion).

Split-test applied: t01 (model-definition vs Karhunen-Loeve/Mercer eigen-machinery) —
kept merged, one "model setup" question, the KL representation IS how the model's error
term is expressed. t03 (estimator definition vs HA-eigenstructure/regimes) — kept
merged, see above.

Unassigned: b010, a paper-roadmap paragraph ("This will be done in Section 2 ...
Section 3 ... Section 4 ...") previewing content resolved across three different later
themes (estimator+theorems, simulation, proofs) — recap-shaped, not a single realistic
search need.

## Verification performed

`eval/scripts/validate_pass_b.py` run against each document's Pass A JSON and source
markdown: schema, span-bounds, intra-theme overlap, trash-disjointness, resplit-boundary
(n/a both docs, zero resplits), full block-coverage, soft-member containment, the 2.0
blocks/theme floor, and the zero-tolerance proof-label gate. First pass failed on both
documents: the zero-tolerance proof-label regex (`\bproofs?\b`, case-insensitive) matched
theme labels that parenthetically said "(with proof)" even though the underlying spans
were correctly R7b-merged (theorem statement + proof as one distributed theme, not a
standalone proof theme) — a labeling issue, not a structural one. Fixed by dropping the
"(with proof)" suffix from three labels (InclanTiao1994's Theorem 1 theme; AueGabrys'
Theorem 2.1 and Theorem 2.2 themes) without touching spans or need text. Re-run passed
on both: `OK validate_pass_b: 17 themes, 0 resplits, 1 unassigned blocks`
(InclanTiao1994) and `OK validate_pass_b: 8 themes, 0 resplits, 1 unassigned blocks`
(AueGabrysHorvathKokoszka2009). Opus reviewed the pre-write plan and directed no
corrections before Go, explicitly endorsing the R7b theorem+proof merges, the
shared-decomposition soft-membership (R8), and the standalone Appendix-A
derivation-as-its-own-need call. Not verified: no semantic/LLM cross-check of theme-need
wording quality beyond the reasoning recorded per theme above.
