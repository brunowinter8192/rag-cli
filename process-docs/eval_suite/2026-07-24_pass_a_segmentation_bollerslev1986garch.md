# Pass A Segmentation Run — Bollerslev1986GARCH.md (2026-07-24)

Applied `eval/queries/segmentation_prompt_pass_a.md` (R1-R4) to
`data/documents/trading-reference/Bollerslev1986GARCH.md` (528 lines, PDF-converted
econometrics paper). Output: `eval/queries/pass_a_runs/Bollerslev1986GARCH.pass_a.json`
— 45 blocks, 9 trash spans.

## Span-ownership convention for blank-line boundaries

The prompt schema requires every line in exactly one span and every boundary to sit on a
blank line, but does not say which span "owns" a boundary blank line. Resolved by absorbing
trailing blank line(s) into the END of the preceding span; the next span starts at the next
content line. This keeps spans contiguous/gapless and trivially satisfies "line before
line_start is blank or file start" — verified with a python script checking all 54 spans
(coverage: 1..528 contiguous no gaps/overlaps; boundary legality: 0 violations).

## Trash classification calls

- Lines 1-9 `title_author` (title/author/affiliation/received-date), 10-11
  `abstract_summary` — standard front-matter.
- Line 18: an acknowledgment footnote injected mid-paragraph by the PDF conversion
  (breaks a sentence spanning 16→20 at "condi-"/"tional"). Classified `title_author`
  (author-thanks content) since it is cleanly delimited by blank lines 17/19 on both
  sides — confirmed before excising, per the rule that only blank-line-delimited spans
  may become trash; a footnote NOT cleanly delimited would have stayed in its block.
- Lines 181-194: a numbered footnote (marker "3") giving specific finite-fourth-moment
  conditions for GARCH(1,2)/GARCH(2,1)/ARCH(q). Kept as a CONTENT block, not trash —
  it carries substantive math, unlike line 18's pure acknowledgment; no R4 category
  fits a substantive footnote.
- Four `caption_stub` spans (Fig.1 @142-144, Fig.2 @361-363, Fig.3 @374-376, Fig.4
  @381-383): each is an inline `![](images/...)` + one-line caption with no
  standalone content, all cleanly blank-delimited.
- Two `conversion_residue` spans: single stray characters "中" (line 402) and "："
  (line 454) inside the Appendix proofs, replacing what was presumably a math symbol
  during OCR/PDF conversion — unreadable on their own line, cleanly blank-delimited,
  excised without disturbing the surrounding proof.

## Block-granularity principle: theorem-proof derivations stay atomic

Applied R2's "elaboration of the SAME object is not a shift" to distinguish two
different formula-dense regimes:
- Numbered sections (§2 GARCH(p,q) definition, §3 GARCH(1,1), §5 estimation, etc.) mix
  genuinely different objects in sequence — model definition, a named theorem
  statement, an alternative equation-form, a different sub-derivation — each such
  transition was treated as a subject shift and cut (yielding e.g. 6 blocks across
  lines 26-99 for §2 alone).
- Appendix A.1 (Proof of Theorem 1, lines 386-475) and A.2 (Proof of Theorem 2,
  476-528) are each ONE continuous algebraic argument proving a single named theorem,
  with no intervening theorem statement or new equation-form to anchor a cut — kept as
  large single blocks (A.1 split only by the two conversion_residue lines forced by
  the atom rule, not by a subject shift).

## Verification performed

Python checks only (pure structural validation of the produced JSON against the
source document): JSON parses; span coverage is gapless/non-overlapping over 1-528;
every span's preceding line is blank or file-start, checked for blocks AND trash
identically. Not verified: no semantic/LLM cross-check of subject-shift correctness
beyond the reasoning recorded per span above — that judgment call is what Pass B (a
separate run) would exercise via re-splitting if a block reads as covering two topics.
