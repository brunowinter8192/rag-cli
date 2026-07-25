# INFRASTRUCTURE
import json
import re
import sys

REQUIRED_TOP_KEYS = {"document", "queries"}
REQUIRED_QUERY_KEYS = {"theme_id", "format", "query"}
REQUIRED_FORMATS = {"keyword_bag", "natural_question", "field_sentence"}
WORD_PATTERN = re.compile(r"[A-Za-z][A-Za-z\-']*")
CLAUSE_BREAK = re.compile(r",\s*(?:and|but|or)\s+|[.;]", re.IGNORECASE)


# ORCHESTRATOR
# Validate a Pass D query-authoring output against its Pass C summaries
def validate_pass_d_workflow(pass_d_path, pass_c_path):
    pass_d = load_json(pass_d_path)
    schema_errors = check_schema(pass_d)
    if schema_errors:
        sys.exit("FAIL validate_pass_d\n" + "\n".join(schema_errors))

    pass_c = load_json(pass_c_path)
    primary_concepts = {s["theme_id"]: s["primary_concept"] for s in pass_c["summaries"]}

    errors = []
    errors += check_theme_format_completeness(pass_d, set(primary_concepts.keys()))
    for query in pass_d["queries"]:
        errors += check_head_concept(query, primary_concepts)
    if errors:
        sys.exit("FAIL validate_pass_d\n" + "\n".join(errors))

    print(f"OK validate_pass_d: {len(pass_d['queries'])} queries across "
          f"{len(primary_concepts)} themes, all checks passed")


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


# Verify top-level and per-query required keys are present, and format is one of the three allowed
def check_schema(pass_d):
    errors = []
    missing_top = REQUIRED_TOP_KEYS - pass_d.keys()
    if missing_top:
        errors.append(f"missing top-level keys: {sorted(missing_top)}")
        return errors
    if not isinstance(pass_d["queries"], list) or not pass_d["queries"]:
        errors.append("'queries' must be a non-empty list")
        return errors
    for i, query in enumerate(pass_d["queries"]):
        missing = REQUIRED_QUERY_KEYS - query.keys()
        if missing:
            errors.append(f"query index {i} missing keys: {sorted(missing)}")
            continue
        if query["format"] not in REQUIRED_FORMATS:
            errors.append(f"query index {i} (theme {query['theme_id']}): invalid format '{query['format']}', must be one of {sorted(REQUIRED_FORMATS)}")
    return errors


# Verify each Pass C theme has exactly 3 entries covering all three formats, no unknown theme_ids
def check_theme_format_completeness(pass_d, valid_theme_ids):
    errors = []
    by_theme = {}
    for query in pass_d["queries"]:
        by_theme.setdefault(query["theme_id"], []).append(query["format"])

    extra = set(by_theme.keys()) - valid_theme_ids
    if extra:
        errors.append(f"queries reference unknown theme_ids: {sorted(extra)}")

    missing_themes = valid_theme_ids - set(by_theme.keys())
    if missing_themes:
        errors.append(f"themes missing from Pass D output: {sorted(missing_themes)}")

    for theme_id, formats in by_theme.items():
        if len(formats) != 3 or set(formats) != REQUIRED_FORMATS:
            errors.append(f"theme {theme_id}: expected exactly 3 entries with formats {sorted(REQUIRED_FORMATS)}, got {formats}")
    return errors


# Truncate a word to a stable stem: strip plural/gerund suffixes, then cap length for inflection tolerance
def stem(word):
    w = re.sub(r"[^a-z0-9]", "", word.lower())
    if len(w) > 4:
        if w.endswith("ies"):
            w = w[:-3] + "y"
        elif w.endswith("es") and not w.endswith("ss"):
            w = w[:-2]
        elif w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        elif w.endswith("ing"):
            w = w[:-3]
        elif w.endswith("ed"):
            w = w[:-2]
    return w[:7] if len(w) > 7 else w


# Extract the leading clause of a sentence: up to the first ", and/but/or" or sentence-ending punctuation
def leading_clause(text):
    match = CLAUSE_BREAK.search(text)
    return text[:match.start()] if match else text.rstrip("?.! ")


# R16b: verify the query leads with the theme's primary_concept, per format
def check_head_concept(query, primary_concepts):
    theme_id = query["theme_id"]
    if theme_id not in primary_concepts:
        return []  # already reported by check_theme_format_completeness
    concept = primary_concepts[theme_id]
    concept_tokens = [stem(w) for w in WORD_PATTERN.findall(concept)]

    if query["format"] == "keyword_bag":
        bag_tokens = [stem(w) for w in WORD_PATTERN.findall(query["query"])]
        if bag_tokens[:len(concept_tokens)] != concept_tokens:
            return [f"theme {theme_id} keyword_bag: does not open with primary_concept '{concept}' (got: {query['query']!r})"]
        return []

    clause = leading_clause(query["query"])
    clause_stem = " " + " ".join(stem(w) for w in WORD_PATTERN.findall(clause)) + " "
    concept_stem = " " + " ".join(concept_tokens) + " "
    if concept_stem not in clause_stem:
        return [f"theme {theme_id} {query['format']}: leading clause does not carry primary_concept "
                f"'{concept}' (leading clause: {clause!r})"]
    return []


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python3 eval/scripts/validate_pass_d.py <pass_d_json> <pass_c_json>")
    validate_pass_d_workflow(sys.argv[1], sys.argv[2])
