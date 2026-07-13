# Server Management — Constellation Design (2026-05-25)

## Pain (Discovery Path)

`--sweep-cross mode top_k` mit 11 Modi auf test_db sollte cc+rerank-8b vs cc+rerank-0.6b vs dense+rerank-{0.6b,8b} vergleichen. Tatsächliches Ergebnis: 6 von 11 Modi liefen sauber (alle no-rerank plus dense+rerank-0.6b mit 97% snippet_recall — bester sauberer Datenpunkt), 5 von 11 Modi (alle rerank-Varianten außer dense+rerank-0.6b) returned 0% snippet_recall durchgehend.

Log-Analyse zeigte zwei separate Failure-Modes die zusammen das Bild produzierten:

**Mode A — httpx-timeouts in eval-client:** Reranker-8b processing erhielt 50 Kandidaten-Pairs pro Query, server-side begannen sich Tasks zu queuen (im Log: cancel events für task_ids 4747-4795, nur ONE successful response am Ende). Eval-side httpx default timeout 300s lief ab, Eval cancelled die Connection, Server cancelled den Task. Cascadiert auf alle 50 Pairs jeder Query. Aufgrund von GPU-Memory-Druck (siehe Memory-Analyse unten) waren Per-Query-Latencies dramatisch höher als die theoretisch berechneten ~10s.

**Mode B — Watchdog killed servers mid-stress:** `IDLE_TIMEOUT=3600s` in `src/rag/server_utils.py:26`. Watchdog checkt state-file mtime in `~/.rag-locks/server-port-{N}.json`. Mtime wird nur via `_touch_state_file(port)` aktualisiert — und dieser Call passierte in Client-Modulen NACH erfolgreichem httpx-Response, nicht VOR dem Request. Failing requests bumpten die mtime nicht. Sweep dauerte ~57min total, davon ~9min produktive Aktivität auf reranker-0.6b (configs 26-30 dense+rerank-0.6b), dann Stille während die rerank-8b Modi failten. Watchdog kalkulierte reranker-0.6b idle > 60min und killte ihn — ab Mode cc+rerank-0.6b (Config 36) waren die Errors dann "Connection refused" statt "timed out", weil der Server wirklich weg war.

## Root Cause Analyse

### Memory Math auf M4 Pro 48GB

Geschätzte VRAM-Footprints (aus llama_memory_breakdown_print + Modell-Sizes):

| Server | Modell-Weights | KV-Cache (4 slots × 32k ctx) | Compute-Buffer | Total |
|---|---|---|---|---|
| embedding-8b | 7.7 GB | 0 (2k ctx, 1 slot) | ~500 MB | ~9 GB |
| reranker-0.6b | 600 MB | ~3.6 GB | ~600 MB | ~5 GB (vs ~1 GB ohne KV) |
| reranker-8b | 7.7 GB | ~4.6 GB | ~2.9 GB | ~15 GB (vs ~9 GB ohne KV) |
| splade | ~500 MB | 0 | ~100 MB | ~600 MB |
| generator-4b | ~4 GB | ~2 GB | ~1 GB | ~7 GB |

Metal-VRAM-Slice auf M4 Pro: ~36 GB von den 48 GB Unified Memory. Gleichzeitiger Run von embedding-8b + reranker-8b + splade + reranker-0.6b (was tatsächlich beim Sweep zeitweise passierte): ~9 + 15 + 0.6 + 5 = ~30 GB. Bereits 83% des Metal-Budgets, plus OS, plus Postgres, plus compute-temporaries die zur Laufzeit zusätzlich allokiert werden. Effekt: Memory-Bus-Stalls, Metal Context-Switching zwischen den Prozessen (Metal parallelisiert nicht über Prozesse hinweg, nur innerhalb), Catastrophic Slowdown.

Per-Query-Latency die wir aus dieser Memory-Pressure-Lage erwarten würden: nicht die ~10s die das Modell isoliert braucht, sondern eher 60-90s — gerade noch unter dem 300s-Timeout aber mit Schwankungen die ihn regelmäßig überschreiten.

### Warum -np 4 das Hauptproblem für Reranker war

llama-server Default ist `n_parallel = 4` (kein explizites `-np` Flag setzt -np = 4). Jede Parallel-Slot allokiert eigenen KV-Cache auf dem konfigurierten `-c 32768` Context. Damit kostet ein einziger reranker-8b-Server ~4.6 GB KV-Cache ZUSÄTZLICH zu den ~7.7 GB Modell-Weights. Mit `-np 1` würde der KV-Cache auf ein Viertel sinken (~1.1 GB), Gesamt-VRAM-Footprint von 15 GB auf ~9 GB — passt deutlich besser ins Memory-Budget.

Die Rerank-Workloads in unserem Pipeline kommen ohnehin sequenziell aus dem Eval-Orchestrator (50-Pair-Batch pro Query, eine Query nach der anderen). Parallel-Slots beim Reranker bringen also keinen Throughput-Gain — sie sind reines Memory-Waste. Setting `-np 1` ist die einzige sinnvolle Konfiguration für unseren Use Case.

## Design-Diskussion (vier Optionen, entschiedene Richtung)

### Optionen die diskutiert wurden

**A — Class-Exclusivity allein.** Pro Klasse läuft genau eine Variante. ensure_ready("reranker-8b") stoppt vorher reranker-0.6b. Adressiert NICHT die cross-class Memory-Konflikte (embedding-8b + reranker-8b bleiben parallel startbar).

**B — Configurable `exclusive_with` per Preset.** Jeder Preset trägt eine Liste konflikt-erzeugender anderer Presets. Daten-getrieben über das Config-Dict, in einer einzigen Datei lesbar. ensure_ready durchläuft die Liste vor Start und stoppt alle Konflikte automatisch.

**C — Memory-Budget mit LRU-Eviction.** Jeder Preset hat eine `memory_gb` Annotation, globales Budget (~30 GB), ensure_ready stoppt LRU-Server wenn neues Starten Budget sprengen würde. Smart, robust gegen zukünftige Preset-Additions, mehr Code-Komplexität.

**D — Explicit Profile-Mode.** User/Code wechselt aktiv Profile (`rag-cli profile use rerank-8b-eval`). Maximal explizit, zwingt jeden Caller das Profil zu setzen.

### Entschieden: B + Idle-Detection-Fix + `-np 1`

Begründung pro B: das `exclusive_with` Feld ist deklarativ, jeder kann in der Config-Datei nachlesen welche Kombinationen incompatible sind und warum. Cross-Class Exklusivität wird OPTIONAL — z.B. `reranker-8b.exclusive_with: ["reranker-0.6b", "embedding-8b"]` falls Messungen zeigen dass die Konstellation kaputt ist. Caller müssen nichts wissen. Wartbar.

Pro Idle-Detection-Fix (höchste Prio): `_touch_state_file` muss VOR dem httpx-Post passieren, nicht nach Success. Damit zählt jeder eintreffende Request als "Server lebt", auch wenn er timeoutet. Watchdog kann nicht mehr während Stress-Phasen fälschlich killen. Einfacher 3-Datei-Change in Client-Modulen, sehr großer Impact auf Robustheit.

Pro `-np 1` auf beide Reranker-Presets: kein Throughput-Verlust für unseren sequenziellen Workload, drastisch reduzierter Memory-Footprint, primärer Single-Lever-Win.

Optionen A, C, D verworfen: A löst nur halbes Problem. C ist Overkill für 6 statische Presets (kein dynamic preset registration). D zu invasiv für die existierenden Caller in embedder/sparse_embedder/reranker.

### Cross-Class Exklusivität: PENDING auf Messdaten

Wir tragen ABSICHTLICH KEINE cross-class `exclusive_with` Einträge ein bevor wir empirische Daten haben. Stattdessen schreiben wir ein Dev-Measurement-Script das systematisch jede sinnvolle Konstellation aktiviert und VRAM + Latency + Stabilität misst. Daten zeigen uns:

- Welche Konstellationen sind stabil bei akzeptabler Latency
- Wo brauchen wir Cross-Class-Exclusivity (z.B. "wenn reranker-8b gestartet wird, stoppe embedding-8b automatisch")
- Wo lohnen sich Per-Mode-Swaps gegenüber paralleler Permanenz (Lade-Zeit vs Latenz-Improvement)

Erst NACH Daten werden die `exclusive_with` Listen final konfiguriert.

## Per-Mode-Swap vs Per-Query-Swap (Sub-Diskussion)

Theoretisch könnten wir Server-Swaps pro QUERY machen — vor jedem rerank-8b call: embedding-8b out, reranker-8b in, rerank durchführen, reranker-8b out, embedding-8b in für nächste Query. Total deterministisch nie mehr als ein großes Modell in VRAM.

Praktisches Problem: GGUF-Loading für 8B-Modelle braucht 5-10s. Per-Query-Swap heißt 10-20s reine Lade-Latenz pro Query, plus die eigentliche Inferenz. Bei einem 17-Query-Sweep wäre das 200-400s nur fürs Swappen.

Per-Mode-Swap ist die richtige Granularität: bei Sweep-Start "cc+rerank-8b" einmal embedding-8b → reranker-8b swappen, dann alle 85 Queries der Mode-Phase (17 × 5 top_k) ohne weitere Swaps. Wechsel zur nächsten Mode → ein Swap. Swap-Kost amortisiert auf 85 Queries = vernachlässigbar.

**Implikation:** der Eval-Orchestrator (oder ein wrapping pre-flight Script) sollte vor jedem Mode entscheiden welche Server gebraucht werden und entsprechend swappen. ensure_ready mit exclusive_with macht das automatisch wenn der Caller den richtigen Server requestet. Pro Production-Query-Pfad kann eine fixe Constellation hardcoded sein (z.B. embedding-8b + splade + chosen reranker), Server-Manager hält das stabil.

## Messplan — was die Profile-Script-Daten beantworten müssen

Konstellationen die das Script in `dev/server_management/A_constellation_profile.py` profilen wird:

1. embedding-8b-solo
2. embedding-0.6b-solo
3. embedding-8b + splade
4. embedding-8b + reranker-0.6b
5. embedding-8b + reranker-0.6b + splade (volle Production-Default-Konstellation)
6. embedding-8b + reranker-8b (DIE Frage — funktioniert das überhaupt?)
7. embedding-8b + reranker-8b + splade (Volle Konstellation mit 8B Reranker)
8. embedding-0.6b + reranker-8b (Fallback wenn 8B+8B nicht geht — kleineres Embedding plus großes Rerank)

Pro Konstellation gemessen:
- VRAM-Footprint nach allen Server-Loads (state-stable nach 30s warm-up)
- Cold-Query-Latency (first 5 queries nach Server-Start — capture warmup-cost)
- Warm-Query-Latency (50 sequential queries — mean, p50, p95, p99, max)
- Stability (timeout count, latency drift über die 50 queries — wächst die Latenz monoton?)

Empirische Entscheidungs-Grundlage die wir aus den Daten ableiten:
- Falls embedding-8b + reranker-8b stabile akzeptable Latenz hat (p95 < 30s zB) → reranker-8b parallel laufen lassen ist OK, kein cross-class exclusive_with nötig, eval kann normal sweepen
- Falls embedding-8b + reranker-8b unstable / Timeouts hat → cross-class exclusive_with zwingt swap, eval muss per-mode swappen
- Falls embedding-0.6b + reranker-8b sauber läuft → das ist eine viable Sweep-Konstellation für 8B-Reranker-Vergleiche
- Falls reranker-8b auch solo schon schlecht performt → Hardware-Limit, reranker-8b ist auf M4 Pro 48GB nicht praktikabel und sollte aus den Production-Optionen rausfallen

## Was diese Session NICHT macht

- Script wird geschrieben aber NICHT ausgeführt. Empirisches Profiling = nächste frische Session.
- Eval-Sweep nicht neu gestartet. Sweep wartet auf Profil-Daten zur Konstellations-Wahl.
- Cross-Class `exclusive_with` Einträge nicht gesetzt. Erst nach Daten.
- Production-Code in `cli.py` / `retriever.py` nicht angepasst. Hardfix-Worker für top_k=12 / cc+rerank-mode kommt SPÄTER, nach Eval-Re-Run mit klaren Sieger-Konfig.

## Nächste Session — Workflow

1. Run `./venv/bin/python dev/server_management/A_constellation_profile.py --all` — produces `dev/server_management/A_constellation_profile_reports/profile_*.md`
2. Lies Report, entscheide:
   - Welche Konstellationen sind stabil → eval-bare
   - Brauchen wir cross-class `exclusive_with` Einträge → ergänzen wenn ja
   - Sollten wir `-c` weiter reduzieren auf den Rerankern (32k → 8k oder 4k) für noch kleineren Footprint
3. Sequenzielle Eval-Sweeps mit der gewählten Konstellation pro Mode-Gruppe (Server-Swap zwischen Mode-Gruppen). Re-run der 5 ausgefallenen Modi auf test_db. Wenn 8B-Reranker stabil läuft auch test_db_2 + test_db_3 erweitern.
4. Nach saubrem Sweep: Sieger-(mode, top_k)-Hardfix in retriever.py + cli.py + tool-use.md

## Quellen

- `decisions/box_architecture.md` — IST der Server-Architektur, wird in dieser Session vom Worker geupdated
- `decisions/OldThemes/eval_suite/methodology_clarification_2026-05-24.md` — Eval-Methodologie-Baseline (binäre Relevanz, snippet_recall primary)
- `decisions/OldThemes/eval_suite/2026-05-24_phase_a_queries_sample.md` — Query-Schema mit chunk_index + identifying_quote
- `dev/retrieval/A_retrieval_eval_reports/cross_mode_top_k_test_db_20260525_004613.md` — original test_db Sweep (7-Modi, vor Schema-Erweiterung)
- `dev/retrieval/A_retrieval_eval_reports/cross_mode_top_k_test_db_20260525_022544.md` — der teilweise-failed 11-Modi-Sweep der diese Diskussion ausgelöst hat
- Server-Manager Logs: `~/.rag-locks/logs/server_manager.log` (Watchdog-Events), `~/.rag-locks/logs/llama-port-{N}.log` (per-Server llama-Aktivität, inkl. memory_breakdown_print am Exit)
- RAG_reference Collection: keine direkten Quellen für dieses Topic (RAG-spezifisch hardware-eval, kein Paper deckt das)
