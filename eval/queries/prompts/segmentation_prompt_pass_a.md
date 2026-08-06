## Task

You receive ONE markdown document (converted from PDF). Work through it LINEARLY, start to end, and partition it into contiguous blocks by setting boundaries where the subject matter shifts. Additionally classify excluded material as trash (taxonomy below).

## Rules

### R1 — Atom: boundaries only at blank lines

A boundary may ONLY be placed at a blank line. Not every blank line is a boundary — blank lines are the legal CUT POINTS, nothing more. Formula-dense text has blank lines around every display formula; a formula↔prose alternation on one subject stays ONE block. [Grounding: Hearst 1997 places TextTiling boundaries at orthographic paragraph breaks; LumberChunker (Duarte 2024) operates on paragraph IDs — the paragraph is the atom.]

### R2 — Boundary criterion: subject-matter shift, not phrasing shift

Set a boundary where the SUBJECT MATTER changes from one block to the next. Signals:
- The set of active field terms/entities is largely replaced by a new set. [Hearst 1997 §4: "a set of lexical items is in use during the course of a given subtopic discussion, and when that subtopic changes, a significant proportion of the vocabulary changes as well" — via Halliday & Hasan 1976 lexical cohesion.]
- The discussion moves to a different object/method/question — a rephrasing or elaboration of the SAME object is NOT a shift. [Chafe 1979 via Hearst: episode boundary = maximal change of subject matter, not of wording.]
- Do not try to define what the topic IS; detect where it CHANGES. [Brown & Yule 1983 via Hearst: replace the undefinable "what is a topic" with detectable topic-shift.]

Headings are HINTS, not authority: a heading often marks a shift, but shifts also occur inside a single heading's scope (sub-heading splits allowed), and a heading with no content shift forces nothing. [Mechanism validation: LLM shift-detection beats semantic/embedding chunking and all other baselines, +7.37% DCG@20, Duarte 2024 Table 1.]

### R3 — Doubt bias: cut

When unsure whether a shift is real, CUT. Pass B merges cheaply; overly coarse blocks force Pass B into re-splitting work.

### R3b — Method mandate: line-by-line reading, no heading shortcuts

You MUST read the document line by line and judge every blank line as a potential R2 cut point. Deriving boundaries from the heading structure (grep for `#`/`##`, block = heading-to-heading) is BANNED: headings only mark where the paper's authors cut, not where subjects shift — the batch01 run that used this shortcut produced median block sizes of 48-56 lines vs. the calibration's 8 and was fully discarded. The validator enforces a granularity corridor (median block size ≤ 25 lines, ≥ 4 blocks per 100 lines); a heading-only segmentation mechanically fails it. Large single blocks remain legitimate ONLY for one continuous argument (e.g. an unbroken appendix proof, per R2's same-object carve-out) — as exceptions inside an otherwise fine-grained segmentation, never as the default grain.

### R4 — Trash classification (excluded from blocks)

Material that is not content gets NO block membership; list it separately with a type:
- `abstract_summary` — abstract / chapter summary / conclusion-recap compressing many topics
- `title_author` — title, author list, affiliations, emails, copyright
- `references` — bibliography / reference lists (incl. headingless reference runs)
- `toc_index` — table of contents, index, list of figures/tables
- `caption_stub` — orphan figure/table captions carrying no standalone content
- `conversion_residue` — UNREADABLE conversion junk (repeated LaTeX fragments, empty math)
- `navigation_meta` — text about the document's own structure ("the remainder of this paper is organized as follows: section 2 covers..."), readable but purely navigational — never an answer to any realistic search

READABILITY RULE: compressed words ("lthoughvolatilityisnotdirectlyobservable...") and spaced math are NOT trash as long as the text is readable and content extractable — such lines stay inside their content block. Trash classification feeds two consumers: the "trash rate in top-k" retrieval metric and future PDF-cleanup rule definitions.

## Output (JSON)

```json
{
  "document": "<filename.md>",
  "model": "<the model you run on, e.g. claude-sonnet-5>",
  "blocks": [
    {"id": "b001", "line_start": 1, "line_end": 42, "subject": "3-8 word subject label"}
  ],
  "trash": [
    {"line_start": 1, "line_end": 6, "type": "title_author"}
  ]
}
```
- Line numbers 1-indexed, spans inclusive, non-overlapping, in document order.
- Every line of the document is in exactly one block or one trash span.
- `subject` is a working label for Pass B, not a title and not a summary.

## Explicit non-goals (Pass B territory)

No theme grouping, no information-need definition, no distributed linking, no splitting reconsideration, no grading, no query or summary writing.
