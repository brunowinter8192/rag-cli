# Pass A Segmentation Run — Tetlock2007 + HorvathKokoszkaReeder2013 (2026-08-06)

Applied `eval/queries/prompts/segmentation_prompt_pass_a.md` (R1-R4, R3b) to two documents:

- `data/documents/trading-reference/Tetlock2007GivingContentInvestorSentiment.md` (441 lines,
  empirical finance paper: media-sentiment VAR regressions, 9 numbered tables, 2 figures with
  substantive captions, no proofs). Output:
  `eval/queries/pass_a_runs/Tetlock2007GivingContentInvestorSentiment.pass_a.json` — 70 blocks,
  3 trash spans. Validator: `OK validate_pass_a: 70 blocks, 3 trash spans, 441 lines covered`
  (median block size 4 lines, 15.87 blocks/100 lines).
- `data/documents/trading-reference/HorvathKokoszkaReeder2013MeanFunctionalTimeSeriesTwoSample.md`
  (998 lines, functional-time-series statistics paper: 9 named theorems, a simulation study
  with 4 numbered tables and 4 figures, and two full proof sections). Output:
  `eval/queries/pass_a_runs/HorvathKokoszkaReeder2013MeanFunctionalTimeSeriesTwoSample.pass_a.json`
  — 75 blocks, 5 trash spans. Validator:
  `OK validate_pass_a: 75 blocks, 5 trash spans, 998 lines covered` (median block size 6 lines,
  7.52 blocks/100 lines).

## Method: full read + line-number verification against source before JSON construction

Both documents were read in full from the embedded task text first to make subject-shift
judgments, then the entire HorvathKokoszkaReeder2013 source was re-read directly from disk
(`Read` on the actual `.md` file, in two passes covering all 998 lines) to verify exact
line numbers in the formula-dense middle sections (Sections 2-3, the numerical algorithm,
Sections 5-6 proofs) before committing to block boundaries. This caught and corrected drift
in my initial manual reconstruction of Table 4.1/4.2's exact start lines and Figure 4.1's
caption line range — manual line-counting across ~150 short formula/blank-line pairs is
error-prone; a second read against the authoritative file removed that risk before writing
JSON, rather than relying on the validator's coverage check alone to catch it.

## Table/figure interposition vs. genuine PDF-pagebreak artifact — both documents exhibit both

Distinguishing rule applied consistently: if a blank line splits a running sentence and NO
content sits between the two halves, it is a PDF-conversion pagebreak artifact (R3b's
explicit gotcha) — merge across it into one block. If a table, figure, or other real content
is interposed between the two sentence halves, that is deliberate document layout, not an
artifact — the table/figure becomes its own content block and the short resuming fragment is
folded into whichever adjacent block it thematically belongs to (never left as a standalone
one-line orphan).

- Tetlock2007: all 9 tables (I-IX) repeatedly split the surrounding argument mid-sentence
  (e.g. line 67 "...I conclude from this" / Table I / line 92 "analysis that the loadings...").
  Table-interposition pattern in every case — each table kept as its own block, each
  resuming fragment merged into the next full paragraph.
- HorvathKokoszkaReeder2013: four genuine pagebreak-artifact merges with no intervening
  content (lines 37/39, 75/77, 413/415, 461/463 — e.g. "...approximated by the long-run" /
  blank / "variance whose estimation has been...") were merged across the blank line into
  one block each. Separately, Table 4.4 (lines 592-601) and Figure 1.1 (lines 31-32) both
  interpose real content mid-sentence in the same way as Tetlock2007's tables — table/figure
  kept as its own block, fragment folded into the following block.

## Proof atomicity (HorvathKokoszkaReeder2013 Sections 5-6)

Six named-theorem proofs, each kept as exactly one block regardless of length or internal
staging language, per R3b's explicit proof exception:

- Proof of Theorem 2.1 (lines 608-719, 112 lines) — one continuous m-dependent-approximation
  argument in two stated steps ("First we show that... Then we establish...").
- Proof of Theorem 2.2 (lines 720-921, 202 lines) — the largest block in either document; one
  continuous reduction (2.15)→(5.2)→(5.6), despite the proof's own internal "First we
  reduce... Then, we reduce..." staging sentence and multiple intermediate labeled results
  (5.1)-(5.6). Not split at any of these internal connectives or step labels.
- Proofs of Theorems 3.1, 3.2, 3.3, 3.4 (932-951, 952-953, 954-995, 996-997) — each its own
  block; Theorem 3.2's proof is a single two-line block (shortest legitimate proof block in
  either document), confirming the atomic-proof rule is about not splitting one proof, not
  about a minimum block size.

The granularity gate is unaffected by these two large outliers: HorvathKokoszkaReeder2013's
median block size is 6 lines because roughly half of its 75 blocks are 2-8 line
definition/equation units; the 112- and 202-line proof blocks sit far above that median
without pulling it up, exactly the corridor design's "median, not max" intent.

## Caption content vs. caption_stub calls

- Tetlock2007 Figures 1 and 2: both captions carry substantive standalone content (Figure 1
  spells out the theoretical prediction shape for short- vs long-horizon returns under two
  competing hypotheses; Figure 2's caption states the lowess bandwidth, sample size, and how
  to read the smoothed curve) — kept as content blocks.
- HorvathKokoszkaReeder2013 Figure 1.1's caption (lines 31-32, describing the Honolulu
  magnetic-observatory data source and measurement resolution) is substantive — kept as
  content. Its accompanying bare axis label "Time in minutes" (lines 33-34, no other text,
  separated from the caption by its own blank-line pair) is an orphan panel label with zero
  extractable content — classified `caption_stub`, the only such span across either document.
  Figures 4.1-4.4 in the simulation/data-example section all carry substantive captions
  (sample construction, what to conclude from a rejection/non-rejection) and were kept as
  content blocks, not stubs.

## Trash classification calls

- Tetlock2007: `title_author` (1-4), `abstract_summary` (5-8), `navigation_meta` (23-24, the
  "Section I provides motivation... Section V..." roadmap paragraph — verbatim match to R4's
  navigation_meta example).
- HorvathKokoszkaReeder2013: `title_author` (1-14, three authors with affiliations),
  `abstract_summary` (15-22, abstract + keywords + abbreviated title), `caption_stub` (33-34,
  see above), `navigation_meta` (43-44, "The remainder of the paper is organized as
  follows..."), and a second `title_author` span for the closing Acknowledgements line (998,
  NSF grant funding note) — no taxonomy entry fits funding acknowledgements exactly;
  `title_author`'s "non-content administrative metadata" spirit was judged the closest fit
  over leaving it uncovered or forcing it into a content block.

## Verification performed

Structural only: `validate_pass_a.py` run against both produced JSONs and their source
documents — schema, trash-type whitelist, full-document coverage with no gaps/overlaps, and
the granularity corridor, all passing on the first run for both documents (no iteration
needed; the HorvathKokoszkaReeder2013 line-number drift described above was caught and fixed
before JSON construction, not after a validator failure). Not verified: no LLM/semantic
cross-check of individual subject-shift judgments beyond the reasoning recorded per
block/trash-span above — that is Pass B's territory if a block turns out to straddle two
topics.
