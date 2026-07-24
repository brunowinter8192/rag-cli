# Two-Pass Segmentation: Design Decisions from Joint Review (2026-07-24)

Records the decisions from the joint rule-by-rule review that produced
`eval/queries/segmentation_prompt_pass_a.md` (approved, first run executed same day) and
`segmentation_prompt_pass_b.md` (DRAFT — R5-R10 not yet jointly reviewed). Framed as of
2026-07-24. The literature grounding per rule lives inline in the prompt files themselves
(deliberate: the prompts are the reusable suite artifact and must be self-justifying).

## Eval target is the TRADING corpus — methodology examples were only didactic

The eval runs against `trading-reference` (the ~80-paper statistics/trading corpus that
batch01 was built from); `rag-cli-reference` is methodology literature only. RAGAS.md, used
throughout the discussion as the worked example (three-metrics over-merge, distributed
faithfulness), is NOT in the target corpus. Consequences: prompts are corpus-agnostic; the
validation run went straight to a target-corpus paper (Bollerslev1986GARCH.md, formula-
dense, 10 ad-hoc batch01 regions available as comparison foil) instead of RAGAS.

## Atom rule: blank line is the ONLY legal cut point — no special atoms

Initial proposal had headings/tables/formula blocks as separate attachable atoms. Rejected
after inspecting Tsay2010 §4.1.4 (Markov switching): MinerU output blank-line-separates
every display formula, with one-sentence connectors between formulas — special atoms would
shatter formula-dense sections. The blank line catches everything: boundaries may only sit
at blank lines, but not every blank line is a boundary. A formula↔prose alternation on one
running argument stays one block; the boundary falls where the argument changes.

## Two passes, two SEPARATE workers (fresh LLM for pass B)

- **Pass A** — linear shift detection only, deliberately dumb (the LumberChunker-validated
  regime). No theme grouping, no need definitions, no grading.
- **Pass B** — meta view over the finished block list: group distributed blocks into
  themes, re-split too-coarse blocks. The split test ("do subsets of a theme's blocks each
  answer a self-standing single-search question?") is structurally impossible on-the-fly
  during linear processing — it needs the completed block list. That is WHY pass B exists
  as a separate run.
- **Fresh worker for pass B** (user decision, reversing the initial same-worker-warm-context
  idea): an unbiased second LLM reviews the blocks without the pass A segmentation history
  in context — a cross-model check by construction. Written into the pass B prompt header.
- Atom rule holds across passes: pass B re-splits also only at blank lines.

## Need level: fixed by what the eval measures, not by linguistics

Needs nest hierarchically (formula ⊂ model ⊂ model family); the level is pinned by two
prior facts: (1) the measured real query distribution (53 dual_log queries) is multi-concept
need queries — symbol/formula lookups effectively absent; (2) the eval unit is the REGION
with expansion-aware metrics — single-formula themes would make expansion-coverage
meaningless. A formula needed for case z is a FACT inside its parent theme (found via
region hit + expansion), not a theme. Operationalized as three tests in the pass B prompt:
one-question test, fact-fold test (too fine), split test (too coarse). Calibration anchor:
batch01 grain (~3-4 regions/need).

## Grading dropped from segmentation

Segmenter output carries NO grades (core/context) — user decision: grading on top of
boundary+grouping judgment overloads the LLM task and is harder to define. Grades enter
later in the pipeline (batch01 format keeps them).

## Trash classification: a metric and a cleanup feedback loop, not just exclusion

Excluded material is classified by type (abstract_summary, title_author, references,
toc_index, caption_stub, conversion_residue). Two consumers:
1. **Retrieval metric:** the 2026-07-23 decision keeps corpus garbage indexed ("good
   retrieval must not surface it") — trash-typed spans make that measurable as a
   trash-rate-in-top-k figure.
2. **PDF-cleanup rules:** observed trash types feed new cleanup-class definitions for the
   PDF conversion skill.
Readability rule (user): compressed words ("lthoughvolatilityisnotdirectlyobservable...")
and spaced math are NOT trash while readable and content-extractable — they stay in their
content block. Sharpened during the first run's dispatch: trash spans obey the blank-line
atom rule like content blocks; a mid-paragraph artifact NOT cleanly blank-delimited stays
in its block.

## First pass A run (same day): rules held

Bollerslev1986GARCH.md, 528 lines → 45 blocks + 9 trash spans; independently re-verified
(full 1..528 coverage, zero overlaps, all 54 boundaries on blank lines). Boundary calls
sound on sample review (prose→equation cut only at argument change; appendix proofs kept
atomic as one derivation of one theorem; substantive numbered footnote kept as content).
Run details + span-ownership convention: see the run entry of this date. Observation
parked for the pass B review: the line-18 footnote excision splits one paragraph into
b001/b002 ("cont.") — exactly the kind of fragment pass B should re-merge.

## Sources

- `eval/queries/segmentation_prompt_pass_a.md`, `segmentation_prompt_pass_b.md` (DRAFT)
- `eval/queries/pass_a_runs/Bollerslev1986GARCH.pass_a.json`
- `data/documents/trading-reference/Tsay2010AnalysisFinancialTimeSeries.md` §4.1.4 (atom-rule test read)
- `eval/queries/batch01_regions.json` (grain anchor; 7 papers incl. Bollerslev1986GARCH)
