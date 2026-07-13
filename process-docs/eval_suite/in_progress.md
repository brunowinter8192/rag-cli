# Eval Suite — In Progress

## Status (2026-05-10)

Baseline-Harness gebaut, Smoke OK, Eval-Execution auf next-session deferred.

**Done:**
- NDCG@K, MRR@K, Recall@K (chunk-level) in `dev/retrieval/A_retrieval_eval.py` — formal IR-Metriken
- test_db Collection in `rag_test` (7 papers / 250 chunks: RAGAS, RAG_Evaluation_Survey_2025, Pipeline_Optimization, Fusion_Functions_Hybrid_Retrieval, Qwen3_Embedding, SPLADE_v3, Rethinking_Chunk_Size_Long_Document)
- 17 Queries in `dev/retrieval/queries_test_db.json` (factual mix, alle snippets grep-verified)
- Production top_k Clamp auf 12 (Ceiling, nach Fix der Floor-vs-Ceiling-Verwechslung — siehe persisted-output-probe SHA 1562575 + follow-up)
- Smoke-Run: NDCG@12=0.834, MRR@12=1.000, Recall@12=33.3%, Doc Recall=100%, Snippet Recall=82%

**Pending (next session):**
- Authoritative Eval-Execution: `--baseline` + Sweeps (mode, alpha, top_k) gegen test_db
- Ergebnisse als SOLL in `decisions/retrieval03_fusion.md` und `decisions/retrieval04_reranking.md` einpflegen
- Query-Inspektion durch User — sind die 17 worker-generated Queries als Baseline akzeptabel oder hand-kuratieren?

## Erweiterungspfad

DB wird sukzessive erweitert um weitere Domänen/Quellen (test_db wächst über die 7 Reference Papers hinaus). Nach jeder Erweiterung Re-Eval gegen die größere Test-Collection um zu prüfen ob die Baseline-Config (CC α=0.8, rerank=False default, top_k=12, Qwen3-Embedding-8B + SPLADE-v3) auch unter veränderter Datenverteilung stabil bleibt.

Erwartete Phasen:

1. **Aktuelle Baseline** (n=250 chunks, 17 queries) — strukturelle Konfig-Validierung auf RAG-internem Methodologie-Material.
2. **Erweiterung 1** (test_db + X Papers/Domänen außerhalb RAG-Methodologie) — Domain-Stabilität prüfen, bricht Baseline-Konfig bei Wechsel auf andere Inhalts-Klassen?
3. **Erweiterung 2** (test_db wieder + X) — Skalierungs-Stabilität, bricht etwas zwischen ~250 und ~1000 Chunks?
4. **Sweep-Re-Runs** an jedem Erweiterungspunkt für alpha, top_k, rerank on/off — sehen ob optimale Werte mit Daten-Skala/Domäne kippen.

Ziel: empirische Evidenz dass die Baseline-Wahl nicht durch die kleine Initial-DB überanpasst ist. Wenn z.B. α=0.8 bei n=250 optimal aber bei n=1000 auf α=0.6 kippt, ist das ein wichtiges Signal.

## Open Questions

- Worker-generated Queries vs hand-kurierte Ground Truth — Qualitäts-Threshold für authoritative Eval. Worker-Queries sind sehr factual-lastig und sehr spezifisch (deutliche Substring-Hits) — könnte den NDCG artifiziell hochziehen weil Snippets quasi exact-match sind.
- Graded Relevance (rel ∈ {0,1,2,3}) statt binary für NDCG — Snippet-Match als rel=2, expected_document ohne Snippet als rel=1, Rest rel=0. Schärfere Metrik aber mehr Curation-Aufwand.
- Statistical Significance (paired t-test) für Sweep-Δs bei n=17 — Power-Limit, kleine Effekte (~2-3pp) wahrscheinlich nicht signifikant von 0 zu unterscheiden.
- Latency-Tracking pro Query — Reranker-Trade-off-Frage aus retrieval04 (Open Questions) bislang ungelöst.

## Quellen

- RAG_reference Collection: RAGAS_Evaluation_Framework, RAG_Evaluation_Survey_2025, Pipeline_Optimization, Fusion_Functions_Hybrid_Retrieval
- `decisions/eval01_methodology.md` — current IST + Evidenz + Pending SOLL
- `decisions/OldThemes/eval_suite/process_2026-05-10.md` — Session-Iteration die zur aktuellen Methodologie führte
- `decisions/OldThemes/eval_suite/historical_setup_march2026.md` — deprecated März-2026 NDCG-Tabellen, preserved
