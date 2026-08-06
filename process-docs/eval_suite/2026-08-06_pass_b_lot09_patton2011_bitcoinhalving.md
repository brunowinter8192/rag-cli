# Pass B Theme Formation — lot09: Patton2011VolatilityForecastImperfectProxies, BitcoinHalvingCycleVolatilityMSGARCH (2026-08-06)

Fresh-worker Pass B over two documents' Pass A output, run one after the other.

## Patton2011VolatilityForecastImperfectProxies.md (61 blocks, 7 trash spans)

Output: `eval/queries/pass_b_runs/Patton2011VolatilityForecastImperfectProxies.pass_b.json`
— 8 themes, 0 resplits, 8 unassigned blocks, 53/61 assignable blocks covered —
6.6 blocks/theme (above the Bollerslev1986GARCH calibration anchor of 5.6).

Themes: DMW test + Definition 1 of a robust loss function; squared-return-proxy
distortion (distributed — Table 1 is physically interposed inside the later
realised-volatility narrative, attaches to this theme by content not position);
realised-volatility/range-proxy distortion (distributed — spans around the
interposed Table 1); the four Propositions (1: necessary/sufficient robust form,
2: MSE/QLIKE uniqueness for error-only/ratio-only losses, 3+4: homogeneous
unit-invariant family) each merged with their Appendix proof as one distributed
theme per R7b (theorem+proof = one theme, no standalone proof themes); the
homogeneous-family theme additionally absorbs the Fig. 1/2 captions, which float
physically into Section 4's text but are referenced only from the Section 3/Appendix
discussion; the IBM empirical DMW comparison (distributed around the same floated
captions plus a trash caption-stub); and a small 2-block distributed theme joining
the introduction's general latent-variable-forecasting framing (citing GDP growth,
default probabilities) with the conclusion's "extending to other latent variables"
paragraph — the intro poses the general problem, the conclusion is the one section
that resolves it.

Split-test applied: the RV/range theme (16 blocks: RV def, range def, combined
optimal-forecast results across all loss functions incl. Table 2) was kept merged —
the realistic need is inherently comparative ("which proxy reduces distortion"),
and neither RV-only nor range-only sub-questions pass the standalone-search test.
The homogeneous-family theme (Prop 3 motivation + Prop 4 parametric family) was
kept merged — Prop 3 only motivates the answer Prop 4 delivers, one search. The
IBM empirical theme (setup + proxy list + Table 3 + significance discussion + MSE-
flexibility remark) was kept merged as one continuous empirical narrative.

Unassigned: b002-b009, the paper's introduction and notation section. Each block
was checked individually against the intro-poses/section-resolves pattern before
being left unassigned: b002 previews the entire noisy-proxy-distortion thesis
(resolved across every downstream theme, not one); b003 previews Section 2 as a
whole (t02+t03); b004's dominant content is the "two contributions" recap spanning
t02/t03 and t04/t05/t06 (a single Section-5 mention inside it was judged a minor
aside, not the block's core, since it cannot be resplit at sub-sentence level
without a blank line per R9); b005 previews t02+t03; b006 previews t04+t06; b007
and b008 are general framework/interpretive background owned by no single theme;
b009 is shared notation (r_t, sigma_t^2, h_t, L, Eq. 2) seeding every downstream
theme as background facts, not itself a search need. b001 was the one block
rescued from an initial "unassign the whole intro" draft on review: it poses
exactly the general latent-variable-forecasting problem (GDP growth, default
probabilities) that the conclusion's b057 resolves, and previews nothing else —
a clean single-theme intro-poses/section-resolves case, moved into t08.

Soft membership: b015 (catalog of nine candidate loss functions, shared setup
for both proxy sections) — core t02, also_in t03.

## BitcoinHalvingCycleVolatilityMSGARCH.md (77 blocks, 5 trash spans)

Output: `eval/queries/pass_b_runs/BitcoinHalvingCycleVolatilityMSGARCH.pass_b.json`
— 16 themes, 0 resplits, 1 unassigned block, 76/77 assignable blocks covered —
4.75 blocks/theme (below the Bollerslev1986GARCH calibration anchor of 5.6, still
well above the validator's 2.0 floor).

Themes track the paper's two objectives: halving-cycle description and adoption
context (cycle stages/sequences, institutional adoption trends); the safe-haven/
hedge testing thread (Baur-McDermott dataset/equations/benchmark, an alternative
threshold regime-switching framework considered and explicitly rejected, pre- vs
post-COVID results, correlation-table analysis); and the regime-switching-
volatility thread (MSGARCH model spec, out-of-sample VaR backtesting, descriptive
stats, in-sample model comparison). Five distributed themes: the halving-
independence causal argument (intro claim -> results confirmation -> conclusion
restatement, extended into the study's practical investment recommendation); the
regime-motivation literature (Section 1.1 preview fully elaborated by Section 2.3);
the gold/Bitcoin safe-haven dispute literature (intro's "digital gold" framing
elaborated by Sections 2.1/2.2); VaR backtesting (Section 3.3 protocol only
meaningful paired with Section 4.2.2 results); and the "regimes reflect volatility
level, not halving stage" finding (stated in results, extended in conclusion).

Split-test applied: the gold/Bitcoin literature-dispute theme (gold-specific vs
Bitcoin-specific studies) was kept merged — the paper frames Bitcoin as a
comparative "digital gold" alternative tested via identical methodology against
identical indices, making this one realistic comparative search rather than two.
Pre- vs post-COVID safe-haven results were kept merged — the paper's own stated
objective is the before/after comparison itself.

Revision during Opus review: b075 (conclusion paragraph containing the explicit
practitioner recommendation "investors should not invest in Bitcoin for Bitcoin
safe haven and hedge properties because time periods with those properties might
coincide with periods of negative correlation") was initially left unassigned as
recap-shaped. On review this was corrected: the recommendation is new synthesis
(halving-independence claim + literature's time-varying-properties finding ->
forward-looking recommendation), not a verbatim restatement, and was attached to
the halving-independence theme as a further distributed span (the direct practical
consequence of that same argument). The block's secondary content (gold ETF-
outflow explanation, "hasn't displaced gold" synthesis) was marked as a soft
member also_in the correlation-analysis theme rather than forcing a single-theme
assignment, since R9 forbids resplitting an atomic Pass-A block without an
internal blank line. b077's separate "Markov-switching model remains recommended"
recommendation sentence was already correctly assigned (not unassigned) prior to
review.

Unassigned: b020, a roadmap paragraph stating the study's twofold objective and
naming the two prior studies it extends — previews content resolved across two
different themes (regime literature, safe-haven literature), recap-shaped.

Soft membership: b060 and b075 (halving-independence conclusion content) — core
in the halving-independence theme, also_in the correlation-analysis theme.

## Verification performed

`eval/scripts/validate_pass_b.py` run against each document's Pass A JSON and
source markdown: schema, span-bounds, intra-theme overlap, trash-disjointness,
resplit-boundary (n/a both docs, zero resplits), full block-coverage, soft-member
containment, the 2.0 blocks/theme floor, and the zero-tolerance proof-label gate
all passed — `OK validate_pass_b: 8 themes, 0 resplits, 8 unassigned blocks`
(Patton2011) and `OK validate_pass_b: 16 themes, 0 resplits, 1 unassigned blocks`
(BitcoinHalvingCycleVolatilityMSGARCH), both on the first attempt after the
pre-write plan was revised (no JSON fix-and-rerun cycle needed). Opus reviewed the
pre-write plan and directed two specific corrections before Go: (1) the b075
recommendation-paragraph call above, citing a batch01 content-grading precedent
for this exact document that had kept equivalent recommendation sentences; (2) a
block-by-block re-audit of Patton2011's 9-block unassigned intro against the
intro-poses/section-resolves pattern, which surfaced b001. Not verified: no
semantic/LLM cross-check of theme-need wording quality beyond the reasoning
recorded per theme above.
