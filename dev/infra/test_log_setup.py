# INFRASTRUCTURE

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from strand_runner import load_rag, run_strands


# ORCHESTRATOR

def run_all() -> None:
    run_strands([
        test_get_logger_writes_to_its_own_file,
        test_get_logger_is_idempotent,
        test_two_names_get_two_files,
    ])


# FUNCTIONS

def test_get_logger_writes_to_its_own_file(workdir: Path) -> None:
    log_setup = load_rag("log_setup")
    logger = log_setup.get_logger("chunker")
    log_path = Path(logger.handlers[0].baseFilename)
    logger.info("probe line one")
    logger.handlers[0].flush()
    assert log_path == workdir / "src" / "rag" / "logs" / "chunker.log", log_path
    assert "probe line one" in log_path.read_text()


def test_get_logger_is_idempotent(workdir: Path) -> None:
    log_setup = load_rag("log_setup")
    first = log_setup.get_logger("embedder")
    second = log_setup.get_logger("embedder")
    assert first is second, "same name must return the same logger"
    assert len(first.handlers) == 1, "repeated calls must not duplicate handlers"


def test_two_names_get_two_files(workdir: Path) -> None:
    log_setup = load_rag("log_setup")
    a = log_setup.get_logger("reranker")
    b = log_setup.get_logger("retriever_probe_b")
    assert a.handlers[0].baseFilename != b.handlers[0].baseFilename


if __name__ == "__main__":
    run_all()
