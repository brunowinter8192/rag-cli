# Search strategy symptoms observed in a wise2627 study session (2026-10-14)

## Context

- Project: wise2627 (M.Sc. BWL study support). Collection `wise2627-reference`, course LUEAG (corporate governance).
- Caller: main agent answering a student's comprehension questions slide by slide, roughly 40 `rag-cli search` calls in one session.
- Default result count at that date: `RERANK_TOP_K = 12` in `src/rag/search_cmd.py`.
- The two relevant textbooks in the collection are of similar size:
  - `LUEAG_Literatur_WelgeEulerichCorporateGovernanceManagement_2021.md` (800 chunks)
  - `LUEAG_Literatur_GrundeiZaumseilAufsichtsratCorporateGovernance_2012.md` (898 chunks)

## User decision (2026-10-14)

The user wants fewer results per search and more searches instead. Everything that is caller behaviour (how many queries, per-source searches, expand_chunks) is to be settled in the rules, not in the tool.

## Symptom 1: a definitional passage in the second textbook was never surfaced

Question: "How does the literature define external control (externe Kontrolle)?"

- Two searches, both with `--document 'LUEAG_%'`:
  - `externe Kontrolle Definition externe Überwachung Unternehmensführung`
  - `externe Corporate Governance Mechanismen Disziplinierung Management`
- 24 results in total. 23 came from Welge/Eulerich, 0 from the Zipperling chapter in Grundei/Zaumseil.
- The agent answered "the literature has no definition of external control, only Welge/Eulerich's external mechanisms".
- The student then pasted the passage that does define it (Grundei/Zaumseil 2012, Zipperling chapter, p. 27, chunks 33-34):
  > "Während die interne Corporate Governance auf die innere Struktur des Unternehmens – Machtverteilung und Kontrolle – fokussiert, betrifft die externe Corporate Governance unternehmensexterne Akteure und Marktkräfte, wie z.B. den Markt für Unternehmenskontrolle, Kapital- und Arbeitsmärkte."
- That passage was found only with a query that restated it almost verbatim (rank 3, no document filter).
- Hypothesis, not tested: the query vocabulary ("Mechanismen", "Disziplinierung") matched Welge/Eulerich's wording, while Zipperling uses "interne/externe Corporate Governance". With 12 slots, one document's many near-duplicate chunks fill the list and push a single matching chunk from another document out.

## Symptom 2: twelve results per query overflow the caller's context

- Two chained searches with 12 results each produced 42-46 KB of output and triggered persisted output.
- This happened five times in the session (e.g. a DCGK + § 91 AktG search at 45.2 KB, a § 93 + § 90 AktG search at 44.2 KB).
- Each overflow needed an extra `poread` call and loaded about 45 KB into context, most of it irrelevant.
- Observed tail quality: in the § 90 AktG search, results 3-12 had reranker scores between 0.70 and 0.009 and were unrelated statute sections (§ 171, § 162, § 124a).

## Symptom 3: the caller narrowed definitional questions to one document

- For stewardship theory, property-rights theory, CG actors and internal/external mechanisms, the agent searched only `--document 'LUEAG_Literatur_Welge%'`.
- The answers were then presented to the student as "the literature".
- The second textbook covers the same topics and was never consulted for them.

## Symptom 4: expand_chunks was not used

- The project rule in wise2627 requires `expand_chunks` after every relevant hit.
- In about 40 searches the agent used `expand_chunks` twice.
- Definitions were answered from the single chunk that matched, without the surrounding paragraph.

## Consequence for the user

The student could not trust the answers, because a source-backed answer depended on which document happened to win the top 12.

## Direction agreed (not implemented)

- Tool: lower the default result count.
- Rules: several narrow queries instead of one broad query; for definitional questions one search per relevant source document; `expand_chunks` on every hit that is used in an answer.
- Related open work in this repository: issue Suchstrategie (search_strategy), issue Querybau (retrieval).
