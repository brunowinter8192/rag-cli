# INFRASTRUCTURE

BUDGETS = (3, 4, 5, 6, 8, 12)
S_LABELS = ("s1", "s2", "s3", "s4")
TIE_TOLERANCE = 1e-9


# FUNCTIONS

def parse_judgments(text: str) -> dict[str, tuple[int, frozenset[str]]]:
    judgments = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 2 or parts[0].startswith("#"):
            continue
        aspects = frozenset(parts[2].split(",")) if len(parts) > 2 else frozenset()
        judgments[parts[0]] = (int(parts[1]), aspects)
    return judgments


def judged_by_key(pool_need: dict, judgments: dict) -> dict[str, tuple[int, frozenset[str]]]:
    result = {}
    for key, entry in pool_need["chunks"].items():
        result[key] = judgments.get(entry["id"], (0, frozenset()))
    return result


def aspect_universe(judged: dict) -> frozenset[str]:
    universe = set()
    for grade, aspects in judged.values():
        if grade >= 1:
            universe |= aspects
    return frozenset(universe)


def key_document(key: str) -> str:
    return key.split("|")[1]


def keys_of(run: dict, count: int) -> list[str]:
    return [f"{run['collection']}|{h['document']}|{h['chunk_index']}" for h in run["hits"][:count]]


def list_metrics(keys: list[str], judged: dict, universe: frozenset[str]) -> dict:
    grades = [judged.get(key, (0, frozenset()))[0] for key in keys]
    relevant_keys = {key for key, grade in zip(keys, grades) if grade >= 1}
    covered = set()
    for key in relevant_keys:
        covered |= judged[key][1]
    return {
        "printed": len(keys),
        "hit": int(any(grade == 2 for grade in grades)),
        "rel": len(relevant_keys),
        "p": sum(1 for grade in grades if grade >= 1) / len(keys) if keys else 0.0,
        "asp": len(covered & universe) / len(universe) if universe else None,
        "reldocs": len({key_document(key) for key in relevant_keys}),
    }


def named_lists(need_runs: list[dict]) -> dict[str, list[str]]:
    by_arm = {(run["arm"], run["label"]): run for run in need_runs}
    lists: dict[str, list[str]] = {}
    for arm in ("A", "G", "M"):
        if (arm, arm) in by_arm:
            for budget in BUDGETS:
                lists[f"{arm}@{budget}"] = keys_of(by_arm[(arm, arm)], budget)
    lists.update(sibling_lists(by_arm))
    lists.update(labelled_lists(by_arm, "F"))
    lists.update(per_source_list(by_arm))
    for depth in (3, 5):
        if ("R", "R") in by_arm:
            lists[f"R@{depth}"] = keys_of(by_arm[("R", "R")], depth)
    return lists


def sibling_runs(by_arm: dict) -> dict[str, dict]:
    runs = {"s1": by_arm[("G", "G")]}
    for label in S_LABELS[1:]:
        runs[label] = by_arm[("S", label)]
    return runs


def sibling_lists(by_arm: dict) -> dict[str, list[str]]:
    runs = sibling_runs(by_arm)
    lists = {}
    for depth in (1, 2, 3):
        merged = []
        for label in S_LABELS:
            merged.extend(keys_of(runs[label], depth))
        lists[f"S@{depth}"] = merged
    return lists


def labelled_lists(by_arm: dict, arm: str) -> dict[str, list[str]]:
    return {f"{arm}:{label}@3": keys_of(run, 3) for (run_arm, label), run in by_arm.items() if run_arm == arm}


def per_source_list(by_arm: dict) -> dict[str, list[str]]:
    sources = [run for (arm, _), run in by_arm.items() if arm == "P"]
    if not sources:
        return {}
    merged = []
    for run in sources:
        merged.extend(keys_of(run, 3))
    return {"P@3": merged}


def compare(first: list[float | None], second: list[float | None]) -> tuple[int, int, int]:
    wins = losses = ties = 0
    for a, b in zip(first, second):
        if a is None or b is None or abs(a - b) <= TIE_TOLERANCE:
            ties += 1
        elif a > b:
            wins += 1
        else:
            losses += 1
    return wins, losses, ties


def mean(values: list[float | None]) -> float:
    present = [v for v in values if v is not None]
    return sum(present) / len(present) if present else 0.0


def sibling_agreement(by_arm: dict, judged: dict) -> dict[int, list[int]]:
    counts: dict[str, int] = {}
    for run in sibling_runs(by_arm).values():
        for key in set(keys_of(run, 3)):
            counts[key] = counts.get(key, 0) + 1
    grouped: dict[int, list[int]] = {}
    for key, count in counts.items():
        grouped.setdefault(count, []).append(1 if judged.get(key, (0, frozenset()))[0] >= 1 else 0)
    return grouped


def known_item_rank(run: dict, known: list[dict]) -> int | None:
    wanted = {(k["document"], k["chunk_index"]) for k in known}
    for rank, hit in enumerate(run["hits"], start=1):
        if (hit["document"], hit["chunk_index"]) in wanted:
            return rank
    return None


def cohen_kappa(first: list[int], second: list[int]) -> float | None:
    total = len(first)
    if total == 0:
        return None
    observed = sum(1 for a, b in zip(first, second) if a == b) / total
    categories = set(first) | set(second)
    expected = sum((first.count(c) / total) * (second.count(c) / total) for c in categories)
    if expected == 1.0:
        return 1.0
    return (observed - expected) / (1 - expected)
