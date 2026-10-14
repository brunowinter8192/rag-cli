# Duplicated dev helpers: `_rerank_at` and `_lookup_server_url` unified (2026-10-14)

Scope: `dev/retrieval/` and `dev/server_management/`. Decision: unify. The module_standards sweep of 2026-09-16 flagged the two pairs and left them alone only because they cross two dev areas. This entry records why that stop was lifted and how the merge was done.

## Facts found before the change

- `_rerank_at(query, results, top_k, url)` existed in `dev/retrieval/eval_runner.py` and `dev/server_management/B_real_smell.py`. Identical body; one inlined the timeout `300.0`, the other used a constant `RERANK_TIMEOUT = 300.0` that only this function read.
- A third copy of the same body was `rerank()` in `dev/retrieval/p1_retriever.py`, with the module-level `RERANKER_URL` and a 60 s timeout. Same HTTP call, same sort, same copy-and-rescore loop.
- `_lookup_server_url(server_name, path="/v1/rerank")` existed in `dev/retrieval/eval_constellation.py` and `B_real_smell.py`. Same glob over `~/.rag-locks/server-port-*.json`, same name match, same URL format. Two real differences:
  - Not found: retrieval copy raised `RuntimeError("No running state file for server: <name>")`, `B_real_smell` copy returned `None`.
  - Corrupt state file: `B_real_smell` copy logged at debug level, retrieval copy skipped silently.
- Callers depend on the difference. `B_real_smell._wait_all_healthy` treats `None` as "not up yet" and keeps polling while servers start. `B_real_smell._patch_retriever_urls` skips silently on `None`. `eval_constellation._patch_retriever_urls` catches the `RuntimeError` and prints `[url-patch] WARNING: ...`. `eval_runner` lets the `RuntimeError` surface, and `_run_query` turns it into a "query failed" warning.
- "Retired" does not apply to the retrieval scripts. The 2026-09-18 retirement in the eval_suite area covers the synthetic four-pass query pipeline (now `dev/eval_suite/`). `dev/retrieval/A_retrieval_eval.py` is the older ground-truth suite and is not mentioned there; the retirement entry itself proposes replaying real queries under two configurations, which is what this harness does. No evidence either way that anyone still runs it, so it was treated as live.
- `B_real_smell.py` already imported `p1_retriever` from `dev/retrieval/`. A dependency from server_management to retrieval therefore existed before this change.

## Decision and why

Unify, because the `_rerank_at` pair plus `rerank()` is pure duplication and the lookup pair differs only in how "not found" is reported, which one function can express for both callers.

Considered and rejected:
- Keep both: the divergence risk is real (a fix to the response parsing in one copy would silently miss the other two), and the only argument for keeping was the cross-area boundary, which already did not exist for `p1_retriever`.
- One lookup function with a `raise_if_missing` flag: a boolean that changes the return type is worse than two named functions.
- Reuse `src/rag/server_state.find_server_url`: the dev convention forbids direct `src` imports, and production semantics differ (class-name resolution, URL without path).

## What was built

- `dev/retrieval/server_urls.py` (new, leaf module, stdlib only): `find_server_url(name, path) -> str | None` holds the single glob/parse implementation (with the debug log); `require_server_url(name, path) -> str` wraps it and raises the exact old `RuntimeError` message.
- `dev/retrieval/p1_retriever.py`: new `rerank_at(query, results, top_k, url, timeout=RERANK_AT_TIMEOUT)`; `rerank()` delegates to it with `RERANKER_URL` and `RERANK_TIMEOUT` (60.0). New constants `RERANK_TIMEOUT = 60.0`, `RERANK_AT_TIMEOUT = 300.0` replace the two literals.
- `eval_constellation.py` and `eval_runner.py` use `require_server_url`; `eval_runner` calls `_retriever.rerank_at`. `B_real_smell.py` uses `find_server_url` and `_retriever.rerank_at`.
- Deleted: both `_rerank_at`, both `_lookup_server_url`, `B_real_smell.RERANK_TIMEOUT`, `eval_constellation.TIMESTAMP_DIR` (its only reader moved), and the now unused `httpx` import in `eval_runner`.
- `TIMESTAMP_DIR` in `server_urls.py` is another per-area copy, same as in `constellation_measure.py` and elsewhere; the sweep decision that separate copies across dev areas are acceptable stands. `B_real_smell` keeps importing its own from `constellation_measure` for VRAM sampling.
- Imports: scripts in `dev/` are run directly, so `from src.x import y` cannot resolve there. The existing convention (sys.path insert, then bare sibling module name, as with `p1_retriever`) was followed, as approved by Main.
- Left alone on purpose: the two `_patch_retriever_urls` (differ in error handling, the sweep entry already says so), `_check_servers`, `_write_report`.

## Tests

`dev/retrieval/test_shared_helpers.py`, 12 strands, run with `./venv/bin/python dev/retrieval/test_shared_helpers.py > /tmp/<log> 2>&1` (a hook wants redirected output). Hermetic: each strand has a tmp `HOME` (so `~/.rag-locks` is its own), and a local `HTTPServer` on an ephemeral port plays health and rerank endpoint. Dev modules are imported inside the strand, not at file top, because the spawned child imports the test file before `strand_runner` sets `HOME`, and `TIMESTAMP_DIR` is evaluated at import.

- Seven caller-level strands were written first and run against the OLD code: 7 of 7 passed (after fixing one wrong expected score in my own test, 0.6 not 0.5; the code was right). They call the callers through names that exist before and after: `B_real_smell._patch_retriever_urls`, `_wait_all_healthy`, `_run_one_query("dense+rerank-0.6b")`, `eval_runner._dispatch_rerank_mode("cc+rerank-8b")`, `eval_constellation._patch_retriever_urls` (found and missing server).
- After the refactor the same seven pass, plus five new strands: `find_server_url` returns URL or `None`; `require_server_url` raises the old message; `rerank_at` orders, truncates to top_k, rounds the score to 6 places and leaves the input dicts untouched; `rerank_at` default timeout is 300.0; `rerank` uses the module `RERANKER_URL` and 60.0. Result: 12 of 12 passed.
- Mutation check: changing `RERANK_AT_TIMEOUT` to 301.0 failed exactly `test_rerank_at_default_timeout` and nothing else; restored.
- Also run: `A_retrieval_eval.py --help` exits 0 (import chain of the whole eval suite intact). `A_retrieval_sandbox.py` still calls `_retriever.rerank(query, candidates, top_k)`, signature unchanged.
- Not run: a live constellation or retrieval run (no GPU servers or Postgres in the worker sandbox). The rerank request/response contract is only proven against the local fake server, not against llama-server.

## Docs

`dev/retrieval/DOCS.md`, `dev/server_management/DOCS.md`, `dev/DOCS.md` updated; LOC in headings match `wc -l`. `docs-drift-check` from the worktree root: 0 LOC-Drift. It still reports 5 findings, all in files this change did not touch (`dev/eval_suite/DOCS.md`, `src/DOCS.md`, root `DOCS.md` title, `src/rag/DOCS.md` title and Role word count).

## Hints for a successor

- A Bash call that a hook rejects (for example an unscoped `grep -r`) is rejected as a whole, including the edits chained before it. After a rejection, check `git diff --stat` before moving on. This happened once here: the `sed` replacing the `eval_runner` import silently did not run.
- BSD `sed` on this machine needs `sed -i ''`.
- `venv` in a worktree is a symlink that `.gitignore` (`venv/`) does not match; do not let `git add -A` commit it.
- If a third caller ever needs "raise on missing" semantics for a different reason than the eval scripts, add it next to `require_server_url` rather than a new lookup copy.
