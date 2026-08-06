# Pass A Segmentation Run — Engle1982ARCHInflation.md + ChuStinchcombeWhite1996MonitoringStructuralChange.md (2026-08-06)

Applied `eval/queries/prompts/segmentation_prompt_pass_a.md` (R1-R4, R3b) to two
PDF-converted econometrics papers in `data/documents/trading-reference/`:

- `Engle1982ARCHInflation.md` (707 lines, dense equation-by-equation derivation paper: model
  motivation, likelihood/estimation theory across 9 sections, UK inflation application, a
  4-theorem appendix). Output: `eval/queries/pass_a_runs/Engle1982ARCHInflation.pass_a.json`
  — 62 blocks, 5 trash spans. `OK validate_pass_a: 62 blocks, 5 trash spans, 707 lines
  covered` (median block size 10 lines, 8.77 blocks/100 lines).
- `ChuStinchcombeWhite1996MonitoringStructuralChange.md` (490 lines, sequential-testing
  theory paper: invariance-principle setup, CUSUM/FL monitoring corollaries, simulations, a
  4-proof appendix). Output:
  `eval/queries/pass_a_runs/ChuStinchcombeWhite1996MonitoringStructuralChange.pass_a.json` —
  86 blocks, 5 trash spans. `OK validate_pass_a: 86 blocks, 5 trash spans, 490 lines
  covered` (median block size 3.5 lines, 17.55 blocks/100 lines).

## Method: line-by-line read, generation script eliminates coverage arithmetic errors

Both documents were read in full (line-numbered) and judged linearly per R3b — no
heading-grep shortcut. Final JSON was generated from an ordered Python list of
`(start_line, kind, subject_or_trash_type)` tuples with `end = next_start - 1` (last entry
closes at the document's true last line), the same technique used in the NadeauBengio2003
run (see area for that entry) — this makes gap/overlap/off-by-one errors structurally
impossible rather than something to catch by inspection. Both files validated OK on the
first `validate_pass_a.py` run, no iteration needed.

## Correction mid-session: proof of one theorem is ONE block, never split at connectives

Initial plan considered splitting long appendix proofs (Engle1982 Theorem 1's 59-line proof;
Chu1996 Lemma 3.1's 39-line proof with internal "Step A/B/C/D" labels) at rhetorical
connectives ("Now", "It remains only to establish...") or at the internal step labels, to
keep block sizes under ~25 lines. Corrected: R2's same-object elaboration rule means a
single theorem/lemma's proof is one continuous argument regardless of internal rhetorical
structure or labeled sub-steps, UNLESS a genuinely different claim/object interposes (a new
theorem, an interleaved different proof). Splitting at "Now" or "Step B:" is phrasing-shift
segmentation, exactly what R2 prohibits. Kept atomic:
- Engle1982 b058 (557-618, 62 lines): full proof of Theorem 1.
- Engle1982 b059 (619-654, 36 lines): full proof of Theorem 2.
- Engle1982 b062 (681-707, 27 lines): full proof of Theorem 4.
- Chu1996 b083 (416-455, 40 lines): full proof of Lemma 3.1, including internal Steps A-D.
- Chu1996 b085 (460-477, 18 lines): full proof of Corollary 3.6.

This is safe against the granularity gate because it checks the MEDIAN block size, not the
max — a handful of large atomic-proof blocks cannot fail the ≤25-line median given the many
short blocks elsewhere (both runs landed well under: median 10 and 3.5 respectively). The
same atomicity was applied to non-"proof"-labeled but self-contained single derivations that
read like a proof: Engle1982 §7's relative-efficiency calculation (b038, 417-436) and
Chu1996's Wald-SPRT LR derivation (b064, 306-325, spanning "Consider a sequential test..."
through "But" / "so we have" / the closed-form result) were each kept as one block rather
than split at their internal connectives, for the same reason.

## Structural discovery: mid-sentence PDF page-break blank lines

Both documents' PDF-to-markdown conversion inserts a blank line mid-sentence at what was
originally a page break, with no other signal distinguishing it from a real paragraph
break. Examples requiring merge across the blank (not a legal boundary despite R1 syntax
allowing it): Engle1982 lines 44-46 ("...The conditional" / blank / "variance of $y_t$
is..."), lines 114-... (McNees quote), lines 479-481 (Lucas/Friedman motivation); Chu1996
lines 47-49 ("...Simulation" / blank / "results show that thirty periods later..."), lines
115-117 (FCLT definition), lines 326-328 ("...boundary in" / blank / "(14) is
suboptimal..."). Caught only by reading full sentences across the blank line, never by
scanning for blank-line positions alone.

## Structural discovery: substantive data tables interposed mid-sentence, kept as their own blocks

In Engle1982, the sentence "The maximum likelihood estimates differ from the least squares
effects primarily in decreasing... and increasing" (line 519) is grammatically completed
only after Table II (521-529) and Table III (531-539) by "the coefficient on the long run,
as incorporated in the error correction mechanism" (line 541). Unlike the mid-sentence blank
line case, this is not a legal merge target — actual data content intervenes, not just a
blank line — so each of the three pieces stays a separate block despite belonging to one
grammatical sentence. Same pattern in Chu1996 around Table III (373-374 "...boundary
crossing" / Table III (375-381) / 382 "probabilities. The growing variance..."). Tables
themselves were kept as CONTENT blocks (not `caption_stub`) in both documents since every
one carries substantive coefficients/CIs/parameter values, not orphan labels.

## Trash classification calls

- Both papers: JSTOR front-matter boilerplate (stable URL, terms, copyright) plus the
  paper's own repeated title/author line as two separate `title_author` spans, and the
  end-of-paper affiliation + "Manuscript received..." line as a third `title_author` span.
- Both papers: `abstract_summary` for the abstract paragraph(s); Chu1996's `KEYWORDS:` line
  was folded into that same span rather than given its own type.
- Chu1996 lines 41-42: `navigation_meta` — "This paper is organized as follows: Section 2...
  Section 5..." — pure section-roadmap, per R4's definition, distinct from the substantive
  intro paragraphs immediately preceding it (kept as content).
- Engle1982 lines 675-680: `conversion_residue` — a `$$...$$` block inside the symmetry
  lemma's proof (preceding "PROOF OF THEOREM 4") reduced by OCR to hundreds of repeated
  `\text{chi}` tokens, uninterpretable; the "PROOF:" label line was folded into this span
  since it introduces only the garbled content. The Lemma's own statement (readable) stayed
  content in the preceding block.
- Chu1996 §5 "CONCLUDING REMARKS" (386-393) kept as CONTENT, not `abstract_summary` trash:
  it states a standalone claim not recapped verbatim elsewhere ("we also widen the class of
  boundary functions beyond those suggested in the literature") and an explicit open-problem
  framing ("there may exist a choice that gives an optimal monitoring... left for further
  research") — not a pure compress-prior-topics recap.
- Chu1996 footnote 3 (line 334, interposed after the Switzer-procedure discussion) was
  folded into its annotated paragraph's block (b066, 330-336) rather than trashed or split
  out, per the footnote-folding instruction.

## Verification performed

Structural only: `validate_pass_a.py` run against each produced JSON and its source
document — schema check, trash-type whitelist, full 1-707 / 1-490 coverage with no
gaps/overlaps, and the granularity corridor (median ≤25, ≥4.0 blocks/100 lines), all passing
on the first run for both documents given the generation script's programmatic span
computation. Not verified: no LLM/semantic cross-check of individual subject-shift
judgments beyond the reasoning recorded above — that is Pass B's territory if a block turns
out to straddle two topics.
