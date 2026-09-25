# INFRASTRUCTURE
from src.rag.config import DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP
from src.rag.log_setup import get_logger

logger = get_logger("chunker")


# ORCHESTRATOR
def chunk_workflow(
    file_path: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP
) -> list[dict]:
    content = load_file(file_path)
    chunks = chunk_semantic(content, chunk_size, overlap)
    enriched = enrich_chunks(chunks, file_path)
    logger.info(f"Chunked {file_path}: {len(enriched)} chunks")
    return enriched


# FUNCTIONS

def load_file(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def chunk_semantic(content: str, chunk_size: int, overlap: int) -> list[str]:
    separators = ["\n\n", "\n", ". ", "! ", "? ", " "]
    splits = recursive_split(content, separators, chunk_size)
    return merge_with_overlap(splits, chunk_size, overlap)


def recursive_split(text: str, separators: list[str], chunk_size: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    if not separators:
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size) if text[i:i+chunk_size].strip()]

    sep = separators[0]
    remaining_seps = separators[1:]

    parts = text.split(sep)
    result = []

    for i, part in enumerate(parts):
        if i < len(parts) - 1:
            part = part + sep

        if len(part) <= chunk_size:
            result.append(part)
        else:
            result.extend(recursive_split(part, remaining_seps, chunk_size))

    return result


def get_word_aligned_overlap(text: str, overlap: int) -> str:
    if not text or overlap <= 0:
        return ""
    raw = text[-overlap:]
    space_idx = raw.find(" ")
    if space_idx != -1 and space_idx < len(raw) - 1:
        return raw[space_idx + 1:]
    return raw


def merge_with_overlap(splits: list[str], chunk_size: int, overlap: int) -> list[str]:
    if not splits:
        return []

    chunks = []
    current = ""

    for split in splits:
        if len(current) + len(split) <= chunk_size:
            current += split
        else:
            if current.strip():
                chunks.append(current.strip())
            overlap_text = get_word_aligned_overlap(current, overlap)
            current = overlap_text + split

    if current.strip():
        chunks.append(current.strip())

    return chunks


def enrich_chunks(chunks: list[str], file_path: str) -> list[dict]:
    return [
        {
            "content": chunk,
            "source": file_path,
            "index": i,
            "total_chunks": len(chunks)
        }
        for i, chunk in enumerate(chunks)
    ]
