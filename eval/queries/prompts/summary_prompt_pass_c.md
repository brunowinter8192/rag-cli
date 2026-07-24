# Summary Prompt — Pass C: Theme Summaries (Worker-1 Role)

Third pass of the eval-suite segmentation pipeline. Input: the document + the Pass B theme
spans (spans ONLY — the Pass B need sentences and labels are withheld, so the summary
cannot inherit segmentation wording). Pass C reads each theme's passages and writes one
NEUTRAL theme summary per theme. The summary is later the ONLY input of the query author,
who never sees the passages: it must be rich enough to seed a realistic multi-concept
query, and poor enough that no passage wording or answer content can be mirrored.

---

## Task

For each theme (a set of line spans), read the passages and write one summary describing
the information NEED those passages answer — as a searcher who does not yet know the
answer would frame it.

## Rules

### R11 — Indicative, not informative
The summary describes WHAT the theme answers, never the answer itself. A searcher knows
their problem, not the document's content.
[Grounding — classic summarization taxonomy: an indicative summary conveys about-ness,
an informative summary "can be read in place of the document" (Nenkova 2011 §1.1);
ANSI/NISO Z39.14 §6.2: indicative abstracts describe purpose/scope, not results. An
informative summary would hand the query author answer wording — the leakage channel the
two-role pipeline exists to close.]

### R12 — Structured slots, fixed budget
Every summary fills exactly these slots, ~60-90 words total:
1. **field** — 1 line, field vocabulary mandatory
2. **information_need** — 1-2 sentences, indicative
3. **sub_concepts** — 3-5 named field terms (the hooks for a multi-concept query)
4. **answer_type** — method derivation / definition / empirical comparison / test
   procedure / ... — the KIND of answer, without the content
[Grounding: structured-abstracts evidence — fixed slots produce more informative, more
consistent abstracts, replicated across five sites (Hartley 2014; Ad-Hoc Working Group
1987).]

### R13 — Practitioner test per term (anti-over-neutralization)
Per term ask: "would a practitioner who never read this passage use this term to describe
the need?" Yes → keep (the field owns the word: GARCH, ACF, maximum likelihood). No → it
is the author's phrasing → out. Nothing is enriched, only not falsely removed. Standard
field terminology is WANTED — real users type jargon; only the passage's distinctive
phrasing is the poison.
[Grounding: over-neutralization evidence from the first (2026-07) summary attempt —
"GARCH" was stripped to "generalized conditional-variance model", pushing queries toward
generic paraphrase instead of the jargon-dense style that dominates the measured real
query distribution.]

### R14 — Bans
No numbers, no results, no theorem contents, no formulas, no author phrasing, no document
structure references ("section 3", "the appendix", "this paper").
[Documented deviation: ANSI/NISO Z39.14 §7.6 prescribes reusing the text's significant
words for retrieval findability — for GT construction exactly the leakage channel. We
adopt the standards' FORM discipline (slots, budget, indicative style) and invert the
terminology rule.]

### R15 — Scope: summaries only
You do NOT write queries, do NOT alter theme boundaries, do NOT grade regions. (Anti-
leakage is enforced structurally by the orchestrator: the query author receives the
summaries only, never the passages, spans, or any need sentence from segmentation.)

## Output (JSON)

```json
{
  "document": "<filename.md>",
  "summaries": [
    {
      "theme_id": "t01",
      "field": "financial econometrics / volatility modeling",
      "information_need": "1-2 indicative sentences describing what is sought",
      "sub_concepts": ["term1", "term2", "term3"],
      "answer_type": "definition + model specification"
    }
  ]
}
```
- One entry per input theme, `theme_id` matching the Pass B ids.
- Word budget counts field + information_need + sub_concepts + answer_type together.
