# CLI command rename: read_document → expand_chunks (2026-09-17)

## Why

`rag-cli read_document <collection> <doc.md> <chunk> --before N --after M` never read a
document — it returned one anchor chunk plus N chunks before and M chunks after, merged with
overlap deduplication. The name repeatedly caused callers (LLM agents reading the rules) to
reach for a filesystem read of the whole markdown file instead of using the command. See the
`infra` area's `connection_hang_cascade.md` for a documented case: a direct filesystem read
triggered by this exact confusion caused a 1+ minute hang.

Fixed name from the user: `expand_chunks`. Clean break, no backward-compatible alias.

## Scope of the rename

Grepping the whole repo for `read_document` outside `process-docs/` turned up exactly four
files, confirmed before and after the change:

- `cli.py`
- `src/rag/retriever.py`
- `src/rag/DOCS.md`
- `dev/rag-chunking/DOCS.md`

No test files, no other DOCS.md, no other module referenced the old name. This was a pure,
narrow rename — no surprises turned up while reading the four files.

## Symbol map (old → new)

| Old | New | File |
|---|---|---|
| `read_document_workflow` | `expand_chunks_workflow` | `src/rag/retriever.py` |
| subcommand string `"read_document"` | `"expand_chunks"` | `cli.py` (`_add_retrieval_parsers`, `_READ_ONLY_CMDS`, `_COMMAND_HANDLERS`) |
| `_cmd_read_document` | `_cmd_expand_chunks` | `cli.py` |
| `_format_read_document` | `_format_expand_chunks` | `cli.py` |

Positional args (`collection`, `document`, `chunk_index`), the `--before`/`--after` flags, the
0–10 clamping in `_cmd_expand_chunks`, and the output format (`_format_expand_chunks`) are
untouched — this was a rename, not a redesign.

`expand_chunks` stayed in `_READ_ONLY_CMDS`, so it remains lock-free exactly as `read_document`
was.

## Help text

Old: `"Read anchor chunk plus N before and M after."` — framed around reading.

New: `"Expand an anchor chunk with N chunks before and M chunks after; merged with overlap
deduplication."` — framed around chunk expansion, matching the actual behavior and the new
command name.

## DOCS.md updates

`src/rag/DOCS.md` had three mentions of the old name (Flow section, `retriever.py` module
Purpose line, `lock.py` module Lock scope line) — all three swapped to `expand_chunks` /
`expand_chunks_workflow`. `retriever.py`'s LOC count in the DOCS.md heading (104) did not
change, since the rename touched only identifier text, not line count. Verified with `wc -l`
after the edit.

`dev/rag-chunking/DOCS.md` had one mention in the Role paragraph (`read_document`'s overlap
deduplication) — swapped to `expand_chunks`'s overlap deduplication.

## Verification performed

1. `python cli.py expand_chunks rag-cli-docs
   process-docs/eval_suite/2026-08-12_pass_prompt_overhaul_worker_blindness.md 0 --after 1`
   against the live `rag-cli-docs` collection (Postgres only, no embedding server needed) —
   returned the expected header (`Document: ... | Chunks 0-1 (anchor: 0)`) followed by the
   merged content of chunk 0 and chunk 1.
2. `python cli.py read_document rag-cli-docs foo.md 0` — rejected by `NoHelpParser`
   (exit code 2, help-redirect message), confirming the old subcommand string is gone from
   argparse.
3. `python cli.py list_documents rag-cli-docs --filter eval_suite` — worked exactly as before,
   confirming dispatch for other commands is unaffected by the rename.
4. Repo-wide grep for `read_document` excluding `process-docs/` and `.git/` — zero hits.

## Note for a follow-up agent

`process-docs/` itself still contains many mentions of `read_document` (delivery, infra,
eval_suite, rag-chunking, module_standards, docs_drift_prevention areas) — these are history and
were deliberately left untouched per the rule that process-docs is never edited except by its
own author, in its own file. A reader of an older process-docs entry mentioning `read_document`
should understand it now refers to what the codebase calls `expand_chunks`.
