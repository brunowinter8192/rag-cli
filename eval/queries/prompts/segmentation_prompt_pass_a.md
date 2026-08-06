## Task

You receive ONE markdown document (converted from PDF). Work through it LINEARLY, start to end, and partition it into contiguous blocks by setting boundaries where the subject matter shifts. Additionally classify excluded material as trash (taxonomy below).

## Rules

### R1 — Atom: boundaries only at blank lines

A boundary may ONLY be placed at a blank line. Not every blank line is a boundary — blank lines are the legal CUT POINTS, nothing more. Formula-dense text has blank lines around every display formula; a formula↔prose alternation on one subject stays ONE block.

### R2 — Boundary criterion: subject-matter shift, not phrasing shift

Set a boundary where the SUBJECT MATTER changes from one block to the next. Signals:
- The set of active field terms/entities is largely replaced by a new set.
- The discussion moves to a different object/method/question — a rephrasing or elaboration of the SAME object is NOT a shift.
- Do not try to define what the topic IS; detect where it CHANGES.

Headings are HINTS, not authority: a heading often marks a shift, but shifts also occur inside a single heading's scope (sub-heading splits allowed), and a heading with no content shift forces nothing.

### R3 — Doubt bias: cut

When unsure whether a shift is real, CUT. Merging blocks later is cheap; overly coarse blocks are expensive to fix.

### R4 — Trash classification (excluded from blocks)

Material that is not content gets NO block membership; list it separately with a type:
- `abstract_summary` — abstract / chapter summary / conclusion-recap compressing many topics
- `title_author` — title, author list, affiliations, emails, copyright
- `references` — bibliography / reference lists (incl. headingless reference runs)
- `toc_index` — table of contents, index, list of figures/tables
- `caption_stub` — orphan figure/table captions carrying no standalone content
- `conversion_residue` — UNREADABLE conversion junk (repeated LaTeX fragments, empty math)
- `navigation_meta` — text about the document's own structure ("the remainder of this paper is organized as follows: section 2 covers..."), readable but purely navigational — never an answer to any realistic search

READABILITY RULE: compressed words ("lthoughvolatilityisnotdirectlyobservable...") and spaced math are NOT trash as long as the text is readable and content extractable — such lines stay inside their content block.

## Output (JSON)

```json
{
  "document": "<filename.md>",
  "model": "claude-sonnet-5",
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
- `subject` is a working label, not a title and not a summary.

## Out of scope

No theme grouping, no information-need definition, no distributed linking, no grading, no query or summary writing.
