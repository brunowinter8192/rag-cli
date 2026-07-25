# INFRASTRUCTURE
import json
import re
import sys

NGRAM_SIZE = 3
WORD_PATTERN = re.compile(r"[A-Za-z][A-Za-z\-']*")
STOPWORDS = {
    "a", "an", "the", "of", "in", "on", "for", "to", "and", "or", "is", "are",
    "be", "by", "with", "as", "at", "from", "that", "this", "it", "its", "which",
}


# ORCHESTRATOR
# Report n-gram overlap between each theme's summary and its source passages, for human leakage review
def audit_leakage_workflow(pass_c_path, source_path, pass_b_path):
    pass_c = load_json(pass_c_path)
    source_lines = load_source_lines(source_path)
    pass_b = load_json(pass_b_path)
    theme_spans = {t["id"]: t["spans"] for t in pass_b["themes"]}

    for summary in pass_c["summaries"]:
        theme_id = summary["theme_id"]
        passage_text = extract_passage_text(source_lines, theme_spans.get(theme_id, []))
        summary_text = build_summary_text(summary)
        candidates = shared_ngrams(passage_text, summary_text, NGRAM_SIZE)
        print_theme_report(theme_id, candidates)


# FUNCTIONS

# Load and parse the input JSON, failing loudly on missing file or bad JSON
def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        sys.exit(f"ERROR: input file not found: {path}")
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: input file is not valid JSON: {path} ({e})")


# Load the source markdown, failing loudly on missing file
def load_source_lines(path):
    try:
        with open(path) as f:
            return f.read().splitlines()
    except FileNotFoundError:
        sys.exit(f"ERROR: source document not found: {path}")


# Concatenate the raw text of a theme's source line spans
def extract_passage_text(source_lines, spans):
    parts = []
    for span in spans:
        parts.extend(source_lines[span["line_start"] - 1:span["line_end"]])
    return " ".join(parts)


# Concatenate a summary's textual fields into one string
def build_summary_text(summary):
    return " ".join([
        summary["field"], summary["information_need"],
        " ".join(summary["sub_concepts"]), summary["answer_type"],
    ])


# Tokenize to lowercase words, dropping stopwords
def tokenize(text):
    return [w.lower() for w in WORD_PATTERN.findall(text) if w.lower() not in STOPWORDS]


# Build the set of n-grams shared between passage text and summary text
def shared_ngrams(passage_text, summary_text, n):
    passage_ngrams = ngram_set(tokenize(passage_text), n)
    summary_ngrams = ngram_set(tokenize(summary_text), n)
    return sorted(passage_ngrams & summary_ngrams)


# Build the set of n-gram strings from a token list
def ngram_set(tokens, n):
    return {" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


# Print the leakage-candidate report for one theme
def print_theme_report(theme_id, candidates):
    print(f"--- {theme_id} ---")
    if not candidates:
        print("  (no shared n-grams >= {}-gram)".format(NGRAM_SIZE))
        return
    for ngram in candidates:
        print(f"  {ngram}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("usage: python3 eval/scripts/audit_leakage.py <pass_c_json> <source_md> <pass_b_json>")
    audit_leakage_workflow(sys.argv[1], sys.argv[2], sys.argv[3])
