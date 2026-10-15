# KVP report

- Generated: 2026-10-15T19:08:04Z
- Window: since beginning until now
- Log dir: `/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/rag-cli/src/rag/logs`
- Transcripts: `/Users/brunowinter2000/.claude/projects/*/*.jsonl`
- Records in window: searches: 372, expands: 28, transcript search calls: 444
- Every verdict is derived offline by `dev/kvp/`; the production logs hold facts only.
- `code_version` is stamped on search and expand records written after the stamp change; older records appear as `unversioned`.
- The time of day of the 2026-10-14 caller-rule change is unknown. Before/after comparisons of caller behaviour (cross-project reference reach) are possible at date granularity only, through `--since`/`--until`.
- Transcript-based figures count only searches that joined a transcript call; the joined share is given under technical indicators.

## Technical

### Provenance, empty and partial lists, cold starts (per code version)

Provenance complete = fingerprint present and its registry entry names embedding preset and model plus reranker preset and model. Partial = 1 to (full list - 1) hits, where full list is the longest list in the group. Cold = a server start was initiated during the search.

| code_version | searches | provenance complete | zero hits | partial lists | cold starts |
|---|---|---|---|---|---|
| all | 372 | 360/372 (96.8 %) | 8 (8 with 0 candidates) | 10 (full list = 12) | 58/372 (15.6 %) |
| unversioned | 372 | 360/372 (96.8 %) | 8 (8 with 0 candidates) | 10 (full list = 12) | 58/372 (15.6 %) |

### Latency in ms (per code version)

| code_version | cold n | cold p50 | warm n | warm p50 | warm p90 | warm max |
|---|---|---|---|---|---|---|
| all | 58 | 6920 | 314 | 4292 | 5244 | 58461 |
| unversioned | 58 | 6920 | 314 | 4292 | 5244 | 58461 |

### Slowest warm searches

| ts | code_version | duration ms | collection |
|---|---|---|---|
| 2026-10-12T20:30:59 | unversioned | 58461 | general-docs |
| 2026-10-11T17:07:28 | unversioned | 39686 | rag-cli-reference |
| 2026-10-12T14:16:10 | unversioned | 27163 | wise2627-reference |
| 2026-10-11T12:40:37 | unversioned | 21537 | websearch-docs |
| 2026-10-11T12:40:15 | unversioned | 21306 | monitor-cc-docs |

### Output size per search in characters (per code version)

Rendered from the content sidecar with the production formatter. 30000 characters is the smallest size at which Claude Code persisted a rag-cli output in the observed transcripts.

| code_version | p50 | p90 | max | > 30000 |
|---|---|---|---|---|
| all | 21832 | 23275 | 24852 | 0/372 (0.0 %) |
| unversioned | 21832 | 23275 | 24852 | 0/372 (0.0 %) |

### Agent calls (transcripts)

| attempted searches | executed, joined to a log row | blocked by a hook | executed, no log row | log rows without a transcript call |
|---|---|---|---|---|
| 444 | 365 | 70 | 9 | 7 |

Hook blocks by hook:

| hook | count |
|---|---|
| block_cli_chained.py: Chaining CLIs with ; or && is fine; piping a CLI's output into another command is not. | 43 |
| block_rag_docs_layer.py: rag-cli search on a *-docs collection must carry a --document or --exclude filter whose va | 18 |
| block_cli_chained.py: Chaining CLIs with ; or && is fine; redirecting rag-cli search to a file is not, its outpu | 7 |
| block_venv_no_redirect.py: add redirect: `./venv/bin/python script.py > /tmp/name.md 2>&1` | 1 |
| block_cli_chained.py: Chaining CLIs with ; or && is fine; reading a CLI's redirected file back with head/tail/ca | 1 |

Executed without a log row (failed searches write no record):

| ts | collection | first output line |
|---|---|---|
| 2026-09-23T10:25:52 | canvas-reference | Indexed Collections: |
| 2026-09-24T10:27:16 | github_releases | Command did not complete within its 120s timeout and was moved to the background (ID: bmr3rfypo). Output is being writte |
| 2026-09-24T15:34:08 | monitor-cc-docs | Exit code 1 |
| 2026-09-25T16:09:15 | monitor-cc-docs | <persisted-output> |
| 2026-09-28T09:49:39 | general-docs | Exit code 1 |
| 2026-09-28T09:49:39 | general-docs | Exit code 1 |
| 2026-10-12T14:28:02 | canvas-docs | Exit code 1 |
| 2026-10-14T21:51:12 | rag-cli-reference | Exit code 2 |
| 2026-10-14T21:51:12 | rag-cli-reference | Exit code 2 |

### Log failures in errors.jsonl

| code | count |
|---|---|
| log_write_failed | 0 |
| log_config_resolve_failed | 0 |

## Relevance (click data and descriptive facts, no relevance verdicts)

### Search to expand_chunks

An expand is attributed to the latest search in the same collection within 60 minutes before it. `exact` = the expanded (document, chunk) is a hit of that search; `document` = same document, other chunk. Expands in window: 28, without any attributed search: 4 (counted in the all row only).

| code_version | searches | with exact expand | with document expand | exact expands | document expands | rank of exact expand (rank:count) |
|---|---|---|---|---|---|---|
| all | 372 | 17/372 (4.6 %) | 5/372 (1.3 %) | 17 | 7 | 1:9, 2:2, 3:1, 5:2, 6:1, 7:1, 8:1 |
| unversioned | 372 | 17/372 (4.6 %) | 5/372 (1.3 %) | 17 | 7 | 1:9, 2:2, 3:1, 5:2, 6:1, 7:1, 8:1 |

### Document dominance (lists with at least 2 hits)

| code_version | lists | median distinct documents | lists from one document only |
|---|---|---|---|
| all | 364 | 6.0 | 53/364 (14.6 %) |
| unversioned | 364 | 6.0 | 53/364 (14.6 %) |

### Reranker score profile (median score at rank)

| code_version | rank 1 | rank 3 | rank 6 | rank 12 |
|---|---|---|---|---|
| all | 0.9973 (n=364) | 0.975 (n=363) | 0.8948 (n=361) | 0.29 (n=354) |
| unversioned | 0.9973 (n=364) | 0.975 (n=363) | 0.8948 (n=361) | 0.29 (n=354) |

## Usefulness (proxies from transcripts)

### Context overflow

Search commands joined to a log row whose output Claude Code persisted instead of showing, and how many of those were read back by a later Bash or Read of the saved path (extra tool calls).

| code_version | joined commands | persisted | persisted, one search in the command | persisted, several searches in the command | persisted outputs read back |
|---|---|---|---|---|---|
| all | 290 | 59/290 (20.3 %) | 6/232 (2.6 %) | 53/58 (91.4 %) | 53 |
| unversioned | 290 | 59/290 (20.3 %) | 6/232 (2.6 %) | 53/58 (91.4 %) | 53 |

### Cross-project reference reach

Session project comes from the transcript working directory, own/foreign from the collection prefix (`<project>-reference`). A reference collection whose project has no working directory of its own (goethe-bwl) always counts as foreign. Facts only; the target is judged by the orchestrator.

| code_version | sessions | with a reference search | with a foreign reference search | with an own reference search | distinct foreign reference collections per session (n:sessions) | reference searches | sessions with unknown project |
|---|---|---|---|---|---|---|---|
| all | 49 | 21/49 (42.9 %) | 11/49 (22.4 %) | 12/49 (24.5 %) | 0:38, 1:10, 3+:1 | 87 | 0 |
| unversioned | 49 | 21/49 (42.9 %) | 11/49 (22.4 %) | 12/49 (24.5 %) | 0:38, 1:10, 3+:1 | 87 | 0 |

Per reference collection (all versions):

| collection | own searches | foreign searches | unknown-project searches | own sessions | foreign sessions |
|---|---|---|---|---|---|
| general-reference | 1 | 2 | 0 | 1 | 1 |
| goethe-bwl-reference | 0 | 16 | 0 | 0 | 7 |
| mineru-reference | 0 | 1 | 0 | 0 | 1 |
| monitor-cc-reference | 5 | 2 | 0 | 2 | 2 |
| rag-cli-reference | 7 | 1 | 0 | 4 | 1 |
| trading-reference | 2 | 2 | 0 | 1 | 1 |
| websearch-reference | 1 | 0 | 0 | 1 | 0 |
| wise2627-reference | 47 | 0 | 0 | 3 | 0 |

### Searches with zero hits

Next gap = seconds until the next search of the same session; `none` = no later search in that session; `-` = not joined to a transcript.

| ts | code_version | collection | document filter | candidates | query | next search in session |
|---|---|---|---|---|---|---|
| 2026-09-24T17:49:12 | unversioned | monitor-cc-reference | %tahoe% | 0 | CGEventPost replaced on Tahoe synthesized keyboard shortcut  | 3638 s |
| 2026-09-25T16:10:01 | unversioned | mineru-docs | process-docs/% | 0 | watchdog abort memory teardown threshold convert | 4 s |
| 2026-09-26T10:49:08 | unversioned | reddit-cli-posts | %Sandqvist% | 0 | Sandqvist durability experience | 5 s |
| 2026-09-26T21:58:04 | unversioned | general-docs | process-docs/% | 0 | tapo smart plug schedule raspberry pi | 6 s |
| 2026-09-28T10:00:23 | unversioned | general-docs | - | 0 | plug switching on off schedule deadman timer controller | 23 s |
| 2026-09-28T10:55:34 | unversioned | general-docs | process-docs/% | 0 | Data Science in Accounting DSIA learning objectives exam | 11 s |
| 2026-10-10T17:16:25 | unversioned | mineru-docs | process-docs/% | 0 | MinerU conversion crash memory reliability speed | 4 s |
| 2026-10-11T12:39:53 | unversioned | monitor-cc-docs | process-docs/pdf_conversion_qa/% | 0 | liteparse extract assemble stats batch Haiku worker conversi | 21 s |

## Not covered

- Whether the agent closed its information gap is not measured; no judge is used.
- Relevance of hits is not judged. Reranker scores saturate (a 0.99 score on an unrelated chunk was observed), so they are shown as a profile only.
- A fuzzy reformulation rate is not computed; it would need a similarity threshold that the observed pairs do not support.
- Searches that failed before logging leave no log row; they appear only under agent calls.
- Session project is a heuristic from the working directory.
