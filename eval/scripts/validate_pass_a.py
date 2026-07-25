# INFRASTRUCTURE
import json
import sys

REQUIRED_TOP_KEYS = {"document", "blocks", "trash"}
REQUIRED_BLOCK_KEYS = {"id", "line_start", "line_end", "subject"}
REQUIRED_TRASH_KEYS = {"line_start", "line_end", "type"}
VALID_TRASH_TYPES = {
    "abstract_summary", "title_author", "references",
    "toc_index", "caption_stub", "conversion_residue",
}


# ORCHESTRATOR
# Validate a Pass A segmentation output against its source document
def validate_pass_a_workflow(pass_a_path, source_path):
    pass_a = load_json(pass_a_path)
    schema_errors = check_schema(pass_a)
    if schema_errors:
        sys.exit("FAIL validate_pass_a\n" + "\n".join(schema_errors))

    source_lines = load_source_lines(source_path)
    errors = []
    errors += check_trash_types(pass_a)
    errors += check_coverage(pass_a, len(source_lines))
    if errors:
        sys.exit("FAIL validate_pass_a\n" + "\n".join(errors))

    print(f"OK validate_pass_a: {len(pass_a['blocks'])} blocks, "
          f"{len(pass_a['trash'])} trash spans, {len(source_lines)} lines covered")


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


# Verify top-level and per-item required keys are present
def check_schema(pass_a):
    errors = []
    missing_top = REQUIRED_TOP_KEYS - pass_a.keys()
    if missing_top:
        errors.append(f"missing top-level keys: {sorted(missing_top)}")
        return errors
    if not isinstance(pass_a["blocks"], list) or not pass_a["blocks"]:
        errors.append("'blocks' must be a non-empty list")
    else:
        for i, block in enumerate(pass_a["blocks"]):
            missing = REQUIRED_BLOCK_KEYS - block.keys()
            if missing:
                errors.append(f"block index {i} ({block.get('id', '?')}) missing keys: {sorted(missing)}")
    if not isinstance(pass_a["trash"], list):
        errors.append("'trash' must be a list")
    else:
        for i, trash in enumerate(pass_a["trash"]):
            missing = REQUIRED_TRASH_KEYS - trash.keys()
            if missing:
                errors.append(f"trash index {i} missing keys: {sorted(missing)}")
    return errors


# Verify every trash entry's type is in the R4 taxonomy
def check_trash_types(pass_a):
    errors = []
    for i, trash in enumerate(pass_a["trash"]):
        if trash["type"] not in VALID_TRASH_TYPES:
            errors.append(
                f"trash index {i} (lines {trash['line_start']}-{trash['line_end']}): "
                f"invalid type '{trash['type']}', must be one of {sorted(VALID_TRASH_TYPES)}"
            )
    return errors


# Verify blocks+trash spans are 1-indexed, non-overlapping, in order, and cover every source line exactly once
def check_coverage(pass_a, total_lines):
    errors = []
    spans = []
    for block in pass_a["blocks"]:
        spans.append((block["line_start"], block["line_end"], "block", block["id"]))
    for i, trash in enumerate(pass_a["trash"]):
        spans.append((trash["line_start"], trash["line_end"], "trash", f"index {i}"))

    for start, end, kind, label in spans:
        if start > end:
            errors.append(f"{kind} {label}: line_start {start} > line_end {end}")
        if start < 1 or end > total_lines:
            errors.append(f"{kind} {label}: span {start}-{end} out of document bounds (1-{total_lines})")
    if errors:
        return errors

    spans.sort(key=lambda s: s[0])
    expected_next = 1
    for start, end, kind, label in spans:
        if start != expected_next:
            if start < expected_next:
                errors.append(f"{kind} {label}: span {start}-{end} overlaps preceding span (expected start {expected_next})")
            else:
                errors.append(f"gap in coverage: line {expected_next} to {start - 1} is in no block or trash span")
        expected_next = end + 1
    if expected_next - 1 != total_lines:
        errors.append(f"coverage ends at line {expected_next - 1}, document has {total_lines} lines")
    return errors


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python3 eval/scripts/validate_pass_a.py <pass_a_json> <source_md>")
    validate_pass_a_workflow(sys.argv[1], sys.argv[2])
