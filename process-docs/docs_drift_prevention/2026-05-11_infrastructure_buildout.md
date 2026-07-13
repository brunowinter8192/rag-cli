# Docs Drift Prevention — Infrastructure Buildout (2026-05-11)

## Context

Session intent at start: execute the deferred RAG-dqr eval baseline + sweeps. First investigation against existing docs revealed multiple stale references and unclear documentation conventions. Decision: pause eval work, fix the doc base + build prevention infrastructure first, since adding new eval evidence onto a drifted base would compound the problem.

What turned into an 11-topic doc-hygiene session:

1. Audit ran against documentation.md spec → 25 findings (10 Critical, 12 Important, 3 Optional) surfaced
2. CLAUDE.md eliminated as a convention (auto-injected + indexed = duplicate context; manually-maintained tree = drift hazard)
3. Sources allocation rule verified (per-decision-step is sufficient, no rationale-column needed)
4. No-Bead-References-in-Docs rule introduced (beads point to docs, not vice versa; backwards-pointers stale at bead-close)
5. Symbol-First Convention introduced (function/constant name as durable anchor; path as navigation only; drift-script verifies both)
6. SOLL → IST direction rule introduced (functional code changes must follow SOLL emergence; no IST update without preceding SOLL; SOLL emerges or changes only with dev/ verification)
7. Persistence Routing table tightened (decisions/ only for SOLL/IST functional changes; pure refactors go to DOCS.md only; OldThemes is the default for session prose)
8. Drift-check script built (`scripts/docs_drift_check.py`, 309 LOC + whitelist); later universalized to `~/.local/bin/docs-drift-check` so any project benefits
9. Refactor skill cross-referenced (Companion Check section added — explicit pointer to docs-drift-check + rule chain)
10. server_manager.py split refactor (1061 LOC → 68 + 4 modules under 400 each; pure refactor, DOCS.md updated, no decisions/ touch per new rule)
11. db.py argument-mutation fix (helper-module code-standards fix; non-mutating return-tuple pattern; no decisions/ touch)

## Rules Codified This Session

| Rule | Location | One-line |
|---|---|---|
| No CLAUDE.md in AI-internal chain | `~/.claude/shared-rules/global/documentation.md` § top | Projects do NOT carry CLAUDE.md; DOCS.md (root) is the entry-point; project-specific auto-context routes through `proj_<name>/` (or now `situational/` for on-demand). |
| Path & Symbol References | `~/.claude/shared-rules/global/documentation.md` § decisions/ | Symbol-first when possible; path as navigation. Legitimate path-anchor cases listed (dev/ scripts, report-MDs, cross-refs, DOCS.md module listings, data files). |
| Cross-project marker | `~/.claude/shared-rules/global/documentation.md` § decisions/ | Paths to other projects' files take `(<ProjectName>)` suffix. Drift script skips. |
| No Bead References in Docs | `~/.claude/shared-rules/global/documentation.md` § top-level | decisions/, OldThemes/, DOCS.md, sources/ never reference beads. Beads → docs is the only direction. |
| Eval results propagate to decisions/ | `~/.claude/shared-rules/global/documentation.md` § Rules | Numbers from dev/ runs land in decisions/ Evidenz with script-path + report-MD path + dataset reference. |
| SOLL emergence/change requires dev/ verification | `~/.claude/shared-rules/global/documentation.md` § Rules | Both initial emergence and later changes need concrete dev/ measurements. Opinion alone is forbidden. |
| IST update timing | `~/.claude/shared-rules/global/documentation.md` § decisions/ | Functional code change → IST update in same commit cycle. Pure refactors → DOCS.md only. |
| SOLL → IST direction | `~/.claude/shared-rules/global/documentation.md` § decisions/ | Workflow: discuss → SOLL with evidence → migrate IST. No functional IST update without preceding SOLL. |
| Persistence Routing | `~/.claude/shared-rules/opus/workers-3.md` § Step 1.4 | Five-row table mapping content type → destination → mandatory criterion. Replaces vague "architecture decision" framing. |
| Drift Check Recap-time | `~/.claude/shared-rules/opus/workers-3.md` § 1.3.3 | Run `docs-drift-check` first; manual checks after for what scripts can't reliably verify. |
| Indexed paths: RAG REPLACES Read | `~/.claude/shared-rules/opus/workers-1.md` § Indexed paths | 4-step escalation chain: search → reformulate → read_document → only then direct-read. Self-check before any cat/Read on indexed paths. |

## Tooling Built

**`~/.local/bin/docs-drift-check`** — universal binary, scans cwd against the documentation rules:
- Path-Drift: file/dir paths in indexed docs that don't exist on disk
- LOC-Drift: DOCS.md module headings claiming LOCs that diverge ≥5 from actual `wc -l`
- Symbol-Drift: `[A-Z_]{4,}` constants and `[a-z_]+\(\)` function references in docs that don't grep in source code

Whitelist resolution: `<cwd>/scripts/docs_drift_whitelist.txt` → `<cwd>/.drift-whitelist.txt` → empty. Exit 0 = clean, 1 = drift. Markdown report to stdout.

Excludes: `.claude/worktrees/`, `__pycache__`, logs/, `decisions/OldThemes/` (process documentation, by definition contains historical references that don't need to resolve).

## Battle-Test Result

First run against post-audit dev state: **38 raw findings**. Worker categorized:
- 2 REAL drift (`box_architecture.md` ref to Monitor_CC's `dev/watchdog_scope/proposal_phaseA_v2.md`; `index03_sparse_embedding.md` ref to non-existent `dev/indexing/splade_truncation/`)
- 36 SCRIPT FPs across 6 distinct heuristic-too-broad causes (function anchors not stripped, template-paths-with-`<>`, HTTP endpoints, OldThemes historical paths, runtime `.jsonl`, SQL/HTTP-method symbols)

After FP fixes (cross-project marker support, OldThemes skip, template skip, endpoint skip, runtime extension skip, function-anchor strip, prefix-wildcard symbol skip) + whitelist additions: 0 findings.

Subsequent test catch: stale `agent-rag-search` Skill reference in `decisions/delivery01_mcp_tools.md` (Skill was intentionally removed in past session, IST never updated → drift). Caught by Path-Drift check. Fixed in same cycle. plugins.md catalog also updated to reflect rag plugin has no Skills/Agents/Commands/MCP anymore — only the `rag-cli` wrapper.

Conclusion: script works as intended. Catches both gross drift (missing files) and convention drift (stale IST). False-positive rate manageable with whitelist + heuristic tuning. Universalized for cross-project use.

## Source-Inventory Updates for Related Beads

- `RAG-dqr` (eval-suite execution): Source-Inventory should now include `decisions/OldThemes/docs_drift_prevention/2026-05-11_infrastructure_buildout.md` (this file) — context for why the eval base is clean. Eval execution itself remains deferred to next session.
- `RAG-bdt` (stale watchdog registrations): no change from this session.

## Open Items

- RAG-dqr eval-suite execution (deferred again — the actual eval baseline + sweeps for test_db)
- RAG-bdt stale watchdog registrations (low priority cleanup)
- 4 process improvements staged for next-session apply (cwd-drift after worker-cli merge, worker-claim-vs-merge-result verification, pre-spawn branch sync at spawn time not only at reuse, RAG-first self-check phrasing strengthening)

## Quellen

- Internal: `~/.claude/shared-rules/global/documentation.md` (current rules), `~/.claude/shared-rules/opus/workers-1.md` and `workers-3.md` (Recap mechanism), `~/.claude/shared-rules/global/tool-use.md` (RAG-first reads escalation)
- Process artifact: this session's full git log on `dev` (commits 8660970 through current head — bead-ref cleanup, drift script wip + tuning + universalization, server_manager split, db.py mutation fix, IST refresh on delivery01)
