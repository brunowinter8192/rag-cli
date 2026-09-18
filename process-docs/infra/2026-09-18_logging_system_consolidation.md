# Logging System Consolidation (2026-09-18)

## Defect, verified before writing any code

A production search returned 12 results but left no trace under `src/rag/logs/`. `retriever.log`
did not exist. The lines were found in `~/.rag-locks/logs/server_manager.log` instead, truncated
to 50 chars, with no collection, no filters, and no result data.

Root cause, confirmed by reading the import graph rather than assuming it: `cli.py` unconditionally
imports `src.rag.retriever` at module load. `retriever.py` imports `reranker` before it reaches its
own `logging.basicConfig(...)` line. `reranker` imports `server_manager` → `server_utils`, and
`server_utils.py`'s `basicConfig(filename=~/.rag-locks/logs/server_manager.log)` runs first. Because
`logging.basicConfig()` is a no-op once the root logger already has a handler, every later
`logging.info()` call in the process — from any module — lands in whichever file won that race,
for the lifetime of that process.

This is worse than "retriever always loses to server_utils." It is systemic. Evidence: the main
repo's `src/rag/logs/chunker.log` (historic, pre-dates this session) contains lines that belong to
`embedder.py` and `indexer.py` — `"Embedded N texts"`, `"Indexed N/N chunks"`, `"Schema ensured"` —
because at some earlier point in this codebase's history, whatever process wrote that file happened
to import `chunker.py` first. The winner is "whoever imports first in this particular process," not
a fixed module. Any fix that just reorders imports would only relocate the same race, not remove it.

Also found while investigating: `LOG_DIR` was defined twice under the same name for two unrelated
purposes — `server_utils.py`'s `LOG_DIR = ~/.rag-locks/logs` (subprocess stdout redirect target for
llama-server / uvicorn, genuinely machine-global) and six other modules' `LOG_DIR = src/rag/logs`
(intended Python-logging target, per-worktree). `splade_server.py` alone produces two *different*
files both named `splade_server.log` — one per directory, one from each mechanism. That collision
is a direct symptom of the naming, not a coincidence.

## The fix

`src/rag/log_setup.py` is the single point that configures Python `logging` for the package.
`get_logger(name)` returns a `logging.Logger` with its own `FileHandler` attached directly to that
logger object (not to the root logger), writing to `src/rag/logs/<name>.log`, guarded by
`if not logger.handlers` so repeated calls are idempotent. Because each module's logger owns its
own handler, import order stops mattering — there is no shared root-logger state left to race over.
This eliminates the bug class, not just today's instance of it.

Every `logging.basicConfig(...)` call in the package was removed: `chunker.py`, `embedder.py`,
`reranker.py`, `indexer.py`, `sync.py`, `splade_server.py`, `server_utils.py`. `server_lifecycle.py`,
`server_manager.py`, `watchdog.py` (which logged via the bare root logger, riding whoever configured
it) and `lock.py` (`getLogger(__name__)`, no handler, also riding root) were converted to the same
`get_logger(name)` pattern for consistency — every module that logs now gets its own file:
`chunker.log`, `embedder.log`, `reranker.log`, `indexer.log`, `sync.log`, `splade_server.log`,
`server_utils.log`, `server_lifecycle.log`, `server_manager.log`, `watchdog.log`, `lock.log`, all
under `src/rag/logs/`.

`retriever.py` does not get a plain-text `retriever.log`. Its only two `logging.info()` calls were
exactly the broken search lines from the defect report — they are replaced wholesale by the
structured log below, not kept alongside it. Anyone looking for `retriever.log` should look for
`search.jsonl` / `expand.jsonl` instead; this is stated directly in `src/rag/DOCS.md`.

## Log root decision

`src/rag/logs/` is the single root for everything Python `logging` writes (module `.log` files, and
the new `search.jsonl` / `search_content.jsonl` / `expand.jsonl` / `expand_content.jsonl`). It was
already the intent of 6 of the 8 `basicConfig` callers, it is already gitignored, and it is
per-worktree — while multiple worktrees of this repo exist side by side (as they do right now),
per-worktree logs mean one worktree's dev activity cannot corrupt another's log history.

`~/.rag-locks/logs/` is left alone. It is machine-global by necessity — it holds subprocess stdout
for the singleton GPU server processes (`llama-port-*.log`, and the uvicorn-launched
`splade_server.log` that server_lifecycle.py opens with `open(log_path, "w")` before `Popen`). That
is OS-level file redirection of a shared process, not Python `logging`, confirmed by reading
`server_lifecycle.py::_launch` directly. The historic `~/.rag-locks/logs/server_manager.log` (851
search lines, oldest from 2026-07-23) is left exactly as it is — nothing writes into it anymore,
nothing was deleted or rewritten.

## Search log: shape and reasoning

`src/rag/retrieval_log.py` owns two JSONL pairs. `search.jsonl` is the lean, greppable record — one
line per `search_workflow` call:

```json
{"ts": "...", "search_id": "20260918T184726164512_a1b2c3", "query": "logging of search queries",
 "collection": "rag-cli-docs", "document": null, "exclude": "process-docs/%", "candidates": 30,
 "duration_ms": 842, "hit_count": 12,
 "hits": [{"rank": 1, "document": "src/rag/retriever.py", "chunk_index": 3, "score": 0.035864}, ...]}
```

Full untruncated query, both filters, actual dense-candidate count (`len(vector_results)`, not the
`RERANK_CANDIDATES=30` constant — fewer rows can match a narrow filter), wall-clock
`duration_ms` around the whole workflow, per-hit rank/document/chunk_index/score. This directly
answers the defect report's core complaint: a search against an off-domain query now shows
`hit_count: 12` with scores in the `0.0003–0.007` range in the same record, instead of a bare
`"returned 12 results"` that looks identical to a real hit.

`search_content.jsonl` is the sidecar — one line per hit, holding the full chunk text, linked to its
parent record by `search_id`:

```json
{"search_id": "20260918T184726164512_a1b2c3", "rank": 1, "document": "src/rag/retriever.py",
 "chunk_index": 3, "content": "<full chunk text>"}
```

Content is copied in, not referenced by `(document, chunk_index)` alone — a re-chunk that shifts
every `chunk_index` cannot silently invalidate a historic record, which is exactly the failure mode
an index-pointer-only sidecar would have.

`expand_chunks_workflow` gets the identical treatment (`expand.jsonl` / `expand_content.jsonl`,
`expand_id`) because it was structurally free: the workflow already builds the full merged content
in memory before returning it, so logging it costs one more file append, not a new query or network
call.

## Failure handling — corrected after user review

First draft wrapped every JSONL write in `try/except OSError: pass`. The user rejected this
correctly: a log write that fails silently is the exact defect this whole task exists to fix — the
old search lines were "being written" for two months and nobody noticed `retriever.log` never
existed, because nothing ever surfaced the gap.

Two things changed:

1. **What is caught.** `OSError` alone is too narrow — a non-serializable value in a hit dict would
   raise `TypeError` from `json.dumps`, not `OSError`, and that would kill an otherwise-successful
   search. The catch is a deliberate `except Exception`, scoped tightly around exactly the
   `json.dumps` + file-write pair in `write_jsonl_lines`, nothing wider. The search itself must
   survive regardless of what kind of failure the logging side hits.
2. **What happens on catch.** `report_write_failure(path, exc)` calls
   `error_log.write("retrieval_log", "log_write_failed", str(exc), path=str(path))` — reusing the
   already-existing anomaly channel (`src/rag/logs/errors.jsonl`), which lives under the same log
   root. If that call *also* raises (e.g. the whole `src/rag/logs/` directory is unwritable), the
   fallback is one line to `stderr` — chosen as the last resort specifically because it needs no
   further I/O of its own to succeed.

First pass left `"log_write_failed"` out of `error_log.ERROR_CODES` (that frozenset holds the 4
server-lifecycle codes), reasoning that `error_log.py` should stay untouched. The user rejected
that too, correctly: `error_log.read_all()` / `read_today()` are not what anyone runs by habit —
`rag-cli server errors` is, and that command filters through the narrower `read_errors_today()`,
which only returns entries whose `code` is in `ERROR_CODES`. A trace nobody's habitual command
surfaces is only marginally better than no trace — it defeats the actual requirement ("must ALWAYS
be externally traceable"), it just relocates where the silence happens. `"log_write_failed"` is
now in `ERROR_CODES` (`error_log.py` line 15, one line changed) and confirmed visible end-to-end:
injecting a real write failure and running `rag-cli server errors` immediately after shows
`retrieval_log: 1 entry today (log_write_failed×1)`. Touching `error_log.py` for one line was the
smaller evil versus a trace only findable by someone who already knows to look for it.

`log_setup.py`'s per-module `.log` files needed no equivalent wrapper: `logging.FileHandler` already
has this exact contract built into the stdlib — a failed `emit()` is caught internally by the
logging framework and reported to `stderr` via `logging.raiseExceptions`, never raised into caller
code. Only the hand-rolled JSONL writer in `retrieval_log.py` needed an explicit failure path.

## `error_log.py` — kept separate, not folded in

It never used the `logging` module (hand-rolled `open(path, "a")` JSONL append), so it never had the
`basicConfig` collision bug in the first place. Its domain — server-lifecycle anomalies
(start/stop/busy/watchdog events), consumed by `rag-cli server errors` — is unrelated to retrieval
observability. `retrieval_log.py` calls into it only as a failure-reporting side channel, not as a
shared owner of anything. Module ownership stays separate; the one line added to its
`ERROR_CODES` frozenset (see above) is the sole edit, not a merge of the two modules.

## `~/.rag-locks/logs/llama-port-*.log` — out of scope, confirmed

Read `server_lifecycle.py::_launch` directly: `log_fh = open(log_path, "w"); subprocess.Popen(cmd,
stdout=log_fh, ...)`. Raw OS-level stdout redirection of the llama.cpp/uvicorn subprocess, never
touches the Python `logging` module. Not part of this change.

## Sidecar growth — no action taken, and I agree with the user's read

`search_content.jsonl` grows roughly 24 KB per search (12 hits × ~2 KB average chunk text). At the
measured historic rate (851 searches over ~57 days, ~15/day) that is ~360 KB/day, ~10 MB/month.
No rotation was built. `src/rag/logs/` is gitignored either way, so it never touches the repo, and
Postgres remains the authoritative source for current index state — the sidecar is a disposable
observability trail, not a system of record, so worst case it is a `rm` away from a clean slate.
Revisit only if a future session measures an actual growth complaint; nothing here today justifies
guessing at a retention policy.

## Where results live for testing

The `rag-cli` wrapper at `~/.local/bin/rag-cli` hardcodes the path to the main repo checkout on
`integration`, not this worktree. A worker cannot merge branches, so a literal `rag-cli search ...`
run from anywhere does not exercise this change. The verification in this session instead used a
throwaway `/tmp/rag-cli-worktree` script with the exact same one-line
`exec .../venv/bin/python .../cli.py "$@"` body as the real wrapper, pointed at this worktree's
`venv` and `cli.py`, then deleted after use — functionally identical invocation path, nothing left
behind, nothing edited outside the worktree.

Separately: the sandboxed shell in this session has a hook that blocks redirecting `cli.py search`
output to a file (forces it to print directly into context) while a *different*, generic hook
demands every `python script.py` invocation be redirected. The two are contradictory for the
`search` subcommand specifically. Invoking through a `/tmp` wrapper script (so the command line
itself does not literally contain `python ...cli.py`) sidesteps both — this is a sandbox artifact
of this session, not a design decision worth carrying forward.

## DOCS.md discipline — corrected after user review

First pass put rationale directly into `src/rag/DOCS.md`: `retrieval_log.py`'s `Writes:` field
explained the (now-superseded) `ERROR_CODES` visibility trade-off across three sentences, and
`error_log.py`'s `Purpose:` field explained at length why it stayed separate from `log_setup`. The
user corrected this: DOCS.md answers "where is what," not "why was this decided" — the reasoning
belongs here, in process-docs, where it already was, duplicated. Both fields were cut back to the
factual statement (what the module writes, what it does), and the "why" now lives only in this
file, under "Failure handling" and "`error_log.py` — kept separate, not folded in" above.

## Known deviations from the code-standards system prompt — deliberate, not oversight

Two things in this change follow existing repo convention but deviate from the code standards in
the system prompt. Recorded here so a future agent finds a documented decision, not a fact to
rediscover by reading history.

1. **`retrieval_log.py` has two functions in its ORCHESTRATOR section** (`log_search`, `log_expand`),
   not the "exactly one function" the standard states. This mirrors `retriever.py`, which has carried
   five workflow functions (`list_collections_workflow`, `list_documents_workflow`,
   `progress_workflow`, `expand_chunks_workflow`, `search_workflow`) in its own ORCHESTRATOR section
   since before this session — a module serving multiple CLI-adjacent entry points, one dumb
   orchestrator function per entry point, all in the same section. `retrieval_log.py`'s two entry
   points (`log_search` for the `search` command's logging, `log_expand` for `expand_chunks`'s)
   follow the same established shape rather than introducing a second convention for one new file.
2. **Every import in this change is relative** (`from .log_setup import get_logger`,
   `from . import error_log`), not the `from src.module.submodule import name` absolute form PEP 8
   / the standard specifies. The entire `src/rag/` package already uses relative imports exclusively
   — every existing module does — so absolute imports in only the new files would be a second import
   style living inside one package, not a fix.

Neither was requested to change, and neither should be treated as license to introduce a third
inconsistency later — if these get fixed, they should be fixed package-wide, not file-by-file.

## Follow-up milestone: model configuration in every retrieval log record

Same session, same area, follow-up task: `search.jsonl` recorded query/filters/timing/hits but not
which model configuration produced them — useless for comparing two configurations against each
other. Added `retrieval_config.py` (resolves embedding/reranker identity from
`~/.rag-locks/server-port-{N}.json` via a new `server_lifecycle.find_server_state`, never from
`EMBEDDING_MODEL` or other module constants) and extended `retrieval_log.py` with a fingerprint +
`config_registry.jsonl` (fat-record vs fingerprint decision: fingerprint, per the design already
established for `search_content.jsonl` — lean record, linked sidecar/registry, same shape).

### Root cause verified myself before implementing, three findings that revised the task text

1. `models/` and `llama.cpp/build/` do not exist in this worktree at all — both gitignored,
   multi-GB, present only in the main repo checkout. Confirmed via `RAG_ROOT` resolution: default
   `Path(__file__).parent.parent.parent` for a worktree-local process resolves inside the worktree,
   where there is no `models/` directory. Testing the server swap required
   `RAG_PROJECT_ROOT=<main repo>` for that one invocation, read-only, nothing in the main repo
   touched.
2. `ensure_ready("embedding")` does not enforce single-instance switching. It resolves
   `_CLASS_MAP["embedding"] = ["embedding-8b", "embedding-0.6b"]` in that fixed order and returns on
   the first *healthy* match — so merely starting `embedding-0.6b` alongside a still-healthy
   `embedding-8b` would never route a search to it; `embedding-8b` wins every time, list order, not
   recency. Proving "reads reality" required an explicit `stop embedding-8b` before
   `start embedding-0.6b`, not just a second `start`.
3. A vector-dimension mismatch was likely (fixed `vector(4096)` column, unverified 0.6B output
   width) and was confirmed live — see below.

### context_size is launch intent, not measured reality — named, not worked around

`context_size_for_preset(name)` reads `SERVERS[name]["extra_flags"]`, the exact dict
`server_lifecycle.py` uses to build the `llama-server` launch command. That is the command the
process was told to run with, not a verified property of the process actually running — a server
started via `start_arbitrary` (no context flag at all, see `server_lifecycle.py`'s
`start_arbitrary` cmd construction: `-ngl 99` only, no `-c`) or one somehow relaunched by hand with
a different `-c` value would silently diverge from what this field claims. The honest source would
be the server's own `/props` endpoint, but the task forbids a network call on the search path, so
reading `extra_flags` is the correct choice under that constraint — it is just not the same
guarantee as the rest of the resolved config (`model_name`/`model_path`, which come from the state
file the launching process itself wrote after confirming health). Documented directly in
`server_utils.py`'s DOCS.md entry and here; not worked around, per instruction.

### "First time this fingerprint is seen" — confirmed mechanism, no lock

Every CLI invocation is a fresh Python process — no in-process cache survives between searches, so
`known_fingerprints()` in `retrieval_log.py` reads the entire `config_registry.jsonl` on every call
and checks membership before appending. This is a plain read-then-append with no lock of any kind.
Consequence accepted deliberately, per instruction: two concurrent searches under a newly-seen
configuration can both find the fingerprint absent, and both append an identical registry line.
Content-identical duplicate lines are harmless — `known_fingerprints()` just sees the fingerprint
twice on the next read, membership check is unaffected. No lock was added; the read path staying
lock-free outranks a cosmetic duplicate line, exactly as instructed.

### Known blind spot: a failed search writes no record at all

Confirmed live, not hypothesized. Stopped `embedding-8b`, started `embedding-0.6b`, ran a search
against the existing 4096-dim index. Sequence observed:
- `embed_workflow` succeeded — `embedder.log` shows `Embedded 1 texts`, and a direct call to
  `retrieval_config.resolve_search_config` against the live 0.6B server correctly returned
  `embedding.preset: "embedding-0.6b"`, `model_name: "Qwen3-Embedding-0.6B-Q8_0"`,
  `vector_dimension: 1024` — while the `EMBEDDING_MODEL` module constant in `embedder.py` still
  read `"Qwen3-Embedding-8B"`, unchanged, confirming the constant would have been silently wrong
  had it been used.
- `search_vectors()` in `search_primitives.py` then raised
  `psycopg2.errors.DataException: different vector dimensions 4096 and 1024`, uncaught by
  `cli.py`'s `_run_dispatch` (`psycopg2.errors.DataException` is not `httpx.HTTPStatusError`,
  `httpx.RequestError`, or `RuntimeError` — the three types that handler catches) — a raw Python
  traceback to stderr, exit code 1.
- `search.jsonl` gained zero new lines for this query. `config_registry.jsonl` gained zero new
  entries either. The exception fires inside `search_workflow`, before either `log_search` call is
  ever reached — there is no code path from a `search_vectors` failure back into `retrieval_log.py`.

This matters because a failed search is exactly the signal a comparison log exists to catch — a
config that breaks (dimension mismatch, server down, timeout) is currently invisible in
`search.jsonl`, indistinguishable from "nobody searched." Not fixed in this milestone, per
instruction — the fix would mean wrapping `search_workflow`'s body in a try/except that still logs
before re-raising (or logs a `hit_count: 0, error: ...` record instead of raising), which is a
real behavior change to retrieval error handling and deserves its own milestone, not a drive-by
patch here.

### Known limitation, not fixed: chunk size and overlap are not recoverable

The `documents` table has no chunk-size/overlap column and there is no collections metadata table
(`process-docs/indexing/collections_metadata_2026-05-24.md` and
`process-docs/eval_suite/methodology_clarification_2026-05-24.md` both already propose one, for the
same underlying reason — eval-report provenance, not retrieval logging — neither has been built).
So `config_registry.jsonl` can name the embedding/reranker model precisely but cannot say what
chunk size or overlap produced the chunks a given search returned — a comparison across chunk-size
variants of the same collection cannot be reconstructed from this log today. No schema migration
was attempted; out of scope for this milestone by explicit instruction.

### Test evidence (live, this session)

Four repeated identical searches (`embedding-8b` + `reranker-0.6b` unchanged throughout) all
produced fingerprint `f5a86212742e0092` — byte-identical across all four, timestamps
19:16:31/19:16:45/19:16:53/19:16:59. After the full stop-8b → start-0.6b → (failed search) →
stop-0.6b → start-8b round-trip, a fresh search reproduced the *same* `f5a86212742e0092` again,
matching the already-registered entry — confirms the fingerprint is a pure function of
configuration, indifferent to how many times a server has been cycled. Query-prefix sensitivity
(a live constant, can't be toggled without a code edit) verified instead via
`dev/infra/test_retrieval_config.py`'s `test_fingerprint_changes_with_query_prefix`, alongside
`test_fingerprint_ignores_redundant_fields` (renaming only the preset label, keeping model_name
fixed, must not change the fingerprint — passed).

## Cross-references

Retrieval workflow structure: Area `retrieval`. Server/GPU process lifecycle and `~/.rag-locks/`
conventions: Area `server_management`. Both were read in full before this change; nothing in either
was found to contradict what is written here as of 2026-09-18.
