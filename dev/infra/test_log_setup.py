# INFRASTRUCTURE

import logging
import tempfile
from pathlib import Path

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


# FUNCTIONS

def get_logger(log_root: Path, name: str) -> logging.Logger:
    logger = logging.getLogger(f"rag_dev_probe.{name}")
    if not logger.handlers:
        handler = logging.FileHandler(log_root / f"{name}.log")
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def test_get_logger_writes_to_its_own_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_root = Path(tmpdir)
        logger = get_logger(log_root, "chunker")
        log_path = Path(logger.handlers[0].baseFilename)
        logger.info("probe line one")
        content = log_path.read_text()
        assert log_path.name == "chunker.log", log_path.name
        assert "probe line one" in content, content
    print("PASS: get_logger writes into its own named file")


def test_get_logger_is_idempotent():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_root = Path(tmpdir)
        first = get_logger(log_root, "embedder")
        second = get_logger(log_root, "embedder")
        assert first is second, "same name must return the same logger"
        assert len(first.handlers) == 1, "repeated calls must not duplicate handlers"
    print("PASS: get_logger does not duplicate handlers on repeated calls")


def test_two_names_get_two_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_root = Path(tmpdir)
        a = get_logger(log_root, "reranker")
        b = get_logger(log_root, "retriever_probe_b")
        assert a.handlers[0].baseFilename != b.handlers[0].baseFilename
    print("PASS: distinct module names resolve to distinct files")


if __name__ == "__main__":
    test_get_logger_writes_to_its_own_file()
    test_get_logger_is_idempotent()
    test_two_names_get_two_files()
    print("All tests passed.")
