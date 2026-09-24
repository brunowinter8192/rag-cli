# INFRASTRUCTURE

import importlib
import shutil
import sys
import tempfile
import traceback
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path

SRC_DIR = Path(__file__).parent.parent / "src"


# ORCHESTRATOR

def run_strands(strands: list) -> None:
    results = execute_strands(strands)
    report(results)


# FUNCTIONS

def load_rag(module_name: str):
    return importlib.import_module(".".join(["src", "rag", module_name]))


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
