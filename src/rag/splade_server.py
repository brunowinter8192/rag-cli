# INFRASTRUCTURE
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SparseEncoder

from src.rag.config import SPLADE_MODEL
from src.rag.log_setup import get_logger

logger = get_logger("splade_server")

MAX_ACTIVE_DIMS = 256

model = SparseEncoder(SPLADE_MODEL)

app = FastAPI()


class EmbedRequest(BaseModel):
    input: list[str]
    model: str = "splade"


# ORCHESTRATOR

@app.post("/v1/sparse-embeddings")
def sparse_embeddings(req: EmbedRequest):
    vectors = encode_sparse(req.input)
    response = build_response(vectors)
    log_encoded(req.input)
    return response


# FUNCTIONS

def encode_sparse(texts: list[str]) -> list[dict]:
    tensors = model.encode(texts, convert_to_tensor=False, max_active_dims=MAX_ACTIVE_DIMS)
    results = []
    for t in tensors:
        t = t.coalesce()
        indices = t.indices().squeeze(0).tolist()
        values = [round(v, 6) for v in t.values().tolist()]
        results.append({"indices": indices, "values": values})
    return results


def build_response(vectors: list[dict]) -> dict:
    return {"data": [{"index": i, "sparse_vector": vector} for i, vector in enumerate(vectors)]}


def log_encoded(texts: list[str]) -> None:
    logger.info(f"Encoded {len(texts)} texts")


@app.get("/health")
def health():
    return {"status": "ok"}
