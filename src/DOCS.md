# src/

## Role
Package root for the RAG pipeline source. Holds only the package marker and the `rag/` package; all pipeline logic lives in `rag/`. Touch nothing here directly; see `rag/DOCS.md`.

## Public Interface
`__init__.py` is empty. Callers import from the sub-package, e.g. `from src.rag.<module> import <name>`.

## Flow
No flow at this level; the pipeline flow (retrieval, indexing, sync, server lifecycle) is described in `rag/DOCS.md`.

## Modules
None. `src/` contains no modules of its own beyond the empty `__init__.py`.

## State
None owned.
