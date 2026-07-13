# Project Visualization Layer (Abstract System Topology)

## Background

Working with a complex AI system through a CLI interface requires maintaining a mental model of how components relate. The current tooling (code, decisions/, DOCS.md) is text-linear — no representation of the abstract topology: which modules call which, how decision files map to code paths, how data collections relate to queries, how skills connect to workflows.

## Goal

> "ich denke das man nur effektiv mit ai arbeiten kann wenn man sieht was man tut. ich kann in eine blackbox reden und einigermaßen versuchen den überblick zu bewahren aber was ich nicht zeitlich kann ist alles nachzulesen und ein mental model aufzubauen was sich in meinem kopf zu einem graph entwickelt"

A visual layer that shows the **abstract system topology** — not just code imports but the relationships between modules, decisions/ files, data collections, queries, and skills/commands. The layer must operate at the level of abstractions the user thinks in, not at the level of code files.

## Constraint

**Zero additional maintenance cost.** The graph must be derived automatically from existing artifacts:
- `decisions/` — link structure inferred from cross-references
- `DOCS.md` Called-by / Calls-out fields
- `.claude-plugin/plugin.json` — skills and commands
- `queries_*.json` — expected_documents → data collection links
- `src/` imports — via AST parse or dep-tree

If a source artifact is not auto-parseable it is excluded. No hand-maintained node lists.

## Candidate Tools

### dep-tree (gabotechs/dep-tree)

- CLI, MIT, ~1.7k stars (2026-04-27), Python supported
- 3D Force-Directed Graph rendered in browser; nodes cluster by coupling strength
- Examples: PyTorch, FastAPI, NumPy, scikit-learn
- **Coverage:** ~80% of code-layer complexity (file-level import graph)
- **Gap:** decisions/ ↔ code paths, DOCS.md Called-by edges, skills/commands → code, queries_*.json expected_documents → indexed docs, data collection → DB state

### Custom HTML (vasturiano/3d-force-graph)

- The WebGL lib dep-tree uses internally, MIT
- Build a single self-contained HTML file with typed nodes: Code-Module, Decision-Doc, Data-Collection, Query — color-coded
- Auto-extraction Python script: parse Markdown links + JSON fields + AST imports → JSON graph payload
- Use when dep-tree coverage alone is insufficient for cross-layer navigation

### Obsidian / Foam / Generic Knowledge-Graph Tools

- Considered as alternative to browser-rendered 3D graph
- Not pursued — require manual backlink maintenance or separate install, conflicting with zero-maintenance constraint

## Open Questions

- Does dep-tree's code-layer view alone provide enough orientation value, or is the decisions/ ↔ code cross-layer essential for the user's mental model?
- If Custom-Layer needed: minimum viable node type set? Code-Module + Decision-Doc + Query + Data-Collection covers the four main axes.
- Edge-weight encoding: coupling strength (import count) vs structural dependency (called-by) vs data flow (query → collection) — can all three coexist without overwhelming the 3D layout?

## Status at Close (2026-05-11)

Concept, tool-choice, and Custom-Layer Plan B fully documented. Implementation not started.

**dep-tree probe attempt:** `brew install dep-tree` failed — SSL certificate error (`curl` could not verify the ghcr.io Bottle). Fallback paths (`npm install -g @gabotechs/dep-tree`, direct GitHub release binary) were not pursued. Deferred in favor of eval preparation.

## Reopen Path

1. **dep-tree install:** retry via direct GitHub release binary (`gh release download gabotechs/dep-tree`) or `npm install -g @gabotechs/dep-tree` — no brew required
2. **Probe:** run `dep-tree graph cli.py` and `dep-tree graph workflow.py` — check whether the 3D view gives orientation or just noise at this codebase size
3. **Decision gate:** dep-tree alone sufficient → done; gap too large → step 4
4. **Custom-Layer:**
   - Sketch node-types, edge-types, cluster/aggregate model
   - Write auto-extraction Python script (Markdown link parse + JSON field extraction + AST import walk)
   - Render via `vasturiano/3d-force-graph` as self-contained HTML
