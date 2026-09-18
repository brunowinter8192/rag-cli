# INFRASTRUCTURE
import os

import httpx
from dotenv import load_dotenv

from .server_manager import ensure_ready, find_server_url, _touch_state_file
from .log_setup import get_logger

load_dotenv()

logger = get_logger("reranker")

RERANK_INSTRUCTION = None


# ORCHESTRATOR
def rerank_workflow(query: str, documents: list[dict], top_k: int) -> list[dict]:
    ensure_ready("reranker")
    contents = [doc['content'] for doc in documents]
    ranked = rerank_documents(query, contents)
    results = []
    for item in ranked[:top_k]:
        doc = documents[item['index']].copy()
        doc['score'] = round(item['relevance_score'], 6)
        results.append(doc)
    logger.info(f"Reranked {len(documents)} docs to top {top_k} for '{query[:50]}...'")
    return results


# FUNCTIONS

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


def rerank_documents(query: str, contents: list[str]) -> list[dict]:
    url = _rerank_url()
    _touch_state_file(int(url.split(":")[2].split("/")[0]))
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
    results = data.get("results", data)
    return sorted(results, key=lambda x: x['relevance_score'], reverse=True)
