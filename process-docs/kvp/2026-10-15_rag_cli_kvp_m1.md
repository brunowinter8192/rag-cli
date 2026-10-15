# rag-cli KVP milestone M1: code version stamp, report, canary (2026-10-15)

Worker record. Branch `ragkvp`. KVP means one closed loop: agents use the tool, the logs record facts, an offline report turns facts into a few indicators, the weakest indicator gets exactly one fix, the same report on the post-fix window shows the effect. The template is the websearch KVP (area `kvp` of that project). This entry holds what M1 built, the definitions behind every indicator, the baseline numbers and the traps.

## What exists

- `src/rag/code_version.py`: 10-character git SHA of the repository that holds the running code, `+dirty` when tracked files differ from HEAD (untracked files ignored), `unknown` on any git failure. Never raises. The repository root comes from the module location, not from `RAG_PROJECT_ROOT`, because that variable can point at the main checkout while worktree code runs.
- `code_version` field in every `search.jsonl` and `expand.jsonl` record. Not in the sidecar lines and not in `config_registry.jsonl`.
- `dev/kvp/`: `kvp_report.py` (entry), `kvp_canary.py` (entry), helper modules, `canary_cases.json`, `fixtures/`, five strand tests. `dev/infra/test_code_version.py` covers the stamp.
- Run: `./venv/bin/python -m dev.kvp.kvp_report [--since ISO] [--until ISO]`, output `dev/kvp/md/kvp_report_<since>_<until>_<ts>.md`. Canary: `./venv/bin/python -m dev.kvp.kvp_canary [--baseline dev/kvp/json/<file>.json]`, output `dev/kvp/md/kvp_canary_<ts>.md` and `dev/kvp/json/kvp_canary_<ts>.json`.
- The report reads the MAIN checkout logs (`/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/rag-cli/src/rag/logs`), not the logs of the worktree it runs from, and all Claude Code transcripts (`~/.claude/projects/*/*.jsonl`).

## Indicators (exact definitions)

Every table has an `all` row plus one row per `code_version`; records without the field are `unversioned`. Transcript-based rows take the version of the log row a call joined to.

### Technical

- Provenance complete: `config_fingerprint` present and its registry entry has non-null embedding preset and model and reranker preset and model. Baseline: 360 of 372. Not complete: 11 records without the field (the first searches of 2026-09-18, before fingerprints existed) and 1 record with fingerprint `e22ba2a5ec1280a6` (reranker null).
- Zero hits, split by `candidates == 0`. All 8 observed zero-hit searches had 0 candidates (a `--document` pattern or a collection matching nothing).
- Partial list: `0 < hit_count < longest list in the group`. Defined relative to the group, never as "less than 12", because worker ragstrat changes the default result count. Baseline: 10 of 372 with the longest list 12.
- Cold search: an embedding or reranker `start_initiated` event in `errors.jsonl` inside [ts - duration_ms - 1 s, ts]. Baseline: 58 of 372 cold, cold p50 6920 ms, warm p50 4292 ms, warm p90 5244 ms, warm max 58461 ms. Six warm searches took 20 s or more and no start event explains them (hypothesis, not checked: concurrent indexing or GPU contention).
- Output size: characters of `format_results` over the content sidecar, i.e. what the CLI prints. Validated against transcripts: 161 of 213 pure single-search outputs are byte-identical after strip; the others differ only because the same Bash call printed more. Baseline: p50 21832, p90 23275, max 24852 characters, so no single search exceeds 30000.
- 30000 characters is the persisted-output threshold of Claude Code. Observed on rag-cli outputs: the smallest persisted stub says 29.3 KB (30000 / 1024), the largest unpersisted output has 29192 characters.
- Agent calls (transcripts): attempted searches, joined to a log row, blocked by a hook before running, executed without a log row. Baseline: 444 attempted, 365 joined, 70 blocked, 9 executed without a log row, 7 log rows without a transcript call. Hook blocks by hook: 43 pipe into another command, 18 missing process-docs filter on a `*-docs` collection, 7 redirect to a file, 2 others. A failed search leaves no log record, so the transcript is the only source for failures.
- `log_write_failed` and `log_config_resolve_failed` counts from `errors.jsonl`. Baseline 0 and 0.

### Relevance (click data and descriptive facts, no verdicts)

- Search to expand: an expand is attributed to the latest search of the same collection within 60 minutes before it. `exact` = the expanded (document, chunk) is a hit of that search, `document` = same document, other chunk. The 60 minutes come from the observed gaps: of 18 exact matches, 17 were within 54 minutes, one after 24 hours. Baseline: 17 searches with an exact expand (4.6 %), 5 with a document-only expand, 4 of 28 expands without any attributed search; ranks of exact expands 1:9, 2:2, 3:1, 5:2, 6:1, 7:1, 8:1.
- Document dominance (lists with at least 2 hits): median distinct documents and the number of lists from one document only. Baseline: median 6, 53 of 364 lists from a single document.
- Score profile: median reranker score at rank 1, 3, 6, 12. Baseline 0.9973, 0.975, 0.8948, 0.29. No threshold is applied: for the two failing Zipperling queries all 24 returned Welge/Eulerich chunks scored 0.92 to 0.99998, so a high score does not mean the right chunk.

### Usefulness (proxies from transcripts)

- Context overflow: share of joined search commands whose result Claude Code persisted, split by one or several searches in the command, plus how many persisted outputs were read back by a later Bash or Read containing the saved path. Baseline: 59 of 290 commands persisted, 6 of 232 single-search commands, 53 of 58 multi-search commands, 53 read back. Overflow is therefore a chaining effect: two 12-result searches in one Bash call exceed 30000 characters. The 6 persisted single-search commands are unexplained (hypothesis: other output in the same Bash call).
- Cross-project reference reach, over sessions with at least one joined search. Session project = the last path component of the transcript `cwd` (after cutting at `.claude`) that equals a collection prefix seen in the log (`<x>-docs` or `<x>-reference`). A search on `<p>-reference` is `own` when `p` equals the session project, else `foreign`. Baseline over the whole window: 49 sessions, 21 with a reference search (42.9 %), 11 with a foreign reference search (22.4 %), 12 with an own one; foreign collections per session 0:38, 1:10, 3 or more:1; 87 of 372 searches go to a `*-reference` collection.
- Caveat for `foreign`: goethe-bwl has no working directory of its own. Its 16 searches come from sessions in `Documents/wise2627` (10) and `Documents/general` (6), so they all count as foreign although the material is used as the study base of those projects. Read the foreign figure with that in mind.
- Date split for the Referenzsuche rule change of 2026-10-14 (time of day unknown, so date granularity only). Until 2026-10-13T23:59:59: 45 sessions, 11 with a foreign reference search (24.4 %), 62 reference searches. Since 2026-10-14: 5 sessions, 0 with a foreign reference search, 3 with an own one, 25 reference searches. n = 5 sessions is too small for any reading; the rule only reaches sessions that start after the change.
- Zero-hit searches: table with the gap to the next search of the same session. In all 8 observed cases the next search followed (4 to 3638 s).

## Decisions and rejected options

- No exact-repeat indicator and no fuzzy reformulation indicator. Exact repeats (same query, collection and filters as the previous search of the session) were 0 in the data. Same-query pairs 4 s apart do exist (about ten observed) but they are the two-pass process search of the workers rule (area filter first, then all other areas), not retries. Token-overlap similarity of consecutive queries separates nothing cleanly.
- No relevance verdict and no usefulness judge. Whether the agent closed its gap is not measured.
- Join of transcript call to log row: same query, collection, `--document`, `--exclude`, and the log timestamp inside [tool_use ts - 2 s, tool_result ts + 2 s] (the window ends at the result timestamp because chained commands start late; method taken from the websearch KVP). Each log row is used once. Baseline: 365 of 372 rows joined.
- Command recognition: the Bash command is tokenised with shlex, unquoted newlines become separators, and `rag-cli search` only counts at command position (start, after an operator, after `do`, `then`, `exec`, `time`). Without the position rule, DOCS text inside a heredoc ("rag-cli search log and the ...") produced calls with collection `and`.
- Canary isolation by in-process redirection of `retrieval_log.SEARCH_LOG_FILE`, `SEARCH_CONTENT_FILE` and `CONFIG_REGISTRY_FILE` into a temp directory `kvp_canary_*` (owner decision, no production code change). The canary reads its evidence from the isolated record and then checks that none of its search ids appear in the worktree's or the main checkout's `search.jsonl`. It does not compare file sizes, because other sessions write the production log at the same time. Server lifecycle events of a cold start still go to `errors.jsonl`; that file holds lifecycle events, not searches.
- Canary pass criterion: an expected (document, chunk) appears anywhere in the returned list, whatever its length. The criterion never assumes 12 results, because ragstrat changes `RERANK_TOP_K` (not touched here). Result count and rank are recorded per case. Compare ranks only between runs with equal list length.
- Canary cases only on reference collections: docs collections are re-indexed and shift chunk indexes. 11 cases, each copied from a real log record whose id is stored in `observed_search_id`: two observed Zipperling misses (query, `--document 'LUEAG_%'`, expected `LUEAG_Literatur_GrundeiZaumseilAufsichtsratCorporateGovernance_2012.md` chunk 33 or 34), the near-verbatim query that found chunk 33 at rank 3 and chunk 34 at rank 7, one zero-candidate case (`--document '%tahoe%'` on monitor-cc-reference), and seven hits the agent expanded afterwards (Küpper chunks 264, 316, 842; Henning script chunk 2; Welge chunks 112 and 474; goethe-bwl `SPO_MScBWL_2024.md` chunk 59).
- Defect cases carry the wanted state as `expect`, so the two Zipperling misses read FAIL until a change makes the Grundei chunk appear.

## Verification (2026-10-15)

- Stamp: a real `search` and a real `expand_chunks` through a wrapper that execs this worktree's `cli.py` wrote `"code_version": "824daa0f67"`. The wrapper sets `RAG_PROJECT_ROOT` to the main checkout because the worktree has no `models/`. The production wrapper `~/.local/bin/rag-cli` runs the main checkout, so records in the main logs carry the stamp only after the merge.
- Canary on the live servers at `824daa0f67`: 11 cases, 9 PASS, 2 FAIL (the two Zipperling misses), 0 errors. Ranks equal the logged ranks exactly (3, 1, 5, 6, 2, 1, 7, 3), and the production-log check passed. File `dev/kvp/json/kvp_canary_20261015T190423.json` is the baseline for the Trefferzahl/Suchstrategie change.
- Report on the real logs, full window: `dev/kvp/md/kvp_report_start_now_*.md`.
- Suite: 15 test scripts, all strands pass (9 existing, `test_code_version.py`, five under `dev/kvp/`).

## For worker ragstrat and the orchestrator

- Before-numbers per `code_version` for the default result count change: context overflow (59 of 290 commands persisted, 53 of 58 multi-search commands), output size p50 21832 characters, document dominance (53 of 364 single-document lists), exact-expand ranks, canary ranks. After the merge the stamp separates old from new records; until then everything reads `unversioned`.
- Rank of exact expands is mostly 1 to 3 (12 of 17), which is the observed basis for a smaller default list. Welge chunk 474 (rank 7) and Küpper chunk 842 (rank 6) are canary cases that fail first if the list shrinks below 7.

## Traps for a successor

- Tests in this repo are strand scripts (`dev/strand_runner.py`), not pytest. A strand copies `src/` into a temp directory and puts it first on `sys.path`, but any module imported at the top of the test file that itself imports `src.rag...` (here `dev.kvp.kvp_classify` imports `src.rag.formatting`) loads the real `src` package first. A later `load_rag("retrieval_log")` then resolves to the real repository and writes into the real `src/rag/logs`. The canary isolation test purges `src*` from `sys.modules` first and asserts that the module path lies in the strand directory. The first version of that test polluted the worktree log.
- Hooks seen on 2026-10-14/15: piping a `rag-cli` output into `head`, redirecting `rag-cli search` into a file and `python script.py` without redirect are blocked. Working recipes: a `/tmp` wrapper script that execs `venv/bin/python cli.py` (the command line then contains no `python`), and `./venv/bin/python -m dev.kvp.kvp_report > /tmp/x.txt 2>&1`.
- A worktree has no `venv`, `models/` or `.env`. A `venv` symlink to the main checkout's venv works; it is excluded through the worktree's `info/exclude` because `.gitignore` has `venv/` (directory) and does not match a symlink. `.env` is found by walking up the directories to the main checkout.
- Servers idle out after 3600 s. A canary run after a pause starts them (cold start, about 6 to 7 s extra on the first case). Set `RAG_PROJECT_ROOT` to the main checkout when running from a worktree.
- The report includes the transcripts of the session that runs it. Commands in the current session that contain `rag-cli search` at command position count as attempts.
- Not decidable from the material: the 7 log rows without a transcript call (6 of them from 2026-09-24 and 2026-09-25 at the first check; the caller is unknown), the 4 expands without an attributed search, the slow warm searches.

## Recap addendum (2026-10-15): default result count 12 to 4

Fact from the orchestrator: worker ragstrat changes `RERANK_TOP_K` from 12 to 4 (a measured decision) and merges together with this branch. The records written by the first merged code therefore carry the new `code_version` and lists of at most 4 hits; everything before reads `unversioned` with lists of 12.

### Canary after the merge, by construction

The canary reproduced the logged ranks exactly on 2026-10-15 (retrieval is deterministic for a fixed index), so the outcome at a list length of 4 follows from the baseline ranks:

| Case | Baseline rank | Expected with 4 results |
|---|---|---|
| zipperling_definition_miss_a, _b | not in the list | FAIL, unchanged |
| zipperling_definition_found_by_near_verbatim_query | chunk 33 at 3, chunk 34 at 7 | PASS (chunk 33 is inside the first 4) |
| expanded_kuepper_planning_purposes | 1 | PASS |
| expanded_henning_governance_definition | 2 | PASS |
| expanded_welge_institutional_control | 1 | PASS |
| expanded_goethe_spo_portfolio_exam | 3 | PASS |
| expanded_kuepper_partial_plans | 5 | FAIL by construction |
| expanded_kuepper_planning_horizons | 6 | FAIL by construction |
| expanded_welge_internal_external_mechanisms | 7 | FAIL by construction |
| zero_candidates_document_pattern_matches_nothing | 0 results | PASS |

Three hit cases fail, not two: besides Welge 474 and Küpper 842, Küpper 316 sits at rank 5. Expected after the merge: 6 PASS, 5 FAIL. With `--baseline dev/kvp/json/kvp_canary_20261015T190423.json` those three show as `regressed`; read that as the known cost of the decision, not as a defect. The cases stay unchanged on purpose. They are the agent-confirmed hits (the agent expanded them at rank 5 to 7 in the 12-result list), so they measure what the smaller list gives up. A canary run that lists any other case as `regressed` or `rank moved` is a real signal.

### What the report should show after the merge (hypotheses, not measured)

- Partial lists are defined against the longest list of the code version, so the new version row reads "full list = 4" and is not flagged for having fewer than 12.
- Output size per search should fall to roughly a third (4 of 12 hits), and chained two-search commands should stay under 30000 characters, so persisted outputs and their read-backs should drop toward 0.
- Exact-expand ranks above 4 (7 of 17 in the baseline: ranks 5, 5, 6, 7, 8 and the document-level class) can no longer occur; the share of searches with an expand shows whether agents expand less or search more.
- Document dominance of the Zipperling kind (all hits from one document) is not changed by the list length; only the caller rules (per-source search) address it.
