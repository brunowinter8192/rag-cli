# Delivery (rag-cli direct)

## Status Quo (IST)

- `cli.py` is the single CLI entry point. `workflow.py` retired.
- Agent-facing subcommands consumed via `rag-cli` wrapper (`~/.local/bin/rag-cli` in PATH)
- Pipeline subcommands invoked directly via `./venv/bin/python cli.py`
- PostgreSQL required for all operations; GPU servers auto-started on demand by `server_manager.py`
- `list_collections`, `list_documents`, `read_document`, `progress`, `status` work without GPU servers; `search_hybrid` and `index` require GPU servers

**Agent-facing — 7 subcommands (consumed via `rag-cli` wrapper):**

| Subcommand | Description |
|---|---|
| `search_hybrid` | Dense retrieval + cross-encoder reranking; `top_k=12` fixed; always-rerank, no toggle |
| `list_collections` | All indexed collections with chunk counts; optional `--filter` |
| `list_documents` | Documents in a collection; optional `--document` / `--filter` |
| `read_document` | Anchor chunk plus N before and M after; `--before`/`--after` 0–10 |
| `delete` | Delete chunks + `indexed_files` manifest + on-disk source; `--collection` required, `--document` optional |
| `index` | Chunk + index `.md` files from `data/documents/<collection>/`; `--collection` required, `--document` optional; skip-by-default via `indexed_files` hash; `--force` re-embeds all |
| `update_docs` | Sync project docs per `.rag-docs.json` manifest; hash-based change detection |

**Wrapper-only / not agent-facing — 3 subcommands:**

| Subcommand | Description |
|---|---|
| `server` | GPU server lifecycle — status/start/stop/restart/list/tail/errors |
| `progress` | Indexing progress per document — done/total chunks; pollable during `index` run |
| `status` | Lock state, GPU server health, Postgres reachability; always lock-free |

## Evidenz

No benchmarks run. Tool interface designed for Claude Code consumption via Skill.

## Recommendation (SOLL)

Pending — needs evaluation.

## Offene Fragen

- Are the current tool signatures optimal for Claude Code usage patterns?
- Should `delete` and `index` be exposed agent-facing (currently yes) or restricted to human-only?

## Quellen

None yet.
