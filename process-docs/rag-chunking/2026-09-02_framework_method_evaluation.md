# read_document assembly method — framework comparison and decision (2026-09-02)

Companion to the probe and fix entries in this area. This entry records the alternatives weighed in
conversation before the fix was dispatched, and why read-time chunk dedup won over the methods the
established frameworks use.

## The three candidate methods

- **A — read-time dedup on DB chunks.** Keep `read_document` assembling from the `documents` table,
  fix the broken suffix/prefix dedup in `merge_chunks`/`find_overlap`.
- **B — slice from the source `.md` at read time.** Locate the anchor/edge chunks in the on-disk
  source file (byte-match) and return the file span. The framework-pure pattern.
- **C — store char offsets per chunk at index time.** Deterministic dedup computed from offsets in
  the DB; needs schema change, chunker change, and re-index (or an A-style fallback) for existing rows.

## What the frameworks actually do (GitHub source reading, 2026-09-02)

- LlamaIndex `PrevNextNodePostprocessor` (`llama-index-core/.../postprocessor/node.py`) fetches
  neighbor nodes from the docstore and returns them as **separate nodes** — no text merge, no dedup.
- LlamaIndex sentence-window stores the assembled window in node **metadata at index time**
  (`MetadataReplacementPostProcessor` pattern) — dedup never arises.
- LangChain `ParentDocumentRetriever` returns the **parent document from the docstore** — slice from
  source by construction.
- Nobody in either framework does suffix/prefix string matching; that part is our own construction.

## Why B lost: state mixing, not staleness

- Staleness is symmetric: with hash-diff syncing (`update_docs`), the index lags edits under every
  method. That is not the discriminator.
- The discriminator is **consistency within one result**. DB assembly returns the same snapshot the
  search scored; file slicing returns current disk text for a hit that was scored on indexed text.
  For docs collections (live project files edited between syncs — the normal mid-session state), a
  slice can deliver text in which the scored passage no longer exists.
- For write-once tool collections under `data/documents/` (releases, reference papers) the file IS
  byte-identical to the index and B would be safe — but a fix that behaves differently per
  collection class was judged the worst option.
- B also needs an A-style fallback for the no-match case, and — since every chunk is a contiguous
  substring of the indexed source by chunker construction — the DB chunks already contain every byte
  a file slice would provide. B buys nothing over a working A.

## Why C was deferred, not rejected

C is the deterministic upgrade path (exact cut positions, no heuristic). It was parked because the
area's probe measurement (see the probe entry: 13,702 adjacent pairs, three collections) showed the
exact-match heuristic with a correct bound leaves **zero** residual failures — there was no gap left
for C to close, and it would cost a schema migration plus re-index while still needing A as the
fallback for unmigrated rows.

## Decision

Method A, shipped as the fix in this area. C remains the named follow-up if a future corpus surfaces
residual dedup failures that exact matching cannot handle.
