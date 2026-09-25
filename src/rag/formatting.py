# FUNCTIONS

def format_results(results: list[dict]) -> str:
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"--- Result {i} (score: {r['score']}) ---")
        if 'chunk_end' in r and r['chunk_end'] != r['chunk_index']:
            chunk_info = f"Chunks: {r['chunk_index']}-{r['chunk_end']}"
        else:
            chunk_info = f"Chunk: {r['chunk_index']}"
        lines.append(f"Collection: {r['collection']} | Document: {r['document']} | {chunk_info}")
        lines.append(r['content'])
        lines.append("")
    return "\n".join(lines)


def format_collections(results: list[dict]) -> str:
    if not results:
        return "No collections indexed."
    lines = ["Indexed Collections:", ""]
    for r in results:
        lines.append(f"  {r['collection']} ({r['chunks']} chunks)")
    return "\n".join(lines)


def format_documents(results: list[dict]) -> str:
    if not results:
        return "No documents in this collection."
    lines = ["Documents:", ""]
    for r in results:
        lines.append(f"  {r['document']} ({r['chunks']} chunks)")
    return "\n".join(lines)


def format_progress(results: list[dict], collection: str = "") -> str:
    if not results:
        return f"No documents found in collection '{collection}'." if collection else "No documents found."
    name_width = max(len(r["document"]) for r in results)
    header = f"Indexing Progress: {collection}" if collection else "Indexing Progress"
    lines = [header, ""]
    lines.append(f"  {'Document'.ljust(name_width)}  {'Done':>6} / {'Total':<6}  {'%':>6}  Status")
    for r in results:
        done = r["done"]
        total = r["total"]
        pct = (100.0 * done / total) if total else 0.0
        status = "done" if done >= total else "in-progress"
        lines.append(
            f"  {r['document'].ljust(name_width)}  {done:>6} / {total:<6}  {pct:>5.1f}%  {status}"
        )
    return "\n".join(lines)
