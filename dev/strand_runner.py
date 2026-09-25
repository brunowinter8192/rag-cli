# INFRASTRUCTURE

import importlib
import os
import shutil
import sys
import tempfile
import traceback
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path

SRC_DIR = Path(__file__).parent.parent / "src"
TEST_ENV = {
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5433",
    "POSTGRES_USER": "rag",
    "POSTGRES_PASSWORD": "rag",
    "POSTGRES_DB": "rag",
    "EMBEDDING_MODEL": "Qwen3-Embedding-8B",
    "VECTOR_DIMENSION": "4096",
}


# ORCHESTRATOR

def run_strands(strands: list) -> None:
    selected = select_strands(strands, sys.argv[1:])
    results = execute_strands(selected)
    report(results)


# FUNCTIONS

def select_strands(strands: list, names: list[str]) -> list:
    if not names:
        return strands
    by_name = {strand.__name__: strand for strand in strands}
    unknown = [name for name in names if name not in by_name]
    if unknown:
        sys.exit(f"unknown strand(s) {unknown}; available: {sorted(by_name)}")
    return [by_name[name] for name in names]


def execute_strands(strands: list) -> list[tuple[str, str | None]]:
    with ProcessPoolExecutor(
        max_workers=len(strands),
        mp_context=get_context("spawn"),
        max_tasks_per_child=1,
    ) as pool:
        futures = [pool.submit(_run_strand, strand) for strand in strands]
        return [future.result() for future in futures]


def _run_strand(strand) -> tuple[str, str | None]:
    workdir = Path(tempfile.mkdtemp(prefix="rag_strand_"))
    try:
        shutil.copytree(SRC_DIR, workdir / "src", ignore=shutil.ignore_patterns("__pycache__", "logs"))
        sys.path.insert(0, str(workdir))
        (workdir / "home").mkdir()
        os.environ["HOME"] = str(workdir / "home")
        os.environ.update(TEST_ENV)
        strand(workdir)
        return strand.__name__, None
    except BaseException:
        return strand.__name__, traceback.format_exc()
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def report(results: list[tuple[str, str | None]]) -> None:
    failed = [(name, error) for name, error in results if error is not None]
    for name, error in results:
        print(f"[{'FAIL' if error else 'PASS'}] {name}")
    for name, error in failed:
        print(f"\n--- {name} ---\n{error}")
    print()
    if failed:
        print(f"{len(failed)} of {len(results)} strand(s) failed: {[name for name, _ in failed]}")
        sys.exit(1)
    print(f"All {len(results)} strands passed.")


def load_rag(module_name: str):
    return importlib.import_module(".".join(["src", "rag", module_name]))
