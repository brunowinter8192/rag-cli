# Result count and search strategy: measurement and decision (2026-10-14)

Worker session of milestone M2. Owner decision of 2026-10-14 (fewer results per search, more searches, caller behaviour in the rules) was the starting point. This entry records how the decision was checked against data, because the eval suite that would normally do this was retired on 2026-09-18.

## Facts established before any measurement

- A single 12-result search prints about 22 KB (median 1942 bytes per printed result, p90 2132, max 3091, 4280 printed results in the production log). It stays under the 30,000-character persisted-output threshold.
- Overflow comes from chaining. Transcripts since 2026-09-18: 55 of 71 Bash commands with two or more `rag-cli search` were persisted, against 7 of about 300 commands with one search (those 7 were mixed commands with other tools or loops). Bootstrap over the logged result sizes (`dev/search_strategy/E_output_size.py`): two chained 12-result searches exceed 30,000 bytes in 100 percent of draws.
- Printing limits by `k` and chain length (probability of exceeding 30,000 bytes, bootstrap over logged sizes): `k=3` chain 4 is 0.000 and chain 5 is 0.015; `k=4` chain 3 is 0.000 and chain 4 is 0.279; `k=5` chain 2 is 0.000 and chain 3 is 0.015; `k=6` chain 3 is 0.948.
- The wise2627 definitional miss reproduces on 2026-10-14. The Grundei/Zaumseil chunk 33 is among the 30 dense candidates for every query variant tried, and the reranker places it at position 22 (query `externe Kontrolle Definition externe Überwachung Unternehmensführung`) or 19 (`externe Corporate Governance Mechanismen Disziplinierung Management`) of 30, behind 28 Welge/Eulerich chunks. A declarative statement without the keyword bag put it at rank 5 to 7. Consequence: a smaller `k` makes the single broad query miss more, not less. Only a per-source search (`--document` on the second textbook) removes the competition at SQL level.
- Reranker scores do not give a cutoff that transfers: in the miss case unrelated tail chunks still score above 0.95, in the § 90 AktG case the tail scored 0.70 to 0.009. Median score at rank 12 in the 369 logged searches is 0.26.
- The expand log joins to the search log for 18 of 28 expansions. Rank of the expanded hit: 1,1,1,1,1,1,1,1,1,2,2,3,3,5,5,6,7,8. Selection bias: the agent reads from the top.
- 0 of 369 logged queries use boolean or operator syntax, 7 are question-form, median length is 8 words, most are keyword bags with three or more concepts.
- `~/.local/bin/rag-cli` executes the main checkout, not a worktree. A change in a worktree is verified with `venv/bin/python <worktree>/cli.py search ...`; the wrapper only after the merge.

## Measurement design (fixed before the first retrieval)

Code and frozen inputs: `dev/search_strategy/`. Needs and all arm queries are in `data/needs.json`, written (file time 22:59:10) before the first retrieval (23:00). They entered git only afterwards, because `data/` is ignored repo-wide and `.gitignore` needed an exception for `dev/search_strategy/data/`; the file times are the proof of order, not the commit history.

- Sample: N = 12 information needs, 6 precision-intent and 6 recall-intent, 4 from reference collections, 4 from docs collections, 4 from other collections. Drawn with seed 20261014 from logged searches that have recoverable transcript context; walk in draw order, accept a candidate if the need can be stated from the user text or the assistant intent sentence before the call. Skip reasons are in `needs.json`. N01 is the mandated wise2627 miss and is not blind: the author had read the answer passage in the symptom record.
- Arms per need, all ranked to depth 30 against one DB state: A logged query verbatim; G one guided query (single concept, declarative, answer-shaped); S four sibling queries (G plus three), top 3 each; M recall needs only, one merged multi-concept statement; F precision needs only, the content of G as keyword list, as natural-language request, with boolean operators; P one G-query per source document with `--document`, top 3 each, reference needs only; R a rewrite of A built from the vocabulary of A's top-3 hits, written after judging.
- Judging: pooled, blind to arm, rank and score; chunk text in random order; one LLM judge (the author, same model family as the callers, which is a stated limit). Grade 0 not relevant, 1 usable part, 2 answers the need alone; aspects covered listed per chunk. Pool capped at 44 chunks per need, trimmed by best normalised rank (trimmed counts are in the report).
- Measures at equal printed results: Hit (a grade-2 chunk present), distinct relevant chunks, aspect coverage, relevant documents, P (relevant share of printed results).
- Decision rules were coded in `decisions.py` after the retrieval run and before the first judgment (and had been stated in the first report to the orchestrator before any code): default count `k*` is the smallest `k <= 5` with `Hit@k(A) >= Hit@12(A) - 1`, confirmed if `Hit@k*(G) >= Hit@k*(A)`; siblings (S, 4x3) replace the single 12-result search iff `Hit(S) >= Hit(A) - 1`, mean aspect coverage of S exceeds A, and S wins more needs than it loses; a claim is "supported" if at least two thirds of the non-tied needs go in the predicted direction.
- Replacement for the eval suite: pooled blind judgments on real needs plus the objective known-item rank for N01. Absolute numbers are pool-relative; only comparisons between arms are claimed.

## Results (N = 12, report: `dev/search_strategy/md/D_analyze_report.md`)

Sample caveats, stated first because they bound every number below:
- N02 (Data Science in Accounting, `goethe-bwl-reference`): the module is not in the indexed handbook (WS 2023/24). All 22 pooled chunks are grade 0, every arm scores zero. The need stays in the sample as a measured negative case ("nothing exists"), it contributes only ties.
- N09 (Yandex SmartCaptcha): no chunk in the pool mentions Yandex. Aspect a1 is uncoverable; grade 2 was given to concrete, reported workarounds for search-engine captchas of other aggregators (DuckDuckGo, Startpage, Google).
- Recall needs saturate: with 12 printed results the logged query already covers every aspect that any chunk covers (aspect coverage 1.00 for the logged query in all five recall needs that have any relevant chunk). The aspect metric cannot separate strategies at 12 printed results.
- Replaying the logged queries reproduced the logged top 12 exactly for N01-N04, N06, N09; for the docs collections (N05, N07, N08) the index had changed since logging (overlap 11, 0, 8 of 12).
- One judge (the author), pooled and blind to arm, rank and score. A re-judge of 22 random pooled chunks (8 percent) agreed 22 of 22. That check ran in the same session, so it measures consistency of recall, not independence. N01 is not blind (the author had read the answer passage).
- Judgments: 276 pooled chunks (264 for stage 1, 12 added by the anchored-rewrite arm R). Grades and aspects are in `dev/search_strategy/data/judgments/`.

Pre-registered decisions:
- Default count. Needs with a grade-2 chunk in the printed list, logged query (A) against guided query (G), 12 needs: A at k=3,4,5,6,8,12 gives 7,9,9,9,9,10; G gives 9,10,10,10,10,10. Rule: smallest k <= 5 with Hit@k(A) >= Hit@12(A) - 1, so **k* = 4**, confirmed because Hit@4(G) = 10 >= Hit@4(A) = 9. First answer-bearing chunk of G sits at rank 1 in 7 needs, 2 in 2, 4 in 1 (N04); none in N02 and N03 (N03 is the filter-too-narrow case, below). Mean precision at 4: G 0.75, A 0.69; at 12: G 0.60, A 0.56.
- Strategy at 12 printed results. S (four sibling queries, top 3 each) against A: Hit 10 vs 10, mean aspect coverage 0.98 vs 1.00, wins/losses/ties 0/1/11. The rule does not adopt S. S against G12 is identical (0/1/11), G12 against A12 is 0/0/12. The single loss is N06 (S covers three of four aspects). Of the 12 results printed by four sibling queries 31 percent are duplicates (distinct share 0.69).
- Per-source search (P, reference needs N01-N04, top 3 per source): Hit 2 vs 2 for A, relevant documents [2,0,4,2] vs [1,0,1,1]. Decisive cases: N03 (logged `--document 'COKA_Skript_%'` is the course slides only) A, G and S find no defining chunk at any depth, the per-source arm finds Ewert and Coenenberg at rank 1. N01: known item Grundei chunk 33 sits at rank 22 for the logged query A, rank 4 for G, rank 1 for the Grundei-only search. N04 is the counter-case: the statute chunks (sections 78 and 82 AktG) are at rank 4 for G inside `LUEAG_%`, and the per-source arm with top 3 misses them in all three sources.

Exploratory, added after seeing the stage 1 results (marked as such in the report):
- Guided against logged query: hits at k=3 3 wins/1 loss/8 ties, at k=4 1/0/11. At four printed results, one query with four results and four queries with one result each give the same Hit (10 of 12); the four-query variant costs four reranker passes (about 4.5 s each).
- Score cutoff: precision by reranker score band (n): 0.9-1.01: 0.63 (102), 0.5-0.9: 0.43 (7), 0.1-0.5: 0.62 (16), below 0.1: 0.21 (19). Only the lowest band is poor and it holds 19 of 144 results. No cutoff is shipped.

## Decisions taken

1. `RERANK_TOP_K` in `src/rag/search_cmd.py` goes from 12 to 4. `RERANK_CANDIDATES` stays 30 (plateau measured on 2026-05-25 and not touched). No `--top-k` flag (owner decision: caller behaviour lives in the rules).
2. The zero-result message in `src/rag/formatting.py` (`format_no_results`) is rewritten. The orchestrator accepted the zero-result message as a place for query-shape guidance. The log shows why that content does not fit there: all 8 searches with `candidates = 0` carried a `--document` or `--exclude` pattern that matched nothing (for example `%tahoe%`, `process-docs/%` on a collection without such paths), none failed because of wording. The message therefore says exactly that and points to `list_documents`. The current rule text tells callers to rephrase the query at least twice on zero chunks; that instruction sends them in the wrong direction.
3. The winning default strategy is: guided single-concept queries at 4 results, one search per relevant source document for source-critical (definitional) questions, and further queries only for further concepts. The measurement does not show that several sibling queries beat one guided query at equal printed size; it shows that guided queries beat the logged keyword bags at small k, and that per-source search is what reaches a passage which a broad search ranks behind a near-duplicate-rich document.
4. Chain limit: bootstrap over 4280 printed results (`dev/search_strategy/md/E_output_size_report.md`), probability that one Bash call exceeds 30,000 bytes. k=4: chain 3 is 0.000, chain 4 is 0.279. k=3: chain 4 is 0.000, chain 5 is 0.015. k=5: chain 3 is 0.015. 12 results: two chained searches always exceed (matches 55 of 71 persisted chained commands in the transcripts). Proposed caller rule: at most 3 searches per Bash call at k=4.

## Verification through the production code path (2026-10-14)

`rag-cli` runs the main checkout, so the worktree was exercised with `venv/bin/python <worktree>/cli.py search` (same code, same servers and DB, logs land in the worktree). Results, wise2627-reference:
- Guided query `Externe Corporate Governance bezeichnet die Kontrolle des Managements durch unternehmensexterne Akteure und Märkte.` with `--document 'LUEAG_Literatur_Grundei%'`: 4 results, 8,210 bytes. Result 1 is chunk 33 of the Grundei/Zaumseil text (the passage the student had to paste), result 2 is chunk 34.
- Same query with `--document 'LUEAG_%'`: 4 results, 8,285 bytes, chunk 33 at result 4.
- The original query `externe Kontrolle Definition externe Überwachung Unternehmensführung` with `--document 'LUEAG_%'`: 4 results, 6,509 bytes, all Welge/Eulerich. The wise2627 miss therefore still reproduces for a caller who repeats the old behaviour (keyword bag, own synonyms, one broad search). It does not reproduce for the guided query or the per-source search.
- `--document GIBTESNICHT`: the new zero-result message. A 12-result search of the same kind printed about 22 KB.
The wrapper check follows after the merge.

## Open and hypotheses (not measured)

- Query language: the rule says queries are always English; the wise2627 corpus is German and every logged query on it is German. One probe (N01, n = 1): the English statement ranks the Grundei chunk at 9, the German one at 4. Hypothesis: queries should be in the language of the corpus. The owner decides; not part of this change.
- `expand_chunks` on every used hit is a rule decision, not a retrieval measurement. Observed usage: 25 expand-only Bash commands against 378 search commands since 2026-09-18 (about 7 percent). The defining sentence of N01 is cut across chunks 33 and 34 (chunk boundary inside the sentence).
- The N04 statute case suggests that per-source search at k=3 can miss where k=4 would hit; with the new default of 4 this is untested.
- The ceiling in the recall needs means this sample cannot show a benefit of sibling queries, only the absence of a large one. A harder recall sample (answers buried behind competing near-duplicates) would be needed.

## Mistakes and traps for a successor

- `data/` is ignored in `.gitignore`; new data directories need an explicit exception, otherwise `git add -A` silently skips them (a commit that "adds data" can be empty of it).
- A shallow `dict(value)` copy of the pool state shared the nested chunk dict with the previous state, so stage 2 of the pool build saw no new ids and wrote no judge sheets. `copy.deepcopy` fixes it.
- `chunks.json` (chunk text of the pool) and `candidates.json` (transcript snippets) are local, not versioned: the first holds copyrighted textbook excerpts and, in the N05 pool, a chunk of the owner's personal document collection with a credential in it; the second holds chat text. Everything the analysis needs (needs, runs, pool keys, judgments) is versioned. The text can be re-fetched by the pool keys (collection, document, chunk index) while the index is unchanged.
- The shell hook rejects `rag-cli search` output redirected to a file and rejects a python script call without a redirect. Run python scripts with `> /tmp/name 2>&1` and read the file.
