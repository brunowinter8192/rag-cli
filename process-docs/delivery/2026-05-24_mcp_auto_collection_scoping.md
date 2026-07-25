# MCP Auto-Collection Routing — Scoping (2026-05-24)

## Pain

`rag-cli search_hybrid <query> <collection>` requires the collection name as an explicit argument. In every CC session, Opus must remember which of the eight production collections is right for the current project — typical pattern: `<project-name>-docs` (internal project docs) plus `<project-name>_reference` (external sources). Forgetting or guessing wrong = search against the wrong collection, hits from unrelated material, or nothing at all.

Second problem: on a project switch within a session, the default isn't carried along automatically — same operator error again.

## Idea

A CC session runs in a working directory. Derive from cwd which project we're in, derive the default collection from that (repo-root detection → basename → collection-prefix mapping). `rag-cli search_hybrid <query>` without a `<collection>` argument then runs automatically against `<project>-docs`. Overridable via an explicit `--collection` flag for any other use case.

Optionally two-tiered: first default collection `<project>-docs`, then automatically also `<project>_reference` as a fallback if the first run has 0 hits. Or an explicit `--reference` flag to switch.

## Mechanics (rough)

- Project identification: walk up from cwd to `.git/` or `.rag-docs.json` (already exists in the repo as an indicator), basename of the found root = project slug
- Mapping project slug → collection name: convention-based (`<slug>-docs` and `<slug>_reference`) plus override via `.rag-docs.json` content when needed
- CLI layer in the `rag-cli` wrapper: inject the collection argument before calling the Python CLI when not set
- Edge cases: no `.git/` found, no matching project in the mapping, multiple collections match — fall back to an explicit requirement with error text "could not auto-detect collection from cwd <path>, specify --collection"

## What's missing to implement

- Mapping table. Currently: Monitor_CC → Monitor_CC-docs / Monitor_CC_reference, RAG → RAG-docs / RAG_reference, searxng → searxng-docs / searxng_reference. Trading → Trading / Trading_internal (outlier — breaks the convention). Decision needed: rename Trading to the convention, or make the mapping table explicit
- Behavior when cwd is in a subdir that has NO project root (e.g. `/tmp/` or `~/Downloads/`): no default, explicit collection name required
- Interaction with the `collections` metadata table: the metadata table could hold the mapping (additional `project_slug` and/or `is_default_for` column)
- MCP-server layer: if `rag-cli` runs over MCP, cwd comes from the MCP-server context, not from the shell — needs its own resolution path

## Open Questions

- Hard-coded convention or configurable mapping? Proposal: convention as default, `.rag-docs.json` as an override mechanism for special cases (Trading)
- `<project>_reference` automatic or opt-in? More hits = more noise, can be desirable when doc search often hopes for an external answer, can be disruptive when searching only project-own material explicitly
- If a project has MULTIPLE docs collections (e.g. Monitor_CC with internal code docs + worker logs indexed separately), how does the default mechanism choose? Proposal: alphabetically first, or the first with a "_docs" suffix, or explicitly configured in `.rag-docs.json`

## Sources

- Convention observation: `<Project>-docs` and `<Project>_reference` are established (see `rag-cli list_collections` output, 2026-05-24)

## Status

Scoping only. No code, no worker dispatched. Next step: decide the mapping source (convention vs config), then dispatch implementation work.
