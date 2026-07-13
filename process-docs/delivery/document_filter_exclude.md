# Document-Filter Exclude (`--exclude`) — Design Discussion

**Date:** 2026-06-19
**Status:** Implemented 2026-06-20 — flag table in the delivery decision record.

## Problem

`search_hybrid` and `list_documents` take `--document PATTERN`, a single POSITIVE SQL LIKE filter
(`%term%`, `cli.py:42-43` / `:55-56`). `list_documents` additionally has `--filter` (case-insensitive
substring, `cli.py:58`) — also positive. There is NO way to EXCLUDE documents from results.

Structural pain: the documentation hierarchy nests process-memory UNDER current-state. `decisions/<step>.md`
is the crystallized current state; `decisions/OldThemes/**` is superseded process memory; OldThemes lives *inside*
`decisions/`. A positive LIKE cannot express "decisions but not OldThemes" — `%decisions%` matches both,
and there is no substring the top-level files share and the OldThemes files lack.

Consequence: a status-quo query ("current state of X") run unfiltered surfaces OldThemes chunks and their
superseded numbers as if current — a real error that already happened (a stale "shrinkage negligible" value
read as current state in a trading session). Workaround = positive-scope to the one relevant decision file; covers the
topic-specific case but NOT the whole-pipeline overview (no single query covers "all decisions, no OldThemes"
→ must read N files).

## Use case (recurring, cross-project)

The `decisions/` vs `OldThemes/` split is structural in EVERY project using this documentation hierarchy.
"Give me current state, not iteration history" is a first-class, recurring query the tool cannot serve.

## Options

### A — generic `--exclude PATTERN` (RECOMMENDED)

Mirror of `--document`: same SQL LIKE, negated (`NOT LIKE`). Composable:
`--document "%decisions%" --exclude "%OldThemes%"`. General beyond OldThemes (drop a noisy doc, blacklist a
file). Low surprise — symmetric to an existing flag. Cheap: add the arg in `cli.py`, thread an `exclude`
param through the search/list query path into the DB WHERE clause as `AND document NOT LIKE %s`.

### B — semantic tier (heavier, NOT recommended now)

Treat OldThemes as a process-memory TIER — metadata tag (`tier: decision | process`) at index time, or a
separate logical sub-collection. "Exclude process memory" becomes a semantic concept, project-wide,
potentially default-on for `-docs` status queries. Cleaner intent capture but costs index-schema work + a
cross-project convention change. Worth it ONLY if OldThemes-exclusion proves the dominant use case.

## Recommendation

Build A, skip B. A is cheap, symmetric, immediately useful, solves the concrete pain; B is a
schema/convention investment justified only if the need proves dominant.

## ROI (honest)

The positive-scope workaround already covers the common topic-specific status query. `--exclude` mainly wins
the whole-pipeline-overview case (one query vs N file reads) and makes status-quo queries less error-prone in
general. Real ergonomic win, not transformative.

## Code touch-points

- `cli.py:42-43` (search_hybrid `--document`), `:55-58` (list_documents `--document` + `--filter`) — add `--exclude`.
- Document-filter WHERE clause in the search/list query path (`src/rag/retriever.py` workflows →
  DB search functions) — add the negated `NOT LIKE` condition. Exact line not yet located (cli.py verified;
  query path not read this session).
- Docs to update on land: the delivery decision record (flag table), root `DOCS.md` + `src/rag/DOCS.md`
  (cli.py subcommand description).

## Open questions

- Scope: `search_hybrid` + `list_documents` first; `read_document`/`delete`/`index` later if needed.
- Repeatable `--exclude` (multiple patterns) vs single — repeatable is more flexible; single keeps parity
  with `--document`.
- Case sensitivity — LIKE vs ILIKE. `--document` uses LIKE; `list_documents --filter` is case-insensitive.
  Decide consistency for `--exclude`.
