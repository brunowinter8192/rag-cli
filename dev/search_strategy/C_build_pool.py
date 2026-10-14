# INFRASTRUCTURE

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from strategy_common import CHUNKS_FILE, NEEDS_FILE, POOL_FILE, RUNS_FILE, chunk_key, load_json

JUDGE_SHEET_DIR = Path("/tmp/ragstrat/judge")
POOL_CAP = 44
SHUFFLE_SEED = 20261015
SHEET_SIZE = 12


# ORCHESTRATOR

def build_pool_workflow() -> None:
    needs = load_json(NEEDS_FILE)["needs"]
    runs = load_json(RUNS_FILE)
    chunks = load_json(CHUNKS_FILE)
    existing = load_json(POOL_FILE) if POOL_FILE.exists() else {}
    pool = extend_pool(existing, needs, runs)
    POOL_FILE.write_text(json.dumps(pool, indent=1, ensure_ascii=False))
    write_judge_sheets(pool, needs, chunks, set_of_new_ids(existing, pool))
    print_summary(pool)


# FUNCTIONS

def extend_pool(existing: dict, needs: list[dict], runs: list[dict]) -> dict:
    pool = {key: dict(value) for key, value in existing.items()}
    for need in needs:
        pool[need["id"]] = extend_need_pool(pool.get(need["id"]), need, [r for r in runs if r["need_id"] == need["id"]])
    return pool


def extend_need_pool(existing: dict | None, need: dict, runs: list[dict]) -> dict:
    state = existing or {"cap": POOL_CAP, "trimmed": [], "chunks": {}, "next_id": 1}
    appearances = collect_appearances(need, runs)
    new_keys = [key for key in appearances if key not in state["chunks"]]
    is_first_build = not state["chunks"]
    kept, trimmed = trim_to_cap(new_keys, appearances) if is_first_build else (new_keys, [])
    shuffled = shuffle_keys(sorted(kept), need["id"], state["next_id"])
    for key in shuffled:
        state["chunks"][key] = {"id": f"{need['id']}-c{state['next_id']:02d}", "appearances": appearances[key]}
        state["next_id"] += 1
    state["trimmed"].extend(trimmed)
    return state


def collect_appearances(need: dict, runs: list[dict]) -> dict[str, list[str]]:
    appearances: dict[str, list[str]] = {}
    for run in runs:
        for rank, hit in enumerate(run["hits"][: run["depth"]], start=1):
            key = chunk_key(run["collection"], hit["document"], hit["chunk_index"])
            appearances.setdefault(key, []).append(f"{run['arm']}:{run['label']}:{rank}/{run['depth']}")
    return appearances


def trim_to_cap(keys: list[str], appearances: dict[str, list[str]]) -> tuple[list[str], list[str]]:
    ordered = sorted(keys, key=lambda key: (best_normalized_rank(appearances[key]), key))
    return ordered[:POOL_CAP], ordered[POOL_CAP:]


def best_normalized_rank(entries: list[str]) -> float:
    return min(int(e.split(":")[2].split("/")[0]) / int(e.split(":")[2].split("/")[1]) for e in entries)


def shuffle_keys(keys: list[str], need_id: str, offset: int) -> list[str]:
    generator = random.Random(f"{SHUFFLE_SEED}-{need_id}-{offset}")
    shuffled = list(keys)
    generator.shuffle(shuffled)
    return shuffled


def set_of_new_ids(existing: dict, pool: dict) -> set[str]:
    old = {entry["id"] for need in existing.values() for entry in need["chunks"].values()}
    return {entry["id"] for need in pool.values() for entry in need["chunks"].values()} - old


def write_judge_sheets(pool: dict, needs: list[dict], chunks: dict, only_ids: set[str]) -> None:
    JUDGE_SHEET_DIR.mkdir(parents=True, exist_ok=True)
    for need in needs:
        entries = [(key, e) for key, e in pool[need["id"]]["chunks"].items() if e["id"] in only_ids]
        ordered = sorted(entries, key=lambda item: item[1]["id"])
        for start in range(0, len(ordered), SHEET_SIZE):
            part = ordered[start : start + SHEET_SIZE]
            (JUDGE_SHEET_DIR / f"{need['id']}_{part[0][1]['id']}.md").write_text(render_sheet(need, part, chunks))


def render_sheet(need: dict, entries: list[tuple[str, dict]], chunks: dict) -> str:
    lines = [f"# {need['id']}", "", f"NEED: {need['need']}", ""]
    lines.extend(f"- {aspect}: {text}" for aspect, text in need["aspects"].items())
    lines.append("")
    for key, entry in entries:
        document = key.split("|")[1]
        lines.extend([f"## {entry['id']} | {document}", "", chunks[key], ""])
    return "\n".join(lines)


def print_summary(pool: dict) -> None:
    for need_id, state in pool.items():
        print(need_id, "pool", len(state["chunks"]), "trimmed", len(state["trimmed"]))


if __name__ == "__main__":
    build_pool_workflow()
