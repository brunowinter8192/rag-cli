# INFRASTRUCTURE

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
NEEDS_FILE = DATA_DIR / "needs.json"
R_QUERIES_FILE = DATA_DIR / "r_queries.json"
RUNS_FILE = DATA_DIR / "runs.json"
CHUNKS_FILE = DATA_DIR / "chunks.json"
POOL_FILE = DATA_DIR / "pool.json"
JUDGMENTS_DIR = DATA_DIR / "judgments"
ARM_DEPTH = {"A": 12, "G": 12, "S": 3, "M": 12, "F": 3, "P": 3, "R": 5}


# FUNCTIONS

def load_json(path: Path):
    return json.loads(path.read_text())


def chunk_key(collection: str, document: str, chunk_index: int) -> str:
    return f"{collection}|{document}|{chunk_index}"
