# INFRASTRUCTURE
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import httpx

import p1_chunker as _chunker
import p5_indexer as _indexer
import p4_db as _db

EMBEDDING_HEALTH_URL = os.getenv("EMBEDDING_HEALTH_URL", "http://localhost:8081/health")
SPLADE_HEALTH_URL = "http://localhost:8083/health"
VECTOR_DIM = 1024

EMBEDDING_MODEL = "Qwen3-Embedding-8B"
EMBEDDING_DIMS = 4096    # full stored dimension; MRL truncation (1024d) is retrieval-time only
SPARSE_MODEL = "naver/splade-v3"
DB_NAME = "rag_test"


# ORCHESTRATOR

def run_index(source_dir: str, collection: str, chunk_size: int, overlap: int) -> None:
    _check_servers()

    _chunker.CHUNK_SIZE = chunk_size
    _chunker.OVERLAP = overlap

    source_path = Path(source_dir)
    if not source_path.is_dir():
        print(f"ERROR: source-dir does not exist: {source_dir}")
        sys.exit(1)

    conn = _db.get_connection("rag_test")
    _db.ensure_schema(conn, VECTOR_DIM)
    _db.ensure_collections_schema(conn)

    deleted = _db.clear_collection(conn, collection)
    if deleted > 0:
        print(f"Cleared {deleted} existing chunks for collection '{collection}'")

    print(f"Indexing {source_dir} -> collection '{collection}'")
    stats = _indexer.index_directory(source_dir, collection, conn)
    _db.upsert_collection_metadata(
        conn,
        name=collection,
        embedding_model=EMBEDDING_MODEL,
        embedding_dims=EMBEDDING_DIMS,
        sparse_model=SPARSE_MODEL,
        chunk_size=chunk_size,
        overlap=overlap,
        db_name=DB_NAME,
        indexed_at=datetime.now(),
        doc_count=stats["files"],
        chunk_count=stats["chunks"],
    )
    conn.close()

    _write_report(stats, collection, chunk_size, overlap)


# FUNCTIONS

# Check that embedding and SPLADE servers are healthy; exit if not
def _check_servers() -> None:
    for name, url in [("embedding (8081)", EMBEDDING_HEALTH_URL), ("SPLADE (8083)", SPLADE_HEALTH_URL)]:
        try:
            resp = httpx.get(url, timeout=3.0)
            if resp.status_code != 200:
                print(f"ERROR: {name} server unhealthy (HTTP {resp.status_code}). Start servers first: ./start.sh")
                sys.exit(1)
        except Exception as e:
            print(f"ERROR: {name} server not reachable ({e}). Start servers first: ./start.sh")
            sys.exit(1)


# Write MD report to md/
def _write_report(stats: dict, collection: str, chunk_size: int, overlap: int) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path(__file__).parent / "md"
    report_path = report_dir / f"index_{collection}_{timestamp}.md"
    report_dir.mkdir(parents=True, exist_ok=True)

    elapsed = stats.get("elapsed", 0)
    total_chunks = stats["chunks"]
    throughput = total_chunks / elapsed if elapsed > 0 else 0

    lines = [
        f"# Index Report: {collection}",
        f"",
        f"**Timestamp:** {timestamp}",
        f"",
        f"## Config",
        f"",
        f"| Parameter | Value |",
        f"|-----------|-------|",
        f"| chunk_size | {chunk_size} |",
        f"| overlap | {overlap} |",
        f"| MRL dims | {VECTOR_DIM} |",
        f"| batch_size | {_indexer.BATCH_SIZE} |",
        f"| source_dir | {stats.get('source_dir', 'N/A')} |",
        f"",
        f"## Per-Document Stats",
        f"",
        f"| Filename | Chunks | Avg Chunk Size (chars) |",
        f"|----------|--------|------------------------|",
    ]

    for f in stats.get("per_file", []):
        lines.append(f"| {f['filename']} | {f['chunks']} | {f['avg_chunk_size']} |")

    lines += [
        f"",
        f"## Summary",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total documents | {stats['files']} |",
        f"| Total chunks | {total_chunks} |",
        f"| Total time | {elapsed:.1f}s |",
        f"| Throughput | {throughput:.1f} chunks/sec |",
        f"| Errors | {len(stats['errors'])} |",
    ]

    if stats["errors"]:
        lines += [f"", f"## Errors", f""]
        for err in stats["errors"]:
            lines.append(f"- **{err['file']}**: {err['error']}")

    report_path.write_text("\n".join(lines) + "\n")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index a directory of .md files into rag_test DB")
    parser.add_argument("--source-dir", required=True, help="Directory with .md files to index")
    parser.add_argument("--collection", default=None, help="Collection name (default: source-dir basename)")
    parser.add_argument("--chunk-size", type=int, default=2000, help="Chunk size in chars (default: 2000)")
    parser.add_argument("--overlap", type=int, default=400, help="Overlap in chars (default: 400)")
    args = parser.parse_args()

    collection = args.collection or Path(args.source_dir).name
    run_index(args.source_dir, collection, args.chunk_size, args.overlap)
