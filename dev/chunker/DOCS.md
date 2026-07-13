# dev/chunker/

## Role

Audit scripts for evaluating chunker output quality. Currently focused on verbatim-quote coverage — whether eval ground-truth identifying_quotes exist as verbatim substrings in indexed chunks.

## Scripts

### A_quote_coverage.py

**Purpose:** For each `identifying_quote` in a query-set JSON, check whether it appears verbatim (single-chunk), spans a chunk boundary (boundary-split), or is absent from the index.

**Usage:**
```bash
./venv/bin/python dev/chunker/A_quote_coverage.py
```

**Output:** `dev/chunker/md/coverage_<timestamp>.md`

Report sections: summary stats (single/boundary/missing counts), per-query status table, detail section for boundary and missing cases, index-mismatch detail (quote found in unexpected chunk).

**Configured for:** `test_db` collection on `rag_test` postgres DB, queries from `dev/retrieval/queries_test_db.json`. To run on a different collection/query-set, change `COLLECTION` and `QUERIES_PATH` constants at the top of the script.
