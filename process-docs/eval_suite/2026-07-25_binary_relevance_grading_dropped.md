# Binary Relevance: Core/Context Grading Dropped as a Pre-Answerability Relic (2026-07-25)

Decision from the 2026-07-25 session: the eval ground truth uses BINARY region relevance —
no core(2)/context(1) grades, no grading pass. Framed as of 2026-07-25.

## Where the grades came from

The graded format ({document, line_start, line_end, grade}, 2=core, 1=context) was designed
2026-07-22/23, when regions were marked ad hoc — before the need level was defined. The
pattern follows INEX-style assessment: with a NARROW topic, a highlighted region contains
both the direct answer and surrounding derivation/setup, and a two-tier grade separates
them. On 2026-07-24 grading was removed from segmentation (overloads the LLM task) with the
note "grades enter later in the pipeline" — a deferral, not a decision to grade.

## Why grading contradicts the settled definitions

- R5 (2026-07-24): a theme is the ALL-AND-ONLY answer set of one realistic information
  need. The "only" half is a precision condition every span must justify — pure
  surroundings do not enter the theme at all (the paper-roadmap block was excluded on
  exactly this ground).
- The need level (R6) is the META case-match need — "does this methodology fit my case,
  under what conditions, derived how" — not a formula lookup. At that level, notation,
  setup, and derivation are PART of the answer, not context around it: the meta need
  swallows the surroundings.
- Consequence: a grade-1 span inside an answerability-defined theme is a contradiction.
  Either the span belongs to the all-and-only answer set (fully relevant) or it does not
  belong in the theme. Relevance is binary BY CONSTRUCTION at this need level.

## Consequences

- No grading pass in the pipeline (a drafted Pass E prompt was discarded unwritten).
- Metrics: region-recall and expansion-coverage unchanged (never needed grades); nDCG
  becomes binary.
- Scaling: one fewer LLM-judgment pass per document across the target corpus, and one
  fewer consistency surface to validate.

## Sources

- `eval/queries/prompts/segmentation_prompt_pass_b.md` (R5/R6 as applied)
- `eval/queries/pass_b_runs/Bollerslev1986GARCH.pass_b.json` (themes carrying no grades)
