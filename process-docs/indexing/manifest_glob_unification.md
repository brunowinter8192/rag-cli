# Manifest Glob Unification across CLI repos

## Problem

Each `.rag-docs.json` across the six repos had its own hand-grown include-glob set, encoding the *current directory layout* rather than the *rule* "index every DOCS.md anywhere + the whole decisions/ tree". Result: silent coverage gaps when a DOCS.md lived outside the enumerated dirs, and full divergence between repos.

Target rule (user): **`**/DOCS.md` (every DOCS.md, any depth) + `decisions/**/*.md` (complete decisions tree)** — identical for every repo, no per-repo specialization.

## Coverage audit (empirical, pathlib.glob mirroring `expand_globs`)

| Repo | Old globs covered | Gap vs. rule |
|---|---|---|
| rag-cli | 49 files | none — old set already complete |
| reddit-cli | 27 files | none |
| gh-cli | 33 files | misses `dev/repo_exploration/DOCS.md` (no dev glob in manifest) |
| searxng-cli | 101 files | misses `src/news/engine/DOCS.md`, `src/news/platforms/coindesk/DOCS.md` (deepest src glob was `src/*/DOCS.md`, one level) |
| iterative-dev | — | **no `.rag-docs.json` at all** — repo entirely un-indexed (6 DOCS.md + 9 decisions never in RAG) |
| trading | 64 files | misses all 4 `dev/**/DOCS.md`; manifest covered concepts/strategies/markets/ops as whole content trees |

So the rule was only *accidentally* satisfied where it held — encoded layout, not rule.

## Worktree pollution finding (blocker for `**/DOCS.md`)

`expand_globs()` ran raw `pathlib.Path.glob()` with `.md`-suffix + dedup only — **no directory exclusion**. The narrow old globs (`src/*/DOCS.md`) never reached `.claude/worktrees/`, so this was latent. Switching to `**/DOCS.md` surfaces it: it matches DOCS.md copies inside live-worker worktrees.

Measured copies pulled in by `**/DOCS.md`: gh-cli **2**, searxng-cli **36** (exact repo copies from worker branches — stale/divergent duplicates). Blind manifest swap would have imported all of them.

→ Fix had to land in `sync.py` BEFORE any manifest swap + re-index.

## Decisions

- **Schema = `**/DOCS.md` + `decisions/**/*.md` for ALL six repos.** No per-repo variants.
- **trading is NOT an exception.** `concepts/` (and strategies/markets/ops, README) are **user-facing** → belong to the external-facing doc chain, NOT the AI-internal `<project>-docs` collection. They are dropped from the manifest. Files stay in the repo; they just leave the RAG collection on the next sync. This is the correct external-vs-AI-internal split, not a loss.
- **README stays out** of the unified manifests (external-facing). Was only ever in trading's manifest.
- **`expand_globs` gets component-based exclusion** — `GLOB_EXCLUDE_DIRS = {.git, venv, node_modules, __pycache__}` + a consecutive-component check for `.claude` + `worktrees`. Component-based (not substring) so `myvenv-notes/DOCS.md` survives but `venv/lib/DOCS.md` is dropped; `.claude/worktrees/` is targeted precisely without sealing all of `.claude/`.
- **GPU re-index is deferred per-project** — runs whenever a repo is next worked on. Only rag-cli re-indexed this session (its `src/rag/DOCS.md` changed).

## Execution (this session)

- `src/rag/sync.py` — `GLOB_EXCLUDE_DIRS` + `_is_excluded_path()` + call inside `expand_globs`; committed on rag-cli (worker `sync-exclude`), merged to dev. Verified: against rag-cli with a live `sync-exclude` worktree present, `expand_globs(["**/DOCS.md","decisions/**/*.md"])` → 8 real DOCS.md, 41 decisions, **0 worktree paths**.
- All six `.rag-docs.json` set to the two-glob schema. rag-cli + iterative-dev (newly created, collection `iterative-dev-docs`) within their repos; gh-cli / reddit-cli / trading cross-project (uncommitted — picked up when each repo is next worked on). searxng-cli was moved to the identical schema independently by a parallel session (commit `3bf5665`, already merged to main) — convergent confirmation of the chosen convention.
- rag-cli re-index: `update_docs` → updated 1 (`src/rag/DOCS.md`, 16 chunks), removed 0, unchanged 48. Confirms exclusion live end-to-end (zero worktree copies added).

## Live status

The `rag-cli` wrapper (`~/.local/bin/rag-cli`) execs the repo checkout directly — so the fix is live as soon as the checkout carries it. Must travel with the dev→main sync at session end, else a `main` checkout falls back to the un-fixed `expand_globs`.
