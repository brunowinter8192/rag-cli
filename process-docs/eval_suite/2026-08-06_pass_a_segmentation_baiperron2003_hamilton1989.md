# Pass A Segmentation Run — BaiPerron2003 and Hamilton1989 (2026-08-06)

Applied `eval/queries/prompts/segmentation_prompt_pass_a.md` (R1-R4, R3b) to two
`data/documents/trading-reference/` papers, one after the other:

- `BaiPerron2003MultipleStructuralChange.md` (440 lines, applied-econometrics paper on
  estimating/testing multiple structural breaks) → `eval/queries/pass_a_runs/
  BaiPerron2003MultipleStructuralChange.pass_a.json` — 95 blocks, 10 trash spans.
  Validator: `OK validate_pass_a: 95 blocks, 10 trash spans, 440 lines covered`
  (median block size 2 lines, 21.6 blocks/100 lines).
- `Hamilton1989RegimeSwitchingBusinessCycle.md` (884 lines, formula-dense regime-switching
  filter/smoother derivation + GNP application) → `eval/queries/pass_a_runs/
  Hamilton1989RegimeSwitchingBusinessCycle.pass_a.json` — 88 blocks, 6 trash spans.
  Validator: `OK validate_pass_a: 88 blocks, 6 trash spans, 884 lines covered`
  (median block size ~7 lines, 9.95 blocks/100 lines).

Both well inside the ≤25 median / ≥4.0 per-100 corridor on the first attempt.

## Ground-truth line numbers via `Read`, not the embedded prompt text

The task prompt embeds the full documents with line numbers, but manual retyping/paraphrase
of a ~900-line formula-dense document from memory drifted (verified against itself twice,
got two different answers for the same boundary). Recovered by `Read`-ing the actual source
files from `data/documents/trading-reference/` directly and using those line numbers as
ground truth for every span boundary — eliminates the drift risk entirely for documents this
long; the embedded prompt text is fine for content/subject judgment but not a substitute for
a direct line-numbered read when transcribing exact spans.

## Mid-sentence interposition handling (table, footnote, and pure blank-line cases)

Three distinct patterns, given three distinct treatments:

- **Pure blank-line split of a running sentence** (PDF line-wrap artifact, no text in
  between): merge the two fragments into one block spanning the blank line — e.g. Hamilton
  lines 17/19 (`...accumulated` / `abundant evidence...`) and 25/27 (`...at most one turning`
  / `point observed...`), each one block.
- **Table/figure with real content interposing mid-sentence**: the table/figure becomes its
  own content block; the sentence fragment before it stands as its own block, and the
  completion fragment after merges FORWARD into the next coherent block (not back into the
  fragment before). Applied at BaiPerron 145/147-150/151 (β̂ⁱ formula split by the copyright/
  citation footer — treated as conversion_residue trash, not real content, so this is really
  the footer sub-case below) and 185/187-190/191; and at Hamilton 581/583-596/597 (Table I
  interposes the GNP-data-description sentence).
- **Interposed footnotes**: fold into the block of the paragraph they annotate rather than
  standing alone, UNLESS a footnote carries a genuinely self-standing claim independent of
  the surrounding text (precedent: Bollerslev's GARCH(1,2)/(2,1) fourth-moment footnote).
  Applied at Hamilton 603-604 (GNP data-vintage descriptor + DFP-maximization robustness/
  thanks note, both folded into b050 covering 601-605) — neither is self-standing enough to
  break the fold-in default.
- **Repeated page-footer noise** (BaiPerron's "Copyright 2002 John Wiley & Sons, Ltd." / "J.
  Appl. Econ. 18: 1-22 (2003)", recurring at 4 page breaks: 91-94, 147-150, 187-190, 245-248):
  classified `conversion_residue`, not folded into surrounding content, since it is pure
  print-artifact junk rather than a real footnote or caption.

## Algorithm-STEP blocks kept atomic (extends the proof-atomicity precedent)

Hamilton's paper states its filter and smoother as literal `STEP 1:` ... `STEP 5:` sequences.
Per R2 (same-object elaboration is not a subject shift) and by analogy to the proof-atomicity
carve-out, each STEP sequence was kept as one block rather than split at step labels:
b036 (439-476, basic filter STEPS 1-5, 38 lines) and b045 (559-578, full-sample smoother
STEPS 1-2(a-c), 20 lines). Both stayed under the 50-line large-block threshold on their own,
but the same reasoning (no genuine subject shift between dependent algorithm steps) was
applied even though neither strictly needed the >50-line justification.

## Trash classification calls

- BaiPerron 438-440 (`## ACKNOWLEDGEMENTS` + paragraph): kept as CONTENT, not folded into
  `title_author`, because the paragraph states where the GAUSS code is archived (JAE Data
  Archive / econ.bu.edu/perron) — a standalone actionable claim, not pure thanks/funding
  boilerplate.
- BaiPerron 57-76: the Figure 1 triangular-matrix table is heavily OCR-mangled (`x^a`/`x^b`/
  `x^c` fragments, broken cell alignment) and unreadable as extracted text → `conversion_
  residue`. Its accompanying Notes block (77-90), by contrast, explains the figure's notation
  in clean prose and was kept as content, per the caption-substantiveness rule.
- Hamilton's Figure 1 (606-611) and Figure 2 (643-685) captions/panel content were kept as
  content blocks throughout, never `caption_stub`: Figure 1's caption spells out how to read
  panels A/B, and Figure 2's block contains real fitted-model equations and AR(4) regression
  coefficients, not orphan labels.
- Both documents' conclusion sections (BaiPerron 434-437, Hamilton 878-881) classified
  `abstract_summary`: both purely recap results already stated in-body, with no standalone
  claim not made elsewhere.

## Verification performed

Structural only: `validate_pass_a.py` run against each JSON and its source document —
schema check, trash-type whitelist, full line coverage with no gaps/overlaps, and the
granularity corridor — all passing in one run per document, no iteration needed. Not
verified: no LLM/semantic cross-check of individual subject-shift judgments beyond the
reasoning recorded per block/trash-span above — that is Pass B's territory if a block turns
out to straddle two topics.
