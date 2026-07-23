# Segment Definition (Answerability) + Theme-Summary Rules (2026-07-24)

Session settled the two pieces deferred from the 2026-07-23 session: what a self-contained segment IS, and the rules for the neutral theme summary. Both grounded in newly procured literature (16 docs indexed into `rag-cli-reference` this session, list below). Framed as of 2026-07-24.

## Semantic ≠ content coherence (the core distinction)

Embedding similarity is a PROXY for topical coherence and fails in both directions, demonstrated on `RAGAS_Evaluation_Framework.md`:
- **Over-merge:** the three RAGAS metrics (faithfulness / answer relevance / context relevance) are semantically near-identical (same LLM/prompt/score/question vocabulary) → an embedding clusterer tends to fuse them into one cluster; content-wise they are three distinct methods with three formulas → three needs.
- **Split:** the faithfulness METHOD (§3, statements/verification vocabulary) and the faithfulness annotation PROTOCOL (§4, annotators/agreement vocabulary) are one topic in different registers → embedding distance may separate them.

RAPTOR groups "based on semantic similarity not just order in the text" (its §3, verbatim) — i.e. by construction the semantic proxy, not content reasoning. TextTiling (Hearst 1997) is linear lexical-cohesion valley detection: content-driven boundaries, but cannot connect a distributed theme and matches surface tokens only (no synonymy).

## Decided: segment = answerability-defined theme

**A self-contained theme is the all-and-only answer set of ONE realistic information need, expressible as one or more non-overlapping line spans (distributed allowed).**

Grounding:
- **Answerability criterion:** Kamps 2008 / INEX Focused Task ("most focused non-overlapping document parts"; precision = as little non-relevant text as possible) + RAGAS context relevance ("relevant to the extent that it EXCLUSIVELY contains information needed to answer the question").
- **Distributed spans are the GT standard:** INEX ground truth = assessor-highlighted passages, Trel(q) explicitly the sum of NON-OVERLAPPING highlighted passages — a set of spans, not one block. Lexical-chain theory (Morris & Hirst via Hearst) models "chain returns": a theme resuming after a digression is one coherence unit.
- **Supporting signals** (not deciders): lexical cohesion (a theme lives while its term/entity set stays active; boundary where a large active set is replaced — Hearst/Halliday-Hasan) and subject-matter shift (Chafe via Hearst: cut on change of subject matter, not phrasing).
- Answerability is the TIE-BREAKER because it binds to the pipeline's end use (theme → summary → query): it splits the RAGAS three-metrics case correctly where pure semantics over-merges.

**Mechanism:** LLM content-reasoning segmentation (one prompt per md, returns line spans per theme) — not TextTiling, not RAPTOR's GMM/UMAP machinery. LumberChunker (Duarte 2024) is the direct literature for LLM-driven content-shift segmentation (+7.37% DCG@20 over baselines on GutenQA per its abstract). Cost: one deterministic-place LLM call per md, no worker orchestration. Known trade-off: less reproducible than mechanical clustering (prompt/temperature sensitivity) — accepted, because the eval GT needs content boundaries, not reproducible-but-wrong ones.

**Circularity guard:** the segmenter imagines "a query could target this" only to place boundaries; the actual query is authored later by a separate role from the summary alone (anti-leakage pipeline unchanged). Segmenter and query author must never be the same pass.

## RAPTOR's 100-token leaf is NOT a grounded value

RAPTOR §3 introduces the 100-token chunking as "similar to traditional retrieval augmentation techniques" — inherited convention, no ablation/sweep anywhere in the paper. The chunk-size literature (Rethinking Chunk Size, Fraunhofer 2025) shows no universal optimum: 64-128 tokens win on concise fact QA (SQuAD 64.1% recall@1 at 64), 512-1024 on long/dispersed/technical corpora (NarrativeQA 4.2%→10.7% recall@1 from 64→1024; TechQA 16.5%→61.3%), and the optimum is embedding-model-dependent. Our reference corpus is technical/dispersed → blind-copying 100 would sit near the bad end. Chunk size = config-sweep candidate (~256-1024), and it is the LEAF granularity knob, distinct from the theme definition above.

## Theme-summary rules (for worker 1)

Diagnosis of the batch01 over-neutralization: the worker stripped standard FIELD terminology (e.g. "GARCH" → "generalized conditional-variance model"). The anti-leakage principle only bans the passage's distinctive PHRASING; natural field-vocabulary overlap is wanted (real users type jargon). The summary rules make that split operational:

- **Indicative, not informative** (classic summarization taxonomy): the summary describes the information NEED the segment answers — never the content/results themselves.
- **Structured slots, not free-form** (structured-abstracts evidence, Hartley 2014 / Ad-Hoc Working Group 1987: fixed slots produce more consistent, more informative abstracts; Zhang 2023: instruction quality dominates LLM summary quality):
  1. Field (1 line, field vocabulary mandatory)
  2. Information need (1-2 sentences, indicative)
  3. Sub-concepts (3-5 named field terms — the hooks for worker 2's multi-concept query)
  4. Answer type (method derivation / definition / empirical comparison … — without the content)
  5. Fixed word budget overall (~60-90 words), no numbers/results, no author phrasing
- **Practitioner test** (replaces the rejected `field_terms` augmentation): per term — "would a practitioner who never read this passage use this term to describe the need?" Yes → keep (field owns the word); no → it is the author's phrasing → out. Nothing is enriched, only not falsely removed.
- **Documented deviation from the abstract standards:** ANSI/NISO Z39.14 prescribes using the text's "significant words" (retrieval-findability rationale) — for our GT construction exactly the leakage channel. We adopt the standards' FORM discipline (slots, budget, indicative style) and overlay the anti-leakage terminology rule.

Validation plan: re-summarize the batch01 segments under these rules, check (a) field terms restored, (b) spot-check against passages for phrasing leaks; then run worker 2 on old vs new summaries and compare query realism.

## Literature procured + indexed this session (rag-cli-reference)

- Segmentation batch: Duarte2024LumberChunkerNarrativeSegmentation, Halliday1976CohesionInEnglish (book), Beaugrande1981IntroductionToTextLinguistics (book).
- Summarization batch: AnsiNisoZ3914GuidelinesForAbstracts, AdHocWorkingGroup1987MoreInformativeAbstracts, Hartley2014StructuredAbstractsResearchUpdate, Nenkova2011AutomaticSummarizationSurvey, Maynez2020FaithfulnessFactualityAbstractiveSummarization, Fabbri2021SummEvalSummarizationEvaluation, Zhang2023BenchmarkingLlmNewsSummarization.
- Query batch: see the query-formulation entry of this date.
- Cleanup: standard classes (backmatter cut incl. Nenkova headingless-refs run + 256 lines, image tags, HTML tables → pipe text with token-set validation, spaced math de-spaced alnum-stable, entities unescaped); one Su2023 table left as HTML (token mismatch on convert — content intact).

## Sources

- `rag-cli-reference`: Hearst1997TextTilingSubtopicSegmentation, Sarthi2024RaptorTreeOrganizedRetrieval, Kamps2008InexFocusedRetrieval, RAGAS_Evaluation_Framework, Rethinking_Chunk_Size_Long_Document + the newly indexed docs above.
- `eval/queries/batch01_regions.json` (over-neutralization evidence).
