# INFRASTRUCTURE

import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from strand_runner import load_rag, run_strands

SHA_LENGTH = 10


# ORCHESTRATOR

def run_all() -> None:
    run_strands([
        test_clean_repo_gives_short_sha,
        test_modified_tracked_file_gives_dirty_suffix,
        test_untracked_file_does_not_make_dirty,
        test_non_repo_gives_unknown,
        test_search_record_carries_code_version,
        test_expand_record_carries_code_version_but_content_line_does_not,
    ])


# FUNCTIONS

def test_clean_repo_gives_short_sha(workdir: Path) -> None:
    code_version = load_rag("code_version")
    repo = _make_repo(workdir)
    version = code_version.read_code_version(repo)
    assert version == _head_sha(repo), version
    assert len(version) == SHA_LENGTH


def test_modified_tracked_file_gives_dirty_suffix(workdir: Path) -> None:
    code_version = load_rag("code_version")
    repo = _make_repo(workdir)
    (repo / "tracked.txt").write_text("changed\n")
    assert code_version.read_code_version(repo) == _head_sha(repo) + "+dirty"


def test_untracked_file_does_not_make_dirty(workdir: Path) -> None:
    code_version = load_rag("code_version")
    repo = _make_repo(workdir)
    (repo / "untracked.txt").write_text("new\n")
    assert code_version.read_code_version(repo) == _head_sha(repo)


def test_non_repo_gives_unknown(workdir: Path) -> None:
    code_version = load_rag("code_version")
    plain = workdir / "plain"
    plain.mkdir()
    assert code_version.read_code_version(plain) == "unknown"


def test_search_record_carries_code_version(workdir: Path) -> None:
    retrieval_log = load_rag("retrieval_log")
    record = retrieval_log.build_search_record("id1", "q", "c", None, None, 0, [], time.perf_counter(), None)
    assert record["code_version"] == "unknown", "the strand copy of src/ has no git repo"


def test_expand_record_carries_code_version_but_content_line_does_not(workdir: Path) -> None:
    expand_log = load_rag("expand_log")
    result = {"collection": "c", "document": "d.md", "chunk_index": 1, "before": 0, "after": 1, "chunks_returned": 2, "content": "text"}
    record = expand_log.build_expand_record("e1", result, time.perf_counter())
    line = expand_log.build_expand_content_line("e1", result)
    assert record["code_version"] == "unknown"
    assert "code_version" not in line


def _make_repo(workdir: Path) -> Path:
    repo = workdir / "repo"
    repo.mkdir()
    empty_hooks = workdir / "empty_hooks"
    empty_hooks.mkdir()
    (repo / "tracked.txt").write_text("v1\n")
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "-c", f"core.hooksPath={empty_hooks}", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init")
    return repo


def _head_sha(repo: Path) -> str:
    return _git(repo, "rev-parse", f"--short={SHA_LENGTH}", "HEAD").stdout.strip()


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True)


if __name__ == "__main__":
    run_all()
