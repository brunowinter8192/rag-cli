# Pass C Theme Summaries — lot09: BengioGrandvalet2004KFoldCVVariance, Cont2001EmpiricalPropertiesAssetReturns (2026-08-09)

Fresh-worker Pass C over two documents' Pass B spans (spans-only input, no need
sentences or labels — need derived fresh from each theme's passage text via line
spans into the source `.md`). Both documents validated OK on first attempt, no
fix rounds needed.

## BengioGrandvalet2004KFoldCVVariance.md (8 themes)

Output: `eval/queries/pass_c_runs/BengioGrandvalet2004KFoldCVVariance.pass_c.json`
— 8 summaries, word budget 60-76 (of the 60-90 range), `validate_pass_c` OK.

Themes trace the paper's structure: hold-out variance estimation and test-error
correlation motivation (t01), the K-fold CV formal setup and which estimand
(single-training-set vs training-set-averaged error) it targets, plus the
paired-difference/jackknife variants (t02), the covariance-matrix block-structure
derivation via permutation symmetry (t03), the non-existence-of-unbiased-estimator
theorem via quadratic-form/moment-matching (t04), the eigendecomposition
explaining why the overall-mean component can't be estimated from one realization
(t05), the admissible-range bounds on the covariance parameters (t06), the
simulation experiments on variance-component magnitude vs sample size/outliers/
fold count (t07), and the special-case specializations — hold-out, two-fold,
leave-one-out (t08).

## Cont2001EmpiricalPropertiesAssetReturns.md (15 themes)

Output: `eval/queries/pass_c_runs/Cont2001EmpiricalPropertiesAssetReturns.pass_c.json`
— 15 summaries, word budget 63-74, `validate_pass_c` OK.

Themes trace: non-parametric method rationale and return/time-scale notation (t01),
the stylized-fact concept itself (t02), stationarity and ergodicity as
preconditions for pooling return data (t03), heavy-tailed distribution family
selection and kurtosis diagnostics (t04), tail-index estimation via sample-moment
convergence (t05), extreme value theory and the block-maxima GEV fit for
value-at-risk (t06), linear autocorrelation absence and its market mechanisms
(t07), volatility clustering as genuine nonlinear dependence (t08), the leverage
effect vs other nonlinear-dependence measures motivating the stochastic-volatility
decomposition (t09), sample-ACF reliability under heavy tails (t10), random
matrix theory as a noise benchmark for the cross-asset correlation matrix (t11),
tail dependence between assets vs covariance-based measures (t12), the Hölder
exponent as a pathwise-roughness target for stochastic models (t13), the
singularity spectrum recovered via the multifractal formalism (t14), and
cross-asset spectrum universality vs finite-sample-artifact risk (t15).

## Notes on this session

Applied Opus's hyphen-free directive (from a prior lot's discovered validator
mechanic — hyphenated compounds written as one token collapse to a merged stem
under `check_primary_concept_leads_need`'s suffix-stripping and silently fail to
anchor) proactively before writing any JSON: compound modifiers de-hyphenated
(`test error correlation`, `hold out estimate`, `within block covariance`,
`bid ask bounce`, `power law decay`, `heavy tailed`, `non parametric`,
`non Gaussian`), while intrinsic-name hyphens (`Cauchy-Schwarz`, `Hölder`) were
kept since they are proper-noun compounds, not modifier compounds, and the
practitioner-test spelling requires the hyphen.

t15 (Cont) was deliberately framed as an open finite-sample-artifact question
("is the observed cross-asset spectrum shape genuine, or could it arise even
from non-multifractal data") rather than asserting the paper's caution as
established fact — R11-compliant indicative framing for a theme whose passage
content is itself a methodological caveat.

Both documents shared primary_concept="singularity spectrum" across two themes
(t14, t15) — differentiated by situation per R12's ordering rule: t14 is the
derivation/formalism question, t15 is the cross-asset-universality/reliability
question.
