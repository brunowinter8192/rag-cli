# dev/eval_suite/scripts/

## Role
Retired validators and helpers of the four-pass query-synthesis pipeline; kept for reference only. Do not extend or run new lots against them. Pipeline context lives in `dev/eval_suite/DOCS.md`.

## Public Interface
No `__init__.py` — scripts run directly: `./venv/bin/python3 dev/eval_suite/scripts/<script>.py <args>`.

## Flow
Each script takes artifact paths as CLI args → checks or transforms one pass artifact against its upstream artifact → prints an OK/FAIL line or a report to stdout.

## Modules


### validate_pass_a.py (141 LOC)

**Purpose:** Check a Pass A segmentation artifact's schema, line-range coverage of the source document, and block/trash granularity.
**Reads:** a `pass_a.json` artifact path and the matching source `.md` path (CLI args).
**Writes:** stdout only (OK/FAIL line).
**Called by:** run directly, no importers.
**Calls out:** (none — stdlib only).

---

### validate_pass_b.py (263 LOC)

**Purpose:** Check a Pass B theme artifact's schema, span coverage against Pass A blocks, resplit/unassigned bookkeeping, and that no theme is a standalone proof.
**Reads:** a `pass_b.json` artifact path, the matching `pass_a.json`, and the source `.md` path (CLI args).
**Writes:** stdout only (OK/FAIL line).
**Called by:** run directly, no importers.
**Calls out:** (none — stdlib only).

---

### filter_spans_only.py (79 LOC)

**Purpose:** Strip a Pass B artifact down to `{document, themes: [{id, spans}]}` so Pass C workers never see Pass B need sentences or labels.
**Reads:** a `pass_b.json` artifact path (CLI arg).
**Writes:** the stripped JSON to the given output path (CLI arg).
**Called by:** run directly, no importers.
**Calls out:** (none — stdlib only).

---

### validate_pass_c.py (191 LOC)

**Purpose:** Check a Pass C summary artifact's schema, word budget, sub-concept count, and absence of structure references or lookup phrasing.
**Reads:** a `pass_c.json` artifact path and the matching `pass_b.json` (CLI args).
**Writes:** stdout only (OK/FAIL line).
**Called by:** run directly, no importers.
**Calls out:** (none — stdlib only).

---

### validate_pass_d.py (150 LOC)

**Purpose:** Check a Pass D query artifact's schema, format coverage per theme, and token-overlap ceiling against the Pass C information_need (the anti-leakage gate).
**Reads:** a `pass_d.json` artifact path and the matching `pass_c.json` (CLI args).
**Writes:** stdout only (OK/FAIL line).
**Called by:** run directly, no importers.
**Calls out:** (none — stdlib only).

---

### audit_leakage.py (89 LOC)

**Purpose:** Report shared n-grams between a Pass C summary and its source theme spans, as a manual leakage-inspection aid alongside `validate_pass_d.py`'s automated overlap check.
**Reads:** a `pass_c.json` artifact path, the source `.md` path, and the matching `pass_b.json` (CLI args).
**Writes:** stdout only (per-theme n-gram report).
**Called by:** run directly, no importers.
**Calls out:** (none — stdlib only).

---

## State
None owned. All scripts are stateless CLI tools.
