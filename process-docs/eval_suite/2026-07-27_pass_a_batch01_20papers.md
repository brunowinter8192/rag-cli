# Pass A Segmentation, Batch01 — 20 Papers (2026-07-27)

Applied `eval/queries/prompts/segmentation_prompt_pass_a.md` (R1-R4) to the first 20-paper
batch from `data/documents/trading-reference/` (per the 2026-07-25 batching plan). Output:
20 `eval/queries/pass_a_runs/<doc>.pass_a.json` files, each validated with
`eval/scripts/validate_pass_a.py` before moving to the next document. Final state: 20/20 OK,
block counts 8-55 per document (median ~21), trash spans 2-14 per document, depending on
document density/structure — see the per-document commit for exact counts.

## Environment note: `data/` is gitignored, not present in the worktree

Worktrees only materialize tracked files; `data/` (`.gitignore:42`) holds the source PDFs-as-
markdown and is therefore absent from the isolated worktree even though the deliverable path
(`eval/queries/pass_a_runs/`) is tracked and present. Resolved by reading source `.md` files
via an absolute path into the main repo checkout and passing that same absolute path as
`validate_pass_a.py`'s second argument — read-only, no edits outside the worktree.

## Two segmentation workflows used, by document size

For the first ~5 documents, blank-line positions were derived by exhaustive line-by-line
reading and manual boundary computation (as in the Bollerslev reference run). For the
remaining ~15, this proved too slow at batch scale; switched to a **heading-boundary
method**: `grep -n "^# \|^## "` to list a document's own heading structure, then set each
block's `line_end = next_heading_line - 1`, absorbing the intervening blank line into the
current span per the established absorb-trailing-blank convention. This is faster because
academic PDF-to-markdown conversions preserve section/subsection headings reliably, and a
heading transition is very often (but not always — see Recap Fix below) also a subject-shift
per R2.

## Trash-type patterns catalogued across 20 documents

- `title_author`: title/author/affiliation front matter; also recurring mid-document
  page-footer boilerplate (e.g. BaiPerron2003's "Copyright (c) 2002 John Wiley... / J. Appl.
  Econ. 18:1-22" pair, repeated 4x through the body from PDF page-break artifacts) — each
  recurrence is its own trash span, not merged.
- `abstract_summary`: abstract + JEL/AMS codes + keywords, treated as one contiguous span
  even when interleaved with blank lines (front-matter metadata bundle).
- `navigation_meta`: roadmap paragraphs ("The rest of this paper is organized as follows...")
  — found reliably right before the first numbered section in ~6 of 20 documents; absent in
  others (not forced).
- `caption_stub`: single descriptive figure/table captions, and — a pattern not seen in the
  Bollerslev reference — multi-line runs of scattered chart-legend/axis-label fragments with
  no coherent sentence structure (e.g. Corsi2009's Figure 9 block, lines 305-326: bare
  series names "AR(3)" / "USD/CHF" / "ARFIMA(5,d,0)" repeated with no prose), a residue of
  PDF charts whose axis labels got flattened into the text stream.
- `conversion_residue`: severely garbled OCR/LaTeX, distinct from caption_stub by being
  content-bearing prose or a figure gone unreadable rather than a caption. Two instances:
  Engle1982's Lemma proof (line 678) degenerating into ~200 repeated "chi" tokens; BaiPerron
  2003's hand-drawn triangular-matrix figure (lines 57-77) converted into an unreadable
  garbled ASCII/pipe table.
- `references`: only DaEngelbergGao2011 had an in-range bibliography section (the rest either
  have no References section in the converted range or it falls beyond the file's tail).

## Recap fix: heading-boundary blocks can under-segment multi-object sections

Post-hoc review (this session) found two documents where a single heading-delimited block
bundled multiple distinct mathematical objects (e.g. two independent theorems about
different statistics, plus a separate estimation result, under one `# 3 Testing the equality
of mean functions` heading) — an R2/R3 violation the heading-boundary method does not catch
by construction, since it only cuts at existing headings. Both were re-split by hand,
re-reading the passage and cutting wherever the narrative moved to a **new named object**
(new statistic, new estimator, new theorem not just restating the previous one's other
case): `HorvathKokoszkaReeder2013...` grew from 11 to 15 blocks (one heading-block split
3-way, one split 2-way); `AueGabrysHorvathKokoszka2009...` grew from 8 to 12 blocks (one
heading-block split 3-way, one split 3-way). Twin theorems covering the H0/HA cases of the
*same* statistic were kept together in both re-splits (elaboration of the same object, per
R2's explicit carve-out) — only cuts where the object itself changed. Both re-validated
0-error after the split; no other document in the batch was re-audited against this specific
failure mode this session.

## Density-driven segmentation coarseness (proof sections)

Proof-heavy appendices (e.g. both Horvath/Kokoszka papers' Section 4-6 / Appendix A-B) were
segmented at markedly coarser grain than the Bollerslev reference (single blocks spanning
100-300+ lines) because each is one continuous, unbroken mathematical argument for one
theorem — R2's "elaboration of the SAME object is NOT a shift" applies directly. This
coarseness was judged acceptable and left unchanged by the recap review, which targeted only
body sections that named more than one object under a single heading.
