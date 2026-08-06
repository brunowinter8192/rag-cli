# Pass A Segmentation Run — Cont2001, Chou2005 CARR, StaricaGranger2005 (2026-08-06)

Applied `eval/queries/prompts/segmentation_prompt_pass_a.md` (R1-R4, R3b) to three
`data/documents/trading-reference/*.md` papers:

- `Cont2001EmpiricalPropertiesAssetReturns.md` (443 lines, stylized-facts survey) →
  71 blocks, 11 trash spans.
- `Chou2005CARRConditionalAutoregressiveRange.md` (465 lines, CARR model paper with
  JSTOR front matter and 6 result tables) → 61 blocks, 11 trash spans.
- `StaricaGranger2005NonstationaritiesStockReturns.md` (324 lines, non-stationarity paper
  with one formal theorem and dense figure captions) → 60 blocks, 4 trash spans.

All three validated clean on the first `validate_pass_a.py` run: full coverage, no
gaps/overlaps, granularity corridor met with margin (medians 2-4 lines, 13-19 blocks/100
lines vs the ≤25 / ≥4.0 gate).

## Method: anchor-resolution script instead of manual blank-line arithmetic

Departure from the grep-blank-line approach used in prior sessions (see
`2026-08-06_pass_a_segmentation_nadeaubengio2003.md` for that method): content judgment
was done by reading each full source document via `Read` once, then instead of manually
computing `line_start`/`line_end` by counting, an ordered list of
`(kind, subject_or_trash_type, unique_anchor_substring)` tuples was written per document
and resolved against the actual file lines in one pass — each anchor located via forward-
only sequential substring search (never regex, to sidestep LaTeX-heavy `$`/`\` escaping),
`line_end` computed as `next_item.line_start - 1`, last block extended to EOF. This
eliminates two failure modes observed while manually re-deriving line numbers from a
pasted/transcribed copy of the document mid-session: (1) transposition errors when
re-typing paragraph-opening text, (2) drift when re-counting blank lines after an earlier
miscount. The anchor list itself still encodes 100% of the subject-shift judgment (R2/R3);
the script only removes arithmetic risk from converting that judgment into line spans. All
three documents resolved every anchor on the first script run with zero "anchor not found"
errors, and all three passed the validator with zero coverage/overlap errors — evidence the
approach is reliable, not just fast.

## Trash classification: title_author extended to acknowledgment/front-matter footnotes

Per explicit correction (consistent with the Bollerslev calibration precedent): an
acknowledgment footnote or thanks-paragraph is `title_author`, not left as an
uncategorized content block, even though R4's literal wording ("title, author list,
affiliations, emails, copyright") doesn't name acknowledgments outright. Applied to:
- Cont2001's `# Acknowledgments` section (441-443).
- Chou2005's five distinct front-matter fragments interleaved with the JSTOR/journal
  boilerplate and the body's opening sentence: the funding/thanks footnote (29), the
  author-bio footnote (31), and the received-date/journal-citation/copyright block
  (33-37) — all `title_author`, distinct from the JEL-codes/keywords line (23-25) which
  was also folded into `title_author` for lack of any better-fitting R4 type.
- StaricaGranger2005's `Acknowledgment.` closing paragraph (324) — `title_author`.

By contrast, Chou2005's **numbered in-text footnotes** (1-13, e.g. "7. A feasible
alternative estimation method is the GMM...") were NOT trashed — they were folded into
whichever content block they physically interrupt, since they annotate a specific claim in
the surrounding paragraph rather than being about the paper itself. This produced several
mid-paragraph "fold-through" blocks where a sentence starting before a footnote and ending
after it stays one block spanning the footnote lines (e.g. the range-history block
45-51 spans across footnotes 1-3 at 47-49).

## Mid-sentence trash interposition: figure captions and page-break front matter

Both papers have PDF-conversion artifacts where a genuinely mid-sentence blank-line split
has non-blank trash content sitting in the gap (not the "nothing between" case that simply
merges):
- Cont2001: 8 instances of a bare `![](images/...)` + one-line `Figure N. ...` caption
  interrupting a sentence (e.g. block ending at line 84 "...Since" / caption trash 86-88 /
  block resuming at 89 "in a typical macroscopic system..."). Handled by ending the first
  block right before the trash and starting a fresh block at the resumption point — never
  forcing a single block to span across a trash span, since block/trash ranges must be
  contiguous and non-overlapping.
- Chou2005: the paper's own opening sentence (line 27, "...important to researchers who
  are") is interrupted by the JSTOR-derived front matter (29-37, five lines of
  acknowledgment/bio/citation trash) before resuming at line 39 ("trying to understand the
  nature of the dynamics of volatilities."). Same split-block handling.

## Block-granularity principles applied

- **Atomic multi-step derivations**: Cont2001's Fisher-Tippett theorem + Cramer-von Mises
  parametrization + block-method MLE estimation (174-209, 36 lines) is one block — a
  single continuous theorem-to-estimator argument, not three subjects, per R3b's
  large-block carve-out (median-only gate, not a per-block cap).
  StaricaGranger2005's Theorem 2.1 (111-136, 26 lines, parts a+b) is likewise one block.
  StaricaGranger2005's reformulated orthogonality-test derivation (278-310, eq 4.10-4.14,
  34 lines) is one block for the same reason — one test being built up algebraically, no
  claim boundary to cut at.
- **Data tables are one block per table regardless of size**: Chou2005's Tables 1/3/5/6
  (27, 20, 28, 24 lines respectively) are each one block — same-object carve-out, a table
  of coefficients or forecast errors is not a sequence of shifting subjects.
- **Figure captions split by substantive content, not by document**: Chou2005's captions
  (`FIG. 1.` etc.) are one-line orphan labels with zero standalone content →
  `caption_stub` (4 spans). StaricaGranger2005's captions (`Figure 3.1 Left: ...`) run
  2-3 lines and state an actual finding (e.g. "Zero is most of the time covered by the
  interval") → kept as CONTENT blocks, never `caption_stub`, per R4's substantive-content
  test. Same taxonomy, opposite classification, driven entirely by caption content, not by
  which paper it's in.
- **`navigation_meta` applied narrowly**: only Chou2005's literal section-roadmap sentence
  ("The paper is organized as follows. We propose...Section 4 concludes...") — the
  substantive introduction paragraphs immediately before and after it stayed content.

## Verification performed

Structural only: `validate_pass_a.py` run against each of the three produced JSONs and
their source documents — schema, trash-type whitelist, full line coverage with no
gaps/overlaps, and the granularity corridor, all passing in one run per document (no
iteration needed, since the anchor-resolution script computes spans programmatically from
already-verified anchor positions). Not verified: no LLM/semantic cross-check of individual
subject-shift judgments beyond the reasoning recorded per block/trash-span above — Pass B's
territory if a block turns out to straddle two topics.
