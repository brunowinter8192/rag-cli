# Pass Prompt Overhaul: Worker Blindness, Rules/Schema Separation (2026-08-12)

Joint walkthrough of the four pass prompts (`eval/queries/prompts/`) after the batch01 re-run, restructuring them around one principle: each pass worker sees ONLY its own role. Companion decision to the inline-injection entry of this date (mechanical prompt assembly, `injection.md`). Walkthrough reached pass C R2; C from R3 and all of D remain un-walked as of this date.

## Worker blindness — no cross-pass knowledge

All cross-pass references removed from the prompts: no pass names, no pipeline position, no mention that other passes exist. Pass B's task now says "a linear block segmentation" (not "the Pass A blocks"); C says "a set of themes, each a set of line spans"; D's summaries carry no provenance. Rationale: a worker that does not know neighbor passes exist can neither peek at their artifacts nor optimize for them; combined with inline injection, the input filter holds structurally. Consequences applied:

- Rule numbering restarts at R1 per prompt (A: R1-R4, B: R1-R6, C: R1-R4, D: R1-R6) — the old R1-R20 chain only made sense reading the pipeline as one document.
- Pass B resplit schema key renamed `pass_a_block` → `input_block` (the key itself leaked pass structure).
- Batch01 failure-history prosa removed from rules (R7b section-echo narrative, R18b's "discarded 214 queries") — history is orchestrator knowledge.
- Bollerslev calibration anchor (~3-4 regions per need) removed from B: run-reference plus a number workers would optimize toward instead of applying the three tests.

## Literature groundings removed

All [Grounding: ...] brackets (Hearst, Duarte, Kamps, Sarthi, Nenkova, Hartley, Bailey, Gao/Wang) stripped from the four prompts — justification is orchestrator/process knowledge, not worker instruction. This REVERSES the 2026-07-24 decision that prompts be self-justifying with inline literature grounding; the grounding now lives only in git history and the design-session entries of this area.

## Anti-pattern lists → output-schema-only line

The negative-scope sections (A "Out of scope", B R10, C R15, D R20) replaced by one line in each Output section: "This schema is your ENTIRE output — nothing beyond it" (C/D additionally: input stays untouched). B's R10 was folded into R2 as the need-field definition rather than dropped, since it carried a real instruction.

## Shared NEED LEVEL wording in B and C

The case-match need definition is now WORD-IDENTICAL in B-R2 and C-R2: practitioner with a case at hand, does-this-fit-my-situation level, always multi-concept, bare artifact lookup never a standalone search. Rationale: B and C independently distill the same need from the same passages (consistency check); identical target definitions make divergence measure theme formation, not wording drift. A grep on the paragraph start finds both copies when the definition ever changes.

## Semantics in rules, schema as pure form

Field meaning lives exclusively in the rules; JSON schemas show keys, types, neutral example values. B's need-field definition (one sentence, practitioner-situation form, never a content question written with the text in view) moved from the schema placeholder into R2; C's information_need placeholder reduced to "..." (R2 is the slot definition); expectation-comments ("expected to be RARE") dropped from schema placeholders.

## Individual rule changes

- A R3b (line-by-line mandate, heading-shortcut ban) deleted entirely: redundant with R2's heading clause, and its partial-read-protection purpose is now carried mechanically by inline injection. The granularity corridor stays enforced in `validate_pass_a.py` unannounced.
- B R4 (was R7b) reduced to the theorem+proof core: statement + (possibly appendix) proof = ONE distributed theme, standalone proof themes banned. The section-echo-is-failure heuristic dropped: mirroring the paper's structure CAN be the correct theming; the degenerate pass-through case is caught mechanically by the validator's blocks/theme floor.
- B R7 (need serves boundary placement) deleted: covered by R1/R2 plus the schema.
- C R1 (indicative-not-informative) challenged against the HyDE principle and KEPT: indicative limits answer CONTENT, not answer FORM; the field_sentence format writes answer-shaped text without answer knowledge, which is exactly the production HyDE situation — an informative summary would let queries mirror passage content and overestimate HyDE performance.
- `model` field in all four output schemas fixed to literal `claude-sonnet-5` (was a placeholder); all lots run sonnet-5. Must be updated if the deferred opus-5 comparison run ever happens.
- All prompts reflowed to full-width lines (no hard wraps in paragraphs).

## Open as of this date

- Prompt walkthrough: C from R3 (practitioner test, bans) and all of D not yet walked.
- Validator follow-ups (source-code work, needed before the next B lot): `validate_pass_b.py` requires `pass_a_block` and must accept `input_block`; validator comments/error messages in all four scripts still cite the old R-numbering (a message "violates R6" now mismatches the worker's prompt).
- Blocks/theme floor 2.0: with section-echo no longer defined as failure, a legitimate paper could land below the floor; decide on the first concrete false-reject in batch02.
- Unchanged from the batch01 re-run entry: human review gate over the 13 leakage candidates, corpus freeze + qrels construction.
