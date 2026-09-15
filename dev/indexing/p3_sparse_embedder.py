# INFRASTRUCTURE
import logging
import os

import httpx

logger = logging.getLogger(__name__)

SPLADE_URL = os.getenv("SPLADE_URL", "http://localhost:8083/v1/sparse-embeddings")


# FUNCTIONS

def embed_sparse(texts: list[str]) -> list[dict]:
    response = httpx.post(
        SPLADE_URL,
        json={"input": texts, "model": "splade"},
        timeout=300.0,
    )
    response.raise_for_status()
    data = response.json()
    return [item["sparse_vector"] for item in data["data"]]
