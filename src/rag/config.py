# INFRASTRUCTURE
import os
from pathlib import Path

LOCK_DIR = Path.home() / ".rag-locks"
SERVER_LOG_DIR = LOCK_DIR / "logs"

RAG_ROOT = Path(os.getenv("RAG_PROJECT_ROOT", str(Path(__file__).parent.parent.parent)))
LLAMA_SERVER_PATH = os.getenv("LLAMA_SERVER_PATH", str(RAG_ROOT / "llama.cpp/build/bin/llama-server"))

SPLADE_MODEL = "naver/splade-v3"

DEFAULT_CHUNK_SIZE = 2000
DEFAULT_OVERLAP = 400

HELP_TEXT = (
    "You triggered the help function. Usage sits in your rules. "
    "Report to the user why you needed help and go idle immediately."
)
