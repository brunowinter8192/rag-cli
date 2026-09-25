# dev/eval_suite/

## Role
Retired. This directory holds a four-pass LLM pipeline that synthesized evaluation queries from the paper corpus (segment, theme, summarize, author-query) and is no longer an active tool — do not extend it or run new lots against it; the artifacts are kept for reference only.

## Public Interface
No `__init__.py` — scripts run directly: `./venv/bin/python3 dev/eval_suite/scripts/<script>.py <args>`.

## Flow
Pass A segments a source document under `data/documents/trading-reference/` into blocks; Pass B groups blocks into themes.
Pass C writes a neutral summary per theme (spans only, no Pass B wording); Pass D authors queries from the Pass C summaries alone.
Each pass's artifact is checked by its matching `validate_pass_*.py` against the artifact one pass upstream plus, for Pass A/B, the source markdown.
`queries/prompts/` holds the pass prompts plus `injection.md`, the recipe for assembling a worker's spawn prompt from a prompt file and its injected inputs.
`queries/pass_{a,b,c,d}_runs/` hold the accepted artifacts; each has a `batch01_archive/` with the discarded first run, which did not reach every document in Pass D.

## Modules

None at this level. The scripts live in `scripts/`, documented in `scripts/DOCS.md`.

## State
None owned. All scripts in `scripts/` are stateless CLI tools reading fixed artifact paths given as arguments and printing to stdout; nothing here is imported by production code (`src/`) or by any other `dev/` subdirectory.
