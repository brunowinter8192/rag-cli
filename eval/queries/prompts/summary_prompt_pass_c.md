## Task

You receive ONE markdown document and a set of themes, each a set of line spans. For each theme, read the passages and write one summary describing the information NEED those passages answer — as a searcher who does not yet know the answer would frame it. The summary must be rich enough that a realistic multi-concept search could be formulated from it alone, and poor enough that no passage wording or answer content can be reconstructed from it.

## Rules

### R1 — Indicative, not informative

The summary describes WHAT the theme answers, never the answer itself. A searcher knows their problem, not the document's content.

### R2 — Structured slots, fixed budget

Every summary fills exactly these slots, ~60-90 words total:
1. **field** — 1 line, field vocabulary mandatory
2. **information_need** — 1-2 sentences, indicative. ORDERING RULE: the first clause carries the theme's PRIMARY component; secondary aspects follow after. This order is load-bearing, not style. NEED LEVEL: a realistic information need is a practitioner's CASE-MATCH question — someone with a case at hand searching the literature for whether it matches theirs: does this methodology fit my situation, under what conditions, derived how. Always multi-concept, always needing context AROUND any formula. A bare artifact lookup ("the definition/statement/proof/theorem/formula of X") is never a standalone search. Lookup phrasings are BANNED and validator-rejected; if a theme seems to support only a lookup need, frame the SITUATION that would drive someone to that content (what they are trying to establish, verify, or apply), not the artifact. The primary_concept must anchor the first clause as a CONCEPT (majority of its content words present, inflection-tolerant) — verbatim embedding is not required.
3. **primary_concept** — exactly ONE of the sub_concepts: the concept the theme is centrally about. This field fixes the theme's weighting decision — choose it deliberately.
4. **sub_concepts** — 3-5 named field terms (the hooks for a multi-concept query), including the primary_concept
5. **answer_type** — method derivation / definition / empirical comparison / test procedure / ... — the KIND of answer, without the content

### R3 — Practitioner test per term (anti-over-neutralization)

Per term ask: "would a practitioner who never read this passage use this term to describe the need?" Yes → keep (the field owns the word: GARCH, ACF, maximum likelihood). No → it is the author's phrasing → out. Nothing is enriched, only not falsely removed. Standard field terminology is WANTED — real users type jargon; only the passage's distinctive phrasing is the poison.

### R4 — Bans

No numbers, no results, no theorem contents, no formulas, no author phrasing, no document structure references ("section 3", "the appendix", "this paper").

## Output (JSON)

```json
{
  "document": "<filename.md>",
  "model": "claude-sonnet-5",
  "summaries": [
    {
      "theme_id": "t01",
      "field": "financial econometrics / volatility modeling",
      "information_need": "...",
      "primary_concept": "term1",
      "sub_concepts": ["term1", "term2", "term3"],
      "answer_type": "definition + model specification"
    }
  ]
}
```
- One entry per input theme, `theme_id` matching the input ids.
- Word budget counts field + information_need + sub_concepts + answer_type together.
- This schema is your ENTIRE output — the input themes stay untouched, nothing beyond the schema.
