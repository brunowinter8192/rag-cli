# INFRASTRUCTURE
from pathlib import Path

MAIN_CHECKOUT = Path("/Users/brunowinter2000/Documents/ai/Meta/ClaudeCode/cli/rag-cli")

DEFAULT_LOG_DIR = MAIN_CHECKOUT / "src" / "rag" / "logs"
DEFAULT_TRANSCRIPTS_GLOB = str(Path.home() / ".claude" / "projects" / "*" / "*.jsonl")
REPORT_DIR = Path(__file__).parent / "md"
CANARY_CASES_PATH = Path(__file__).parent / "canary_cases.json"
CANARY_JSON_DIR = Path(__file__).parent / "json"

SEARCH_LOG_NAME = "search.jsonl"
SEARCH_CONTENT_NAME = "search_content.jsonl"
EXPAND_LOG_NAME = "expand.jsonl"
REGISTRY_NAME = "config_registry.jsonl"
ERRORS_NAME = "errors.jsonl"

UNVERSIONED = "unversioned"
ALL_GROUP = "all"

PERSIST_THRESHOLD_CHARS = 30000
EXPAND_ATTRIBUTION_WINDOW_MINUTES = 60
JOIN_MARGIN_SECONDS = 2
COLD_START_LEFT_MARGIN_SECONDS = 1
SCORE_PROFILE_RANKS = (1, 3, 6, 12)
SLOWEST_WARM_LISTED = 5

REFERENCE_SUFFIX = "-reference"
DOCS_SUFFIX = "-docs"
COLD_START_SERVER_PREFIXES = ("embedding", "reranker")
COLD_START_CODE = "start_initiated"
LOG_FAILURE_CODES = ("log_write_failed", "log_config_resolve_failed")

RESULT_EXECUTED = "executed"
RESULT_PERSISTED = "persisted"
RESULT_HOOK_BLOCKED = "hook_blocked"
RELATION_OWN = "own"
RELATION_FOREIGN = "foreign"
RELATION_UNKNOWN_PROJECT = "unknown_project"
EXPAND_EXACT = "exact"
EXPAND_DOCUMENT = "document"
