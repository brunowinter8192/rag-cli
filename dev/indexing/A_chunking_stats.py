# INFRASTRUCTURE
import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import p1_chunker as _chunker

SEPARATORS = ["\n\n", "\n", ". ", "! ", "? ", " "]


# ORCHESTRATOR

def run_stats(source_dir: str, chunk_size: int, overlap: int) -> None:
    source_path = Path(source_dir)
    if not source_path.is_dir():
        print(f"ERROR: source-dir does not exist: {source_dir}")
        sys.exit(1)

    _chunker.CHUNK_SIZE = chunk_size
    _chunker.OVERLAP = overlap

    md_files = sorted(source_path.glob("*.md"))
    if not md_files:
        print(f"ERROR: no .md files found in {source_dir}")
        sys.exit(1)

    per_file = []
    for md_path in md_files:
        chunks = _chunker.chunk_file(str(md_path))
        sizes = [len(c["content"]) for c in chunks]
        file_size = md_path.read_text(encoding="utf-8")
        per_file.append({
            "filename": md_path.name,
            "file_size_chars": len(file_size),
            "num_chunks": len(chunks),
            "avg_chunk_size": sum(sizes) // len(sizes) if sizes else 0,
            "min_chunk": min(sizes) if sizes else 0,
            "max_chunk": max(sizes) if sizes else 0,
            "sizes": sizes,
        })

    collection = source_path.name
    _write_report(per_file, collection, chunk_size, overlap)


# FUNCTIONS

# Write MD report to md/
def _write_report(per_file: list[dict], collection: str, chunk_size: int, overlap: int) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path(__file__).parent / "md"
    report_path = report_dir / f"stats_{collection}_{timestamp}.md"
    report_dir.mkdir(parents=True, exist_ok=True)

    all_sizes = [s for f in per_file for s in f["sizes"]]
    total_chunks = sum(f["num_chunks"] for f in per_file)
    overall_avg = sum(all_sizes) // len(all_sizes) if all_sizes else 0
    overall_min = min(all_sizes) if all_sizes else 0
    overall_max = max(all_sizes) if all_sizes else 0

    buckets = {"0-500": 0, "500-1000": 0, "1000-1500": 0, "1500-2000": 0, "2000+": 0}
    for s in all_sizes:
        if s < 500:
            buckets["0-500"] += 1
        elif s < 1000:
            buckets["500-1000"] += 1
        elif s < 1500:
            buckets["1000-1500"] += 1
        elif s < 2000:
            buckets["1500-2000"] += 1
        else:
            buckets["2000+"] += 1

    lines = [
        f"# Chunking Stats: {collection}",
        f"",
        f"**Timestamp:** {timestamp}",
        f"",
        f"## Config",
        f"",
        f"| Parameter | Value |",
        f"|-----------|-------|",
        f"| chunk_size | {chunk_size} |",
        f"| overlap | {overlap} |",
        f"| separators | `{SEPARATORS}` |",
        f"",
        f"## Per-Document Stats",
        f"",
        f"| Filename | File Size (chars) | Chunks | Avg Chunk Size | Min Chunk | Max Chunk |",
        f"|----------|-------------------|--------|----------------|-----------|-----------|",
    ]

    for f in per_file:
        lines.append(
            f"| {f['filename']} | {f['file_size_chars']} | {f['num_chunks']} "
            f"| {f['avg_chunk_size']} | {f['min_chunk']} | {f['max_chunk']} |"
        )

    lines += [
        f"",
        f"## Summary",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total documents | {len(per_file)} |",
        f"| Total chunks | {total_chunks} |",
        f"| Overall avg chunk size | {overall_avg} chars |",
        f"| Overall min chunk size | {overall_min} chars |",
        f"| Overall max chunk size | {overall_max} chars |",
        f"",
        f"## Size Distribution",
        f"",
        f"| Bucket (chars) | Count | % |",
        f"|----------------|-------|---|",
    ]

    for bucket, count in buckets.items():
        pct = round(100 * count / total_chunks, 1) if total_chunks else 0
        lines.append(f"| {bucket} | {count} | {pct}% |")

    report_path.write_text("\n".join(lines) + "\n")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chunking stats for a directory of .md files (no GPU needed)")
    parser.add_argument("--source-dir", required=True, help="Directory with .md files to analyze")
    parser.add_argument("--chunk-size", type=int, default=2000, help="Chunk size in chars (default: 2000)")
    parser.add_argument("--overlap", type=int, default=400, help="Overlap in chars (default: 400)")
    args = parser.parse_args()

    run_stats(args.source_dir, args.chunk_size, args.overlap)
