# INFRASTRUCTURE
import os

from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SparseEncoder

from .log_setup import get_logger

logger = get_logger("splade_server")

SPLADE_MODEL = "naver/splade-v3"
SPLADE_PORT = int(os.getenv("SPLADE_PORT", "8083"))
MAX_ACTIVE_DIMS = 256

model = SparseEncoder(SPLADE_MODEL)

app = FastAPI()


class EmbedRequest(BaseModel):
    input: list[str]
    model: str = "splade"


# ORCHESTRATOR

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/sparse-embeddings")
def sparse_embeddings(req: EmbedRequest):
    vectors = encode_sparse(req.input)
    data = [
        {"index": i, "sparse_vector": vectors[i]}
        for i in range(len(req.input))
    ]
    logger.info(f"Encoded {len(req.input)} texts")
    return {"data": data}


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SPLADE_PORT)
