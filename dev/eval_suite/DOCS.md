# dev/eval_suite/

## Role
Retired. This directory holds a four-pass LLM pipeline that synthesized evaluation queries from the paper corpus (segment, theme, summarize, author-query) and is no longer an active tool — do not extend it or run new lots against it; the artifacts are kept for reference only.

## Public Interface
No `__init__.py` — scripts run directly: `./venv/bin/python3 dev/eval_suite/scripts/<script>.py <args>`.

## Flow
Pass A segments a source document (`data/documents/trading-reference/*.md`) into blocks → Pass B groups blocks into themes → Pass C writes a neutral summary per theme (spans only, no Pass B wording) → Pass D authors queries from the Pass C summaries alone, never touching the source text. Each pass's artifact is checked by its matching `validate_pass_*.py` against the artifact one pass upstream plus, for Pass A/B, the source markdown.

`queries/prompts/` holds the four pass prompts (`segmentation_prompt_pass_a.md`, `segmentation_prompt_pass_b.md`, `summary_prompt_pass_c.md`, `query_prompt_pass_d.md`) plus `injection.md`, the recipe for mechanically assembling a worker's spawn prompt from a prompt file and its injected inputs. `queries/pass_{a,b,c,d}_runs/` hold the 84 accepted artifacts (21 documents times 4 passes) plus a `batch01_archive/` subdirectory per pass holding the discarded first run — 20 documents for Pass A/B/C, 17 for Pass D, because that first run never reached the remaining 3 documents in Pass D before it was discarded.

## Modules

### scripts/validate_pass_a.py (141 LOC)

**Purpose:** Check a Pass A segmentation artifact's schema, line-range coverage of the source document, and block/trash granularity.
**Reads:** a `pass_a.json` artifact path and the matching source `.md` path (CLI args).
**Writes:** stdout only (OK/FAIL line).
**Called by:** run directly, no importers.
**Calls out:** (none — stdlib only).

---

### scripts/validate_pass_b.py (263 LOC)

**Purpose:** Check a Pass B theme artifact's schema, span coverage against Pass A blocks, resplit/unassigned bookkeeping, and that no theme is a standalone proof.
**Reads:** a `pass_b.json` artifact path, the matching `pass_a.json`, and the source `.md` path (CLI args).
**Writes:** stdout only (OK/FAIL line).
**Called by:** run directly, no importers.
**Calls out:** (none — stdlib only).

---

### scripts/filter_spans_only.py (79 LOC)

**Purpose:** Strip a Pass B artifact down to `{document, themes: [{id, spans}]}` so Pass C workers never see Pass B need sentences or labels.
**Reads:** a `pass_b.json` artifact path (CLI arg).
**Writes:** the stripped JSON to the given output path (CLI arg).
**Called by:** run directly, no importers.
**Calls out:** (none — stdlib only).

---

### scripts/validate_pass_c.py (191 LOC)

**Purpose:** Check a Pass C summary artifact's schema, word budget, sub-concept count, and absence of structure references or lookup phrasing.
**Reads:** a `pass_c.json` artifact path and the matching `pass_b.json` (CLI args).
**Writes:** stdout only (OK/FAIL line).
**Called by:** run directly, no importers.
**Calls out:** (none — stdlib only).

---

### scripts/validate_pass_d.py (150 LOC)

**Purpose:** Check a Pass D query artifact's schema, format coverage per theme, and token-overlap ceiling against the Pass C information_need (the anti-leakage gate).
**Reads:** a `pass_d.json` artifact path and the matching `pass_c.json` (CLI args).
**Writes:** stdout only (OK/FAIL line).
**Called by:** run directly, no importers.
**Calls out:** (none — stdlib only).

---

### scripts/audit_leakage.py (89 LOC)

**Purpose:** Report shared n-grams between a Pass C summary and its source theme spans, as a manual leakage-inspection aid alongside `validate_pass_d.py`'s automated overlap check.
**Reads:** a `pass_c.json` artifact path, the source `.md` path, and the matching `pass_b.json` (CLI args).
**Writes:** stdout only (per-theme n-gram report).
**Called by:** run directly, no importers.
**Calls out:** (none — stdlib only).

---

## State
None owned. All six scripts are stateless CLI tools reading fixed artifact paths given as arguments and printing to stdout; nothing here is imported by production code (`src/`) or by any other `dev/` subdirectory.
