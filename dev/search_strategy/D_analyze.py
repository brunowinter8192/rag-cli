# INFRASTRUCTURE

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from decisions import (decide_agreement, decide_claim_pair, decide_default_count, decide_score_cutoff,
                       decide_strategy)
from metrics import (BUDGETS, aspect_universe, cohen_kappa, judged_by_key, known_item_rank,
                     list_metrics, named_lists, parse_judgments, sibling_agreement)
from report import render_report
from strategy_common import JUDGMENTS_DIR, NEEDS_FILE, POOL_FILE, RUNS_FILE, load_json

REPORT_FILE = Path(__file__).parent / "md" / "D_analyze_report.md"
REJUDGE_FILE = JUDGMENTS_DIR / "rejudge.txt"
SCORE_BANDS = ((0.9, 1.01), (0.5, 0.9), (0.1, 0.5), (0.0, 0.1))


# ORCHESTRATOR

def analyze_workflow() -> None:
    needs = load_json(NEEDS_FILE)["needs"]
    runs = load_json(RUNS_FILE)
    pool = load_json(POOL_FILE)
    judgments = load_judgments()
    per_need = compute_per_need(needs, runs, pool, judgments)
    results = compute_results(needs, runs, pool, judgments, per_need)
    REPORT_FILE.write_text(render_report(needs, per_need, results))
    print(REPORT_FILE)


# FUNCTIONS

def load_judgments() -> dict:
    merged = {}
    for path in sorted(JUDGMENTS_DIR.glob("N*.txt")):
        merged.update(parse_judgments(path.read_text()))
    return merged


def runs_of(runs: list[dict], need_id: str) -> list[dict]:
    return [r for r in runs if r["need_id"] == need_id]


def compute_per_need(needs: list[dict], runs: list[dict], pool: dict, judgments: dict) -> dict:
    per_need = {}
    for need in needs:
        judged = judged_by_key(pool[need["id"]], judgments)
        universe = aspect_universe(judged)
        lists = named_lists(runs_of(runs, need["id"]))
        per_need[need["id"]] = {name: list_metrics(keys, judged, universe) for name, keys in lists.items()}
    return per_need


def compute_results(needs: list[dict], runs: list[dict], pool: dict, judgments: dict, per_need: dict) -> dict:
    ids = [n["id"] for n in needs]
    recall_ids = [n["id"] for n in needs if n["intent"] == "recall"]
    form_ids = [n["id"] for n in needs if n["forms"]]
    source_ids = [n["id"] for n in needs if n["per_source"]]
    return {
        "count": decide_default_count(hit_sums(per_need, ids, "A"), hit_sums(per_need, ids, "G")),
        "curve": budget_curve(per_need, ids),
        "strategy": strategy_results(per_need, ids, recall_ids),
        "per_source": per_source_results(per_need, source_ids),
        "form": form_claim(per_need, form_ids),
        "multi_concept": decide_claim_pair(column(per_need, recall_ids, "S@3", "asp"), column(per_need, recall_ids, "M@12", "asp")),
        "anchor": anchor_claim(per_need, ids),
        "agreement": agreement_result(needs, runs, pool, judgments),
        "cutoff": decide_score_cutoff(score_bands(needs, runs, pool, judgments)),
        "rank_profile": rank_profile(needs, runs, pool, judgments),
        "known_item": known_item_results(needs, runs),
        "trimmed": {nid: len(pool[nid]["trimmed"]) for nid in ids},
        "self_agreement": self_agreement(pool, judgments),
    }


def column(per_need: dict, ids: list[str], list_name: str, field: str) -> list:
    return [per_need[i][list_name][field] for i in ids if list_name in per_need[i]]


def hit_sums(per_need: dict, ids: list[str], arm: str) -> dict[int, int]:
    return {k: sum(per_need[i][f"{arm}@{k}"]["hit"] for i in ids) for k in BUDGETS}


def budget_curve(per_need: dict, ids: list[str]) -> dict:
    curve = {}
    for arm in ("A", "G"):
        for k in BUDGETS:
            name = f"{arm}@{k}"
            curve[name] = {
                "hit": sum(per_need[i][name]["hit"] for i in ids),
                "rel": sum(per_need[i][name]["rel"] for i in ids),
                "p": sum(per_need[i][name]["p"] for i in ids) / len(ids),
            }
    return curve


def strategy_results(per_need: dict, ids: list[str], recall_ids: list[str]) -> dict:
    precision_ids = [i for i in ids if i not in recall_ids]
    return {
        "all": decide_strategy([per_need[i]["S@3"] for i in ids], [per_need[i]["A@12"] for i in ids]),
        "recall_only": decide_strategy([per_need[i]["S@3"] for i in recall_ids], [per_need[i]["A@12"] for i in recall_ids]),
        "precision_only": decide_strategy([per_need[i]["S@3"] for i in precision_ids], [per_need[i]["A@12"] for i in precision_ids]),
        "multiplicity_control": decide_strategy([per_need[i]["S@3"] for i in ids], [per_need[i]["G@12"] for i in ids]),
        "shape_control": decide_strategy([per_need[i]["G@12"] for i in ids], [per_need[i]["A@12"] for i in ids]),
    }


def per_source_results(per_need: dict, source_ids: list[str]) -> dict:
    return {
        "hit_p": sum(per_need[i]["P@3"]["hit"] for i in source_ids),
        "hit_a": sum(per_need[i]["A@12"]["hit"] for i in source_ids),
        "reldocs_p": [per_need[i]["P@3"]["reldocs"] for i in source_ids],
        "reldocs_a": [per_need[i]["A@12"]["reldocs"] for i in source_ids],
        "ids": source_ids,
    }


def form_claim(per_need: dict, form_ids: list[str]) -> dict:
    guided = column(per_need, form_ids, "G@3", "p")
    claims = {}
    for label in ("kw", "nl", "bool"):
        name = f"F:{label}@3"
        claims[label] = decide_claim_pair(guided, column(per_need, form_ids, name, "p"))
        claims[label]["hit_guided"] = sum(per_need[i]["G@3"]["hit"] for i in form_ids)
        claims[label]["hit_form"] = sum(per_need[i][name]["hit"] for i in form_ids)
    return claims


def anchor_claim(per_need: dict, ids: list[str]) -> dict:
    with_r = [i for i in ids if "R@5" in per_need[i]]
    if not with_r:
        return {"available": False}
    return {
        "available": True,
        "precision": decide_claim_pair(column(per_need, with_r, "R@3", "p"), column(per_need, with_r, "A@3", "p")),
        "recall": decide_claim_pair(column(per_need, with_r, "A@5", "asp"), column(per_need, with_r, "R@5", "asp")),
        "reldocs": decide_claim_pair(column(per_need, with_r, "A@5", "reldocs"), column(per_need, with_r, "R@5", "reldocs")),
    }


def agreement_result(needs: list[dict], runs: list[dict], pool: dict, judgments: dict) -> dict:
    merged: dict[int, list[int]] = {}
    for need in needs:
        by_arm = {(r["arm"], r["label"]): r for r in runs_of(runs, need["id"])}
        for count, flags in sibling_agreement(by_arm, judged_by_key(pool[need["id"]], judgments)).items():
            merged.setdefault(count, []).extend(flags)
    return decide_agreement(merged)


def score_bands(needs: list[dict], runs: list[dict], pool: dict, judgments: dict) -> list[dict]:
    observations = a_hit_observations(needs, runs, pool, judgments)
    bands = []
    for low, high in SCORE_BANDS:
        inside = [rel for _, score, rel in observations if low <= score < high]
        bands.append({"low": low, "high": high, "n": len(inside), "precision": sum(inside) / len(inside) if inside else 0.0})
    return bands


def a_hit_observations(needs: list[dict], runs: list[dict], pool: dict, judgments: dict) -> list[tuple[int, float, int]]:
    observations = []
    for need in needs:
        judged = judged_by_key(pool[need["id"]], judgments)
        run = next(r for r in runs_of(runs, need["id"]) if r["arm"] == "A")
        for rank, hit in enumerate(run["hits"][:12], start=1):
            key = f"{run['collection']}|{hit['document']}|{hit['chunk_index']}"
            observations.append((rank, hit["score"], int(judged.get(key, (0, frozenset()))[0] >= 1)))
    return observations


def rank_profile(needs: list[dict], runs: list[dict], pool: dict, judgments: dict) -> list[dict]:
    observations = a_hit_observations(needs, runs, pool, judgments)
    profile = []
    for rank in range(1, 13):
        flags = [rel for r, _, rel in observations if r == rank]
        profile.append({"rank": rank, "n": len(flags), "precision": sum(flags) / len(flags) if flags else 0.0})
    return profile


def known_item_results(needs: list[dict], runs: list[dict]) -> dict:
    results = {}
    for need in needs:
        if need["known_item"]:
            results[need["id"]] = {f"{r['arm']}:{r['label']}": known_item_rank(r, need["known_item"]) for r in runs_of(runs, need["id"])}
    return results


def self_agreement(pool: dict, judgments: dict) -> dict:
    if not REJUDGE_FILE.exists():
        return {"available": False}
    second = parse_judgments(REJUDGE_FILE.read_text())
    ids = sorted(i for i in second if i in judgments)
    return {
        "available": True,
        "n": len(ids),
        "kappa_relevant": cohen_kappa([int(judgments[i][0] >= 1) for i in ids], [int(second[i][0] >= 1) for i in ids]),
        "kappa_grade": cohen_kappa([judgments[i][0] for i in ids], [second[i][0] for i in ids]),
    }


if __name__ == "__main__":
    analyze_workflow()
