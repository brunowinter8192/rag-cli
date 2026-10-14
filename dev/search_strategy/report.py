# FUNCTIONS

def render_report(needs: list[dict], per_need: dict, results: dict) -> str:
    sections = [
        "# D_analyze report",
        render_sample(needs, results),
        render_per_need(needs, per_need),
        render_count(results),
        render_strategy(results["strategy"]),
        render_per_source(results["per_source"], results["known_item"]),
        render_claims(results),
        render_profiles(results),
        render_self_agreement(results["self_agreement"]),
    ]
    return "\n\n".join(sections) + "\n"


def fmt(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def table(header: list[str], rows: list[list]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines.extend("| " + " | ".join(fmt(cell) for cell in row) + " |" for row in rows)
    return "\n".join(lines)


def render_sample(needs: list[dict], results: dict) -> str:
    rows = [[n["id"], n["stratum"], n["intent"], n["collection"], results["trimmed"][n["id"]]] for n in needs]
    return "## Sample (N = %d)\n\n%s" % (len(needs), table(["need", "stratum", "intent", "collection", "pool chunks trimmed"], rows))


def render_per_need(needs: list[dict], per_need: dict) -> str:
    rows = []
    for need in needs:
        row = [need["id"], need["intent"]]
        for name in ("A@12", "G@12", "S@3", "M@12", "P@3"):
            m = per_need[need["id"]].get(name)
            row.append("-" if m is None else f"hit {m['hit']} rel {m['rel']} asp {fmt(m['asp'])} docs {m['reldocs']}")
        rows.append(row)
    return "## Per need (printed results: A 12, G 12, S 12, M 12, P 3 per source)\n\n" + table(["need", "intent", "A@12", "G@12", "S 4x3", "M@12", "P"], rows)


def render_count(results: dict) -> str:
    count = results["count"]
    rows = [[name, v["hit"], v["rel"], v["p"]] for name, v in results["curve"].items()]
    return (
        "## Default count\n\n"
        + table(["list", "needs with grade-2 hit (of 12)", "relevant chunks (sum)", "mean P"], rows)
        + f"\n\nDecision rule: smallest k <= 5 with Hit@k(A) >= Hit@12(A) - 1.\n\nk* = {fmt(count['k_star'])}; confirmed on guided queries: {count['confirmed_on_guided_queries']}"
    )


def render_strategy(strategy: dict) -> str:
    rows = [[name, v["adopt_siblings"], v["hit_s"], v["hit_a"], v["asp_mean_s"], v["asp_mean_a"], f"{v['wins']}/{v['losses']}/{v['ties']}"] for name, v in strategy.items()]
    return (
        "## Strategy at 12 printed results\n\n"
        + table(["comparison (first vs second)", "first adopted", "hit first", "hit second", "asp first", "asp second", "wins/losses/ties"], rows)
        + "\n\nRows: all and the intent splits compare S (4x3) with A (12). multiplicity_control compares S with G (12). shape_control compares G (12) with A (12)."
    )


def render_per_source(per_source: dict, known_item: dict) -> str:
    text = "## Per-source search\n\n"
    text += f"Needs with per-source arm: {per_source['ids']}. Hit sum P {per_source['hit_p']} vs A {per_source['hit_a']}. Relevant documents P {per_source['reldocs_p']} vs A {per_source['reldocs_a']}."
    for need_id, ranks in known_item.items():
        text += f"\n\nKnown-item rank in the 30-deep ranking for {need_id}: " + ", ".join(f"{k}={fmt(v)}" for k, v in ranks.items())
    return text


def render_claims(results: dict) -> str:
    lines = ["## Querybau claims"]
    for label, claim in results["form"].items():
        lines.append(f"- Form, guided vs {label}: verdict {claim['verdict']} (P@3 wins/losses/ties {claim['wins']}/{claim['losses']}/{claim['ties']}, mean P {fmt(claim['mean_first'])} vs {fmt(claim['mean_second'])}, hit {claim['hit_guided']} vs {claim['hit_form']})")
    mc = results["multi_concept"]
    lines.append(f"- Multi-concept failure, siblings vs one merged query on recall needs: verdict {mc['verdict']} (asp wins/losses/ties {mc['wins']}/{mc['losses']}/{mc['ties']}, mean {fmt(mc['mean_first'])} vs {fmt(mc['mean_second'])})")
    anchor = results["anchor"]
    if anchor["available"]:
        for name in ("precision", "recall", "reldocs"):
            a = anchor[name]
            lines.append(f"- Anchor effect, {name}: verdict {a['verdict']} (wins/losses/ties {a['wins']}/{a['losses']}/{a['ties']}, mean {fmt(a['mean_first'])} vs {fmt(a['mean_second'])})")
    agreement = results["agreement"]
    lines.append(f"- Sibling agreement: P(relevant | returned by 2+ siblings) {fmt(agreement['p_multiple'])} (n {agreement['n_multiple']}) vs by 1 {fmt(agreement['p_single'])} (n {agreement['n_single']}); supported: {agreement['supported']}")
    return "\n".join(lines)


def render_profiles(results: dict) -> str:
    rank_rows = [[r["rank"], r["n"], r["precision"]] for r in results["rank_profile"]]
    band_rows = [[f"{b['low']}-{b['high']}", b["n"], b["precision"]] for b in results["cutoff"]["bands"]]
    return (
        "## Rank and score profile of the logged queries (arm A)\n\n"
        + table(["rank", "n", "P(relevant)"], rank_rows)
        + "\n\n"
        + table(["score band", "n", "P(relevant)"], band_rows)
        + f"\n\nScore cutoff supported by data: {results['cutoff']['cutoff_supported']}"
    )


def render_self_agreement(agreement: dict) -> str:
    if not agreement["available"]:
        return "## Judge self-agreement\n\nNot run."
    return f"## Judge self-agreement\n\nn = {agreement['n']}, kappa relevant {fmt(agreement['kappa_relevant'])}, kappa grade {fmt(agreement['kappa_grade'])}"
