# Pass B → Pass C Spans-Only Filter Script (2026-07-25)

Wrote `eval/scripts/filter_spans_only.py`, the anti-leakage boundary step between Pass B
(theme formation) and Pass C (summary authoring): reads a Pass B output JSON and writes
`{document, themes: [{id, spans}]}`, dropping need sentences, labels,
`distributed_justification`, `soft_members`, and `resplits` — the fields Pass C's summary
prompt (R11-R15) explicitly says must be withheld so a summary cannot inherit segmentation
wording. Stdlib only (`json`, `sys`). CLI: `python3 eval/scripts/filter_spans_only.py
<pass_b_json> <output_json>`.

## Design: whitelist assertion, not selective copy

The output is built by an explicit whitelist assertion (`validate_output_whitelist`) run
against the constructed output right before it is written, rather than trusted to follow
from `build_spans_only` only ever picking two keys. Rationale: this script's entire purpose
is an anti-leakage boundary — over-copying is the failure mode that matters, so the
correctness argument should not depend solely on the copy logic staying minimal as the
script evolves; a structural assertion catches drift even if a future edit widens
`build_spans_only`.

## Gap found in review: whitelist stopped at theme level

First version whitelisted top-level (`document`/`themes`) and theme-level (`id`/`spans`)
keys but never inspected the span dicts themselves, since `build_spans_only` passes each
theme's `spans` list through by reference. A Pass B span carrying an extra key (e.g. a
reviewer annotation) would have flowed into the Pass C input unchecked. Fixed by adding
`ALLOWED_OUTPUT_SPAN_KEYS = {"line_start", "line_end"}` and a per-span check inside the same
`validate_output_whitelist` function, run before `write_json`. Kept the same fail-loud
pattern as the doc/theme checks (`sys.exit` with the offending theme id, span index, and
sorted extra-key list) rather than silently stripping the extra key — the point of a
whitelist boundary is to surface a schema drift upstream, not paper over it.

## Verification performed

Ran the script against the real `eval/queries/pass_b_runs/Bollerslev1986GARCH.pass_b.json`
(8 themes) and diffed the theme-id sequence against the already-committed
`eval/queries/pass_c_runs/Bollerslev1986GARCH.pass_c.json` from this session's Pass C run —
matched exactly (`t01`..`t08`), confirming the filtered shape is what Pass C actually
consumed, not just schema-plausible. Exercised all four failure paths (missing input file,
malformed JSON, missing top-level key, theme missing `id`/`spans`) and the span-level gap
fix (injected an `"annotation"` key into a real span) — each exits nonzero with a specific
message and, for the whitelist-violation case, confirmed the output file is never created.
Not verified: no live Pass C worker run consuming this exact filtered file (would require
re-invoking the Pass C role, out of scope for this script's own task).
