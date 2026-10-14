# INFRASTRUCTURE

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.rag.formatting import format_results

PRODUCTION_LOG_DIR = Path("/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/rag-cli/src/rag/logs")
REPORT_FILE = Path(__file__).parent / "md" / "E_output_size_report.md"
PERSIST_LIMIT = 30000
RESULT_COUNTS = (3, 4, 5, 6, 12)
CHAIN_LENGTHS = (1, 2, 3, 4, 5)
DRAWS = 20000
SEED = 20261015


# ORCHESTRATOR

def output_size_workflow() -> None:
    sizes = per_result_sizes()
    rows = overflow_rows(sizes)
    REPORT_FILE.write_text(render(sizes, rows))
    print(REPORT_FILE)


# FUNCTIONS

def load_lines(name: str) -> list[dict]:
    return [json.loads(line) for line in (PRODUCTION_LOG_DIR / name).read_text().splitlines() if line.strip()]


def per_result_sizes() -> list[tuple[int, int]]:
    searches = {r["search_id"]: r for r in load_lines("search.jsonl")}
    scores = {(r["search_id"], h["rank"]): h["score"] for r in searches.values() for h in r["hits"]}
    sizes = []
    for line in load_lines("search_content.jsonl"):
        record = searches.get(line["search_id"])
        if record is None:
            continue
        result = {"score": scores[(line["search_id"], line["rank"])], "chunk_index": line["chunk_index"],
                  "collection": record["collection"], "document": line["document"], "content": line["content"]}
        text = format_results([result])
        sizes.append((len(text), len(text.encode("utf-8"))))
    return sizes


def overflow_rows(sizes: list[tuple[int, int]]) -> list[list]:
    generator = random.Random(SEED)
    rows = []
    for k in RESULT_COUNTS:
        for chain in CHAIN_LENGTHS:
            draws = [generator.choices(sizes, k=k * chain) for _ in range(DRAWS)]
            chars = [sum(c for c, _ in draw) for draw in draws]
            octets = [sum(b for _, b in draw) for draw in draws]
            rows.append([k, chain, sum(1 for t in chars if t > PERSIST_LIMIT) / DRAWS, sum(1 for t in octets if t > PERSIST_LIMIT) / DRAWS,
                         sorted(octets)[len(octets) // 2]])
    return rows


def quantile(values: list[int], share: float) -> int:
    ordered = sorted(values)
    return ordered[min(int(share * len(ordered)), len(ordered) - 1)]


def render(sizes: list[tuple[int, int]], rows: list[list]) -> str:
    chars = [c for c, _ in sizes]
    octets = [b for _, b in sizes]
    lines = [
        "# E_output_size report", "",
        f"Printed results observed in the production log: {len(sizes)}.", "",
        f"Characters per printed result: median {quantile(chars, 0.5)}, p90 {quantile(chars, 0.9)}, max {max(chars)}.",
        f"Bytes per printed result: median {quantile(octets, 0.5)}, p90 {quantile(octets, 0.9)}, max {max(octets)}.", "",
        f"Bootstrap, {DRAWS} draws per cell, seed {SEED}: probability that a Bash call with `chain` searches of `k` results prints more than {PERSIST_LIMIT} characters or bytes.", "",
        "| k | chain | P(over, characters) | P(over, bytes) | median bytes |", "|---|---|---|---|---|",
    ]
    lines.extend(f"| {k} | {c} | {pc:.3f} | {pb:.3f} | {m} |" for k, c, pc, pb, m in rows)
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    output_size_workflow()
