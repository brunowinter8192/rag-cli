# Segmentation Prompt — Pass B: Theme Formation (Meta Pass)

Second pass of the eval-suite segmentation pipeline. Input: the document + the Pass A block
list. Pass B takes the META view over the finished blocks that linear processing cannot:
group blocks into themes (distributed allowed) and re-split blocks that Pass A left too
coarse. Run by a FRESH worker, never the Pass A worker: an unbiased second LLM reviews the
blocks without the segmentation history in context (cross-model check by construction).

---

## Task

Given the document and the Pass A blocks, form THEMES. A theme is the unit later used as
graded ground-truth region set and as the seed of one eval query.

## Rules

### R5 — Theme definition: all-and-only answer set of ONE realistic information need
A theme comprises ALL blocks needed to answer one realistic practitioner question and ONLY
those blocks.
[Grounding — "only" (precision): INEX Focused Task, retrieved parts must "contain as little
non-relevant text as possible" (Kamps 2008 §3.2); RAGAS context relevance: relevant "to the
extent that it EXCLUSIVELY contains information that is needed to answer the question".
"All" (completeness): INEX recall over Trel(q) = the SUM of all non-overlapping highlighted
passages of a topic — the GT of a need is the complete set of its relevant spans.]

### R6 — Need level: the three tests (operationalizes R5)
Not a separate definition — three checks that pin the LEVEL of R5's "realistic information
need". The anchor is REAL usage: the practitioner has a case at hand and searches the
literature for whether its case matches theirs (methodology validation) — always
multi-concept, always needing context AROUND any formula. Symbol/formula lookups do not
occur as standalone searches in the measured query distribution.
1. **One-question test:** the need is expressible as ONE search question — an enumeration
   ("and also...") indicates multiple needs.
2. **Standalone-search test (too fine):** would this ever be issued as its own search in
   real usage, or only ever as part of a broader case-match need? A formula, symbol, or
   single fact is never its own search — it is a FACT inside its parent theme, found via
   region hit + expansion.
3. **Split test (too coarse):** if subsets of a theme's blocks each answer a self-standing
   single-search question AND no realistic single question needs their union → separate
   themes. This test needs the meta view — it is WHY Pass B exists.
Calibration anchor: ~3-4 regions per need (validated on the Bollerslev1986GARCH run, 8
themes over 45 blocks). Counter-check per theme: its need must be formulable as a
realistic multi-concept search query.

### R7 — Distributed themes allowed
Blocks of one theme need NOT be adjacent (method §, protocol §, appendix example = one
theme). Each grouping of non-adjacent blocks carries a one-sentence justification of why
they serve the same need.
[Grounding: INEX GT is by construction a SET of non-overlapping highlighted passages spread
over the document (Kamps 2008); Morris & Hirst lexical chains model "chain returns" — a
theme resuming after a digression is one coherence unit.]

### R8 — Soft membership allowed, flagged
A block may belong to multiple themes (a passage can be core to one need and context to
another). Mark such blocks explicitly so validation sees every multi-assignment.
[Grounding: RAPTOR soft clustering rationale — "individual text segments often contain
information relevant to various topics, thereby warranting their inclusion in multiple
summaries" (Sarthi 2024).]

### R9 — Re-split at blank lines only
When the split test fires on a Pass A block, the new boundary must again sit on a blank
line (atom rule R1 holds across passes). Report every re-split with old block id → new
spans.

### R10 — Scope: boundaries only
The question you imagine per theme exists ONLY to place boundaries. You do NOT write
queries, do NOT write summaries — those are separate roles in the pipeline. (Anti-leakage
is enforced structurally by the orchestrator: the query author's input is filtered to
summaries only and never contains the recorded need sentences or spans.)

## Output (JSON)

```json
{
  "document": "<filename.md>",
  "themes": [
    {
      "id": "t01",
      "label": "3-8 word theme label",
      "need": "one sentence, PRACTITIONER-SITUATION form: 'someone working on X needs Y' — never a content question ('what is X, how is it specified') written with the text in view. Same need definition as the downstream summary pass, so the two independently distilled needs are directly comparable as a consistency check.",
      "spans": [{"line_start": 120, "line_end": 168}, {"line_start": 402, "line_end": 431}],
      "distributed_justification": "required iff spans are non-adjacent",
      "soft_members": [{"block": "b014", "also_in": ["t03"]}]
    }
  ],
  "resplits": [
    {"pass_a_block": "b007", "new_spans": [{"line_start": 300, "line_end": 340}, {"line_start": 341, "line_end": 380}], "reason": "split test: two self-standing needs"}
  ],
  "unassigned": [
    {"block": "b023", "reason": "why this content block answers no realistic search need — expected to be RARE; Pass A's trash taxonomy (incl. navigation_meta) should already have caught most non-content"}
  ]
}
```
- Spans inside ONE theme never overlap; spans across themes may (soft membership).
- Trash spans from Pass A stay excluded and are not re-assigned.
