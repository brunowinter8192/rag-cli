# Refactor sweep, orchestrator record and the Phase 4 control-flow scan (2026-09-16)

Orchestrator half of an `iterative-dev-refactor` run over this whole project. Phases 1 to 3 were
executed and merged. Phase 4 was scanned and deliberately NOT acted on — the list at the bottom is
the handover.

The worker's own milestone entry is
`2026-09-16_comment_docstring_and_docs_format_triage.md` in this same folder. This entry holds what
only the orchestrator saw.

## Starting state, measured

49 Python modules, 8550 lines. Two modules over the 400-LOC ceiling and thirteen functions at or
above the 50-LOC ceiling, two of those at or above 100.

- `dev/retrieval/A_retrieval_eval.py` 886 LOC, more than double the ceiling
- `dev/server_management/A_constellation_profile.py` 409 LOC
- `dev/retrieval/A_retrieval_eval.py::_write_cross_sweep_report` 111 LOC
- `dev/chunker/A_quote_coverage.py::_write_report` 102 LOC

Every single hit was in `dev/`. `src/rag/`, 23 modules and 3274 lines, was already fully compliant
on both thresholds.

After Phase 1: 55 modules, 8735 lines, zero modules over 400, largest at 369, zero functions at or
above 50.

## The one case where duplication removal WAS the split

`A_retrieval_eval.py` did not need cosmetic shrinking, it needed the duplication taken out. Two
pieces of it were copy-pasted rather than factored:

- The "loop all queries, call `_run_query`, assemble the per-query result dict" block existed three
  times, in `run_baseline`, `run_sweep` and `run_cross_sweep`. Extracting `_run_config_queries` is
  what got `run_cross_sweep` under 50 LOC, and it shrank the other two for free.
- Inside `_write_cross_sweep_report`, the header, separator and row-loop that renders one
  param1-by-param2 matrix table was written out six times. One parameterised `_cross_table_block`
  replaced all six call sites.

Both were approved on that basis: removing code that is duplicated today is a concern split, while
moving lines around to get under a number is not. The condition attached was that `run_baseline` and
`run_sweep` be proven byte-identical too, not just the function that was over the threshold.

The file went from 886 LOC to 186, split into `eval_constellation.py`, `eval_runner.py`,
`eval_metrics.py`, `eval_report.py` and `eval_cross_report.py`.

## A direction I got wrong, and the correction

I instructed that within one area a constant used by two modules is defined once and imported, and
named `A_constellation_profile.py` as the place `TIMESTAMP_DIR` should live, with the new
`constellation_measure.py` importing it from there.

That would have been a real circular import. `A_constellation_profile.py` already imports several
symbols from `constellation_measure.py`, so the back-import cycles — and because a script run
directly registers as `__main__` rather than under its filename, the back-import re-executes the
file as a second module object and fails on the partially initialised module. The correct direction
is the opposite: the leaf module that depends on nothing else in the area holds the definition, and
both consumers import from it. `B_real_smell.py`'s own separate copy was folded into that import
too, so the area now has exactly one definition.

The three copies of `TIMESTAMP_DIR` that live in three *different* dev areas were left alone. Across
areas a separate copy is correct; inside one area it is not.

## Phase 2, the comment purge, in numbers

519 hits across 53 files: 505 comments and 14 docstrings. 208 were deleted as already covered by the
owning `DOCS.md` or by an existing process-docs entry, and 311 carried substance that existed
nowhere else and were relocated verbatim before deletion.

That 60 percent relocation rate is the highest of the four projects in this sweep by a long way — in
gh-cli the same triage relocated 9 of 652. Read that as a statement about this project: a very large
share of what was known about `src/rag/`'s server lifecycle, lock handling and watchdog behaviour
lived only in comments, and nowhere else.

Eight `DOCS.md` were rewritten to the Role / Public Interface / Flow / Modules / State format, with
all 46 module headings cross-checked against the real `wc -l`.

## Phase 3

Every `DOCS.md` was already under the 400-line split threshold, the largest at 258 lines, so no
directory needed splitting into unit subfolders. `docs-drift-check` reported zero findings in all
three categories, before and after.

## What the sweep deliberately did NOT do

Two functions exist in two byte-identical copies each, across two different dev areas:

- `_rerank_at(query, results, top_k, url)` in `dev/retrieval/eval_runner.py` and
  `dev/server_management/B_real_smell.py`, identical except that one inlines the timeout literal
  `300.0` where the other names a constant of the same value.
- `_lookup_server_url(server_name, path="/v1/rerank")` in the same two files, identical
  implementation: glob `~/.rag-locks/server-port-*.json`, match on name, build the URL.

They were flagged rather than merged. Crossing two dev areas makes this a control-flow decision.

Everything else that shares a name across scripts — `_write_report`, `_check_servers`,
`_patch_retriever_urls` — was checked and differs in real content. Do not treat those as duplicates.

## Phase 4 candidate list, scanned and not classified

An AST pass over every `except` handler, classified by what the handler does. Thirty handlers
produce output, eight have a body of only `pass`, nine of only `continue` or `break`, twenty only
log, and twenty-five re-raise or exit and are tripwires that stay.

The seventeen `pass` and `continue` handlers are the ones to look at first, because a handler whose
entire body is `pass` cannot be anything but a swallow. They cluster tightly and almost all of them
are the same shape — reading a JSON state file from `~/.rag-locks/` and silently skipping it when
the read or the parse fails.

- `src/rag/watchdog.py` carries five of them, at lines 25, 52, 79, 89 and 103
- `src/rag/server_lifecycle.py` at 190, 216 and 227
- `src/rag/server_cli.py` at 171 and 254
- `src/rag/server_manager.py` at 96
- `src/rag/server_utils.py` at 141 and 178
- `src/rag/server_lock.py` at 43, whose `__exit__` swallows `except Exception` entirely
- `src/rag/error_log.py` at 54
- `dev/error_log/analyze_errors.py` at 63 and `dev/retrieval/eval_constellation.py` at 114

The question those raise as a group is one question, not sixteen: when a server state file is
corrupt or unreadable, should the watchdog and the lifecycle code skip it silently, or should that
be loud? Right now a corrupt state file is indistinguishable from no state file at all.

Two more worth naming separately, both in `src/rag/db.py`: `_postgres_reachable` returns `False` on
`psycopg2.OperationalError` and `_docker_daemon_up` returns `False` on `FileNotFoundError` or
`TimeoutExpired`. Both are probe functions whose entire job is to answer a yes-or-no question about
the environment, so returning `False` is arguably the answer rather than a fallback. They are in the
list so the review can say so explicitly.

## Method notes for a successor

Main scanned, workers fixed. Every number above came from an AST walk run at orchestration level.

For the comment purge, the check that actually proves nothing moved is AST equality: parse before
and after, strip docstrings from both trees, compare the dumps. All 53 files in this project passed
that check independently at orchestration level. A behaviour test cannot give you that guarantee,
because it only covers the inputs it happens to exercise.

This project cannot be exercised live in a worker sandbox — no venv, no GPU, no Postgres. The
working method was a harness that monkeypatches `_check_servers`, `_ensure_constellation_for_mode`,
`_load_queries`, `_verify_drift` and `_run_query`, captures every `Path.write_text` call, and diffs
the captured report content with the wall-clock timestamp normalised away. It produced a
byte-identical 11259-character comparison across all six generated reports. Reuse it rather than
rebuilding it.
