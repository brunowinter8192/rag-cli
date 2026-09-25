# dev/chunker/

## Role
Audit scripts for evaluating chunker output quality. Currently focused on verbatim-quote coverage — whether eval ground-truth identifying_quotes exist as verbatim substrings in indexed chunks. Touch this when auditing chunk-boundary quality against eval ground truth; not for the chunker implementation itself (`src/rag/chunker.py`, `dev/indexing/p1_chunker.py`).

## Public Interface
No `__init__.py` — run directly: `./venv/bin/python dev/chunker/A_quote_coverage.py`.

## Flow
Reads a query-set JSON with `identifying_quote` ground truth.
Reads the indexed chunks of a fixed collection from Postgres.
Checks each quote for a single-chunk verbatim match, a boundary-split match across two adjacent chunks, or absence.
Writes a Markdown coverage report to `md/`.

## Modules

### A_quote_coverage.py (237 LOC)

**Purpose:** For each `identifying_quote` in a query-set JSON, check whether it appears verbatim (single-chunk), spans a chunk boundary (boundary-split), or is absent from the index.
**Reads:** `dev/retrieval/queries_test_db.json`; PostgreSQL `documents` table (`rag_test` DB, `test_db` collection) via `dev/indexing/p4_db.py`.
**Writes:** `dev/chunker/md/A_quote_coverage_<timestamp>.md`.
**Called by:** run directly, no importers.
**Calls out:** `dev/indexing/p4_db.py` (intra-dev).

---

## State
None owned — reads existing Postgres state and queries JSON, writes only report files under `md/`.
