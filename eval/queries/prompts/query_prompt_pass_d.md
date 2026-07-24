# Query Prompt — Pass D: Query Authoring (Query-Author Role)

Fourth pass of the eval-suite pipeline. Input: the Pass C theme summaries ONLY — never the
document, never the theme spans, never any segmentation output. You author search queries
from each summary alone; you cannot mirror passage wording you never saw. Per theme you
write THREE queries, one per format below: the format is a measured sweep dimension, not a
style choice.
[Grounding: UQV100 (Bailey 2016) — same information need, many formulations, measured
variance (10,835 queries / 100 topics); the region-graded ground truth hangs on the NEED,
so K format variants per need share one grading.]

---

## Task

For each summary, put yourself in the position of the practitioner the summary describes:
you have their problem, you have NOT read any answering document. Formulate the search you
would issue — three times, once per format.

## Rules

### R16 — Ground every query in the summary alone
Use the summary's field vocabulary and sub_concepts as your term pool; you may add terms
the FIELD owns (standard terminology a practitioner would naturally use) but never invent
specifics the summary does not support (no concrete conditions, values, named theorems).
Multi-concept: each query combines 2+ of the theme's sub-concepts — single-concept lookup
queries do not occur in the measured need distribution.

### R17 — Format definitions (one query each, labeled)
1. **keyword_bag** — concatenated field terms, no syntax, no question form, need-first.
   ~6-12 words. Example shape (foreign domain, illustrative only): `random forest feature
   importance permutation vs impurity bias correction`.
2. **natural_question** — ONE grammatical question, as a colleague would ask it aloud.
   Natural length. Example shape (foreign domain): `how does permutation-based feature
   importance in random forests correct the bias of impurity-based measures?`
3. **field_sentence** — 1-2 declarative sentences written as if they could STAND IN the
   target corpus: academic field prose, assertive register, no question form. This is a
   HYPOTHESIS about the answer formulated from the summary alone — it may be vague or
   even wrong; it must only sound like the field. Do not guess concrete conditions or
   values; assert THAT a result/condition/method of the summary's answer_type exists,
   in field vocabulary.
   Example shape (foreign domain): `permutation-based importance measures correct the
   systematic bias that impurity-based feature rankings exhibit for high-cardinality
   predictors in random forest models.`
   [Grounding: HyDE (Gao 2023) / Query2doc (Wang 2023) — embedding answer-like text
   lands nearer the target region than embedding the question; here the mechanism is a
   formulation rule at zero latency because the query author IS an LLM under rules.]

### R18 — Register, not answer knowledge
Every query must be writable by someone who never read the answering passages. If a query
only makes sense with the answer in hand (names the specific condition, the specific
formula, the specific empirical result), it is wrong — this holds for field_sentence
especially.

### R19 — Length is per-format, not global
The formats deliberately differ in length; do not compress the question or the field
sentence toward keyword length, and do not pad the keyword bag toward prose.

### R20 — Scope: queries only
You do NOT alter summaries, do NOT grade, do NOT rank. One output file, nothing else.

## Output (JSON)

```json
{
  "document": "<filename.md>",
  "queries": [
    {"theme_id": "t01", "format": "keyword_bag", "query": "..."},
    {"theme_id": "t01", "format": "natural_question", "query": "..."},
    {"theme_id": "t01", "format": "field_sentence", "query": "..."}
  ]
}
```
- Exactly three entries per theme, formats as labeled above.
