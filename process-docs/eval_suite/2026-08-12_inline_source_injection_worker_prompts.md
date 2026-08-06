# Inline Source Injection into Worker Prompts (2026-08-12)

Decision from the batch01 post-review walkthrough: for all future eval-pipeline lots
(batch02 onward), pipeline inputs are injected INLINE into the worker spawn prompt instead
of handed over as filesystem paths. User decision; encoded into all four pass prompts under
`eval/queries/prompts/` as an "Input delivery (orchestrator contract)" section.

## Problem

The reusable pass prompts said only "You receive ONE markdown document" — the handover
mechanism lived in per-lot prompts and process-docs entries, not in the reusable artifact.
The actual batch01 mechanism was an absolute-path read into the main checkout (worktrees
lack the gitignored `data/`). A path handover leaves reading depth to worker discipline:
the discarded first batch01 died exactly there — the Pass A worker switched to a
heading-grep shortcut under throughput pressure, i.e. stopped reading properly. R3b bans
the shortcut by RULE; inline injection removes the possibility by MECHANISM.

## Decision

- Source documents: injected via `cat -n` (1-indexed line numbers, authoritative for
  `line_start`/`line_end` spans). Fits the budget: a 150 KB source lot is roughly 40k
  tokens as prompt content.
- Pass B: document (`cat -n`) + Pass A block JSON, both inline.
- Pass C: document (`cat -n`) + spans-only JSON, with the anti-leakage strip (need
  sentences, labels removed) applied by the orchestrator BEFORE injection — the filter
  becomes part of the injected content, not worker discipline.
- Pass D: Pass C summaries JSON inline; the worker gets no paths into the pipeline at
  all, so the summaries-only input filter holds structurally (document/spans/needs are
  absent from reachable context, not merely off-limits).
- Side effect: the absolute-path workaround for the gitignored `data/` dir is obsolete —
  workers no longer touch the filesystem for pipeline inputs.

## Scope

Prompt-mechanics change only: no pass rules, validators, or artifacts changed. First
applies at the next dispatched lot (batch02 or the next worker-run pipeline work).
