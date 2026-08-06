## Task

You receive ONE markdown document and a linear block segmentation of it (contiguous line-span blocks plus trash spans). Form THEMES over the blocks. A theme is the unit later used as a graded ground-truth region set.

## Rules

### R1 — Theme definition: all-and-only answer set of ONE realistic information need

A theme comprises ALL blocks needed to answer one realistic practitioner question and ONLY those blocks.

### R2 — Need level: the three tests (operationalizes R1)

Not a separate definition — three checks that pin the LEVEL of R1's "realistic information need". The anchor is REAL usage: the practitioner has a case at hand and searches the literature for whether its case matches theirs (methodology validation) — always multi-concept, always needing context AROUND any formula. Symbol/formula lookups do not occur as standalone searches in the measured query distribution.
1. **One-question test:** the need is expressible as ONE search question — an enumeration ("and also...") indicates multiple needs.
2. **Standalone-search test (too fine):** would this ever be issued as its own search in real usage, or only ever as part of a broader case-match need? A formula, symbol, or single fact is never its own search — it is a FACT inside its parent theme, found via region hit + expansion.
3. **Split test (too coarse):** if subsets of a theme's blocks each answer a self-standing single-search question AND no realistic single question needs their union → separate themes. This test needs the meta view over the whole block list.

Calibration anchor: ~3-4 regions per need (validated on the Bollerslev1986GARCH run, 8 themes over 45 blocks). Counter-check per theme: its need must be formulable as a realistic multi-concept search query.

### R3 — Distributed themes allowed

Blocks of one theme need NOT be adjacent (method §, protocol §, appendix example = one theme). Each grouping of non-adjacent blocks carries a one-sentence justification of why they serve the same need.

### R4 — Theorem + proof = ONE theme; section echo is failure

A theorem/lemma statement and its (possibly distant, appendix) proof serve one need — "under what condition does X hold, derived how" — and form ONE distributed theme. A standalone "Proof of Theorem N" theme is BANNED; the validator rejects any theme whose label marks it as a proof. More broadly: a theme list that mirrors the paper's section structure 1:1 means the meta view was never exercised. The validator enforces a blocks/theme floor of 2.0. Expect distributed themes in any paper with an appendix; their absence needs to be justifiable, not the default.

### R5 — Soft membership allowed, flagged

A block may belong to multiple themes (a passage can be core to one need and context to another). Mark such blocks explicitly so validation sees every multi-assignment.

### R6 — Re-split at blank lines only

When the split test fires on a block, the new boundary must again sit on a blank line — blank lines are the only legal cut points. Report every re-split with old block id → new spans.

### R7 — The need sentence serves boundary placement

The question you imagine per theme exists ONLY to place boundaries; record it as the `need` field, nothing more.

## Output (JSON)

```json
{
  "document": "<filename.md>",
  "model": "claude-sonnet-5",
  "themes": [
    {
      "id": "t01",
      "label": "3-8 word theme label",
      "need": "one sentence, PRACTITIONER-SITUATION form: 'someone working on X needs Y' — never a content question ('what is X, how is it specified') written with the text in view.",
      "spans": [{"line_start": 120, "line_end": 168}, {"line_start": 402, "line_end": 431}],
      "distributed_justification": "required iff spans are non-adjacent",
      "soft_members": [{"block": "b014", "also_in": ["t03"]}]
    }
  ],
  "resplits": [
    {"input_block": "b007", "new_spans": [{"line_start": 300, "line_end": 340}, {"line_start": 341, "line_end": 380}], "reason": "split test: two self-standing needs"}
  ],
  "unassigned": [
    {"block": "b023", "reason": "why this content block answers no realistic search need — expected to be RARE; the input's trash spans should already have caught most non-content"}
  ]
}
```
- Spans inside ONE theme never overlap; spans across themes may (soft membership).
- Trash spans from the input stay excluded and are not re-assigned.
- This schema is your ENTIRE output — nothing beyond it.
