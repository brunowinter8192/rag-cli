# INFRASTRUCTURE
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CHUNK_SIZE = 2000
OVERLAP = 400
SEPARATORS = ["\n\n", "\n", ". ", "! ", "? ", " "]


# FUNCTIONS

def chunk_file(path: str, chunk_size: int | None = None, overlap: int | None = None) -> list[dict]:
    if chunk_size is None:
        chunk_size = CHUNK_SIZE
    if overlap is None:
        overlap = OVERLAP
    content = Path(path).read_text(encoding='utf-8')
    chunks = chunk_text(content, chunk_size, overlap)
    doc_name = Path(path).name
    return [
        {
            "content": chunk,
            "source": path,
            "document": doc_name,
            "chunk_index": i,
            "total_chunks": len(chunks),
        }
        for i, chunk in enumerate(chunks)
    ]


def chunk_text(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    if chunk_size is None:
        chunk_size = CHUNK_SIZE
    if overlap is None:
        overlap = OVERLAP
    splits = recursive_split(text, SEPARATORS, chunk_size)
    return merge_with_overlap(splits, chunk_size, overlap)


def recursive_split(text: str, separators: list[str], chunk_size: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    if not separators:
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size) if text[i:i + chunk_size].strip()]

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
