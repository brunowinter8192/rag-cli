# INFRASTRUCTURE

from metrics import BUDGETS, compare, mean

INLINE_CAP_K = 5
HIT_TOLERANCE = 1
SUPPORT_SHARE = 2 / 3
AGREEMENT_MARGIN = 0.10
AGREEMENT_MIN_GROUP = 10
CUTOFF_MAX_PRECISION = 0.10
CUTOFF_MIN_RESULTS = 50


# FUNCTIONS

def verdict(wins: int, losses: int) -> str:
    decided = wins + losses
    if decided == 0:
        return "inconclusive"
    if wins > losses and wins / decided >= SUPPORT_SHARE:
        return "supported"
    if losses > wins and losses / decided >= SUPPORT_SHARE:
        return "not supported"
    return "inconclusive"


def decide_default_count(hit_a: dict[int, int], hit_g: dict[int, int]) -> dict:
    eligible = [k for k in BUDGETS if k <= INLINE_CAP_K and hit_a[k] >= hit_a[12] - HIT_TOLERANCE]
    k_star = min(eligible) if eligible else None
    confirmed = k_star is not None and hit_g[k_star] >= hit_a[k_star]
    return {"k_star": k_star, "confirmed_on_guided_queries": confirmed, "hit_a": hit_a, "hit_g": hit_g}


def decide_strategy(per_need_s: list[dict], per_need_a: list[dict]) -> dict:
    hit_s = sum(m["hit"] for m in per_need_s)
    hit_a = sum(m["hit"] for m in per_need_a)
    wins, losses, ties = compare([m["asp"] for m in per_need_s], [m["asp"] for m in per_need_a])
    mean_s = mean([m["asp"] for m in per_need_s])
    mean_a = mean([m["asp"] for m in per_need_a])
    adopted = hit_s >= hit_a - HIT_TOLERANCE and mean_s > mean_a and wins > losses
    return {"adopt_siblings": adopted, "hit_s": hit_s, "hit_a": hit_a, "asp_mean_s": mean_s, "asp_mean_a": mean_a,
            "wins": wins, "losses": losses, "ties": ties}


def decide_claim_pair(first: list[float | None], second: list[float | None]) -> dict:
    wins, losses, ties = compare(first, second)
    return {"wins": wins, "losses": losses, "ties": ties, "verdict": verdict(wins, losses), "mean_first": mean(first), "mean_second": mean(second)}


def decide_agreement(grouped: dict[int, list[int]]) -> dict:
    single = grouped.get(1, [])
    multiple = [flag for count, flags in grouped.items() if count >= 2 for flag in flags]
    p_single = sum(single) / len(single) if single else None
    p_multiple = sum(multiple) / len(multiple) if multiple else None
    enough = len(single) >= AGREEMENT_MIN_GROUP and len(multiple) >= AGREEMENT_MIN_GROUP
    supported = enough and p_multiple - p_single >= AGREEMENT_MARGIN
    return {"p_single": p_single, "n_single": len(single), "p_multiple": p_multiple, "n_multiple": len(multiple), "supported": bool(supported)}


def decide_score_cutoff(bands: list[dict]) -> dict:
    candidates = [b for b in bands if b["n"] >= CUTOFF_MIN_RESULTS and b["precision"] < CUTOFF_MAX_PRECISION]
    return {"cutoff_supported": bool(candidates), "bands": bands}
