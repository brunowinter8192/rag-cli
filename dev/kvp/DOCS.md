# dev/kvp/

## Role
Continuous-improvement instruments for rag-cli: an offline report turns the production logs and Claude Code transcripts into indicators per code version, and a canary re-runs fixed real queries with known expected hits. Touch it to change an indicator or a canary case; never write verdicts into the production logs.

## Public Interface
No `__init__.py`. Run from the repo root as `./venv/bin/python -m dev.kvp.kvp_report [--since ISO] [--until ISO]`; optional `--log-dir`, `--transcripts-glob`. Canary: `./venv/bin/python -m dev.kvp.kvp_canary [--baseline json/<file>.json]`. Tests: `./venv/bin/python dev/kvp/test_<name>.py`.

## Flow
Report: search, expand, sidecar, registry and error logs plus the transcripts are filtered to the window -> transcript calls are joined to log rows, expands to searches -> indicators per code version -> markdown in `md/`. Canary: each case runs the real `search_workflow` with the three search-log paths redirected to a temp directory -> expected hit checked in the isolated record -> markdown in `md/`, JSON in `json/`.

## Modules

### kvp_report.py (124 LOC)

**Purpose:** Entry point of the report: parses the window, loads the sources, runs the analysis, renders and writes the report.
**Reads:** rag-cli `search.jsonl`, `search_content.jsonl`, `expand.jsonl`, `config_registry.jsonl`, `errors.jsonl` of the main checkout; Claude Code transcripts.
**Writes:** `md/kvp_report_<since>_<until>_<timestamp>.md`; the path on stdout.
**Called by:** invoked directly with `-m`; dev/kvp/test_kvp_report.py.
**Calls out:** none.

---

### kvp_config.py (41 LOC)

**Purpose:** Paths, log file names and constants shared by two or more modules of this directory.
**Reads:** none.
**Writes:** none.
**Called by:** every other module here except the tests.
**Calls out:** none.

---

### kvp_load.py (48 LOC)

**Purpose:** Timestamp parsing, window filtering and reading of the JSONL logs, content sidecar grouping and registry indexing.
**Reads:** the JSONL files it is handed.
**Writes:** none.
**Called by:** kvp_report.py, kvp_canary.py, kvp_join.py, kvp_classify.py, kvp_indicators.py, kvp_transcripts.py and the tests.
**Calls out:** none.

---

### kvp_transcripts.py (165 LOC)

**Purpose:** Extracts `rag-cli search` calls with their results and the read-backs of persisted outputs from Claude Code transcripts.
**Reads:** transcript JSONL files matched by the glob.
**Writes:** none.
**Called by:** kvp_report.py, dev/kvp/test_kvp_transcripts.py and the other tests.
**Calls out:** none.

---

### kvp_join.py (86 LOC)

**Purpose:** Joins transcript calls to search log rows by query, collection, filters and time, and attributes expands to the searches whose hits they used.
**Reads:** none.
**Writes:** none.
**Called by:** kvp_report.py, kvp_indicators.py and the tests.
**Calls out:** none.

---

### kvp_classify.py (114 LOC)

**Purpose:** Pure rules: command result state, session project from the working directory, own or foreign reference collection, cold start, provenance completeness, rendered output size.
**Reads:** none.
**Writes:** none.
**Called by:** kvp_indicators.py, kvp_report.py, kvp_canary_logic.py and the tests.
**Calls out:** src/rag/formatting.py.

---

### kvp_indicators.py (283 LOC)

**Purpose:** Builds one item per search and computes the technical, relevance and usefulness indicators for all records and per code version.
**Reads:** the loaded, joined and classified records.
**Writes:** none.
**Called by:** kvp_report.py and the tests.
**Calls out:** none.

---

### kvp_render.py (160 LOC)

**Purpose:** Renders the indicator data as markdown tables.
**Reads:** none.
**Writes:** none.
**Called by:** kvp_report.py.
**Calls out:** none.

---

### kvp_canary.py (134 LOC)

**Purpose:** Entry point of the canary: runs the cases through the production search workflow into redirected logs, checks isolation, writes report and JSON.
**Reads:** `canary_cases.json`, an earlier canary JSON via `--baseline`, the production search logs (isolation check only).
**Writes:** `md/kvp_canary_<timestamp>.md`, `json/kvp_canary_<timestamp>.json`; repoints `retrieval_log` file paths for its own process.
**Called by:** invoked directly with `-m`; dev/kvp/test_kvp_canary.py.
**Calls out:** src/rag/search_cmd.py, src/rag/retrieval_log.py, src/rag/code_version.py.

---

### kvp_canary_logic.py (144 LOC)

**Purpose:** Pure canary functions: evaluates a case against an isolated search record, compares two runs, renders the canary report.
**Reads:** none.
**Writes:** none.
**Called by:** kvp_canary.py, dev/kvp/test_kvp_canary.py.
**Calls out:** none.

---

### canary_cases.json

The one hand-maintained data file: fixed real queries with the expected hit or an expected empty result, each with the id of the log record it was copied from.

---

### test_kvp_report.py (79 LOC), test_kvp_transcripts.py (89 LOC), test_kvp_classify.py (119 LOC), test_kvp_indicators.py (120 LOC), test_kvp_canary.py (130 LOC)

**Purpose:** Hermetic strand tests of the report pipeline and the canary logic against fixtures copied from real records.
**Reads:** `fixtures/`.
**Writes:** stdout only (PASS/FAIL per strand); exits non-zero on any failed strand.
**Called by:** run directly, no importers.
**Calls out:** `dev/strand_runner.py`.

---

## State
None. Each run is stateless; files in `md/` and `json/` are written once and never edited. Indicator definitions, observed numbers and caveats: process-docs area kvp.
