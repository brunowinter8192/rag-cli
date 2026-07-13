# CC Persisted-Output Threshold — Empirical Investigation

**Date:** 2026-05-10  
**Worker:** persisted-output-probe  
**CC version:** 2.1.114.793 (from `x-anthropic-billing-header` in session log)

---

## 1. Threshold: Exact Value

**30,000 bytes (decimal) — strict upper bound for inline delivery.**

`output_size > 30,000 bytes` → persisted  
`output_size ≤ 30,000 bytes` → inline

The threshold is **30 KB decimal** (1 KB = 1,000 bytes), NOT 30 KiB (1 KiB = 1,024 = 30,720 bytes).

---

## 2. Binary Search: Probe Results

All probes run as `python3 -c "..."` Bash calls. File sizes verified via `wc -c` on persisted output files.

| Target bytes | Actual bytes | Lines | Status    | Log entry |
|-------------:|-------------:|------:|-----------|-----------|
| 30,000       | 30,000       | 2     | **INLINE** | P1  |
| 30,270       | 30,270       | 2     | PERSISTED  | P2  |
| 30,135       | 30,135       | 2     | PERSISTED  | P3  |
| 30,067       | 30,067       | 2     | PERSISTED  | P4  |
| 30,033       | 30,033       | 2     | PERSISTED  | P5  |
| 30,016       | 30,016       | 2     | PERSISTED  | P6  |
| 30,008       | 30,008       | 2     | PERSISTED  | P7  |
| 30,004       | 30,004       | 2     | PERSISTED  | P8  |
| 30,002       | 30,002       | 2     | PERSISTED  | P9  |
| 30,001       | 30,001       | 2     | PERSISTED  | P10 |

Binary search converged in 10 probes: 30,000 inline, 30,001 persisted. Threshold is between these two values — i.e., CC uses `size > 30,000` (not ≥).

**Pre-existing Phase A data points** (from log analysis of historical sessions):

| Actual bytes | Status    | Session |
|-------------:|-----------|---------|
| 29,582       | **INLINE** | searxng_1778102741 |
| 29,415       | **INLINE** | searxng_1778345101 |
| 28,913       | **INLINE** | searxng_1778280216 |
| 30,541       | PERSISTED  | this session (Phase A analysis script) |
| 31,346       | PERSISTED  | searxng_1778102741 |
| 31,334       | PERSISTED  | searxng_1778280216 |

These independently confirm the threshold in the 29,582–30,541 byte range, consistent with 30,000 bytes.

---

## 3. Bytes vs. Lines: Disambiguation

Same byte count tested with 2-line structure (1 marker + 1 long padding) vs. 2,726-line structure (1 marker + 2,724 × "XXXXXXXXXX" + 1 short final line):

| Size    | Lines  | Status     |
|--------:|-------:|------------|
| 30,000  | 2      | **INLINE** |
| 30,000  | 2,726  | **INLINE** |
| 30,001  | 2      | PERSISTED  |
| 30,001  | 2,726  | PERSISTED  |

**Conclusion: Line count has NO effect. Only byte count determines the threshold.**

---

## 4. Proxy Log Analysis

**Log file:** `api_requests_worker_8e6b2517_persisted-output-probe_1778447076.jsonl`  
`/Users/brunowinter2000/Documents/ai/Monitor_CC/src/logs/`

**How the log captures persisted vs. inline:**

- **Inline:** `raw_payload.messages[N].content[K].content[0].text` = full output. The logged `text` has 1 fewer byte than the raw output (CC strips trailing `\n` when constructing API messages).
- **Persisted:** `raw_payload.messages[N].content[K].content[0].text` = 240-byte wrapper:
  ```
  <persisted-output>
  Output too large (29.3KB). Full output saved to: /Users/brunowinter2000/.claude/projects/.../.../tool-results/<id>.txt
  </persisted-output>
  ```

**KB reporting format:** `reported_kb = actual_bytes / 1024`, rounded to 1 decimal. Example: 30,001 bytes → "29.3KB" (30,001/1024 = 29.30). This means the reported KB can appear *smaller* than the round-number threshold — e.g. "29.3KB" is above the 30,000-byte limit. Do not rely on the KB number in the wrapper for threshold reasoning.

**All 14 persisted outputs confirmed in session log:**
- 3 from Phase A analysis scripts (unintentional probes)
- 11 from binary search + disambiguation probes
- File sizes all match the computed output sizes to the byte

**Session identification:** The log file is named per session (`worker_8e6b2517_persisted-output-probe`). Probes used marker `PROBE_<size>_<utc_ts>` as first line for exact identification.

---

## 5. rag-cli Output Size: Empirical Measurement

**Source:** Session log `api_requests_opus_rag_1778440771.jsonl`, search result with 7 chunks.

**Per-result format:**
```
--- Result N (score: 0.XXXXX) ---
Collection: <name> | Document: <path> | Chunk: N
<chunk content — up to 2000 chars>
```

**Empirically measured per-result sizes:**

| Result | Bytes |
|-------:|------:|
| 1      | 2,090 |
| 2      | 2,080 |
| 3      | 1,387 ← shorter chunk (doc boundary) |
| 7      | 2,092 |

**Average across 56 results (5 sessions):** 1,831 bytes/result  
**Max observed for full-length chunks:** ~2,092 bytes/result

**Overhead breakdown per full-length result:**
- Header: `--- Result N (score: X.XXXXX) ---\n` ≈ 33–36 bytes
- Metadata: `Collection: X | Document: Y | Chunk: Z\n` ≈ 50–80 bytes (varies by path length)
- Content: up to 2,000 chars (2,000 bytes for ASCII; more for multi-byte UTF-8)
- Total overhead beyond content: ~90 bytes

---

## 6. rag-cli Recommendation

**Current retriever.py behavior:**

```python
DEFAULT_TOP_K = 5
top_k = max(top_k, 20)   # clamped minimum of 20
top_k = min(top_k, 50)   # clamped maximum of 50
```

`rag-cli search_hybrid` always returns **20–50 results** regardless of `--top-k` input below 20.

**At minimum (20 results, max per-result size 2,092 bytes):**  
20 × 2,092 = **41,840 bytes → always PERSISTED** (40% over threshold)

**At 50 results:**  
50 × 2,092 = **104,600 bytes → PERSISTED** (3.5× over threshold)

**To stay inline:** ≤ **13 results** (13 × 2,092 = 27,196 bytes — leaves ~9% margin to threshold)

**Practical recommendation:**

| Scenario | top_k | Est. output | Status |
|----------|------:|------------:|--------|
| Current default (min 20) | 20 | ~38,000 bytes | PERSISTED — always |
| Safe inline | ≤ 13 | ≤ 27,196 bytes | **INLINE** |
| Comfortable margin | 10 | ~20,920 bytes | **INLINE** |
| Aggressive inline | 14 | ~29,288 bytes | INLINE (tight margin) |

**Blocker:** `retriever.py` clamps `top_k ≥ 20`. To make `--top-k 10` or `--top-k 13` effective for inline delivery, change:

```python
# Current
top_k = max(top_k, 20)

# Proposed
top_k = max(top_k, 5)    # allow lower top_k for inline use cases
```

This change is needed in all three workflow functions (`dense_workflow`, `hybrid_workflow`, `bm25_workflow`).

**Without this change:** All rag-cli output is persisted. Workaround: always follow up with `grep` or `Read` on the persisted file path.

---

## 7. Log Sample Excerpts

**Session log path:**  
`/Users/brunowinter2000/Documents/ai/Monitor_CC/src/logs/api_requests_worker_8e6b2517_persisted-output-probe_1778447076.jsonl`

**Inline tool_result (P1, 30,000 bytes raw / 29,999 logged):**  
Entry 96 in session log. `raw_payload.messages[-1].content[0].content[0].text` starts:
```
PROBE_30000_1778447817
XXXXXXXXXXXXXXXXXXXX...
```
Length in API message: 29,999 bytes (trailing `\n` stripped by CC).

**Persisted tool_result (P10, 30,001 bytes):**  
File: `...tool-results/byk4pojbe.txt` — 30,001 bytes, 2 lines.  
Wrapper seen in subsequent API requests (entry 129+):
```
<persisted-output>
Output too large (29.3KB). Full output saved to: /Users/brunowinter2000/.claude/projects/-Users-brunowinter2000-Documents-ai-Meta-ClaudeCode-MCP-RAG--claude-worktrees-persisted-output-probe/ec33b0da-b330-4f78-95c9-82a2925a1207/tool-results/byk4pojbe.txt
</persisted-output>
```

**Historical reference — searxng session 1778102741:**  
Log: `api_requests_opus_searxng_1778102741.jsonl`  
- Entry 47: inline Bash result, 29,582 bytes (largest inline in that session)  
- Entry 36: persisted result, actual file size 31,346 bytes (`bdri98499.txt`)  
- File: `/Users/brunowinter2000/.claude/projects/-Users-brunowinter2000-Documents-ai-Meta-ClaudeCode-MCP-searxng/54199c6f-8978-44da-9ccb-c01103d8bb45/tool-results/bdri98499.txt`

---

## 8. Summary

| Question | Answer |
|----------|--------|
| Exact threshold | **30,000 bytes** (decimal) |
| Trigger condition | `raw_output_size > 30,000` |
| Line count effect | **None** — only bytes matter |
| KB unit | Decimal (30,000 B = 30 KB, not 30 KiB = 30,720 B) |
| Confidence | Exact — binary search converged to 1-byte gap (30,000 inline, 30,001 persisted) |
| rag-cli default output | 20–50 results ≈ 38,000–104,000 bytes → **always persisted** |
| Safe top-k for inline | **≤ 13** results (requires `retriever.py` clamping change) |
| Current workaround | Accept persisted-output; always `grep`/`Read` the file path |
