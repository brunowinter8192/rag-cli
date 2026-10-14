# INFRASTRUCTURE

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from strategy_common import CHUNKS_FILE, NEEDS_FILE, POOL_FILE, load_json

SHEET_FILE = Path("/tmp/ragstrat/judge_rejudge.md")
SAMPLE_SHARE = 0.08
SEED = 20261016


# ORCHESTRATOR

def rejudge_sheet_workflow() -> None:
    needs = {n["id"]: n for n in load_json(NEEDS_FILE)["needs"]}
    entries = sample_entries(load_json(POOL_FILE))
    write_sheet(render_sheet(entries, needs, load_json(CHUNKS_FILE)), len(entries))


# FUNCTIONS

def write_sheet(text: str, count: int) -> None:
    SHEET_FILE.write_text(text)
    print(SHEET_FILE, count)


def sample_entries(pool: dict) -> list[tuple[str, str, str]]:
    everything = sorted((need_id, entry["id"], key) for need_id, state in pool.items() for key, entry in state["chunks"].items())
    count = round(len(everything) * SAMPLE_SHARE)
    return random.Random(SEED).sample(everything, count)


def render_sheet(entries: list[tuple[str, str, str]], needs: dict, chunks: dict) -> str:
    lines = ["# Re-judge sheet", ""]
    for need_id, chunk_id, key in entries:
        need = needs[need_id]
        lines.append(f"## {chunk_id} | {key.split('|')[1]}")
        lines.append("")
        lines.append(f"NEED: {need['need']}")
        lines.extend(f"- {aspect}: {text}" for aspect, text in need["aspects"].items())
        lines.extend(["", chunks[key], ""])
    return "\n".join(lines)


if __name__ == "__main__":
    rejudge_sheet_workflow()
