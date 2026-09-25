# INFRASTRUCTURE
import argparse
import importlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

_error_log = importlib.import_module(".".join(["src", "rag", "error_log"]))

ERROR_CODES = _error_log.ERROR_CODES
ERRORS_FILE = _error_log.ERRORS_FILE
DEFAULT_TAIL = 10


# ORCHESTRATOR

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Filter errors.jsonl to anomaly codes and print summary + detail."
    )
    parser.add_argument("--all", dest="all_", action="store_true",
                        help="Include full history (default: today only)")
    parser.add_argument("--tail", type=int, default=DEFAULT_TAIL, metavar="N",
                        help=f"Number of detail entries to show (default {DEFAULT_TAIL})")
    parser.add_argument("--raw", action="store_true",
                        help="Dump matching entries as raw JSONL (for piping)")
    args = parser.parse_args()

    entries = _load_entries(all_=args.all_)

    if args.raw:
        _print_raw(entries)
        return

    label = "all time" if args.all_ else "today"
    print(f"Anomaly entries ({label}): {len(entries)}")
    if not entries:
        return

    _print_summary(entries)
    print()
    _print_detail(entries, args.tail)


# FUNCTIONS

def _load_entries(all_: bool) -> list[dict]:
    try:
        lines = ERRORS_FILE.read_text().splitlines()
    except FileNotFoundError:
        return []
    parsed = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            parsed.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if not all_:
        now_local = datetime.now().astimezone()
        today_start = now_local.replace(
            hour=0, minute=0, second=0, microsecond=0
        ).astimezone(timezone.utc)
        parsed = [e for e in parsed if datetime.fromisoformat(e["ts"]) >= today_start]
    return [e for e in parsed if e.get("code") in ERROR_CODES]


def _print_summary(entries: list[dict]) -> None:
    by_code = Counter(e["code"] for e in entries)
    by_server = Counter(e["server"] for e in entries)
    print("By code:")
    for code, cnt in by_code.most_common():
        print(f"  {code}: {cnt}")
    print("By server:")
    for srv, cnt in by_server.most_common():
        print(f"  {srv}: {cnt}")


def _print_detail(entries: list[dict], n: int) -> None:
    shown = entries[-n:]
    print(f"Last {len(shown)} entr{'y' if len(shown) == 1 else 'ies'}:")
    for e in shown:
        ts = datetime.fromisoformat(e["ts"]).astimezone().strftime("%Y-%m-%d %H:%M:%S")
        extras = " ".join(
            f"{k}={v}" for k, v in e.items()
            if k not in {"ts", "server", "code", "msg"}
        )
        line = f"  {ts} | {e['server']} | {e['code']} | {e['msg']}"
        if extras:
            line += f" | {extras}"
        print(line)


def _print_raw(entries: list[dict]) -> None:
    for e in entries:
        print(json.dumps(e))


if __name__ == "__main__":
    main()
