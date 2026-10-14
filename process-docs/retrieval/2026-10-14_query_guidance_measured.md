# Query guidance for rag-cli search, with the measured status of every claim (2026-10-14)

Written by the worker of milestone M2 (areas retrieval and search_strategy). The rules files are edited by the owner only; this entry holds the evidence, the proposed rule text is in the report that went to the orchestrator. Method, sample and caveats: see the entry of the same date in the area search_strategy. The eval suite was retired on 2026-09-18, so "verified" here means: tested on 12 real information needs taken from the production log, pooled blind judgments, pre-registered decision rules, plus one objective known-item rank. Absolute numbers are pool-relative; only comparisons are claimed.

## Where callers meet this guidance

1. The caller rules (rag-cli section of `tool-use.md`): proposed text in the orchestrator report, not applied.
2. The zero-result message of `rag-cli search` (`format_no_results`). It does not carry query-shape advice, because all 8 logged zero-candidate searches failed on a filter, never on wording.
3. This entry, for agents working on rag-cli.

## Two retrieval intents

- Precision intent: find the one chunk that answers a known question. One query, the default 4 results. If the answer is cut (a definition spans two chunks: N01, chunks 33 and 34 of the Grundei/Zaumseil text), extend with `expand_chunks`.
- Recall intent: check whether anything relevant exists that was not anticipated. One narrow query per concept, one search per relevant source document, results combined as a deduplicated union.

## Status of each statement

| Statement | Test | Result | Status |
|---|---|---|---|
| A guided query (one concept, corpus vocabulary, phrased as the answer) beats the keyword bag callers actually write, at small result counts | G against A on 12 needs | Hit@3 9 vs 7 (3 wins, 1 loss, 8 ties), Hit@4 10 vs 9 (1/0/11), mean precision@4 0.75 vs 0.69; known item N01 rank 4 vs 22 | measured, small effect |
| The stated gain comes from content, not from syntax | G against keyword list, natural-language request and boolean form of the same content, 6 precision needs, top 3 | hit 4 / 4 / 5 / 5 (G, keyword, request, boolean), mean precision 0.72 / 0.72 / 0.67 / 0.78; N01 known-item ranks 4 / 5 / 2 / 8 | measured: no form is reliably better or worse |
| "A dense query is not boolean / operator syntax / keyword list / request" | same test | no failure observed; 0 of 369 logged queries use operators; the boolean form was not worse here | not reproduced; do not state it as a measured failure |
| Use the vocabulary of the corpus, not your own synonyms | N01: the logged query used "Kontrolle" and "Überwachung", the corpus says "Corporate Governance" | rank 22 vs 4; statements containing the corpus term (guided, keyword, request, boolean form and one sibling) rank 2 to 8, the two siblings worded with "Kontrolle" / "Überwachung" rank 16 and 12 | observed in one need; consistent with the 4 other German needs, not a test of its own |
| Counter-case | N04: the logged query copied the statute heading words and ranked the answer first, the paraphrased guided query ranked it fourth | rank 1 vs 4 | a query in the exact words of the source can beat a paraphrase |
| Multi-concept queries fail | one merged statement (M) against four sibling queries (S) on 6 recall needs | aspect coverage M 1.00 vs S 0.95 at 12 printed; at 4 printed M 0.95 vs S@1 0.88; M needs 1 search instead of 4 | not reproduced: the merged query matched or beat the siblings. One concept per query remains the safe default, not a measured necessity |
| Anchor effect: a rewrite built from the vocabulary of the first hits raises precision and lowers recall | R against A, top 3 and top 5 | precision@3 0.78 vs 0.72 (2 wins, 0 losses), relevant documents at 5: 1.83 vs 2.00 for A (A more in 3 needs, R more in 1), aspect coverage unchanged (ceiling) | direction as predicted, effect small, 12 needs: weakly supported |
| Several sibling queries beat one broad query for recall | S (4 x 3) against A and G at 12 printed | Hit 10/10/10, aspect coverage 0.98/1.00/1.00, 31 percent of sibling results are duplicates | not supported at equal printed size; sample too easy to show a gain (ceiling) |
| Combine sibling result sets by union and use agreement between siblings as a relevance signal | P(relevant) for chunks returned by two or more siblings vs by one | 0.68 (n 38) vs 0.62 (n 61); margin below the 0.10 rule | agreement signal not supported; union with deduplication by (document, chunk) is the only measured-neutral combination |
| One search per relevant source document for definitional questions | per-source arm P, 4 reference needs | N03: finds the definitions (rank 1 in two textbooks) where broad search at any depth finds none; N01: Grundei-only search rank 1 vs 22 | measured, 2 decisive cases; counter-case N04 (statute chunks at rank 4 inside the filter, missed by top 3 per source) |
| Do not narrow `--document` to one document when other sources cover the topic | N03 logged filter `COKA_Skript_%` (slides only) | no definition of coordination reachable under that filter | measured (1 case), same pattern as the wise2627 symptom 3 |
| Reranker score is a cutoff signal | precision by score band | no band above 0.1 is poor | not supported; no cutoff |
| Query language = language of the corpus | N01, English statement vs German statement | known item rank 9 vs 4 | one probe, hypothesis |
| `expand_chunks` on every used hit | not a retrieval measurement | usage in transcripts 25 expand-only commands against 378 searches | rule decision of the owner; supported only by the chunk-boundary observation in N01 |

## Examples (observed)

- N01, "How does the course literature define external control?" Logged query `externe Kontrolle Definition externe Überwachung Unternehmensführung`, filter `LUEAG_%`: all 4 default results from Welge/Eulerich, the defining passage of Grundei/Zaumseil at rank 22. Guided query `Externe Corporate Governance bezeichnet die Kontrolle des Managements durch unternehmensexterne Akteure und Märkte.` with the same filter: that passage at rank 4. Same query with `--document 'LUEAG_Literatur_Grundei%'`: rank 1 and 2.
- N03, "How is coordination defined?" Logged filter `COKA_Skript_%` (slides): no defining chunk at any depth for logged, guided or sibling queries. Searches restricted to `COKA_Literatur_Ewert%` and `COKA_Literatur_Coenenberg%`: the defining sentence at rank 1 in each ("Koordination beinhaltet die Abstimmung von Einzelaktivitäten zur Erreichung übergeordneter Ziele.").
- N05, "Is there information on when course admissions are announced?" Logged `Fächerbelegung Zulassung Bekanntgabe`: first answer at rank 4; guided `Die Zulassung zu den belegten Fächern wird an einem festgelegten Termin bekanntgegeben.`: rank 1.
- N11, "Reddit alternatives to Tumi": logged `affordable alternative to Tumi laptop briefcase good value`: first answer at rank 4; guided `A cheaper alternative to a Tumi laptop briefcase gives good value for money.`: rank 1.
- N02: the module is not in the corpus; every arm returns twelve unrelated module descriptions with reranker scores that still look confident. A result list never says "nothing found"; the caller has to judge the content.

## Output size, the reason for the chain limit

Printed result: median 1,942 bytes, p90 2,132, max 3,091 (4,280 printed results). The probability that one Bash call prints more than 30,000 bytes: 12 results x 2 searches 1.00; 4 results x 3 searches 0.00, x 4 searches 0.28; 3 results x 4 searches 0.00, x 5 searches 0.02. Transcripts since 2026-09-18: 55 of 71 Bash commands with two or more searches were persisted, 7 of about 300 with one.
