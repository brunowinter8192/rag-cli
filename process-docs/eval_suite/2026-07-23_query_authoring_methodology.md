# Eval Query-Authoring Methodology + Open Segment-Definition (2026-07-23)

Records the query-authoring procedure settled this session for the retrieval eval-set, the artifacts produced, and the one open piece deferred to the next session (how a self-contained segment is defined). Framed as of 2026-07-23.

## Two-worker theme-fed pipeline (anti-leakage by construction)

The gold set must be free of INJECTED lexical overlap between query and gold passage, or the config sweep just measures which config exploits that overlap (a BM25-flattering artefact) instead of retrieval quality. Natural field-vocabulary overlap (a real user typing "GARCH") is fine and wanted; copying the passage's distinctive phrasing is the poison. The eval papers (RAGAS, ARES) all go passage→query and do NOT solve this — RAGAS's only guard is one prompt rule, ARES actively filters FOR queries that retrieve their own passage.

Adopted a two-worker split that removes intra-pipeline leakage structurally:
- **Worker 1 (reader):** reads passages, marks graded ground-truth regions, and writes a NEUTRAL theme summary per need — describing the information need WITHOUT the passage's distinctive terminology.
- **Worker 2 (query author):** sees ONLY the summaries, never the passages, and formulates the query from the summary alone. It cannot mirror wording it never saw.

Rejected `field_terms` augmentation (worker 1 attaching a list of standard field terms per need) — the user judged it reintroduces a vocabulary channel.

## Query spec (fixed)

Derived from the measured real query distribution (dual_log, 53 distinct queries: median 9 words, ~70% dense multi-concept keyword bags): 9-12 words, technical terminology, no question form, multi-concept, need-first. Type-labeled (keyword / natural / paraphrase / multi-hop). This spec is to be pinned as a production query rule too, so eval and prod query styles match by construction.

## Ground-truth format

Per need: a list of graded regions `{document, line_start, line_end, grade}` where grade 2 = core (directly answers the need), 1 = context (surrounding perspective / expansion target). Answer breadth ~3-4 regions, MAY be distributed within a paper or across papers. ~10-15% of needs are genuine cross-document multi-hop (a topic truly split across papers with no single-paper superset — NOT the false kind where one paper restates another). Line ranges (not chunk ids) are the anchor so the GT survives re-chunking.

## Literature grounding — what is and is not backed (checked against rag-cli-reference)

- **Grounded:** graded + multi-relevant relevance consumed by nDCG (BEIR: nDCG handles binary and graded; TREC-COVID has 3-level relevance with up to 493 relevant docs/query). Scale floor ~100-150 labeled datapoints for reliable system ranking (ARES Kendall-tau: 0.44 at 50, 0.72-0.83 at 150, 0.89-1.0 at 300-400) — so the N=100 target sits at the reliability edge, and region-graded queries (each ~30 graded items) plausibly need fewer, though that per-query-signal hypothesis is unproven.
- **NOT grounded (our own engineering choices):** the line-range span as the relevance UNIT — the literature marks relevance at document (BEIR, classic IR), passage (ARES/MS MARCO), or sentence (RAGAS context relevance) level, never free line spans; ours is a drift-robust anchor. The theme summary and its length — no paper has a summary step at all (they go passage/section→query directly), so any summary-length number is arbitrary; it must be set functionally (enough need for a spec-conforming query, not enough to reproduce the passage) and validated empirically.

## Artifacts produced this session

- `eval/queries/batch01_regions.json` — worker 1 first validation batch: 20 needs across 7 papers (GARCH/volatility, functional-data/FPCA, structural-breaks, ML/cross-validation), each with 3-4 graded regions + neutral summary; 2 genuine cross-document needs (n15, n20). This is the batch-first validation of the format before scaling to N=100.
- Observation on batch01: worker 1 over-neutralized — it stripped standard field terminology (e.g. "GARCH" → "generalized conditional-variance model"), which cleanly prevents leakage but risks pushing worker 2 toward generic paraphrase queries rather than the jargon-dense style that dominates real usage. This is the crux the open segment/summary work must resolve.

## Open — deferred to next session: how a self-contained segment is defined

The unresolved first question is NOT summary length but the UNIT: what makes a self-contained sub-topic to which one summary can be written — content-driven (the information the sentences carry), not a fixed sentence/line count. This is the text/topic-segmentation problem. To ground it, three papers were fetched, cleaned, and indexed into `rag-cli-reference` this session:
- `Hearst1997TextTilingSubtopicSegmentation` — subtopic passages via lexical-cohesion shifts (the canonical content-driven boundary definition).
- `Sarthi2024RaptorTreeOrganizedRetrieval` (RAPTOR) — cluster chunks into coherent groups + write a summary per group, recursively; nearest tested analog to "coherent region + summary" for RAG.
- `Kamps2008InexFocusedRetrieval` — INEX focused retrieval, graded sub-document relevance (specificity/exhaustivity), the literature-nearest anchor for graded region GT.

C99 (Choi 2000) was not fetched (optional); the two textbooks (Jurafsky & Martin, Manning et al.) were dropped as over-the-top. `CLiMB.1year.report.pdf` appeared in the source batch but is off-topic (not a research paper) and was NOT indexed — its inclusion is unresolved.

Next-session plan: read TextTiling + RAPTOR, distill an explicit "a segment is characterized by X, its summary covers Y" definition, hand THAT to worker 1, then run worker 2 (query authoring from summaries) — first on the 20-batch to validate query realism vs the over-neutralization observation, then scale to ~100.

## Sources

- `eval/queries/batch01_regions.json`; the two-stage worker outputs (worker 1 done, worker 2 not yet run).
- `rag-cli-reference`: Hearst1997TextTilingSubtopicSegmentation, Sarthi2024RaptorTreeOrganizedRetrieval, Kamps2008InexFocusedRetrieval, ARES_Automated_RAG_Evaluation, BEIR_Zero_Shot_IR_Benchmark, RAGAS_Evaluation_Framework.
- Real query distribution: `monitor-cc/src/logs/dual_log/*.jsonl`.
