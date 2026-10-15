# INFRASTRUCTURE

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from strand_runner import run_strands

from dev.kvp import kvp_report

FIXTURES = Path(__file__).parent / "fixtures"
STAMPED_VERSION = "abc1234567"
LOG_FILES = ("search.jsonl", "search_content.jsonl", "expand.jsonl", "config_registry.jsonl", "errors.jsonl")


# ORCHESTRATOR

def run_all() -> None:
    run_strands([
        test_report_covers_all_three_levels_on_fixture_logs,
        test_stamped_records_get_their_own_version_row,
        test_window_excludes_records_before_since,
    ])


# FUNCTIONS

def _run_report(workdir: Path, extra_args: list[str] | None = None, stamp_from: str | None = None) -> str:
    log_dir = workdir / "logs"
    log_dir.mkdir()
    for name in LOG_FILES:
        shutil.copy(FIXTURES / name, log_dir / name)
    if stamp_from:
        _stamp_records(log_dir / "search.jsonl", stamp_from)
    kvp_report.REPORT_DIR = workdir / "md"
    sys.argv = ["kvp_report", "--log-dir", str(log_dir), "--transcripts-glob", str(FIXTURES / "transcript.jsonl"), *(extra_args or [])]
    kvp_report.main()
    reports = list((workdir / "md").glob("kvp_report_*.md"))
    assert len(reports) == 1
    return reports[0].read_text(encoding="utf-8")


def _stamp_records(path: Path, stamp_from: str) -> None:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    for record in records:
        if record["ts"] >= stamp_from:
            record["code_version"] = STAMPED_VERSION
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


def test_report_covers_all_three_levels_on_fixture_logs(workdir: Path) -> None:
    report = _run_report(workdir)
    for heading in ("## Technical", "## Relevance", "## Usefulness", "### Cross-project reference reach", "### Context overflow"):
        assert heading in report, heading
    assert "| all | 9 | 7/9 (77.8 %) | 2 (2 with 0 candidates) |" in report
    assert "| all | 3 | 1/3 (33.3 %) | 0/2 (0.0 %) | 1/1 (100.0 %) | 1 |" in report
    assert "| all | 2 | 2/2 (100.0 %) | 1/2 (50.0 %) | 1/2 (50.0 %) |" in report
    assert "block_cli_chained.py" in report
    assert "2026-10-14 caller-rule change is unknown" in report


def test_stamped_records_get_their_own_version_row(workdir: Path) -> None:
    report = _run_report(workdir, stamp_from="2026-10-01")
    assert f"| {STAMPED_VERSION} | 5 |" in report
    assert "| unversioned | 4 |" in report


def test_window_excludes_records_before_since(workdir: Path) -> None:
    report = _run_report(workdir, ["--since", "2026-10-14"])
    assert "searches: 3, expands: 0" in report
    assert "| all | 3 |" in report


if __name__ == "__main__":
    run_all()
