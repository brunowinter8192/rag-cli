# INFRASTRUCTURE
import json
import sys

REQUIRED_DOC_KEYS = {"document", "themes"}
REQUIRED_THEME_KEYS = {"id", "spans"}
ALLOWED_OUTPUT_DOC_KEYS = {"document", "themes"}
ALLOWED_OUTPUT_THEME_KEYS = {"id", "spans"}


# ORCHESTRATOR
# Read a Pass B output JSON, strip it to the spans-only Pass C input, write it
def filter_workflow(input_path, output_path):
    pass_b = load_json(input_path)
    validate_pass_b_shape(pass_b)
    filtered = build_spans_only(pass_b)
    validate_output_whitelist(filtered)
    write_json(filtered, output_path)


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


# Verify document/themes keys and every theme's id/spans are present
def validate_pass_b_shape(pass_b):
    missing_doc_keys = REQUIRED_DOC_KEYS - pass_b.keys()
    if missing_doc_keys:
        sys.exit(f"ERROR: input JSON missing required top-level keys: {sorted(missing_doc_keys)}")
    if not isinstance(pass_b["themes"], list) or not pass_b["themes"]:
        sys.exit("ERROR: 'themes' must be a non-empty list")
    for i, theme in enumerate(pass_b["themes"]):
        missing_theme_keys = REQUIRED_THEME_KEYS - theme.keys()
        if missing_theme_keys:
            theme_id = theme.get("id", f"index {i}")
            sys.exit(f"ERROR: theme {theme_id} missing required keys: {sorted(missing_theme_keys)}")


# Build the {document, themes: [{id, spans}]} Pass C input, dropping all other fields
def build_spans_only(pass_b):
    return {
        "document": pass_b["document"],
        "themes": [
            {"id": theme["id"], "spans": theme["spans"]}
            for theme in pass_b["themes"]
        ],
    }


# Assert the output contains no key beyond the anti-leakage whitelist before it is ever written
def validate_output_whitelist(filtered):
    extra_doc_keys = filtered.keys() - ALLOWED_OUTPUT_DOC_KEYS
    if extra_doc_keys:
        sys.exit(f"ERROR: refusing to write - output has non-whitelisted top-level keys: {sorted(extra_doc_keys)}")
    for theme in filtered["themes"]:
        extra_theme_keys = theme.keys() - ALLOWED_OUTPUT_THEME_KEYS
        if extra_theme_keys:
            sys.exit(f"ERROR: refusing to write - theme {theme.get('id')} has non-whitelisted keys: {sorted(extra_theme_keys)}")


# Write the filtered JSON to the output path
def write_json(filtered, path):
    with open(path, "w") as f:
        json.dump(filtered, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python3 eval/scripts/filter_spans_only.py <pass_b_json> <output_json>")
    filter_workflow(sys.argv[1], sys.argv[2])
