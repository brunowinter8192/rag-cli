# Layer-1 Query Formats Fixed; Layer 2 Narrowed to the Instruction Prefix (2026-07-25)

Session settled the two design surfaces opened by the 2026-07-24 reframe (spec = hypothesis,
form = measured dimension). Framed as of 2026-07-25.

## Layer 1: three formats, per-format length, no global word rule

The global 9-12-word length rule fell with the reframe — it was part of the measured habit,
not a law; enforcing it globally would mutilate the longer formats and bias the sweep.
Formats fixed (each per need, sharing one region GT):

1. **keyword_bag** (incumbent) — concatenated field terms, no syntax, no question form,
   need-first, ~6-12 words.
2. **natural_question** — ONE grammatical question as a colleague would ask aloud, natural
   length. Hypothesis: question form may aid a model trained on question-passage pairs.
3. **field_sentence** (HyDE-derived) — 1-2 declarative sentences in target-corpus register;
   a HYPOTHESIS about the answer written from the summary alone (may be vague/wrong, must
   only sound like the field; asserts THAT a result exists, never which). HyDE's mechanism
   as a zero-latency formulation rule, since layer 1 is itself an LLM under rules.

Fourth candidate on hold: Bendersky & Croft 2008 (verbose-query key-concept reduction) —
half-covered by keyword_bag; fetch only if the sweep shows long formats losing.

Old type labels (keyword/natural/paraphrase/multi-hop) replaced by the format label;
multi-hop remains a NEED property (cross-document themes), not a query property.

## Layer 2: instruction prefix only, query-side, zero latency

LLM rewriting in layer 2 stayed rejected (latency, mid-pipeline non-determinism — per the
2026-07-24 reframe). What remains is the deterministic tool: prepend a task instruction to
the query before embedding.

- Qwen3-Embedding (prod model) is instruction-aware: input format "{Instruction} {Query}
  <|endoftext|>", instruction goes ONLY to the query side, documents embed unchanged (its
  §2) → no re-indexing, existing embeddings stay valid. Prod currently embeds the naked
  query — a format mismatch vs the model's training.
- Instructor (Su 2023) gives the template ("Represent the (Domain) TextType for
  TaskObjective") and the monotonic finding: performance rises with instruction detail
  (none < dataset tag < one-word domain < detailed), and is robust to paraphrase — the
  exact wording need not be perfect, only reasonably detailed.
- Implementation shape: static lookup collection-type → task string (docs / reference),
  string concatenation, zero latency.

## Sweep grid (unchanged from the reframe, now concretely fixed)

3 layer-1 formats x 2 layer-2 states (naked / instruction prefix) = 6 cells, all
prod-viable, no LLM in the search pipeline. Prefix application is a HARNESS dimension —
query files stay format-only; Pass D authors 3 queries per theme.

## Open procurement

Qwen3-Embedding HuggingFace model card (vendor default instruction string + no-instruction
performance delta) — needed before the sweep harness is built, not before batching.

## Sources

- `eval/queries/prompts/query_prompt_pass_d.md` (format definitions as executed)
- `rag-cli-reference`: Qwen3_Embedding, Su2023InstructorInstructionFinetunedEmbeddings,
  Gao2023HydeZeroShotDenseRetrieval, Wang2023Query2docQueryExpansionLlm, Bailey2016Uqv100QueryVariability
