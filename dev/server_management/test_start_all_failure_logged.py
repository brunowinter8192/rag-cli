# INFRASTRUCTURE

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from strand_runner import load_rag, run_strands


# ORCHESTRATOR

def run_all() -> None:
    run_strands([
        test_start_all_reports_and_logs_failed_starts,
    ])


# FUNCTIONS

def test_start_all_reports_and_logs_failed_starts(workdir: Path) -> None:
    server_lifecycle = load_rag("server_lifecycle")
    results = server_lifecycle.start_all()
    assert set(results) == {"embedding-8b", "reranker-0.6b", "splade"}, results
    assert all(v.startswith("error: ") for v in results.values()), results
    for handler in server_lifecycle.logger.handlers:
        handler.flush()
    log_text = (workdir / "src" / "rag" / "logs" / "server_lifecycle.log").read_text()
    for name in results:
        assert f"start_all: {name} failed:" in log_text, log_text


if __name__ == "__main__":
    run_all()
