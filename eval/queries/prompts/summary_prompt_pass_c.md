# Summary Prompt — Pass C: Theme Summaries (Worker-1 Role)

Third pass of the eval-suite segmentation pipeline. Input: the document + the Pass B theme spans (spans ONLY — the Pass B need sentences and labels are withheld, so the summary cannot inherit segmentation wording). Pass C reads each theme's passages and writes one NEUTRAL theme summary per theme. The summary is later the ONLY input of the query author, who never sees the passages: it must be rich enough to seed a realistic multi-concept query, and poor enough that no passage wording or answer content can be mirrored.

## Input delivery (orchestrator contract)

Both inputs are injected INLINE into the worker prompt: the source document via `cat -n` (1-indexed; `data/` is gitignored and absent from worktrees) and the Pass B spans as a spans-only JSON (need sentences and labels stripped by the orchestrator BEFORE injection — the anti-leakage filter is applied to the injected content, not left to worker discipline). No path handover — inline injection makes partial reading structurally impossible and closes the leakage channel of the worker opening the full Pass B artifact.

---

## Task

For each theme (a set of line spans), read the passages and write one summary describing the information NEED those passages answer — as a searcher who does not yet know the answer would frame it.

## Rules

### R11 — Indicative, not informative

The summary describes WHAT the theme answers, never the answer itself. A searcher knows their problem, not the document's content. [Grounding — classic summarization taxonomy: an indicative summary conveys about-ness, an informative summary "can be read in place of the document" (Nenkova 2011 §1.1); ANSI/NISO Z39.14 §6.2: indicative abstracts describe purpose/scope, not results. An informative summary would hand the query author answer wording — the leakage channel the two-role pipeline exists to close.]

### R12 — Structured slots, fixed budget

Every summary fills exactly these slots, ~60-90 words total:
1. **field** — 1 line, field vocabulary mandatory
2. **information_need** — 1-2 sentences, indicative. ORDERING RULE: the first clause carries the theme's PRIMARY component; secondary aspects follow after. The query author reads rank from this order — it is load-bearing, not style. NEED LEVEL (anti-lookup): the need is a practitioner's CASE-MATCH question — does this methodology fit my situation, under what conditions, derived how — never a bare artifact lookup. Phrasings of the form "wants the definition/statement/proof/theorem/formula of X" are BANNED and validator-rejected: a searcher with a case does not fetch artifacts, they match their problem against the literature. If a theme seems to support only a lookup need, frame the SITUATION that would drive someone to that content (what they are trying to establish, verify, or apply), not the artifact. The primary_concept must anchor the first clause as a CONCEPT (majority of its content words present, inflection-tolerant) — verbatim embedding is not required.
3. **primary_concept** — exactly ONE of the sub_concepts: the concept the theme is centrally about. You know the passages; the query author does not — this field is where the weighting decision is made, so it cannot be re-interpreted downstream.
4. **sub_concepts** — 3-5 named field terms (the hooks for a multi-concept query), including the primary_concept
5. **answer_type** — method derivation / definition / empirical comparison / test procedure / ... — the KIND of answer, without the content

[Grounding: structured-abstracts evidence — fixed slots produce more informative, more consistent abstracts, replicated across five sites (Hartley 2014; Ad-Hoc Working Group 1987).]

### R13 — Practitioner test per term (anti-over-neutralization)

Per term ask: "would a practitioner who never read this passage use this term to describe the need?" Yes → keep (the field owns the word: GARCH, ACF, maximum likelihood). No → it is the author's phrasing → out. Nothing is enriched, only not falsely removed. Standard field terminology is WANTED — real users type jargon; only the passage's distinctive phrasing is the poison. [Grounding: over-neutralization evidence from the first (2026-07) summary attempt — "GARCH" was stripped to "generalized conditional-variance model", pushing queries toward generic paraphrase instead of the jargon-dense style that dominates the measured real query distribution.]

### R14 — Bans

No numbers, no results, no theorem contents, no formulas, no author phrasing, no document structure references ("section 3", "the appendix", "this paper"). [Documented deviation: ANSI/NISO Z39.14 §7.6 prescribes reusing the text's significant words for retrieval findability — for GT construction exactly the leakage channel. We adopt the standards' FORM discipline (slots, budget, indicative style) and invert the terminology rule.]

### R15 — Scope: summaries only

You do NOT write queries, do NOT alter theme boundaries, do NOT grade regions. (Anti-leakage is enforced structurally by the orchestrator: the query author receives the summaries only, never the passages, spans, or any need sentence from segmentation.)

## Output (JSON)

```json
{
  "document": "<filename.md>",
  "model": "<the model you run on, e.g. claude-sonnet-5>",
  "summaries": [
    {
      "theme_id": "t01",
      "field": "financial econometrics / volatility modeling",
      "information_need": "1-2 indicative sentences, primary component first",
      "primary_concept": "term1",
      "sub_concepts": ["term1", "term2", "term3"],
      "answer_type": "definition + model specification"
    }
  ]
}
```
- One entry per input theme, `theme_id` matching the Pass B ids.
- Word budget counts field + information_need + sub_concepts + answer_type together.
