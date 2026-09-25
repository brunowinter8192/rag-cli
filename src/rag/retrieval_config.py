# INFRASTRUCTURE
import re

from src.rag.embedder import MAX_TOKENS
from src.rag.reranker import RERANK_INSTRUCTION
from src.rag.search_primitives import DEFAULT_QUERY_PREFIX
from src.rag.server_state import find_server_state
from src.rag.server_utils import context_size_for_preset

_QUANT_PATTERN = re.compile(r"(Q\d[A-Z0-9_]*|BF16|F16|F32)$", re.IGNORECASE)


# ORCHESTRATOR

def resolve_search_config(vector_dimension: int, candidates_requested: int) -> dict:
    embedding = resolve_embedding_config(vector_dimension)
    reranker = resolve_reranker_config()
    return {
        "embedding": embedding,
        "query_prefix": DEFAULT_QUERY_PREFIX,
        "truncation_limit_tokens": MAX_TOKENS,
        "reranker": reranker,
        "candidate_count_requested": candidates_requested,
    }


# FUNCTIONS

def resolve_embedding_config(vector_dimension: int) -> dict:
    state = find_server_state("embedding")
    config = build_model_config(state)
    config["vector_dimension"] = vector_dimension
    return config


def resolve_reranker_config() -> dict:
    state = find_server_state("reranker")
    config = build_model_config(state)
    config["instruction"] = RERANK_INSTRUCTION
    return config


def build_model_config(state: dict | None) -> dict:
    if state is None:
        return {
            "preset": None,
            "model_name": None,
            "model_path": None,
            "quantization": None,
            "context_size": None,
        }
    preset = state.get("name")
    model_name = state.get("model_name")
    return {
        "preset": preset,
        "model_name": model_name,
        "model_path": state.get("model_path"),
        "quantization": extract_quantization(model_name),
        "context_size": context_size_for_preset(preset),
    }


def extract_quantization(model_name: str | None) -> str | None:
    if not model_name:
        return None
    match = _QUANT_PATTERN.search(model_name)
    return match.group(1).upper() if match else None
