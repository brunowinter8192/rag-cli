# dev/search_strategy/

## Role
Measurement of result count, search strategy and query shape on real logged information needs, replacing the retired eval suite, plus the hermetic tests of the result-count change. Touch this when re-deciding the default result count or re-verifying query guidance; not for the production search workflow (`src/rag/search_cmd.py`).

## Public Interface
No `__init__.py` — scripts run directly with the project venv: `./venv/bin/python dev/search_strategy/<script>.py`. Letter-prefixed scripts form the measurement pipeline in order A, B, C, C2, D; E is independent.

## Flow
`A_select_candidates.py` joins the production search log to Claude Code transcripts and writes seeded candidate lists. The needs and all arm queries are written by hand into `data/needs.json` and frozen by a commit. `B_run_arms.py` runs every arm query to depth 30 through the production retrieval functions without writing to the production search log. `C_build_pool.py` pools the retrieved chunks per need and renders blind judge sheets. Judgments go to `data/judgments/`. `D_analyze.py` computes metrics and the pre-registered decisions and writes `md/D_analyze_report.md`.

## Modules

### strategy_common.py (23 LOC)

**Purpose:** Shared paths, the per-arm depth table and the chunk key format of the measurement pipeline.
**Reads:** `data/needs.json` (via `load_json`).
**Writes:** nothing.
**Called by:** `B_run_arms.py`, `C_build_pool.py`, `C2_rejudge_sheet.py`, `D_analyze.py`.
**Calls out:** (none — stdlib only).

---

### A_select_candidates.py (181 LOC)

**Purpose:** Join logged searches to transcript calls with their preceding user and assistant text and write seeded per-stratum candidate lists.
**Reads:** production `search.jsonl` (read-only); `~/.claude/projects/*/*.jsonl` transcripts.
**Writes:** `data/candidates.json`.
**Called by:** run directly, no importers.
**Calls out:** (none — stdlib only).

---

### B_run_arms.py (112 LOC)

**Purpose:** Run every arm query of every need to depth 30 against the live servers and store ranked hits and chunk text, resumable.
**Reads:** `data/needs.json`, `data/r_queries.json` (stage `r`); PostgreSQL, embedding and reranker servers via `src/rag/search_cmd.py` and `src/rag/reranker.py`.
**Writes:** `data/runs.json`, `data/chunks.json`; nothing to the production search log, because `log_search` is never called.
**Called by:** run directly, no importers.
**Calls out:** `src/rag/search_cmd.py`, `src/rag/reranker.py`.

---

### C_build_pool.py (115 LOC)

**Purpose:** Pool the chunks of all arms per need (stage 1 and the later rewrite stage), trim to a cap by best normalised rank, shuffle with a seed and render blind judge sheets.
**Reads:** `data/needs.json`, `data/runs.json`, `data/chunks.json`, `data/pool.json` (for later stages).
**Writes:** `data/pool.json`; judge sheets under `/tmp/ragstrat/judge/`.
**Called by:** run directly, no importers.
**Calls out:** (none — stdlib only).

---

### C2_rejudge_sheet.py (50 LOC)

**Purpose:** Draw a seeded 8 percent sample of the judged chunks and render a re-judge sheet for a self-consistency check.
**Reads:** `data/needs.json`, `data/pool.json`, `data/chunks.json`.
**Writes:** `/tmp/ragstrat/judge_rejudge.md`.
**Called by:** run directly, no importers.
**Calls out:** `strategy_common.py` (intra-dev).

---

### metrics.py (164 LOC)

**Purpose:** Pure functions: judgment parsing, list metrics (hit, relevant, aspect coverage, precision), arm list construction, comparisons, known-item rank, kappa.
**Reads:** in-memory runs and judgments.
**Writes:** nothing.
**Called by:** `D_analyze.py`, `decisions.py`, `test_analysis.py`.
**Calls out:** (none — stdlib only).

---

### decisions.py (62 LOC)

**Purpose:** The decision rules fixed before the run: default count, strategy adoption, claim verdicts, sibling agreement, score cutoff.
**Reads:** in-memory metric dictionaries.
**Writes:** nothing.
**Called by:** `D_analyze.py`, `test_analysis.py`.
**Calls out:** `metrics.py` (intra-dev).

---

### D_analyze.py (268 LOC)

**Purpose:** Orchestrate the analysis of runs, pool and judgments and write the markdown report.
**Reads:** `data/needs.json`, `data/runs.json`, `data/pool.json`, `data/judgments/*.txt` (`rejudge.txt` for the self-agreement figure).
**Writes:** `md/D_analyze_report.md`.
**Called by:** run directly, no importers.
**Calls out:** `metrics.py`, `decisions.py`, `report.py`, `strategy_common.py` (intra-dev).

---

### report.py (123 LOC)

**Purpose:** Render the analysis results as markdown tables and claim lines.
**Reads:** in-memory results.
**Writes:** nothing.
**Called by:** `D_analyze.py`.
**Calls out:** (none — stdlib only).

---

### E_output_size.py (89 LOC)

**Purpose:** Bootstrap how often a Bash call with a chain of searches of a given result count exceeds the persisted-output limit, from the printed sizes in the production log.
**Reads:** production `search.jsonl` and `search_content.jsonl` (read-only); `src/rag/formatting.py`.
**Writes:** `md/E_output_size_report.md`.
**Called by:** run directly, no importers.
**Calls out:** `src/rag/formatting.py`.

---

### test_analysis.py (149 LOC)

**Purpose:** Verify the metric functions and decision rules on small synthetic inputs.
**Reads:** `metrics.py`, `decisions.py`.
**Writes:** stdout only (PASS/FAIL per strand); exits non-zero on any failed strand.
**Called by:** run directly, no importers.
**Calls out:** `dev/strand_runner.py`.

---

### test_search_count.py (84 LOC)

**Purpose:** Verify the default result count reaches the reranker and the caller, that chained searches stay below the persisted-output limit and that the zero-result message carries the query-shape guidance.
**Reads:** `src/rag/search_cmd.py`, `src/rag/formatting.py` (real modules, loaded from a per-strand tmp copy of `src/`).
**Writes:** stdout only (PASS/FAIL per strand); exits non-zero on any failed strand.
**Called by:** run directly, no importers.
**Calls out:** `dev/strand_runner.py`.

---

## State
`data/` holds the frozen inputs (needs, rewrite queries), the run results, the pool keys and the judgments; all are versioned, written once per stage and read by later stages. `data/chunks.json` (chunk text) and `data/candidates.json` (transcript snippets) are local only and ignored by git. The production logs are only read.
