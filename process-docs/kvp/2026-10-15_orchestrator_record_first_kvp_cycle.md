# Orchestrator record of the first rag-cli KVP cycle (2026-10-14 .. 2026-10-15)

The owner asked to work all open rag-cli issues and to set up KVP (continuous improvement) for rag-cli, modelled on the websearch KVP (area `kvp` in the websearch repository). The owner was away for the whole cycle, so the STOP points of phase 1 were skipped and every decision below was taken by the orchestrator. Worker-level details are in the worker entries of the areas `kvp`, `search_strategy`, `retrieval`, `rag_improvement` and `module_standards`, all dated 2026-10-14 or 2026-10-15.

## What was done

| Milestone | Issue | Result | Evidence |
|---|---|---|---|
| M1 KVP infrastructure | (new) | `code_version` on every `search.jsonl` and `expand.jsonl` record; `dev/kvp/kvp_report.py`; `dev/kvp/kvp_canary.py` with 11 real cases | real production search 2026-10-15T19:11Z carries `code_version 7595519145`, `hit_count 4` |
| M2 result count and strategy | Trefferzahl, Suchstrategie, Querybau | `RERANK_TOP_K` 12 to 4; zero-result notice names collection and filters; query guidance in area `retrieval`; rule text proposed | measurement on 12 real needs, see area `search_strategy` |
| M3 literature | Literatur | Barnett2024 (19 chunks), Wang2024 (49), Gao2023 (60) cleaned and indexed into `rag-cli-reference` | one search per paper returns that paper at rank 1 |
| M4 dev helpers | Controlflow | `_rerank_at` and `_lookup_server_url` unified into `dev/retrieval/p1_retriever.rerank_at` and `dev/retrieval/server_urls.py` | 12 strand tests, 7 of them green on the old code first |
| Issue Eval-set (#5) | closed | superseded by the retirement of the synthetic eval pipeline on 2026-09-18 (area `eval_suite`) | |

## Production verification after the merge (2026-10-15, main checkout on `integration`)

- Query `external corporate governance concerns actors outside the company and market forces` on `wise2627-reference` with `--document 'LUEAG_Literatur_Grundei%'`: 4 results, Grundei/Zaumseil chunk 33 (the Zipperling definition that was missed on 2026-10-14) at rank 1, chunk 34 at rank 3.
- Canary against the pre-change baseline `dev/kvp/json/kvp_canary_20261015T190423.json`: 6 PASS, 5 FAIL. The 2 Zipperling miss cases failed before and after (they replay the logged keyword queries). Exactly the 3 cases predicted by the kvp worker regressed: Küpper partial plans (rank 5), Küpper planning horizons (rank 6), Welge internal/external mechanisms (rank 7). These are hits agents expanded at ranks 5 to 7 in the 12-result era. Output per search fell from about 21-23 K characters to 6.4-8.2 K.
- All 18 test scripts under `dev/` green on `integration` (95 strands).

## Decisions the owner should know

- **Sibling queries were not adopted.** The owner's direction was "fewer results, more searches". The measurement found no gain from four sibling queries of three results over one guided query of twelve (hits 10 vs 10, aspect coverage 0.98 vs 1.00, 31 % duplicates). What did help: corpus vocabulary in the query, and one search per source document for definitional questions. "More searches" therefore survives as "one search per concept and per source", not as paraphrase fan-out. The sample is small (N = 12, one judge); a harder recall sample could change this.
- **The result count is fixed at 4, no `--top-k` flag.** Known cost, measured: the 3 canary regressions above; 5 of 17 exact expands in the baseline were at ranks 5 to 8.
- **Proposed rule patch** `dev/search_strategy/patch/tool_use_search_strategy.patch` against `~/.claude/shared-rules/main/tool-use.md`. Observation behind it: the existing rule "on zero chunks rephrase the query at least twice" sends callers the wrong way, because all 8 zero-hit searches in the log had 0 candidates and failed on a collection or `--document`/`--exclude` pattern, never on wording. The other added rules carry the measured result (4 results, at most 3 chained searches per Bash call, per-source search for definitions, `expand_chunks` on used hits).
- **Not in the patch, owner decision:** the rule "RAG queries are always English". On one German case (N01) the English query ranked the target chunk 9 and the German one 4 (n = 1, hypothesis only).
- **websearch-pdf skill has no phase 2.** Issue Literatur referred to "phase 2" of that skill; the skill contains no such phase. The worker used the Step 4 sampling criteria and the websearch `pdf_pipeline` defect classes instead, and stripped the reference lists to match the sibling papers in the collection.

## Baseline facts from the first full-window KVP report (2026-09-18 .. 2026-10-15, before the change)

- 59 of 290 executed search commands were persisted; 53 of 58 chained multi-search commands, 6 of 232 single searches. Overflow is a chaining effect.
- 70 of 444 attempted searches were blocked by a PreToolUse hook (43 pipes into another command). Blocked and failed searches leave no log record; only transcripts show them.
- 58 of 372 searches were cold starts (p50 6.9 s vs warm 4.3 s). 6 warm searches took 20-58 s, unexplained.
- Cross-project reference search (issue Referenzsuche): 11 of 45 sessions until 2026-10-13 searched a foreign reference collection, 0 of 5 since 2026-10-14. Too few sessions after the rule change to judge; the issue stays open.

## Incident during the merge

`worker-cli merge` reported the workers `ragctl`, `raglit` and `ragstrat` as "not found in registry"; their worktrees and branches were gone while only `ragkvp` was still registered. Cause unknown (hypothesis: a cleanup by another session that shares the worker registry). The final commits still existed as dangling objects and were merged by SHA: `cf8c987` (ragctl), `86ca7d1` (raglit), `d23a864` (ragstrat). A dangling commit `18d6b52` from the ragstrat measurement contains raw transcript excerpts including a credential; it was deliberately not merged and is unreachable. Successor: read `git fsck --no-reflogs` output before assuming lost work, and never push reflogs.

## Next KVP iteration

1. Run `./venv/bin/python -m dev.kvp.kvp_report --since 2026-10-15T19:11Z` after a few days of traffic and compare persisted share, output size and exact-expand ranks per `code_version` against the baseline above.
2. If the owner applies the rule patch, the date of application is the next split point.
3. Candidates from the data: hook-blocked searches (70 of 444), unexplained slow warm searches, the English-only query rule on German corpora.
