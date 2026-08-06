# INFRASTRUCTURE
import json
import re
import sys

REQUIRED_TOP_KEYS = {"document", "model", "summaries"}
REQUIRED_SUMMARY_KEYS = {"theme_id", "field", "information_need", "primary_concept", "sub_concepts", "answer_type"}
WORD_BUDGET_MIN = 60
WORD_BUDGET_MAX = 90
SUB_CONCEPTS_MIN = 3
SUB_CONCEPTS_MAX = 5
STRUCTURE_REF_WORDS = {"section", "appendix", "paper", "author", "chapter"}
WORD_PATTERN = re.compile(r"[A-Za-z][A-Za-z\-']*")
PARENTHETICAL_NUMBERS = re.compile(r"\(\s*\d+(?:\s*,\s*\d+)*\s*\)")
CLAUSE_BREAK = re.compile(r",\s*(?:and|but|or)\s+|[.;]", re.IGNORECASE)
# Anti-lookup gate (2026-08-06 batch01 diagnosis): needs phrased as bare artifact lookups
# ("a researcher wants the definition of X") violate R6's case-match need level. The
# batch01 failure mode; Bollerslev summaries carry zero hits.
LOOKUP_PHRASING = re.compile(
    r"\bwants?\s+(?:the|a|an)\s+(?:definition|statement|derivation|proof|formula|expression|theorem|lemma)\b",
    re.IGNORECASE,
)


# ORCHESTRATOR
# Validate a Pass C theme-summary output against its Pass B themes
def validate_pass_c_workflow(pass_c_path, pass_b_path):
    pass_c = load_json(pass_c_path)
    schema_errors = check_schema(pass_c)
    if schema_errors:
        sys.exit("FAIL validate_pass_c\n" + "\n".join(schema_errors))

    pass_b = load_json(pass_b_path)
    theme_ids = {t["id"] for t in pass_b["themes"]}

    errors = []
    errors += check_theme_id_coverage(pass_c, theme_ids)
    for summary in pass_c["summaries"]:
        errors += check_word_budget(summary)
        errors += check_sub_concepts_count(summary)
        errors += check_no_stray_digits(summary)
        errors += check_no_structure_references(summary)
        errors += check_primary_concept_membership(summary)
        errors += check_primary_concept_leads_need(summary)
        errors += check_no_lookup_phrasing(summary)
    if errors:
        sys.exit("FAIL validate_pass_c\n" + "\n".join(errors))

    print(f"OK validate_pass_c: {len(pass_c['summaries'])} summaries, all checks passed")


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


# Verify top-level and per-summary required keys are present
def check_schema(pass_c):
    errors = []
    missing_top = REQUIRED_TOP_KEYS - pass_c.keys()
    if missing_top:
        errors.append(f"missing top-level keys: {sorted(missing_top)}")
        return errors
    if not isinstance(pass_c["summaries"], list) or not pass_c["summaries"]:
        errors.append("'summaries' must be a non-empty list")
        return errors
    for i, summary in enumerate(pass_c["summaries"]):
        missing = REQUIRED_SUMMARY_KEYS - summary.keys()
        if missing:
            errors.append(f"summary index {i} ({summary.get('theme_id', '?')}) missing keys: {sorted(missing)}")
    return errors


# Verify exactly one summary per Pass B theme, matching theme_ids
def check_theme_id_coverage(pass_c, theme_ids):
    errors = []
    summary_ids = [s["theme_id"] for s in pass_c["summaries"]]
    seen = set()
    for tid in summary_ids:
        if tid in seen:
            errors.append(f"duplicate summary for theme_id '{tid}'")
        seen.add(tid)
    missing = theme_ids - seen
    extra = seen - theme_ids
    if missing:
        errors.append(f"summaries missing for Pass B theme_ids: {sorted(missing)}")
    if extra:
        errors.append(f"summaries reference unknown theme_ids: {sorted(extra)}")
    return errors


# Count whitespace-delimited words in a text string (wc -w semantics)
def count_words(text):
    return len(text.split())


# Verify field+information_need+sub_concepts+answer_type together fall in the 60-90 word budget
def check_word_budget(summary):
    combined = " ".join([
        summary["field"],
        summary["information_need"],
        " ".join(summary["sub_concepts"]),
        summary["answer_type"],
    ])
    n = count_words(combined)
    if not (WORD_BUDGET_MIN <= n <= WORD_BUDGET_MAX):
        return [f"theme {summary['theme_id']}: word budget {n} outside {WORD_BUDGET_MIN}-{WORD_BUDGET_MAX}"]
    return []


# Verify sub_concepts has 3-5 entries
def check_sub_concepts_count(summary):
    n = len(summary["sub_concepts"])
    if not (SUB_CONCEPTS_MIN <= n <= SUB_CONCEPTS_MAX):
        return [f"theme {summary['theme_id']}: sub_concepts has {n} entries, must be {SUB_CONCEPTS_MIN}-{SUB_CONCEPTS_MAX}"]
    return []


# Verify sub_concepts contain no digits outside parenthetical model-order notation, e.g. GARCH(1,1);
# field, information_need, answer_type allow no digits at all (R14 whole-summary digit ban)
def check_no_stray_digits(summary):
    errors = []
    for term in summary["sub_concepts"]:
        cleaned = PARENTHETICAL_NUMBERS.sub("", term)
        if re.search(r"\d", cleaned):
            errors.append(f"theme {summary['theme_id']}: sub_concept '{term}' has digits outside parenthetical model-order notation")
    for field_name in ("field", "information_need", "answer_type"):
        if re.search(r"\d", summary[field_name]):
            errors.append(f"theme {summary['theme_id']}: {field_name} contains digits (not allowed): {summary[field_name]!r}")
    return errors


# Verify no document-structure references appear in the summary text
def check_no_structure_references(summary):
    errors = []
    combined = " ".join([
        summary["field"], summary["information_need"],
        " ".join(summary["sub_concepts"]), summary["answer_type"],
    ])
    words = {w.lower() for w in WORD_PATTERN.findall(combined)}
    hits = words & STRUCTURE_REF_WORDS
    if hits:
        errors.append(f"theme {summary['theme_id']}: document-structure references found: {sorted(hits)}")
    return errors


# Verify primary_concept is present and exactly matches one entry of sub_concepts
def check_primary_concept_membership(summary):
    if summary["primary_concept"] not in summary["sub_concepts"]:
        return [f"theme {summary['theme_id']}: primary_concept '{summary['primary_concept']}' not a member of sub_concepts {summary['sub_concepts']}"]
    return []


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


# Verify information_need's first clause carries the primary_concept via stemmed token overlap.
# Concept-level, not verbatim (2026-08-06): requiring EVERY concept token forced verbatim
# primary_concept embedding (documented in the Pass C batch01 completion entry), which fed the
# Pass D paraphrase collapse. A majority of concept tokens in the leading clause suffices.
def check_primary_concept_leads_need(summary):
    clause = leading_clause(summary["information_need"])
    concept_tokens = {stem(w) for w in WORD_PATTERN.findall(summary["primary_concept"])}
    clause_tokens = {stem(w) for w in WORD_PATTERN.findall(clause)}
    present = concept_tokens & clause_tokens
    if len(present) * 2 < len(concept_tokens):
        return [f"theme {summary['theme_id']}: information_need's first clause does not carry primary_concept "
                f"'{summary['primary_concept']}' (leading clause: {clause!r})"]
    return []


# Anti-lookup gate: reject information_need phrased as a bare artifact lookup (R6 case-match level)
def check_no_lookup_phrasing(summary):
    match = LOOKUP_PHRASING.search(summary["information_need"])
    if match:
        return [f"theme {summary['theme_id']}: information_need uses lookup phrasing ({match.group(0)!r}) — "
                f"R6 requires a case-match need, not an artifact lookup"]
    return []


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python3 eval/scripts/validate_pass_c.py <pass_c_json> <pass_b_json>")
    validate_pass_c_workflow(sys.argv[1], sys.argv[2])
