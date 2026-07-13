# Phase A Checkpoint — Queries Schema Extension, Q1–Q3 Sample

**Date:** 2026-05-24 | **Worker:** eval-infra | **Status:** Phase A complete, Phase B not started

## Method

For each query: (1) locate primary chunk via DB LIKE search on existing `expected_snippets` text in `test_db`; (2) scan all chunks of the expected document(s) for additional chunks that independently answer the query as a standalone response (paraphrase counts; near-mention does not); (3) for each relevant chunk, select an `identifying_quote` — verbatim substring unique within the document across all three collections via `SELECT chunk_index FROM documents WHERE collection=X AND document=Y AND content LIKE '%QUOTE%'`; (4) report any case where uniqueness fails (overlap conflict or 0/2+ hits) rather than resolving silently.

---

## Q1 — "What MRR@10 does SPLADE-v3 achieve on the MS MARCO dev set?"

**Document:** `SPLADE_v3.md`

### Primary chunk — Table 1 (exact score: MRR@10 = 40.2)

| Variant | chunk_index |
|---|---|
| test_db (2000/400) | 7 |
| test_db_2 (1000/200) | 15 |
| test_db_3 (512/100) | 29 |

**identifying_quote:** `"SPLADE-v3 | 40.2 | 72.3 | 75.4"`
Unique in all three variants (one hit each). Content: Table 1 row for SPLADE-v3 giving MSM=40.2, TREC19=72.3, TREC20=75.4.

### Additional relevant chunk — Abstract (approximate: "more than 40 MRR @ 10")

Content: *"Specifically, it gets more than 40 MRR @ 10 on the MS MARCO dev set"* — approximate answer, standalone-relevant.

**⚠ CONFLICT in test_db_2:** The sentence falls in the 200-char overlap between chunks 0 and 1 of `test_db_2`. Both chunks contain the full sentence. Resolution (user-confirmed): treat BOTH chunk 0 and chunk 1 as relevant for test_db_2, using per-chunk unique identifying_quotes.

| Variant | chunk_index | identifying_quote | Notes |
|---|---|---|---|
| test_db | 0 | `"it gets more than 40 MRR @ 10 on the MS MARCO dev set"` | Unique: [0] only ✓ |
| test_db_2 | 0 | `"Carlos Lassance Cohere"` | Author header; before overlap region; unique: [0] only ✓ |
| test_db_2 | 1 | `"This technical report is a companion to the release of the latest version of the SPLADE library1. Given the improvements"` | Introduction body unique to chunk 1 — verify before Phase B write ✓ |
| test_db_3 | 2 | `"it gets more than 40 MRR @ 10 on the MS MARCO dev set"` | Unique: [2] only ✓ (abstract split further at 512-char; relevant sentence lands in chunk 2) |

**Result:** test_db_2 gets one extra relevant chunk entry (both 0 and 1) vs the other two variants.

### No other relevant chunks

Chunk 6 (test_db) has Table 1's caption ("We report MRR @ 10 for MS MARCO (MSM)...") but NOT SPLADE-v3's actual score — data is in chunk 7. Not standalone-relevant.

---

## Q2 — "What two distillation losses does SPLADE-v3 combine during training and what are their respective weights?"

**Document:** `SPLADE_v3.md`

### Primary chunk — §2.3 "Two Distillation Losses"

| Variant | chunk_index |
|---|---|
| test_db | 2 |
| test_db_2 | 6 |
| test_db_3 | 12 |

**identifying_quote:** `"two main distillation losses have proven to be effective"`
Unique in all three variants ✓. Content: full §2.3 section naming both losses (KL-Div [14], MarginMSE [10]) and their weights (λ_KL = 1, λ_MSE = 0.05).

### Additional relevant chunk — overlap tail of §2.3 / head of §2.4

| Variant | chunk_index |
|---|---|
| test_db | 3 |
| test_db_2 | 7 |
| test_db_3 | 13 |

**identifying_quote:** `"starting from SPLADE++ Self Distil4"`
Unique in all three variants ✓. Content: starts mid-paragraph (overlap from primary chunk) but contains *"We then chose to combine both, with different weights λ_KL = 1 for KL-Div, λ_MSE = 0.05 for MarginMSE"* plus both loss names (MarginMSE, KL-Div) — standalone-relevant. The quote `"combine both, with different weights"` hits [2,3] in test_db (not unique); `"starting from SPLADE++ Self Distil4"` is unique to the overlap chunk.

### No other relevant chunks

No other SPLADE_v3.md chunk names both losses with weights.

---

## Q3 — "What Acc@3 does Qwen3-Embedding-8B achieve compared to GTE-large in the pipeline optimization study?"

**Document:** `Pipeline_Optimization.md`

### Primary chunk — Abstract

| Variant | chunk_index |
|---|---|
| test_db | 0 |
| test_db_2 | 1 |
| test_db_3 | 3 |

**identifying_quote:** `"0.571 versus 0.412 for GTElarge"`
Unique in all three variants ✓. Content: *"Qwen3-Embedding-8B/4096 achieves Top-3 accuracy ≈ 0.571 versus 0.412 for GTElarge/1024"* — direct comparison statement.

### Additional relevant chunk 1 — model comparison table + Key Findings paragraph

| Variant | chunk_index |
|---|---|
| test_db | 8 |
| test_db_2 | 18 |
| test_db_3 | 36 |

**identifying_quote:** `"GTE-large (1024-dim) scores 0.412"`
Unique in all three variants ✓. Content: (a) table row `Qwen3-Embed-8B | 4096 | 0.571 | ...` AND `gte-large-en-v1.5 | 1024 | 0.412 | ...`; (b) Key Findings paragraph *"Qwen3-Embedding-8B (4096-dim) achieves Top-3 accuracy of 0.571"* + *"GTE-large (1024-dim) scores 0.412"*. Both model scores present — standalone-relevant. Note: chunk 7 (test_db) also contains `"Qwen3-Embed-8B | 4096 | 0.571"` (table row spans chunks 7 and 8) but does NOT contain the GTE-large 0.412 row — not standalone-relevant.

### Additional relevant chunk 2 — Conclusions restatement (user-confirmed)

| Variant | chunk_index |
|---|---|
| test_db | 17 |
| test_db_2 | ? — verify in Phase B |
| test_db_3 | ? — verify in Phase B |

**identifying_quote (test_db):** `"achieving Top-3 accuracy of 0.571 versus 0.412 for GTE-large (1024 dimensions)"`
Unique in test_db ✓. Content: Conclusions section restates the comparison. Phase B must look up corresponding chunk_index for test_db_2 and test_db_3 via same LIKE search on this quote.

---

## User Decisions (incorporated into Phase B spec)

1. **Q1 test_db_2 conflict:** accept split — chunk 0 via `"Carlos Lassance Cohere"`, chunk 1 via Introduction-body quote. Both marked relevant. test_db and test_db_3 keep single secondary entry each.
2. **Q3 chunk 17:** include as third relevant chunk (Conclusions restatement). Phase B must verify chunk_index in test_db_2 and test_db_3 and confirm quote uniqueness in those variants.

---

## Phase B Scope (for successor)

Full spec at `/tmp/eval-queries-extension-task.md`. Phase A complete: Q1–Q3 primary + additional chunks identified, identifying_quotes DB-verified, conflicts reported and resolved. Execute Phase B without re-deriving Q1–Q3.

Phase B steps (from task spec):
1. Q4–Q17: same per-query process (primary chunk, additional relevant chunks, identifying_quotes, cross-variant lookup)
2. Write `dev/retrieval/queries_test_db.json` — new schema with `expected_chunks` per query (test_db chunk_indices)
3. Generate `dev/retrieval/queries_test_db_2.json` + `queries_test_db_3.json` — same quotes, LIKE-lookup chunk_index per variant; report any 0/2+ hits
4. Update `dev/retrieval/A_retrieval_eval.py` — load per-collection queries file; NDCG/MRR/Recall@K on `expected_chunks` binary relevance; snippet_recall over `identifying_quote` fields; eval-time assertion (quote → chunk_index must resolve at load)
5. Smoke: `--baseline --override collection=test_db` (and test_db_2, test_db_3); paste aggregate rows
6. Update `decisions/eval01_methodology.md` IST — new schema, three queries files, chunk-level ground truth
7. Commit

## Sources

- `/tmp/eval-queries-extension-task.md` — full Phase B task spec
- `decisions/OldThemes/eval_suite/methodology_clarification_2026-05-24.md` — binary relevance, by-construction methodology
- `dev/retrieval/queries_test_db.json` — original 17-query ground truth (input for migration)
