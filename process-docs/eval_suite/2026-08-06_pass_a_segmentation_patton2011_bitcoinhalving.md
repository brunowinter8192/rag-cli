# Pass A Segmentation Run — Patton2011 + BitcoinHalvingCycleVolatilityMSGARCH (2026-08-06)

Applied `eval/queries/prompts/segmentation_prompt_pass_a.md` (R1-R4, R3b) to two documents in
`data/documents/trading-reference/`, worked linearly and sequentially per document (embedded
full text with authoritative line numbers, no disk re-read needed for segmentation itself).

- `Patton2011VolatilityForecastImperfectProxies.md` (585 lines, econometrics paper: analytical
  distortion results for volatility-forecast loss functions, four numbered
  Propositions with an appendix of full proofs, two empirical tables). Output:
  `eval/queries/pass_a_runs/Patton2011VolatilityForecastImperfectProxies.pass_a.json` — 61
  blocks, 7 trash spans. Validator: `OK validate_pass_a: 61 blocks, 7 trash spans, 585 lines
  covered` (median 4 lines, 10.4 blocks/100 lines).
- `BitcoinHalvingCycleVolatilityMSGARCH.md` (408 lines, empirical finance paper: Bitcoin
  safe-haven/hedge testing + MSGARCH regime analysis, heavily garbled two-column PDF
  conversion in the introduction). Output:
  `eval/queries/pass_a_runs/BitcoinHalvingCycleVolatilityMSGARCH.pass_a.json` — 77 blocks, 5
  trash spans. Validator: `OK validate_pass_a: 77 blocks, 5 trash spans, 408 lines covered`
  (median 2 lines, 18.9 blocks/100 lines).

## Off-by-one document length: header line-count is informational only

Patton2011's embedded-prompt header stated "~584 lines"; the source file is actually 585 lines
(`python3 -c "print(len(open(path).read().splitlines()))"` → 585, while `wc -l` reported 584
because the file has no trailing newline after its final content line). The first validator
run failed with `coverage ends at line 584, document has 585 lines`. Root cause: the final
appendix block (Proof of Proposition 4) was bounded at line 584 per the embedded numbering,
but the actual last line (585, the proof's closing sentence about substituting `C` and
`C̃` into Eq. 23) fell one past that. Fixed by extending the block's `line_end` to 585 and
re-running — passed immediately. Takeaway consistent with the task's own caveat: never trust
the informational header count over the embedded/authoritative line numbers, and when a
validator flags a coverage-length mismatch on the *last* span specifically, first suspect a
trailing-newline discrepancy between `wc -l` and the actual line count before re-examining the
segmentation logic.

## Atomic proof blocks (R3b) confirmed viable at the >50-line ceiling

Patton2011's Appendix contains four independent "Proof of Proposition N" sections (1 through
4), each a single continuous algebraic argument with internal step markers (§1⇒§2⇒§3⇒§1 style)
and multiple embedded formula displays. Kept each as one atomic block per R3b's proof
exception: 64, 44, 34, and 27 lines respectively. Only the largest (Proof of Proposition 1,
64 lines) exceeds the 50-line "flag for justification" threshold used in this pipeline's
reporting convention — all four are legitimate under the corridor because the gate is on the
document-wide *median*, and the other 57 blocks in this document (median 4 lines) carry that
median comfortably under the ≤25 ceiling regardless of these four outliers.

## Formula-catalog and definition-list blocks (R1) reused from prior sessions

Confirmed the same-subject formula/list merge pattern already established for this corpus
(e.g. HansenLundeNason2011's KLIC-criterion block): Patton2011's nine numbered candidate loss
functions (Eqs. 5-13, lines 109-146) merged into one 38-line block since they are one
enumerated catalog with no prose subject-shift between entries; similarly the Assumptions
A1-A5 for Proposition 1 (307-316) merged into one block. BitcoinHalving's MSGARCH variable
definitions (the seven `y_t`/`S_t`/`k`/... numbered items, 206-219) and its Baur-McDermott
equation-plus-variable-definitions block (Eqs. 1-2 plus four numbered terms, 149-166) followed
the identical pattern.

## Table/figure mid-sentence interposition (PDF float-placement artifact)

Both documents exhibit a distinct artifact from the first-pass-A-run PDF conversions: a
table or figure is float-placed into the *middle* of a running sentence, splitting it into a
before-fragment and an after-fragment with unrelated table/figure content between them —
different from the ordinary mid-sentence blank-line split (which has *nothing* between the
two fragments). Handled per the task's explicit rule: the table/figure becomes its own content
block (or `caption_stub` trash if the caption itself is orphan/minimal), and the completion
fragment merges forward into the next coherent block rather than standing alone.

- Patton2011 line 285: "...which is a necessary condition for a loss function to be robust"
  is cut off by Table 2 (287-304), completing at line 305 ("to noise in the volatility
  proxy..."); the completion was merged into the following Assumptions/Proposition-framing
  block (305-316) since it reads as one continuous thought with that block, not with the
  truncated intro sentence.
- Patton2011 lines 373/379: "Recall that the theory in the previous / section requires..." is
  split by Fig. 1 and Fig. 2 captions (both kept as content — each spells out the `b`
  parameter, the σ²=2 example, and which `b` values correspond to MSE/QLIKE, i.e. substantive
  standalone content, not orphan stubs). A second interposition in the same passage (line
  381/397: "...not likely true for very high / frequencies...") is split by an orphan Fig. 3
  caption (`caption_stub` — just names the plotted series/timeframe, no parameters or
  interpretation) and Table 3 (kept as its own content block, DMW t-statistics).

## Two-column PDF-merge garbling: readable-but-degraded stays content, not conversion_residue

BitcoinHalving's introduction (lines 42-71: halving-cycle stage description, the six-item bear
market sequence list, five figure captions) is a two-column layout collapsed into one stream,
producing duplicated/interleaved phrase fragments (e.g. line 44 repeats "Bitcoin halving cycle
typically consists of three stages..." twice with overlapping wording, and the numbered
sequence list at 49-59 has item numbers attached to the wrong fragment). Judged this readable
rather than `conversion_residue`: despite the visual mess, every distinct claim is still
recoverable by a careful read (the three cycle stages, the specific six sequence items, the
specific dollar figures in each figure caption). Kept all of it as content per the task's
READABILITY RULE ("compressed words... are NOT trash as long as text is readable and content
extractable") — `conversion_residue` was reserved for genuinely unreadable output (this
document had none; its one `caption_stub` span, Fig. 6's caption at 368-372, is trash for being
an orphan label, not for being unreadable).

## Conclusion sections judged CONTENT, not abstract_summary, in both documents

Per the task's explicit carve-out ("any paragraph carrying a standalone actionable claim not
stated elsewhere is CONTENT"), neither document's final section was blanket-trashed:

- Patton2011 Section 5 (403-412): the first two paragraphs (403-410) purely recap contributions
  already stated in the introduction and were trashed `abstract_summary`; the closing paragraph
  (411-412) was kept as content — it makes a novel claim not stated elsewhere in the paper
  (extending the latent-variable framework to real-line support "should not be difficult" vs.
  discrete-support proxies "may require a different method of proof").
- BitcoinHalving Section 5 (390-397): kept as three content blocks in full. Each paragraph
  carries a standalone claim beyond a pure results recap — an investment-behavior
  recommendation (investors should not hold Bitcoin specifically for its safe-haven/hedge
  property), an explicit scope caveat (findings may not extrapolate past the COVID black-swan
  event and should be reinvestigated), and forward-looking research guidance (revisit
  safe-haven/hedge status as continued institutional adoption may break the halving-cycle
  pattern) — none of which restate the Results section verbatim.

## Verification performed

Structural only: `validate_pass_a.py` run against both produced JSONs and their source
documents — schema, trash-type whitelist, full-document coverage with no gaps/overlaps, and
the granularity corridor. Patton2011 required one fix-and-rerun (the off-by-one above);
BitcoinHalving passed on the first run. Not verified: no LLM/semantic cross-check of individual
subject-shift judgments beyond the reasoning recorded per block/trash-span above — that remains
Pass B's territory if a block turns out to straddle two topics.
