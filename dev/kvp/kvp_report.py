# INFRASTRUCTURE
import argparse
from datetime import datetime, timezone
from pathlib import Path

from dev.kvp.kvp_classify import known_projects
from dev.kvp.kvp_config import (
    COLD_START_CODE,
    COLD_START_SERVER_PREFIXES,
    DEFAULT_LOG_DIR,
    DEFAULT_TRANSCRIPTS_GLOB,
    ERRORS_NAME,
    EXPAND_LOG_NAME,
    REGISTRY_NAME,
    REPORT_DIR,
    SEARCH_CONTENT_NAME,
    SEARCH_LOG_NAME,
)
from dev.kvp.kvp_indicators import build_search_items, compute_report_data
from dev.kvp.kvp_join import attribute_expands, join_calls_to_searches
from dev.kvp.kvp_load import (
    filter_window,
    group_contents_by_search,
    index_registry,
    parse_ts,
    parse_window_bound,
    read_jsonl,
)
from dev.kvp.kvp_render import render_report
from dev.kvp.kvp_transcripts import load_transcripts


# ORCHESTRATOR

def main() -> None:
    args = parse_args()
    since, until = parse_window_bound(args.since), parse_window_bound(args.until)
    sources = load_sources(Path(args.log_dir), args.transcripts_glob, since, until)
    data = analyze(sources)
    meta = build_meta(args, sources)
    path = write_report(render_report(meta, data), REPORT_DIR, args.since, args.until)
    print(path)


# FUNCTIONS

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="KVP report over the rag-cli logs and Claude Code transcripts")
    ap.add_argument("--since", type=str, default=None, help="Window start, ISO date or timestamp, UTC if no zone is given")
    ap.add_argument("--until", type=str, default=None, help="Window end, ISO date or timestamp, UTC if no zone is given")
    ap.add_argument("--log-dir", type=str, default=str(DEFAULT_LOG_DIR))
    ap.add_argument("--transcripts-glob", type=str, default=DEFAULT_TRANSCRIPTS_GLOB)
    return ap.parse_args()


def load_sources(log_dir: Path, transcripts_glob: str, since, until) -> dict:
    all_records = read_jsonl(log_dir / SEARCH_LOG_NAME)
    records = filter_window(all_records, since, until)
    calls, readbacks = load_transcripts(transcripts_glob, since, until)
    log_start = min((r["ts"] for r in all_records), default=None)
    return {
        "all_records": all_records,
        "records": records,
        "contents": group_contents_by_search(read_jsonl(log_dir / SEARCH_CONTENT_NAME), {r["search_id"] for r in records}),
        "expands": filter_window(read_jsonl(log_dir / EXPAND_LOG_NAME), since, until),
        "registry": index_registry(read_jsonl(log_dir / REGISTRY_NAME)),
        "errors": read_jsonl(log_dir / ERRORS_NAME),
        "calls": [c for c in calls if log_start is not None and c["tool_use_ts"] >= log_start],
        "readbacks": readbacks,
        "window": (since, until),
        "log_dir": log_dir,
        "transcripts_glob": transcripts_glob,
    }


def analyze(sources: dict) -> dict:
    joined, unjoined = join_calls_to_searches(sources["calls"], sources["records"])
    items = build_search_items(
        sources["records"], sources["contents"], sources["registry"], cold_start_times(sources["errors"]), joined,
    )
    attributions = attribute_expands(sources["expands"], sources["records"])
    errors_in_window = filter_window(sources["errors"], *sources["window"])
    return compute_report_data(
        items, attributions, unjoined, sources["readbacks"], errors_in_window,
        known_projects(sources["all_records"]), sources["expands"],
    )


def cold_start_times(errors: list[dict]) -> list:
    return [
        parse_ts(e["ts"]) for e in errors
        if e["code"] == COLD_START_CODE and e["server"].startswith(COLD_START_SERVER_PREFIXES)
    ]


def build_meta(args: argparse.Namespace, sources: dict) -> dict:
    return {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "since": args.since,
        "until": args.until,
        "log_dir": str(sources["log_dir"]),
        "transcripts_glob": sources["transcripts_glob"],
        "counts": {
            "searches": len(sources["records"]), "expands": len(sources["expands"]),
            "transcript search calls": len(sources["calls"]),
        },
    }


def write_report(report: str, report_dir: Path, since: str | None, until: str | None) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    window = f"{_slug(since) or 'start'}_{_slug(until) or 'now'}"
    path = report_dir / f"kvp_report_{window}_{stamp}.md"
    path.write_text(report, encoding="utf-8")
    return path


def _slug(value: str | None) -> str:
    return "".join(c if c.isalnum() else "-" for c in value) if value else ""


if __name__ == "__main__":
    main()
