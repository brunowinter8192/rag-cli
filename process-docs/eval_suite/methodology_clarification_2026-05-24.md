# Eval Methodology Clarification — 2026-05-24

## Status

Session-Klärung der Eval-Methodologie nach 14 Tagen Pending (siehe `in_progress.md`).
Vier Kernpunkte:

1. **Relevanz-by-Konstruktion** ersetzt doc-level Approximation und LLM-Judge — Pain-Resolution für das Eval-Vertrauen.
2. **`queries_test_db.json` Schema-Erweiterung** um `expected_chunks` (Chunks aus denen die Query gebaut wurde).
3. **`collections` Metadata-Tabelle** als Voraussetzung für Sweeps mit unterschiedlichen Indexing-Configs (Chunk-Size, Modell, mit/ohne Sparse) — eigener OldThemes-Topic, hier nur verlinkt.
4. **`DENSE_SCORE_THRESHOLD = 0.01` Entfernung** — Side-Decision, top_k=12 Cap ist die wirkliche Obergrenze.

Plus Snapshot was test_db aktuell ist, plus offene SPLADE-Frage die in den Sweep wandert.

## Test-DB Snapshot (Stand 2026-05-24)

7 Paper, 250 Chunks, durchgängig akademische RAG/Retrieval-Methodologie, Englisch, prose mit eingebetteten Tabellen + Code:

| Dokument | Chunks | Avg Chars | Max Chars |
|---|---|---|---|
| Fusion_Functions_Hybrid_Retrieval | 70 | 1713 | 1993 |
| RAG_Evaluation_Survey_2025 | 65 | 1834 | 2053 |
| Qwen3_Embedding | 32 | 1758 | 2213 |
| Rethinking_Chunk_Size_Long_Document | 25 | 1704 | 2363 |
| RAGAS_Evaluation_Framework | 24 | 1696 | 2038 |
| Pipeline_Optimization | 22 | 1809 | 1995 |
| SPLADE_v3 | 12 | 1683 | 1998 |

Anerkannte Schwäche: **EIN Domain-Cluster**. Die Eval-Ergebnisse aus dieser Collection sagen "für RAG-Methodologie-Paper ist X gut" — nicht ob X auch für API-Docs (Monitor_CC_reference), Trading-Bücher (Trading) oder unsere eigenen technischen Docs (RAG-docs / Monitor_CC-docs) gut ist. Erweiterungspfad bleibt wie in `in_progress.md` skizziert: alle paar Wochen test_db um andere Domänen erweitern und Re-Eval gegen die größere Collection laufen lassen. Aktueller Stand reicht als Baseline.

## Relevanz-by-Konstruktion

**Vorher (falsches mentales Modell):** Eval-Relevanz wurde behandelt als hätte sie eine Approximations-Lücke, die durch entweder doc-level Heuristik (`expected_documents` als "relevant = alle Chunks aus dieser Datei"), Substring-Matching (`expected_snippets` als "relevant = Chunk der diesen String enthält") oder LLM-Judge (RAGAS-style) geschlossen werden müsste.

**Tatsächlich:** Die 17 Queries entstanden so — Worker hat MDs gelesen und auf Basis dessen was er gelesen hat Queries formuliert. Zum Zeitpunkt der Query-Formulierung wusste er zu 100% welcher Text die Quelle der Query war. Relevanz war kein Schätzproblem, sondern Eingangsdatum. Die Frage existiert nur weil ein spezifischer Chunk existiert und der ihn zur Vorlage genommen hat.

Konsequenz:

- **Kein LLM-Judge nötig.** RAGAS / ähnliche Frameworks brauchen LLM-Judge weil dort Queries und Dokumente unabhängig existieren — Relevanz muss nachträglich approximiert werden. Bei uns kommt die Query aus dem Dokument, Relevanz ist by-design fixiert.
- **Doc-level Approximation entfällt für Recall@K.** Aktuell zählt `Recall@K` jeden Chunk aus `expected_documents` als relevant. Bei 70 Chunks in Fusion_Functions sind alle 70 "relevant", obwohl nur 1-2 Quelle der Query waren. Falsch und durch konstruktive Chunk-Indizes korrekt machbar.
- **`snippet_recall` wird Sanity-Check, nicht Primärmetrik.** Wenn Chunk-Index direkt im Test-Set steht, ist Substring-Matching auf den Snippet nur noch Robustheits-Prüfung — "hat das System wirklich den erwarteten Wortlaut zurückgegeben". Primärmetrik wird positionbasiert auf dem konstruktiven Chunk.

Trade-off der Konstruktions-Methode (transparent halten): die Definition ist *strikt*. Wenn ein anderer Chunk in der Collection zufällig dieselbe Information enthält (Duplikat in Survey-Paper-Sektion, Re-Statement in einem zweiten Paper), zählt der nicht als relevant — nur der Original-Chunk aus dem die Query gebaut wurde. Das ist Präzisions-orientiert, nicht Recall-orientiert auf Inhalts-Ebene. Für unsere Pipeline-Verifikation (kommt das System zum erwarteten Source?) ist das genau richtig; für "kann das System alle inhaltlich passenden Stellen finden" wäre es zu eng. Letzteres ist hier nicht das Eval-Ziel.

## Schema-Erweiterung `queries_test_db.json`

Vorher:
```json
{
  "query": "...",
  "type": "factual",
  "expected_documents": ["X.md"],
  "expected_snippets": ["..."]
}
```

Nachher:
```json
{
  "query": "...",
  "type": "factual",
  "expected_documents": ["X.md"],
  "expected_chunks": [{"document": "X.md", "chunk_index": 17}, ...],
  "expected_snippets": ["..."]
}
```

`expected_chunks` ist die per-Konstruktion-Liste der Quell-Chunks. Eine Query kann mehrere Source-Chunks haben (Cross-Document-Queries wie die zwei am Ende der test_db haben mindestens zwei). Wenn ein Snippet über einen Chunk-Boundary läuft (möglich bei unserem 400-Char-Overlap), beide Chunks eintragen.

**Migrations-Aufgabe für die 17 existierenden Queries:** mechanisch — pro Query den existierenden Snippet in der DB suchen (oder im MD), Chunk-Index ablesen, eintragen. Edge-Cases pro Hand: Snippet über Chunk-Boundary, Snippet mit Whitespace-Drift gegen DB-Inhalt, Snippet als paraphrased rather than literal (sollte nicht passieren weil die Queries grep-verified sind, aber prüfen).

## Metrik-Semantik unter der neuen Definition

`snippet_recall` (Sanity-Check): pro Query, Anteil der `expected_snippets` die als Substring in irgendeinem top-K Hit erscheinen. 1.0 wenn alle, 0.0 wenn keiner. Robust gegen Chunk-Index-Drift bei Re-Indexing mit anderem Chunk-Size, aber empfindlich gegen Wortlaut-Drift.

`doc_recall` (Diagnostik): pro Query, hat *irgendein* Chunk aus jedem `expected_documents` es in top-K geschafft. Binär per expected_doc, aggregiert über Liste. Wenn `doc_recall=1` aber neue chunk-level Recall=0 → richtige Quelle gefunden aber falsche Stelle drin → Chunking/Ranking-Problem im Retrieval.

**`Recall@K` (chunk-level, neu definiert):** |`expected_chunks` in top-K| / |`expected_chunks` total|. Die "total" ist jetzt eine kleine Zahl (1-3 pro Query), nicht die ganze Datei. Damit wird Recall@K eine ehrliche Metrik: "von den Chunks die diese Query verursacht haben, wie viele kamen zurück".

**`MRR@K` (Mean Reciprocal Rank):** 1 / Position des ersten `expected_chunks`-Hits in top-K. 0 wenn keiner. Misst "wie weit oben steht der konstruktive Source". Wichtig wenn das System nur top-Ergebnisse anzeigt.

**`NDCG@K` (Normalized DCG):** Standard-IR-Metrik, summiert Relevanz mit log-Discount nach Position, normalisiert gegen ideale Anordnung. Bei binärer Relevanz (Chunk ∈ expected_chunks oder nicht) auf konstruktiver Ground Truth: misst Ranking-Qualität präzise — System wird bestraft sowohl für fehlende Hits als auch für Hits an schlechter Position. Das ist die Königsmetrik die diskriminativ ist für Konfig-Vergleiche (α-Sweep, mode-Sweep, top_k-Sweep).

**Welche ist primär für unsere Entscheidungen?** Vorschlag: NDCG@K als Primärmetrik für Sweep-Vergleiche (diskriminativ, ranking-aware), Recall@K als "absolutes Coverage" Plausibilitätscheck, snippet_recall als Sanity-Check gegen Wortlaut-Drift. doc_recall nur als Diagnostik wenn Hauptmetriken schlechte Werte zeigen und wir verstehen wollen ob das Dokument überhaupt gefunden wurde.

## SPLADE-Frage bleibt offen, wandert in den Sweep

User-Frage in dieser Session: brauchen wir SPLADE überhaupt im Retrieval, oder ist es nur Indexing-Boost? Antwort aus Code-Inspektion: SPLADE wird zur Query-Zeit aktiv eingesetzt — in `search_hybrid` wird die Query sparse-embedded, gegen `sparse_embedding` Spalte gematcht, mit dem Dense-Branch via CC-Fusion fusioniert. Ohne SPLADE im Retrieval fällt der gesamte Sparse-Branch weg → `search_hybrid` reduziert sich auf pure Dense (oder Dense + BM25 als lexikalischer Ersatz).

Historische Evidenz uneindeutig:
- searxng (technische Docs, n=2337): Hybrid mit SPLADE *schlechter* als Dense (NDCG@3 0.298 vs 0.465). SPLADE schadet.
- qwen3_paper (akademisch, n=66): Hybrid besser, Sparse allein sogar besser als Dense. SPLADE hilft.
- RAG_MCP (gemischt, n=483): CC α=0.8 mit SPLADE +6pp Snippet Recall über Dense. SPLADE hilft.

Production-Verteilung ist Mix — wir haben *keine* belastbare Evidenz ob SPLADE bei uns aggregat hilft oder schadet. **Entscheidung:** keine voreilige SPLADE-Entfernung, sondern der `--sweep mode` Lauf in der nächsten Eval-Etappe enthält dense / sparse / hybrid / cc als Vergleichsmodi auf test_db. Wenn das Ergebnis klar pro Dense ausfällt, ist die Konsequenz eine eigene Diskussion: SPLADE aus Indexing entfernen (Server weg, Sparsevec-Spalte weg, nnz-Corruption-Bug irrelevant) und Retrieval auf Dense-only umstellen. Aber das ist evidence-gated, nicht intuition-driven.

## DENSE_SCORE_THRESHOLD = 0.01 — Entfernung

`src/rag/retriever.py:23` definiert `DENSE_SCORE_THRESHOLD = 0.01` mit Kommentar "noise floor; was 0.5 (unverified Haiku heuristic)". Wird in `search_workflow` und `search_hybrid_workflow` (no-rerank branch) auf die top-K Ergebnisse nach Fusion angewandt.

Mechanik: `top_k = min(top_k, 12)` ist der Hard-Cap auf wie viele Treffer überhaupt zurückkommen. Filter danach killt nur Treffer *innerhalb der top-12* die unter 0.01 Cosine liegen. In der Praxis: Dense-Cosine auf relevanten Matches liegt im Bereich 0.4-0.8, auf nicht-relevanten 0.1-0.3. Werte < 0.01 sind extrem selten und bedeuten "Collection hat nichts zur Query".

Effekt: in 99% der Fälle ändert der Filter nichts. In dem 1%-Fall wo nichts passt: User bekommt 0 Treffer statt 12 Garbage-Treffer. Das wäre als Feature argumentierbar ("ehrliches kein-Ergebnis-Signal"), aber:

- Wert ist seit 2026-05-11 explizit als "unverified" markiert
- Niemand misst gegen ihn
- Edge-Case (nur 1% der Fälle), und in diesem Edge-Case kann der User die Low-Scores aus 12 Ergebnissen auch selbst ablesen
- Konsistenz: wir entfernen lieber unkalibrierte Defaults als sie unverified im Code zu behalten

**Entscheidung:** Threshold entfernen. `filter_by_score(results, DENSE_SCORE_THRESHOLD)`-Aufrufe in `search_workflow` und `search_hybrid_workflow` (no-rerank) raus. BM25-Branch (`search_keyword_workflow`) verwendet einen separaten `0.05`-Wert, der bleibt unangetastet (BM25 ist andere Skala, eigene Diskussion).

`decisions/retrieval04_reranking.md` muss nach dem Code-Change aktualisiert werden — die Erwähnung des `DENSE_SCORE_THRESHOLD = 0.01` "unverified" Pending-Item entfällt.

## Collections Metadata-Tabelle — eigener Topic, hier nur verlinkt

User-Forderung: pro Collection muss aus der DB abfragbar sein womit indexiert wurde (Embedding-Modell, Sparse-Modell, Chunk-Size, Overlap, etc.), damit Eval-Reports saubere Provenance haben.

Aktueller `documents`-Tabellen-Schema hat keine solche Metadata-Spalte:
```
id, content, collection, document, chunk_index, total_chunks, embedding, sparse_embedding, tsv
```

Vorschlag: neue Tabelle `collections` mit:
```
name PK, embedding_model, embedding_dims, sparse_model (nullable),
chunk_size, overlap, db_name, indexed_at, doc_count, chunk_count, notes
```

Nicht-Reindex-Migration: Schema-Migration + Indexer-Update (schreibt Row bei jedem Index-Run, upsert bei Re-Index), Backfill der existierenden acht Collections aus bekannten Configs in den decisions-MDs. test_db kriegt ihren Eintrag mit den heute aufgenommenen Werten.

Nebeneffekt: `rag-cli list_collections` kann Modell + Chunk-Size mitanzeigen — selbst-beschreibendes System.

**Topic-Splitting:** das ist Infrastruktur-Arbeit die mehrere Pipeline-Steps berührt (Indexing-Pipeline, Retrieval-CLI, Eval-Reports). Eigene OldThemes-Topic `decisions/OldThemes/collections_metadata/` für die Detail-Diskussion. Eval-Thread referenziert nur "wird vorausgesetzt für saubere Sweep-Reports".

## Updated Worker-Pipeline für nächste Etappen

In Reihenfolge der Abhängigkeit:

1. **Methodology-Update** (diese OldThemes plus Update von `decisions/eval01_methodology.md` IST/SOLL plus Schema-Erweiterung `queries_test_db.json` mit Chunk-Indices). Voraussetzung für alles weitere.
2. **Collections Metadata-Tabelle** (Schema-Migration, Indexer-Update, Backfill, Eval-Reports konsumieren die neue Tabelle). Voraussetzung für (4) damit neue test_db-Varianten saubere Provenance haben.
3. **DENSE_SCORE_THRESHOLD entfernen** (mini, klein, kann parallel zu (2) oder als Side-Commit darin).
4. **Chunk-Size-Sweep auf test_db / test_db_2 / test_db_3** mit 2000/1000/512 Chars Chunk-Size, gleiche Source-MDs, gleiche 17 Queries (Chunk-Indices in queries_test_db.json müssen pro Variante mitwandern — entweder neue queries-Files pro Variante oder Schema-Hack mit chunk-size-conditional Index). Eval-Run, Reports, IST-Updates in `decisions/index01_chunking.md`.
5. **`--sweep mode` auf der aktuellen test_db** (separat oder zusammen mit (4)) — beantwortet die SPLADE-Frage final. Reports in `decisions/retrieval03_fusion.md`.
6. **Beads** für MCP Auto-Collection Routing und Graph RAG (Anlage, kein Code diese Session).

(1)-(3) sind diese oder nächste Session machbar. (4) braucht 3× Indexing-Runs + Sweep-Lauf, eigene Session. (5) kann mit (4) zusammen oder separat. (6) am Ende.

## Offene Fragen

- **Chunk-Indices pro Chunk-Size-Variante.** Wenn wir test_db_2 mit chunk_size=1000 indexieren, sind die Chunk-Boundaries andere → derselbe Source-Text liegt an anderen Chunk-Indices. Die `expected_chunks` aus queries_test_db.json sind chunk-size-spezifisch. Lösung muss in der Methodology-Worker-Aufgabe (1) mitkommen: entweder pro test_db-Variante eigene queries-File mit angepassten Indices, oder Eval-Code rechnet "expected_text-span" auf die Variante um (komplizierter, robuster). Vorschlag: pro Variante eigene queries-File (queries_test_db.json, queries_test_db_2.json, queries_test_db_3.json), mechanisch ableitbar aus der Source-MD-Position des expected_snippets.
- **Cross-Document-Queries** (Q16, Q17 in test_db) sind besonders empfindlich gegen die strikte Konstruktions-Definition — wenn beide Source-Docs gefunden werden müssen, ist Recall@K relativ zu 2 nicht 1. Aktuell schon korrekt im neuen Schema (`expected_chunks` als Liste über mehrere Dokumente), aber bei der Migration prüfen ob die existierenden Q16/Q17 wirklich pro Quell-Doc einen oder mehrere Chunks haben.
- **Whether Snippet_Recall Bleibt** — wenn Chunk-Index die Primärmetrik wird, ist Substring-Matching auf den Snippet im Grunde redundant (wenn der Chunk getroffen wurde, war der Snippet ja drin per Konstruktion). Aber als Robustheitstest gegen "System hat den richtigen Chunk gefunden aber falsch zugeschnitten / ein anderer Chunk-Boundary war im Indexing aktiv" lohnt sich's behalten. Klärt sich in Worker (1).

## Quellen

- `decisions/OldThemes/eval_suite/in_progress.md` — vorherige Pending-Liste, durch dieses Doc teilweise abgelöst
- `decisions/OldThemes/eval_suite/process_2026-05-10.md` — Iteration die zur aktuellen Harness führte
- `decisions/eval01_methodology.md` — IST der Eval-Methodologie, muss nach Worker (1) aktualisiert werden
- `decisions/retrieval03_fusion.md`, `retrieval04_reranking.md` — IST der Konfig-Defaults, betroffen vom Sweep-Ergebnis und Threshold-Removal
- `decisions/index01_chunking.md` — IST der Chunk-Size, Ziel der Sweep-Ergebnisse aus (4)
- `decisions/index02_dense_embedding.md`, `index03_sparse_embedding.md` — IST der Modelle, betroffen falls SPLADE-Drop-Entscheidung fällt
- RAG_reference Collection: RAGAS_Evaluation_Framework (LLM-Judge Pattern als Alternative die wir EXPLIZIT NICHT brauchen), RAG_Evaluation_Survey_2025 (Metrik-Taxonomie), Fusion_Functions_Hybrid_Retrieval (NDCG als IR-Standard)
