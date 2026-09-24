# INFRASTRUCTURE

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from strand_runner import load_rag, run_strands


# ORCHESTRATOR

def run_all() -> None:
    run_strands([
        test_quantization_extraction_both_casings,
        test_context_size_for_preset,
        test_build_model_config_from_state,
        test_fingerprint_is_deterministic,
        test_fingerprint_changes_with_query_prefix,
        test_fingerprint_ignores_redundant_fields,
    ])


# FUNCTIONS

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


def test_quantization_extraction_both_casings(workdir: Path) -> None:
    config = load_rag("retrieval_config")
    assert config.extract_quantization("Qwen3-Embedding-8B-Q8_0") == "Q8_0"
    assert config.extract_quantization("qwen3-reranker-0.6b-q8_0") == "Q8_0"
    assert config.extract_quantization(None) is None
    assert config.extract_quantization("model-with-no-quant-token") is None


def test_context_size_for_preset(workdir: Path) -> None:
    server_utils = load_rag("server_utils")
    assert server_utils.context_size_for_preset("embedding-8b") == 2048
    assert server_utils.context_size_for_preset("reranker-0.6b") == 32768
    assert server_utils.context_size_for_preset(None) is None
    assert server_utils.context_size_for_preset("unknown-preset") is None


def test_build_model_config_from_state(workdir: Path) -> None:
    config = load_rag("retrieval_config")
    state = {"name": "embedding-8b", "model_name": "Qwen3-Embedding-8B-Q8_0", "model_path": "/models/x.gguf"}
    built = config.build_model_config(state)
    assert built == {
        "preset": "embedding-8b",
        "model_name": "Qwen3-Embedding-8B-Q8_0",
        "model_path": "/models/x.gguf",
        "quantization": "Q8_0",
        "context_size": 2048,
    }, built
    assert set(config.build_model_config(None).values()) == {None}


def test_fingerprint_is_deterministic(workdir: Path) -> None:
    retrieval_log = load_rag("retrieval_log")
    a = retrieval_log.compute_fingerprint(_sample_snapshot())
    b = retrieval_log.compute_fingerprint(_sample_snapshot())
    assert a == b, (a, b)


def test_fingerprint_changes_with_query_prefix(workdir: Path) -> None:
    retrieval_log = load_rag("retrieval_log")
    a = retrieval_log.compute_fingerprint(_sample_snapshot(query_prefix="Instruct: ..."))
    b = retrieval_log.compute_fingerprint(_sample_snapshot(query_prefix="A different prefix entirely"))
    assert a != b, "changing the query prefix must change the fingerprint"


def test_fingerprint_ignores_redundant_fields(workdir: Path) -> None:
    retrieval_log = load_rag("retrieval_log")
    renamed_preset = _sample_snapshot()
    renamed_preset["embedding"]["preset"] = "some-other-preset-name"
    assert retrieval_log.compute_fingerprint(_sample_snapshot()) == retrieval_log.compute_fingerprint(renamed_preset), (
        "preset name is excluded from the hash by design"
    )


if __name__ == "__main__":
    run_all()
