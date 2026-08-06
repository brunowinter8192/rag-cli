# Injection Recipe — Assembling Worker Prompts for Pass A-D Lots

Orchestrator recipe for building the spawn prompt of every eval-pipeline lot. The spawn prompt is ASSEMBLED MECHANICALLY via bash concatenation — the pass prompt file goes in VERBATIM via `cat`, never read-and-retyped by the orchestrator. Retyping is a drift source: every paraphrase of a rule is a chance to lose a validator-mechanic fix. The orchestrator authors only the lot header; everything else is `cat`.

## Assembly order (every pass)

Build `/tmp/spawn-worker-rag-cli-<lot>.md` in this order:

1. **Lot header** — the only orchestrator-written part: "You are a WORKER.", worktree path, deliverable file paths (`eval/queries/pass_<x>_runs/<doc>.pass_<x>.json`), validator command per deliverable, negative scope ("Do NOT add features/improvements beyond the listed deliverables"), task-specific completion checklist.
2. **Pass prompt, verbatim** — `cat eval/queries/prompts/<pass_prompt>.md`.
3. **Injected inputs** — per pass, see table. Each injected document is wrapped in explicit delimiters naming the file, so the worker can never confuse sources:

```
===== BEGIN SOURCE: <filename.md> (cat -n) =====
<content>
===== END SOURCE: <filename.md> =====
```

## Per-pass input table

| Pass | Prompt file | Injected inputs | Lot budget |
|---|---|---|---|
| A | `segmentation_prompt_pass_a.md` | source docs via `cat -n` | 150 KB source per lot (first-fit-decreasing packing) |
| B | `segmentation_prompt_pass_b.md` | source docs via `cat -n` + Pass A JSON via `cat` | 150 KB source per lot |
| C | `summary_prompt_pass_c.md` | source docs via `cat -n` + spans-only JSON (stripped, see below) | 2 docs per lot |
| D | `query_prompt_pass_d.md` | Pass C summaries JSON via `cat` — NO source docs, NO Pass B artifacts | 3-6 docs per lot |

Budgets per the 2026-08-06 KB-budget decision: the binding constraint is worker care (~400 KB effective load), not context capacity. Sources for A/B lots are packed by KB of source text, never by document count.

## Pass C strip (orchestrator-side, BEFORE injection)

The Pass C worker gets spans ONLY — Pass B need sentences and labels must not enter its context. Strip mechanically, never by hand:

```bash
python3 -c "
import json, sys
d = json.load(open(sys.argv[1]))
out = {'document': d['document'], 'themes': [{'id': t['id'], 'spans': t['spans']} for t in d['themes']]}
json.dump(out, open(sys.argv[2], 'w'), indent=2)
" eval/queries/pass_b_runs/<doc>.pass_b.json /tmp/<doc>.spans_only.json
```

Inject `/tmp/<doc>.spans_only.json`, never the full Pass B artifact.

## Canonical assembly example (Pass A lot)

```bash
{
  cat /tmp/lot_header.md
  cat eval/queries/prompts/segmentation_prompt_pass_a.md
  for doc in Doc1.md Doc2.md Doc3.md; do
    echo "===== BEGIN SOURCE: $doc (cat -n) ====="
    cat -n "data/documents/trading-reference/$doc"
    echo "===== END SOURCE: $doc ====="
  done
} > /tmp/spawn-worker-rag-cli-pass-a-lotNN.md
```

Then `worker-cli spawn pass-a-lotNN /tmp/spawn-worker-rag-cli-pass-a-lotNN.md <repo_path>`.

## Invariants

- The pass prompt file is the single source of truth for pass rules. A rule change happens in the prompt file (committed), NEVER as ad-hoc wording in a lot header.
- Workers receive no filesystem paths to pipeline inputs — everything they consume is inline in the spawn prompt. Rationale: (1) `data/` is gitignored and absent from worktrees; (2) inline injection makes partial reading structurally impossible (the discarded batch01 heading-grep shortcut was a partial-read failure); (3) for Pass C/D it closes the leakage channel of a worker opening upstream pipeline files — the anti-leakage filter is applied to the injected content, not left to worker discipline.
- `cat -n` line numbers are authoritative for all `line_start`/`line_end` spans.
- Size check before spawn: `wc -c` the assembled prompt; a Pass A/B lot prompt lands around 150-200 KB — an order-of-magnitude deviation means a packing error.
