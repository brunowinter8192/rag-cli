# INFRASTRUCTURE

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

sys.path.insert(0, str(Path(__file__).parent))

from src.rag.reranker import rerank_workflow
from src.rag.search_cmd import retrieve_candidates
from strategy_common import ARM_DEPTH, CHUNKS_FILE, NEEDS_FILE, R_QUERIES_FILE, RUNS_FILE, chunk_key, load_json

RANKING_DEPTH = 30


# ORCHESTRATOR

def run_arms_workflow() -> None:
    specs = build_specs(load_json(NEEDS_FILE)["needs"], include_r=len(sys.argv) > 1 and sys.argv[1] == "r")
    runs = load_existing(RUNS_FILE, [])
    chunks = load_existing(CHUNKS_FILE, {})
    run_pending(pending_specs(specs, runs), runs, chunks)


# FUNCTIONS

def run_pending(specs: list[dict], runs: list[dict], chunks: dict) -> None:
    for spec in specs:
        run = execute_spec(spec)
        runs.append(run)
        store_chunks(chunks, spec, run["_ranked"])
        persist(runs, chunks)
        print(spec["need_id"], spec["arm"], spec["label"], len(run["hits"]), flush=True)


def load_existing(path: Path, default):
    if path.exists():
        return load_json(path)
    return default


def build_specs(needs: list[dict], include_r: bool) -> list[dict]:
    if include_r:
        return build_r_specs(needs)
    specs = []
    for need in needs:
        specs.extend(build_need_specs(need))
    return specs


def build_need_specs(need: dict) -> list[dict]:
    specs = [spec_for(need, "A", "A", need["logged_query"]), spec_for(need, "G", "G", need["g"])]
    for index, query in enumerate(need["siblings"], start=2):
        specs.append(spec_for(need, "S", f"s{index}", query))
    if need.get("m"):
        specs.append(spec_for(need, "M", "M", need["m"]))
    for label, query in (need.get("forms") or {}).items():
        specs.append(spec_for(need, "F", label, query))
    for source in need.get("per_source") or []:
        specs.append(spec_for(need, "P", source["label"], need["g"], document=source["document"]))
    return specs


def build_r_specs(needs: list[dict]) -> list[dict]:
    by_id = {need["id"]: need for need in needs}
    return [spec_for(by_id[item["need_id"]], "R", "R", item["query"]) for item in load_json(R_QUERIES_FILE)]


def spec_for(need: dict, arm: str, label: str, query: str, document: str | None = None) -> dict:
    return {
        "need_id": need["id"],
        "arm": arm,
        "label": label,
        "query": query,
        "collection": need["collection"],
        "document": document or need["document"],
        "exclude": need["exclude"],
        "depth": ARM_DEPTH[arm],
    }


def pending_specs(specs: list[dict], runs: list[dict]) -> list[dict]:
    done = {(r["need_id"], r["arm"], r["label"]) for r in runs}
    return [s for s in specs if (s["need_id"], s["arm"], s["label"]) not in done]


def execute_spec(spec: dict) -> dict:
    _, candidates = retrieve_candidates(spec["query"], spec["collection"], spec["document"], spec["exclude"])
    ranked = rerank_workflow(spec["query"], candidates, RANKING_DEPTH) if candidates else []
    return {
        **spec,
        "candidates": len(candidates),
        "hits": [{"document": h["document"], "chunk_index": h["chunk_index"], "score": h["score"]} for h in ranked],
        "_ranked": ranked,
    }


def store_chunks(chunks: dict, spec: dict, ranked: list[dict]) -> None:
    for hit in ranked[: spec["depth"]]:
        chunks[chunk_key(spec["collection"], hit["document"], hit["chunk_index"])] = hit["content"]


def persist(runs: list[dict], chunks: dict) -> None:
    clean = [{k: v for k, v in run.items() if k != "_ranked"} for run in runs]
    RUNS_FILE.write_text(json.dumps(clean, ensure_ascii=False))
    CHUNKS_FILE.write_text(json.dumps(chunks, ensure_ascii=False))


if __name__ == "__main__":
    run_arms_workflow()
