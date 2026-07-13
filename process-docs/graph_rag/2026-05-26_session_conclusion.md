# Graph RAG — Session-Konklusion (2026-05-26)

## Kontext

Bead `RAG-3h3` aufgemacht zur Diskussion. Im 2026-05-24 Scoping waren zwei Richtungen unterschieden: A (Projekt-Visualisierung als Graph) vs B (Graph-augmented Retrieval / klassisches GraphRAG-Paradigma). Erste Indikation damals: A primär, B optional später. Diese Session hat zu beiden Richtungen eine Entscheidung getroffen.

## Was Richtung B (Graph-augmented Retrieval) konkret ist

Über die Scoping-Doc-Kurzbeschreibung hinaus präzisiert:

**Indexing-Phase.** Jeder Chunk wird durch einen LLM gejagt mit dem Prompt „extrahiere Entitäten und Relationen". Output: typed Entities (z.B. `Reranker`/Component, `Qwen3-Reranker-0.6B`/Model, `snippet recall 97%`/Metric) plus Relations (`(Reranker)-[USES_MODEL]->(Qwen3-Reranker-0.6B)`, `(decisions/retrieval04_reranking.md)-[CITES]->(Qwen3-Paper)`). Entities + Relations landen in einer Graph-DB (Neo4j, NetworkX in-memory, oder einfacher: JSON/SQLite mit Edge-Tabelle). Vektor-DB bleibt parallel bestehen.

**Query-Phase.** Zwei Pfade simultan: (1) klassische Vektor-Suche auf Chunks, (2) Entity-Extraction aus der Query plus Graph-Traversal von matched Entities zu N-Hop-Nachbarn. Beide Treffer-Mengen werden gemerged, dedupliziert, gerankt → Top-K an LLM.

**Was es bringt.** Multi-Hop-Queries („welche Decisions zu X zitieren auch Quelle Y"), compositional Queries, abstrakte Themenfragen — Antworten die rein semantisch im Embedding-Raum nicht zuverlässig erreichbar sind, weil die Verbindung strukturell ist (`CITES`, `USES_MODEL`, `SUPERSEDES`) nicht semantisch.

**Was es kostet.** LLM-Call pro Chunk beim Indexing (linear skalierend), Graph-DB als zusätzlicher Storage-Layer, Entity-Extraction-Prompt-Tuning, Traversal-Logik plus Merging mit Vektor-Treffern. Implementations-Aufwand: mehrere Tage. Maintenance bei jedem `update_docs`-Lauf: neue Chunks müssen extrahiert werden.

## User-Einwand: B ist visualisierbar

Bisher implizit angenommen war B = unsichtbar (Daten-Struktur intern). User: der intern aufgebaute Knowledge Graph IST visualisierbar — als Mermaid-Diagram, als 3D Force-Directed Graph, wie auch immer. Stimmt technisch. Das Force-Directed-Graph-Bild das gezeigt wurde (vermutlich Obsidian-Vault-Style, pinke Knoten = Dokumente, blaue Knoten = Hubs mit hoher Konnektivität, hellblauer Cluster = selektierter Knoten + Nachbarn) wäre prinzipiell aus B's Entity-Graph genauso renderbar wie aus A's Code-Symbol-Graph.

Praktisch landen A und B aber an unterschiedlichen Layern des Projekts: A operiert auf File-Level (Module, Decisions, OldThemes als Knoten), B operiert auf Entity-Level (extrahierte Begriffe / Konzepte als Knoten). Beide Visualisierungen wären gleichzeitig möglich aber sie zeigen unterschiedliche Topologien.

## Entscheidung: Beide Richtungen deferred

**Kernargument gegen B: Maintainability für ständig wachsende Projekt-Docs.**

GraphRAG-Paradigmen (Microsoft GraphRAG, LightRAG, nano-graphrag) sind für **feste Daten-Korpora** designed — wissenschaftliche Paper-Sammlungen, Knowledge-Bases, statische Dokumentations-Korpora. Indexing einmal teuer, dann steht der Graph. Bei einem aktiv entwickelten Projekt mit decisions/, OldThemes/, DOCS.md die sich mit jeder Session ändern, kippt die Kostenrechnung:

- Bei jeder Doc-Änderung muss die Entity-Extraktion neu laufen → laufender LLM-Cost
- Entity-Extraktions-Fehler in einer einzigen Doc-Edit pflanzen sich in den Graph fort → verzerrte Retrieval-Ergebnisse bei zukünftigen Queries
- Conceptual Overhead beim Schreiben: jede neue Doc zwingt zur impliziten Frage „wie hängt die mit X, Y, Z zusammen" damit die Relations vollständig sind — sonst wird die nächste Multi-Hop-Query nicht finden was sie finden sollte
- Korrekturen am Graph (z.B. wenn eine Entity falsch extrahiert wurde) sind teuer und nicht trivial sichtbar — der Graph ist nicht das Primär-Artefakt das man pflegt

**B passt zu festen Korpora, nicht zu lebenden Projekt-Docs.** Wenn das RAG-Projekt mal in einen Zustand kommt wo es weniger aktiv wächst und mehr als Wissens-Archiv genutzt wird, ist B plausibler. Aktuell ist es das genaue Gegenteil — Projekt-Docs ändern sich pro Session.

**Direction A (Visualisierung) ist appealing aber kein primärer Hebel jetzt.** Das Force-Directed-Graph-Bild würde Orientierung geben, ja. Aber: in der aktuellen Projekt-Größe (~10 src/-Module, ~30 decisions+OldThemes-Files) ist die textuelle Navigation über RAG + DOCS.md + Bead-Source-Inventory funktional. Der Graph würde das nicht-essential ersetzen sondern ergänzen.

## Was bleibt: aktuelles System verfeinern

User-Statement explizit: „erstmal das aktuelle System produktiv weiter testen bevor man wieder ein neues feature added — lieber das jetzt verfeinern und verbessern". Die hier sichtbaren strukturellen Hebel:

- **Indexing-Setup:** chunker-Konfiguration (chunk-size, overlap), document-format-aware Splitting wenn die Korpora das verlangen
- **Retrieval-Setup:** dense+rerank ist seit `f8f35c0` (2026-05-26) der einzige Prod-Pfad. RERANK_CANDIDATES=30 fixiert (Phase B Plateau)
- **Modelle:** Qwen3-Embedder-8B + Qwen3-Reranker-0.6B als aktuelles Set. Wo es noch echte Hebel gibt, hängen sie eher an Modell-Updates / Modell-Vergleichen als an Architektur-Änderungen

User-Einschätzung: „ich sehe gerade wenig Hebel die es nicht verkomplizieren". Das ist eine valide IST-Beschreibung. RAG-Systems-Komplexität ist nicht das was die aktuelle Retrieval-Qualität bremst — die wichtigen Trade-offs (rerank vs no-rerank, fusion vs dense-only, top_k=12) sind durchmessen und festgelegt. Was bleibt sind Eval-Erweiterung (test_db ausbauen, cross-domain Queries) und Modell-Beobachtung.

## Status

Beide Richtungen (A + B) deferred. Bead `RAG-3h3` bleibt offen als Marker für „später wenn das Projekt deutlich größer wird ODER aufhört aktiv zu wachsen" — beides verschiebt die Kostenrechnung gegen die aktuelle Lage.

Reopen-Trigger wären:
1. Projekt wächst auf ein Volumen wo textuelle Navigation nicht mehr reicht (~50+ Module + ~100+ Decisions/OldThemes)
2. Projekt geht in Maintenance-Modus über (Docs ändern sich nicht mehr ständig) — dann wird B's Indexing-Kostenrechnung tragbar
3. Compositional Queries werden zum Pain Point („welche Decisions zu X zitieren auch Quelle Y") — Vektor-Suche allein liefert dann nicht mehr aus

Bis dahin: keine Aktion.

## Quellen

- `decisions/OldThemes/graph_rag/2026-05-24_scoping.md` — initiale Scoping-Doc, Richtungs-Trennung A/B, Tools-Übersicht
- `decisions/OldThemes/project_viz_layer.md` — ältere (2026-05-11) Variante der Visualisierungs-Diskussion mit dep-tree als konkretem Tool-Kandidaten und gescheitertem brew-install (reopen-path dokumentiert)
- Microsoft GraphRAG, HKUDS/LightRAG, gusye1234/nano-graphrag — die drei kanonischen B-Implementierungen; bislang nicht im RAG_reference indexiert
