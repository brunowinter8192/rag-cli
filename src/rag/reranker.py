# INFRASTRUCTURE
import os

import httpx
from dotenv import load_dotenv

from src.rag.log_setup import get_logger
from src.rag.server_manager import ensure_ready
from src.rag.server_state import find_server_url
from src.rag.server_utils import touch_state_file

load_dotenv()

logger = get_logger("reranker")

RERANK_INSTRUCTION = None


# ORCHESTRATOR
def rerank_workflow(query: str, documents: list[dict], top_k: int) -> list[dict]:
    ensure_ready("reranker")
    ranked = rerank_documents(query, extract_contents(documents))
    results = apply_scores(documents, ranked, top_k)
    log_reranked(query, documents, top_k)
    return results


# FUNCTIONS

def rerank_documents(query: str, contents: list[str]) -> list[dict]:
    url = _rerank_url()
    touch_state_file(int(url.split(":")[2].split("/")[0]))
    response = httpx.post(
        url,
        json={
            "query": query,
            "documents": contents,
            "top_n": len(contents)
        },
        timeout=60.0
    )
    response.raise_for_status()
    data = response.json()
    results = data["results"]
    return sorted(results, key=lambda x: x['relevance_score'], reverse=True)


def _rerank_url() -> str:
    env = os.getenv("RERANKER_URL")
    if env:
        return env
    base = find_server_url("reranker")
    if not base:
        raise RuntimeError(
            "Reranker server not running. Start with `rag-cli server start reranker`."
        )
    return f"{base}/v1/rerank"


def apply_scores(documents: list[dict], ranked: list[dict], top_k: int) -> list[dict]:
    results = []
    for item in ranked[:top_k]:
        doc = documents[item['index']].copy()
        doc['score'] = round(item['relevance_score'], 6)
        results.append(doc)
    return results


def log_reranked(query: str, documents: list[dict], top_k: int) -> None:
    logger.info(f"Reranked {len(documents)} docs to top {top_k} for '{query[:50]}...'")


def extract_contents(documents: list[dict]) -> list[str]:
    return [doc['content'] for doc in documents]
