# INFRASTRUCTURE
import logging
import os
from pathlib import Path
from typing import Union

import httpx
from dotenv import load_dotenv

from .server_manager import ensure_ready, find_server_url, _touch_state_file

load_dotenv()

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "embedder.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "Qwen3-Embedding-8B")
MAX_TOKENS = 4000
CHARS_PER_TOKEN = 3


# ORCHESTRATOR
def embed_workflow(texts: Union[str, list[str]], prefix: str | None = None) -> list[list[float]]:
    ensure_ready("embedding")
    if isinstance(texts, str):
        texts = [texts]
    texts = [truncate_to_max_tokens(t, MAX_TOKENS) for t in texts]
    embeddings = generate_embeddings(texts, prefix)
    logging.info(f"Embedded {len(texts)} texts")
    return embeddings


# FUNCTIONS

def _embedding_url() -> str:
    env = os.getenv("EMBEDDING_URL")
    if env:
        return env
    base = find_server_url("embedding")
    if not base:
        raise RuntimeError(
            "Embedding server not running. Start with `rag-cli server start embedding`."
        )
    return f"{base}/v1/embeddings"


def truncate_to_max_tokens(text: str, max_tokens: int) -> str:
    max_chars = max_tokens * CHARS_PER_TOKEN
    if len(text) <= max_chars:
        return text
    logging.warning(f"Truncated text from {len(text)} to {max_chars} chars (~{max_tokens} tokens)")
    return text[:max_chars]


def generate_embeddings(texts: list[str], prefix: str | None = None) -> list[list[float]]:
    if prefix:
        texts = [f"{prefix}{t}" for t in texts]
    url = _embedding_url()
    _touch_state_file(int(url.split(":")[2].split("/")[0]))
    response = httpx.post(
        url,
        json={"input": texts, "model": EMBEDDING_MODEL},
        timeout=300.0
    )
    response.raise_for_status()
    data = response.json()
    return [item["embedding"] for item in data["data"]]
