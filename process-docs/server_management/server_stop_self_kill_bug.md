# `rag-cli server stop` Self-Kill via Port-Based PID Lookup

**Datum:** 2026-05-25
**Commits:** c6f9269 (lsof LISTEN), d1a12c9 (stop() state-file-only)
**Scope:** `src/rag/server_lifecycle.py::stop()`, `src/rag/server_utils.py::find_all_pids_on_port`

## Symptom

Worker `eval-sweep` (Sonnet) starb zweimal in Folge nach dem Emit eines Bash tool_use für `rag-cli server stop`. Beide Deaths exakt **~10 Sekunden nach dem tool_use**, status 143 (SIGTERM), kein `tool_result` im JSONL.

Death 1: 2026-05-25 18:56:43
Death 2: 2026-05-25 19:31:14

Pattern reproduzierbar. Ausgeschlossen als Ursachen: OOM-watchdog (Threshold 26 GB nie überschritten, letzter Kill 4. Mai), Monitor_CC menubar bg_timer abort (killt nur sleep-PIDs nicht Worker), PreToolUse-Hooks (kein Signal-Senden in irgendeiner Hook-Quelle), proxy_addon.py (keine Bash/tool_use-spezifische Reaction-Logik).

## Root Cause

`stop(name)` in `src/rag/server_lifecycle.py:118-126`:

```python
url = find_server_url(name)
port = int(url.split(":")[-1]) if url else cfg["default_port"]  # ← (1) Fallback auf hardcoded default_port
pids = find_all_pids_on_port(port)                              # ← (2) lsof returnt alle Port-Toucher
for pid in pids:
    os.kill(pid, signal.SIGTERM)
```

Zwei Komponenten kombiniert zum Self-Kill:

**(1) Default-Port-Fallback bei nicht-running Servern.** `stop_all()` iteriert alle Server-Presets (auch nicht-running). Für nicht-running fällt `stop()` auf `cfg["default_port"]` zurück. Beispiel: reranker-0.6b nicht running → port = 8082.

**(2) `find_all_pids_on_port` via `lsof -ti :PORT` matched ALLE Prozesse die den Port berühren** — sowohl Listener als auch outbound TCP-Connectors. Ohne `-sTCP:LISTEN`-Flag.

**Kollision:** Der Worker-spezifische mitmproxy lebte auf Port 8082 (weil Port 8081 zu dem Zeitpunkt vom Trading-Session-mitmproxy belegt war; `_worker_proxy_setup` wählt `main_port + 1` und walked bis free port gefunden). 8082 = reranker-0.6b default_port = Kollision.

Worker's claude.exe hatte HTTPS_PROXY=http://localhost:8082 gesetzt — outbound Connection auf 8082 etabliert. `lsof -ti :8082` returnte beide PIDs: mitmproxy (Listener) UND claude.exe (Connector).

`os.kill(claude.exe_PID, SIGTERM)` → Worker killt sich selbst.

## Smoking Gun

`~/.rag-locks/logs/server_manager.log`:

```
2026-05-25 19:31:05,389 - INFO - Stopping embedding-8b (PIDs [41662]) on port 8081...
2026-05-25 19:31:06,055 - INFO - Stopping reranker-0.6b (PIDs [2013, 2022]) on port 8082...
```

- PID 41662 = **Trading-Session's mitmproxy** (collateral damage durch embedding-8b default_port 8081 collision)
- PID 2013 = worker mitmproxy (listener auf 8082)
- **PID 2022 = worker claude.exe (HTTPS_PROXY-Connection auf 8082)** ← Self-Kill

Bestätigt durch Logger-Death-Snapshot in `dev/server_management/B_real_smell_reports/` (via iterative-dev plugin's worker_logger.sh).

## Fix — zwei Commits

### Commit c6f9269 — `find_all_pids_on_port` LISTEN-only

`src/rag/server_utils.py:154`:
```python
["lsof", "-ti", f":{port}", "-sTCP:LISTEN"]
```

Defensiv. Schützt auch andere Aufrufer (`status()`, `start_arbitrary()`, `_wait_for_health()`) vor zukünftigen Connector-Collisions.

### Commit d1a12c9 — `stop()` State-File-Only

`src/rag/server_lifecycle.py::stop()` komplett rewritten. Iteriert `~/.rag-locks/server-port-*.json`, matched auf `name`-Feld, ruft existierendes `_stop_by_state(state, sf, ...)` (kapselt SIGTERM→SIGKILL-Eskalation + State-File-Cleanup). Wenn kein State-File für den Namen: `return False` mit "not running" log.

**Komplett eliminiert:**
- `find_server_url(name)` → port lookup
- `cfg["default_port"]` Fallback
- `find_all_pids_on_port(port)` Aufruf

Removed-Imports: `os`, `signal`, `find_all_pids_on_port`, `_allocate_port` (nicht mehr benötigt).

Net change: −34/+15 Zeilen.

## Architektur-Entscheidung — `default_port` bleibt für `start()`

Option B aus der Worker-Phase-A-Diskussion gewählt: `default_port`-Feld bleibt in `SERVERS` dict für `start()` als "preferred start port" (start versucht default first, fällt auf free port zurück wenn busy). NUR `stop()` wurde vom default_port-Fallback befreit.

**Begründung:** Konsistente default-Ports erleichtern Logs/Status-Display ("embedding-8b auf 8081" als bekanntes Mapping). Dynamic-allocation-from-start würde jede Restart-Sequenz unvorhersagbar machen ohne Bug-Fix-Mehrwert (der Bug saß nur im stop-Path).

## Offene Folge-Arbeit

- `status()` hat dieselbe default_port-Fallback-Logik aber nur fürs Display (kein Kill). Less dangerous, aber für Konsistenz später angleichen. Nicht Teil dieses Fixes.
- `decisions/box_architecture.md` IST muss aktualisiert werden für die neue `stop()`-Semantik (state-file-only, kein port-fallback). Folge-Recap-Aufgabe für den eval-sweep Worker wenn er den Phase-1+2-Sweep abgeschlossen hat.

## Quellen

- `~/.rag-locks/logs/server_manager.log` — die "Stopping reranker-0.6b (PIDs [2013, 2022])" Zeile
- Logger-Snapshot `worker_logger.sh` (via iterative-dev plugin): `eval-sweep_20260525_192702_revive_DEATH.txt` mit Process-Tree, vm_stat, JSONL-Tail
- Cross-Projekt: `decisions/OldThemes/worker_revive_proxy_and_logger.md (iterative-dev)` — Diagnostic-Logger der die Death-Captures geliefert hat
- Bead-Pointer: RAG-8r8 (server constellation profiling + eval sweep)
