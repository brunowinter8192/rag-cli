## Task

You receive ONE markdown document and a linear block segmentation of it (contiguous line-span blocks plus trash spans). Form THEMES over the blocks. A theme is the unit later used as a graded ground-truth region set.

## Rules

### R1 — Theme definition: all-and-only answer set of ONE realistic information need

A theme comprises ALL blocks needed to answer one realistic practitioner question and ONLY those blocks.

### R2 — Need level: the three tests (operationalizes R1)

Not a separate definition — three checks that pin the LEVEL of R1's "realistic information need".

NEED LEVEL: a realistic information need is a practitioner's CASE-MATCH question — someone with a case at hand searching the literature for whether it matches theirs: does this methodology fit my situation, under what conditions, derived how. Always multi-concept, always needing context AROUND any formula. A bare artifact lookup ("the definition/statement/proof/theorem/formula of X") is never a standalone search.

Record each theme's need in the `need` field: ONE sentence, PRACTITIONER-SITUATION form ("someone working on X needs Y") — never a content question ("what is X, how is it specified") written with the text in view.
1. **One-question test:** the need is expressible as ONE search question — an enumeration ("and also...") indicates multiple needs.
2. **Standalone-search test (too fine):** would this ever be issued as its own search in real usage, or only ever as part of a broader case-match need? A formula, symbol, or single fact is never its own search — it is a FACT inside its parent theme, found via region hit + expansion.
3. **Split test (too coarse):** if subsets of a theme's blocks each answer a self-standing single-search question AND no realistic single question needs their union → separate themes. This test needs the meta view over the whole block list.

### R3 — Distributed themes allowed

Blocks of one theme need NOT be adjacent (method §, protocol §, appendix example = one theme). Each grouping of non-adjacent blocks carries a one-sentence justification of why they serve the same need.

### R4 — Theorem + proof = ONE theme

A theorem/lemma statement and its (possibly distant, appendix) proof serve one need — "under what condition does X hold, derived how" — and form ONE distributed theme. A standalone "Proof of Theorem N" theme is BANNED.

### R5 — Soft membership allowed, flagged

A block may belong to multiple themes (a passage can be core to one need and context to another). Mark such blocks explicitly so validation sees every multi-assignment.

### R6 — Re-split at blank lines only

When the split test fires on a block, the new boundary must again sit on a blank line — blank lines are the only legal cut points. Report every re-split with old block id → new spans.

## Output (JSON)

```json
{
  "document": "<filename.md>",
  "model": "claude-sonnet-5",
  "themes": [
    {
      "id": "t01",
      "label": "3-8 word theme label",
      "need": "someone working on X needs Y",
      "spans": [{"line_start": 120, "line_end": 168}, {"line_start": 402, "line_end": 431}],
      "distributed_justification": "required iff spans are non-adjacent",
      "soft_members": [{"block": "b014", "also_in": ["t03"]}]
    }
  ],
  "resplits": [
    {"input_block": "b007", "new_spans": [{"line_start": 300, "line_end": 340}, {"line_start": 341, "line_end": 380}], "reason": "why the split test fired"}
  ],
  "unassigned": [
    {"block": "b023", "reason": "why this content block answers no realistic search need"}
  ]
}
```
- Spans inside ONE theme never overlap; spans across themes may (soft membership).
- Trash spans from the input stay excluded and are not re-assigned.
- This schema is your ENTIRE output — nothing beyond it.
