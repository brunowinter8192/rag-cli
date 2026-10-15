# INFRASTRUCTURE
import argparse
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from dev.kvp.kvp_canary_logic import compare_runs, error_result, evaluate_case, render_canary_report
from dev.kvp.kvp_config import (
    CANARY_CASES_PATH,
    CANARY_JSON_DIR,
    DEFAULT_LOG_DIR,
    REGISTRY_NAME,
    REPORT_DIR,
    SEARCH_CONTENT_NAME,
    SEARCH_LOG_NAME,
)
from dev.kvp.kvp_load import read_jsonl
from src.rag import retrieval_log
from src.rag.code_version import code_version
from src.rag.search_cmd import search_workflow

RUN_DIR_PREFIX = "kvp_canary_"


# ORCHESTRATOR

def main() -> None:
    args = parse_args()
    cases = load_cases(CANARY_CASES_PATH)
    production_paths = production_search_logs()
    run_dir = isolate_logs()
    results, search_ids = run_cases(cases, run_dir)
    isolation = check_isolation(search_ids, production_paths)
    baseline = load_baseline(args.baseline)
    comparison = compare_runs(baseline, results) if baseline is not None else None
    meta = build_meta(args.baseline, isolation)
    report = render_canary_report(meta, results, comparison)
    md_path, json_path = write_outputs(report, meta, results)
    print(md_path)
    print(json_path)


# FUNCTIONS

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="KVP canary: fixed real queries with known expected hits, run against the live servers")
    ap.add_argument("--baseline", type=str, default=None, help="JSON written by an earlier canary run")
    return ap.parse_args()


def load_cases(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def production_search_logs() -> list[Path]:
    return [retrieval_log.SEARCH_LOG_FILE, DEFAULT_LOG_DIR / SEARCH_LOG_NAME]


def isolate_logs() -> Path:
    run_dir = Path(tempfile.mkdtemp(prefix=RUN_DIR_PREFIX))
    retrieval_log.SEARCH_LOG_FILE = run_dir / SEARCH_LOG_NAME
    retrieval_log.SEARCH_CONTENT_FILE = run_dir / SEARCH_CONTENT_NAME
    retrieval_log.CONFIG_REGISTRY_FILE = run_dir / REGISTRY_NAME
    return run_dir


def run_cases(cases: list[dict], run_dir: Path) -> tuple[list[dict], list[str]]:
    results, search_ids = [], []
    for case in cases:
        result, search_id = run_case(case, run_dir)
        results.append(result)
        if search_id:
            search_ids.append(search_id)
    return results, search_ids


def run_case(case: dict, run_dir: Path) -> tuple[dict, str | None]:
    before = len(read_jsonl(run_dir / SEARCH_LOG_NAME))
    try:
        search_workflow(case["query"], case["collection"], case["document"], case["exclude"])
    except Exception as exc:
        return error_result(case, f"{type(exc).__name__}: {exc}"), None
    records = read_jsonl(run_dir / SEARCH_LOG_NAME)
    if len(records) <= before:
        return error_result(case, "no search record written"), None
    record = records[-1]
    content = [line for line in read_jsonl(run_dir / SEARCH_CONTENT_NAME) if line["search_id"] == record["search_id"]]
    return evaluate_case(case, record, content), record["search_id"]


def check_isolation(search_ids: list[str], production_paths: list[Path]) -> str:
    leaked = [str(path) for path in production_paths if _holds_any(path, search_ids)]
    if leaked:
        return "NO, canary search ids found in " + ", ".join(leaked)
    return f"yes, none of the {len(search_ids)} canary search ids appear in {', '.join(str(p) for p in production_paths)}"


def load_baseline(path: str | None) -> list[dict] | None:
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))["results"]


def build_meta(baseline: str | None, isolation: str) -> dict:
    return {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "code_version": code_version(),
        "cases_file": CANARY_CASES_PATH.name,
        "baseline": baseline,
        "isolation": isolation,
    }


def write_outputs(report: str, meta: dict, results: list[dict]) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CANARY_JSON_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    md_path = REPORT_DIR / f"kvp_canary_{stamp}.md"
    json_path = CANARY_JSON_DIR / f"kvp_canary_{stamp}.json"
    md_path.write_text(report, encoding="utf-8")
    json_path.write_text(json.dumps({"meta": meta, "results": results}, ensure_ascii=False, indent=1), encoding="utf-8")
    return md_path, json_path


def _holds_any(path: Path, search_ids: list[str]) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return any(search_id in text for search_id in search_ids)


if __name__ == "__main__":
    main()
