# INFRASTRUCTURE
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "indexing"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from eval_config import BASELINE, SWEEP_RANGES
from eval_constellation import MODE_CONSTELLATIONS, _check_servers, _ensure_constellation_for_mode
from eval_runner import _load_queries, _resolve_queries_path, _verify_drift, _run_query
from eval_metrics import _check_document_match, _check_snippet_match, _compute_rank_metrics, _compute_avg_metrics
from eval_report import _write_report, _write_sweep_comparison
from eval_cross_report import _write_cross_sweep_report


# ORCHESTRATOR

def run_baseline(queries_path: str, config: dict) -> None:
    collection = config["collection"]
    mode = config["mode"]
    if MODE_CONSTELLATIONS.get(mode):
        _ensure_constellation_for_mode(mode)
    else:
        _check_servers([mode])
    queries = _load_queries(queries_path)
    _verify_drift(queries, collection)
    print(f"Running baseline: {len(queries)} queries | mode={config['mode']} | top_k={config['top_k']} | collection={collection}")

    query_results = _run_config_queries(queries, collection, config)

    _write_report(query_results, collection, config, label="baseline")


def run_cross_sweep(queries_path: str, param1: str, param2: str, base_config: dict,
                    restrict_values: list[str] | None = None) -> None:
    for p in (param1, param2):
        if p not in SWEEP_RANGES:
            print(f"ERROR: '{p}' is not a sweepable parameter. Valid: {sorted(SWEEP_RANGES)}")
            sys.exit(1)

    collection = base_config["collection"]
    values1 = (restrict_values if restrict_values and param1 == "mode" else None) or SWEEP_RANGES[param1]
    values2 = (restrict_values if restrict_values and param2 == "mode" else None) or SWEEP_RANGES[param2]

    mode_is_swept = param1 == "mode" or param2 == "mode"
    if not mode_is_swept:
        _check_servers([base_config["mode"]])

    queries = _load_queries(queries_path)
    _verify_drift(queries, collection)
    print(f"Running cross-sweep: {param1} × {param2} | {len(values1)}×{len(values2)}={len(values1)*len(values2)} configs | {len(queries)} queries | collection={collection}")

    results: dict[tuple, tuple] = {}
    total_configs = len(values1) * len(values2)
    done = 0
    for v1 in values1:
        if param1 == "mode":
            _ensure_constellation_for_mode(v1)
        for v2 in values2:
            if param2 == "mode":
                _ensure_constellation_for_mode(v2)
            config = {**base_config, param1: v1, param2: v2}
            query_results = _run_config_queries(queries, collection, config)
            results[(v1, v2)] = _compute_avg_metrics(query_results)
            done += 1
            r = results[(v1, v2)]
            print(f"  [{done}/{total_configs}] {param1}={v1} {param2}={v2}: snippet_recall={r[1]:.0%} NDCG={r[2]:.3f} mean_lat={r[5]:.0f}ms")

    _write_cross_sweep_report(results, param1, param2, values1, values2, base_config)


def run_sweep(queries_path: str, param: str, base_config: dict,
              restrict_values: list[str] | None = None) -> None:
    if param not in SWEEP_RANGES:
        print(f"ERROR: '{param}' is not a sweepable parameter. Valid: {sorted(SWEEP_RANGES)}")
        sys.exit(1)

    collection = base_config["collection"]
    values = restrict_values if restrict_values is not None else SWEEP_RANGES[param]
    if param != "mode":
        mode = base_config["mode"]
        if MODE_CONSTELLATIONS.get(mode):
            _ensure_constellation_for_mode(mode)
        else:
            _check_servers([mode])

    queries = _load_queries(queries_path)
    _verify_drift(queries, collection)
    print(f"Running sweep: {param} over {values} | {len(queries)} queries | collection={collection}")

    comparison_rows = []
    for val in values:
        config = {**base_config, param: val}
        if param == "mode":
            _ensure_constellation_for_mode(val)
        query_results = _run_config_queries(queries, collection, config)

        label = f"sweep_{param}_{val}"
        _write_report(query_results, collection, config, label=label, sweep_param=param)
        avg_doc, avg_snip, avg_ndcg, avg_mrr, avg_recall_k, mean_lat = _compute_avg_metrics(query_results)
        comparison_rows.append((param, val, config["mode"], avg_doc, avg_snip, avg_ndcg, avg_mrr, avg_recall_k, mean_lat))

    _write_sweep_comparison(comparison_rows, param, base_config)


# FUNCTIONS

def _run_config_queries(queries: list[dict], collection: str, config: dict) -> list[dict]:
    total_q = len(queries)
    query_results = []
    for qi, entry in enumerate(queries, 1):
        hits, latency_ms = _run_query(entry["query"], collection, config)
        print(f"  [q{qi}/{total_q}] mode={config['mode']} top_k={config['top_k']} latency={latency_ms:.0f}ms", flush=True)
        query_results.append({
            "entry": entry,
            "hits": hits,
            "latency_ms": latency_ms,
            "doc_match": _check_document_match(entry["expected_documents"], hits),
            "snippet_match": _check_snippet_match(entry["expected_chunks"], hits),
            "rank_metrics": _compute_rank_metrics(hits, entry["expected_chunks"], config["top_k"]),
        })
    return query_results


def _parse_overrides(override_list: list[str], base_config: dict) -> dict:
    config = dict(base_config)
    for item in override_list or []:
        if "=" not in item:
            print(f"ERROR: --override must be key=val (got: '{item}')")
            sys.exit(1)
        key, raw_val = item.split("=", 1)
        if key not in config:
            print(f"ERROR: --override key '{key}' not in BASELINE. Valid keys: {sorted(config)}")
            sys.exit(1)
        original = base_config[key]
        if isinstance(original, bool):
            config[key] = raw_val.lower() in ("true", "1", "yes")
        elif isinstance(original, int):
            config[key] = int(raw_val)
        elif isinstance(original, float):
            config[key] = float(raw_val)
        else:
            config[key] = raw_val
    return config


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate retrieval against expected_chunks ground truth")
    parser.add_argument("--collection", default=None, help="Collection to query — shorthand for --override collection=X")
    parser.add_argument("--queries", default=None, help="Queries JSON path (default: auto-derived from collection)")
    parser.add_argument("--baseline", action="store_true", help="Run single pass at BASELINE config values")
    parser.add_argument("--sweep", metavar="PARAM", help="Sweep PARAM over SWEEP_RANGES[PARAM]; others fixed at BASELINE")
    parser.add_argument("--sweep-cross", metavar=("PARAM1", "PARAM2"), nargs=2, help="Cross-product sweep PARAM1 × PARAM2 over SWEEP_RANGES; others fixed at BASELINE")
    parser.add_argument("--override", metavar="key=val", action="append", help="Override a BASELINE key (repeatable)")
    parser.add_argument("--restrict-modes", metavar="M1,M2,...", default=None,
                        help="Restrict --sweep/--sweep-cross mode dimension to this comma-separated subset of SWEEP_RANGES['mode']")
    args = parser.parse_args()

    if not args.baseline and not args.sweep and not args.sweep_cross:
        parser.error("Specify --baseline, --sweep PARAM, or --sweep-cross PARAM1 PARAM2")

    config = _parse_overrides(args.override, BASELINE)
    if args.collection:
        config["collection"] = args.collection
    queries_path = _resolve_queries_path(config["collection"], args.queries)

    restrict_values = None
    if args.restrict_modes:
        restrict_values = [m.strip() for m in args.restrict_modes.split(",")]
        unknown = [m for m in restrict_values if m not in SWEEP_RANGES["mode"]]
        if unknown:
            parser.error(f"Unknown modes in --restrict-modes: {unknown}. Valid: {SWEEP_RANGES['mode']}")

    if args.sweep_cross:
        run_cross_sweep(queries_path, args.sweep_cross[0], args.sweep_cross[1], config, restrict_values)
    elif args.sweep:
        run_sweep(queries_path, args.sweep, config, restrict_values)
    else:
        run_baseline(queries_path, config)
