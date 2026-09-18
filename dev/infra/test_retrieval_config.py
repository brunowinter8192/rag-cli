# INFRASTRUCTURE

import hashlib
import json
import re

_QUANT_PATTERN = re.compile(r"(Q\d[A-Z0-9_]*|BF16|F16|F32)$", re.IGNORECASE)


# FUNCTIONS

def extract_quantization(model_name: str | None) -> str | None:
    if not model_name:
        return None
    match = _QUANT_PATTERN.search(model_name)
    return match.group(1).upper() if match else None


def context_size_for_preset(servers: dict, name: str | None) -> int | None:
    if name is None or name not in servers:
        return None
    flags = servers[name].get("extra_flags", [])
    if "-c" not in flags:
        return None
    try:
        return int(flags[flags.index("-c") + 1])
    except (IndexError, ValueError):
        return None


def build_hash_input(snapshot: dict) -> dict:
    embedding = snapshot["embedding"]
    reranker = snapshot["reranker"]
    return {
        "embedding_model_name": embedding["model_name"],
        "embedding_context_size": embedding["context_size"],
        "embedding_vector_dimension": embedding["vector_dimension"],
        "query_prefix": snapshot["query_prefix"],
        "truncation_limit_tokens": snapshot["truncation_limit_tokens"],
        "reranker_model_name": reranker["model_name"],
        "reranker_context_size": reranker["context_size"],
        "reranker_instruction": reranker["instruction"],
        "candidate_count_requested": snapshot["candidate_count_requested"],
    }


def compute_fingerprint(snapshot: dict) -> str:
    hash_input = build_hash_input(snapshot)
    canonical = json.dumps(hash_input, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _sample_snapshot(query_prefix: str = "Instruct: ...", model_name: str = "Qwen3-Embedding-8B-Q8_0") -> dict:
    return {
        "embedding": {
            "preset": "embedding-8b",
            "model_name": model_name,
            "model_path": "/models/Qwen3-Embedding-8B-Q8_0.gguf",
            "quantization": "Q8_0",
            "context_size": 2048,
            "vector_dimension": 4096,
        },
        "query_prefix": query_prefix,
        "truncation_limit_tokens": 4000,
        "reranker": {
            "preset": "reranker-0.6b",
            "model_name": "qwen3-reranker-0.6b-q8_0",
            "model_path": "/models/qwen3-reranker-0.6b-q8_0.gguf",
            "quantization": "Q8_0",
            "context_size": 32768,
            "instruction": None,
        },
        "candidate_count_requested": 30,
    }


def test_quantization_extraction_both_casings():
    assert extract_quantization("Qwen3-Embedding-8B-Q8_0") == "Q8_0"
    assert extract_quantization("qwen3-reranker-0.6b-q8_0") == "Q8_0"
    assert extract_quantization(None) is None
    assert extract_quantization("model-with-no-quant-token") is None
    print("PASS: quantization extraction handles both casings and absence")


def test_context_size_for_preset():
    servers = {
        "embedding-8b": {"extra_flags": ["-ngl", "99", "-c", "2048"]},
        "splade": {"extra_flags": []},
    }
    assert context_size_for_preset(servers, "embedding-8b") == 2048
    assert context_size_for_preset(servers, "splade") is None
    assert context_size_for_preset(servers, None) is None
    assert context_size_for_preset(servers, "unknown-preset") is None
    print("PASS: context_size_for_preset reads the launch-intent -c flag, null when absent")


def test_fingerprint_is_deterministic():
    a = compute_fingerprint(_sample_snapshot())
    b = compute_fingerprint(_sample_snapshot())
    assert a == b, (a, b)
    print("PASS: two identical snapshots produce the identical fingerprint")


def test_fingerprint_changes_with_query_prefix():
    a = compute_fingerprint(_sample_snapshot(query_prefix="Instruct: ..."))
    b = compute_fingerprint(_sample_snapshot(query_prefix="A different prefix entirely"))
    assert a != b, "changing the query prefix must change the fingerprint"
    print("PASS: changing the query prefix changes the fingerprint")


def test_fingerprint_ignores_redundant_fields():
    base = _sample_snapshot()
    renamed_preset = _sample_snapshot()
    renamed_preset["embedding"]["preset"] = "some-other-preset-name"
    assert compute_fingerprint(base) == compute_fingerprint(renamed_preset), (
        "preset name is excluded from the hash by design"
    )
    print("PASS: preset name alone does not change the fingerprint (excluded by design)")


if __name__ == "__main__":
    test_quantization_extraction_both_casings()
    test_context_size_for_preset()
    test_fingerprint_is_deterministic()
    test_fingerprint_changes_with_query_prefix()
    test_fingerprint_ignores_redundant_fields()
    print("All tests passed.")
