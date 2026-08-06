# Pass A Segmentation Run — InclanTiao1994 + AueGabrysHorvathKokoszka2009 (2026-08-06)

Applied `eval/queries/prompts/segmentation_prompt_pass_a.md` (R1-R4, R3b) to two documents in
`data/documents/trading-reference/`:

- `InclanTiao1994CumulativeSumsSquaresVariance.md` (596 lines, JASA paper on the ICSS algorithm
  for retrospective variance change detection) → `eval/queries/pass_a_runs/InclanTiao1994CumulativeSumsSquaresVariance.pass_a.json`
  — 85 blocks, 9 trash spans. Validator: `OK validate_pass_a: 85 blocks, 9 trash spans, 596 lines
  covered` (median block size 4 lines, 14.3 blocks/100 lines).
- `AueGabrysHorvathKokoszka2009ChangePointMeanFunction.md` (810 lines, functional-data
  change-point estimation paper: theorem/proposition statements, a proof section with four
  lemmas, two appendices of six further lemmas) → `eval/queries/pass_a_runs/AueGabrysHorvathKokoszka2009ChangePointMeanFunction.pass_a.json`
  — 47 blocks, 5 trash spans. Validator: `OK validate_pass_a: 47 blocks, 5 trash spans, 810 lines
  covered` (median block size 8 lines, 5.8 blocks/100 lines — matches the calibration median of 8
  exactly).

## Method: full disk read of both source files, not the embedded prompt text

The orchestrating session embedded both documents inline with line numbers, but the embedding
for the second document was truncated mid-formula near its end (cut off at line ~793 of 810).
Rather than trust the truncated embed, both files were re-read in full from disk (`Read` in
2-3 chunks each) and cross-checked against the embedded text for the overlapping region —
identical line-for-line, confirming the embed was a display truncation only, not a content
drift. All block/trash spans were built from the disk-verified line numbers. Segmentation
decisions (where a subject shifts) were made from the full read; span arithmetic (`start`,
`end = next_start - 1`) was done by hand this run, then double-checked by walking the full
sequence start-to-end verifying `next.line_start == prev.line_end + 1` before writing the JSON
— no gaps or overlaps on the first validator run for either document.

## Lemma-statement-plus-proof merge rule, applied consistently within each document

Per explicit orchestrator instruction this run: a lemma/proposition statement immediately
followed by its own "Proof. ... □" with no other content interposed is ONE block (the proof is
the same continuous argument about that exact claim). Where a claim's proof is NOT adjacent —
separated by other lemmas or sections — statement and proof are separate blocks, and Pass B is
left to link them. Applied in AueGabrysHorvathKokoszka2009:

- Theorem 2.1's statement (lines 192-215) sits ~260 lines before "Proof of Theorem 2.1"
  (474-475, a one-line pointer to Lemmas 4.1+4.2) — kept as two separate blocks, since the
  theorem's own proof is not adjacent to its statement.
- Lemma 4.1 (360-415, 56 lines) and Lemma 4.2 (418-473, 56 lines) each merge their own
  statement with their own immediately-following proof — one block each, both qualifying for
  the R3b large-block exception (one continuous proof argument).
- Lemma 4.4's proof (524-611, 88 lines) is the largest single block in either document: one
  unbroken weak-convergence argument (Skorohod-Dudley-Wichura representation, sup-bound chain)
  with no interior claim to anchor a legal subject-shift cut — kept atomic per R3b rather than
  split at the proof's internal step markers.
- The same statement+adjacent-proof rule was applied to all six Appendix A/B lemmas
  (A.1-A.3, B.1-B.3), each 20-58 lines, each one block.

## Mid-sentence figure interposition (R2's "same-object" carve-out, figure variant)

AueGabrysHorvathKokoszka2009 has two cases of a sentence broken by an interposed figure with
real caption content (lines 319→328 around Fig. 2's caption, and similarly near Fig. 1 at
289-296): the sentence fragment before the figure stays with the block it started in, the
figure's substantive caption becomes its own content block (parameters named: `t·n^0.05/√n`
+BM combination for Fig. 1, `sin(t)·n^0.45/√n`+BB for Fig. 2), the bare panel labels
("Change point at 2n/4") immediately preceding each caption are `caption_stub` trash (isolated
by a blank line from the caption itself), and the sentence's completion after the figure opens
a new block rather than trying to reattach to the pre-figure fragment.

## Trash classification calls without a clean taxonomy fit

- InclanTiao1994 line 536, a bare running-header artifact ("Inclán and Tiao: Retrospective
  Detection of Changes in Variance") interposed mid-derivation between two Appendix A
  formula blocks — classified `conversion_residue` (PDF page-header leakage, not orphan
  caption, not navigation).
- InclanTiao1994 line 596, the journal's "[Received June 1992. Revised September 1993.]"
  editorial stamp — classified `title_author` (closest fit: journal/copyright-adjacent
  front-matter metadata), same bucket as the JSTOR citation header at the top.
- AueGabrysHorvathKokoszka2009 lines 9-32, the ARTICLE INFO block (received/available dates,
  AMS classification codes, keyword list) — bundled into the same `title_author` trash span
  as the title/author/affiliation block above it; no taxonomy entry fits a keyword list
  precisely, and it is unambiguously front matter, not content.

## Verification performed

Structural only: `validate_pass_a.py` run against both produced JSONs and their source
documents — schema check, trash-type whitelist check, full line-range coverage with no
gaps/overlaps, and the granularity corridor, all passing on the first run for both documents.
Not verified: no LLM/semantic cross-check of individual subject-shift judgments beyond the
reasoning recorded per block/trash-span above — that is Pass B's territory if a block turns
out to straddle two topics.
