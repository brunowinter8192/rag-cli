# Pass D Query Authoring — Lot04 (3 Documents, 39 Themes / 117 Queries) (2026-08-10)

Applied `eval/queries/prompts/query_prompt_pass_d.md` (R16-R20) to three Pass C summary sets:
`BaiPerron2003MultipleStructuralChange` (17 themes), `Hamilton1989RegimeSwitchingBusinessCycle`
(14 themes), `Patton2011VolatilityForecastImperfectProxies` (8 themes). Output:
`eval/queries/pass_d_runs/<doc>.pass_d.json` per document, 51/42/24 queries respectively —
`validate_pass_d.py` OK on all three on the committed content.

## Method: local re-implementation of the validator's stem/overlap logic, checked pre-write

Same approach as lot01-lot03: replicated `stem()`, `check_head_concept()` (via direct import of
`eval/scripts/validate_pass_d.py`, not a hand copy), and the overlap ratio in a `/tmp` script; ran
every draft through it during the pre-flight (sample queries shown to the orchestrator before Go)
and again for the full 117-query set after Go, before writing any deliverable file. Ran the real
`eval/scripts/validate_pass_d.py` CLI per document as the final gate — all three printed OK.

## Guardrail: 0.72 rewrite-trigger below the 0.80 formal ceiling

First full-batch pass produced 18 overlap violations (>0.80) concentrated in `natural_question` and
`field_sentence`: BaiPerron t04 fs 0.91, t12/t13/t15 nq ~0.82; Hamilton t01 nq/fs 0.83/0.85, t02 nq
0.81, t06 fs 0.91, t08 fs 0.86, t12/t13/t14 nq 0.85-0.89; Patton t04 nq 0.96 (near-verbatim of the
information_need — a first-draft slip, not a borderline case), t06 nq 0.81. Root cause matched prior
lots: drafts followed the need sentence's own clause order and reused its multi-word phrase clusters
directly. Rewrote all 18 with situational framing (practitioner voice, restructured clause order,
angle-shift rather than synonym-swap), then swept a second time for anything still above the
orchestrator-set 0.72 self-trigger (14 more queries in the 0.72-0.79 band) and a third time for the
2-3 queries still sitting exactly at 0.72. Final per-document maxima: BaiPerron 0.69 (t16 nq),
Hamilton 0.68 (t07 fs), Patton 0.67 (t05 nq) — all comfortably under both the self-trigger and the
0.80 ceiling.

## Orchestrator correction: primary_concept as grammatical subject, not a discarded aside

Mid-task the orchestrator flagged that a mechanically-passing `natural_question` pattern
("X aside, what is ...?") inverts the concept's role — it dismisses the primary_concept as a scene-
setting clause rather than making it the subject of the question. `check_head_concept` only verifies
the concept's stemmed tokens appear in the sentence's leading clause, so this pattern passes the
validator but violates the R16b intent. Fixed by standardizing on two constructions that keep the
concept as true grammatical subject: `How does <primary_concept> ...?` / `Does <primary_concept>
...?` for direct questions, and `<Primary concept> is <situational framing>, but/and <question>?`
(comma-plus-conjunction before the interrogative clause, so `leading_clause`'s break regex still
captures the concept-bearing lead-in) for situated framings. Applied across all three documents
after the correction, not just to the flagged BaiPerron t01 example.

## Secondary defect caught only by direct string inspection, not the validator

Three `natural_question` entries (Hamilton t11, Patton t02, Patton t07) were declarative sentences
ending in a period, not a question — the validator has no check for R17's "ONE grammatical question"
requirement, only for head-concept and overlap. Caught by a manual `.endswith("?")` sweep over all
117 queries before final write; all three rewritten to end in `?` while preserving their overlap and
head-concept status.

## R16 field-owned additions beyond summary vocabulary (audit)

Minimal, traceable to each theme's `information_need` or `sub_concepts`; no invented concrete
conditions, values, or named results beyond what each summary supports:
- BaiPerron t13: "Schwarz-type penalized criterion" as the standard field paraphrase of the
  summary's "Bayesian information criterion" / "modified Schwarz criterion" sub_concepts.
- Hamilton t05: "diagonalizing a transition matrix" as the standard field description of the
  summary's "eigenvalue decomposition" sub_concept applied to a "vector recursion".
- Patton t02: "quadratic loss" / "absolute-deviation loss" as standard field synonyms for the
  summary's "MSE loss" / "mean absolute error loss" sub_concepts, used to avoid literal reuse.

## Angle differentiation for identical-primary_concept themes

Patton t01 and t04 share the identical `primary_concept` ("robust loss function"): t01 kept to the
single-loss necessary-condition register matching its `answer_type` ("definition plus necessary
condition"), t04 to the general-class/derivation register matching its `answer_type` ("method
derivation of a functional form") — verified no cross-theme phrase collision by direct diff of the
two drafts before Go.
