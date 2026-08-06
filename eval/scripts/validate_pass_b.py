# INFRASTRUCTURE
import json
import re
import sys

REQUIRED_TOP_KEYS = {"document", "model", "themes"}
# Anti-section-echo gates (2026-08-06 batch01 diagnosis): batch01 themes mirrored the papers'
# section structure — blocks/theme median 1.47 (Bollerslev calibration: 5.62), 10 standalone
# proof themes against the theorem+proof merge precedent (R7: statement + appendix proof =
# ONE distributed theme). Floor 2.0 rejects 1:1 section echo while allowing genuinely
# fine-blocked documents; proof-label tolerance is zero.
BLOCKS_PER_THEME_MIN = 2.0
PROOF_LABEL = re.compile(r"\bproofs?\b", re.IGNORECASE)
REQUIRED_THEME_KEYS = {"id", "label", "need", "spans"}
REQUIRED_SPAN_KEYS = {"line_start", "line_end"}
REQUIRED_RESPLIT_KEYS = {"pass_a_block", "new_spans", "reason"}
REQUIRED_SOFT_MEMBER_KEYS = {"block", "also_in"}
REQUIRED_UNASSIGNED_KEYS = {"block", "reason"}


# ORCHESTRATOR
# Validate a Pass B theme-formation output against its Pass A blocks and source document
def validate_pass_b_workflow(pass_b_path, pass_a_path, source_path):
    pass_b = load_json(pass_b_path)
    schema_errors = check_schema(pass_b)
    if schema_errors:
        sys.exit("FAIL validate_pass_b\n" + "\n".join(schema_errors))

    pass_a = load_json(pass_a_path)
    source_lines = load_source_lines(source_path)
    total_lines = len(source_lines)
    trash_spans = [(t["line_start"], t["line_end"]) for t in pass_a["trash"]]
    blocks = {b["id"]: (b["line_start"], b["line_end"]) for b in pass_a["blocks"]}

    errors = []
    errors += check_span_bounds(pass_b, total_lines)
    errors += check_no_intra_theme_overlap(pass_b)
    errors += check_disjoint_from_trash(pass_b, trash_spans)
    errors += check_resplit_boundaries(pass_b, blocks, source_lines)
    errors += check_block_coverage(pass_b, blocks)
    errors += check_soft_members(pass_b, blocks)
    errors += check_blocks_per_theme(pass_b, blocks)
    errors += check_no_proof_themes(pass_b)
    if errors:
        sys.exit("FAIL validate_pass_b\n" + "\n".join(errors))

    print(f"OK validate_pass_b: {len(pass_b['themes'])} themes, "
          f"{len(pass_b.get('resplits', []))} resplits, "
          f"{len(pass_b.get('unassigned', []))} unassigned blocks")


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


# Verify top-level and per-theme/resplit/soft-member required keys are present
def check_schema(pass_b):
    errors = []
    missing_top = REQUIRED_TOP_KEYS - pass_b.keys()
    if missing_top:
        errors.append(f"missing top-level keys: {sorted(missing_top)}")
        return errors
    if not isinstance(pass_b["themes"], list) or not pass_b["themes"]:
        errors.append("'themes' must be a non-empty list")
        return errors
    for theme in pass_b["themes"]:
        missing = REQUIRED_THEME_KEYS - theme.keys()
        if missing:
            errors.append(f"theme {theme.get('id', '?')} missing keys: {sorted(missing)}")
            continue
        if not isinstance(theme["spans"], list) or not theme["spans"]:
            errors.append(f"theme {theme['id']}: 'spans' must be a non-empty list")
            continue
        for j, span in enumerate(theme["spans"]):
            missing = REQUIRED_SPAN_KEYS - span.keys()
            if missing:
                errors.append(f"theme {theme['id']} span {j} missing keys: {sorted(missing)}")
        if len(theme["spans"]) > 1 and not theme.get("distributed_justification"):
            errors.append(f"theme {theme['id']}: multiple non-adjacent spans require 'distributed_justification'")
        for sm in theme.get("soft_members", []):
            missing = REQUIRED_SOFT_MEMBER_KEYS - sm.keys()
            if missing:
                errors.append(f"theme {theme['id']} soft_member {sm} missing keys: {sorted(missing)}")
    for i, resplit in enumerate(pass_b.get("resplits", [])):
        missing = REQUIRED_RESPLIT_KEYS - resplit.keys()
        if missing:
            errors.append(f"resplit index {i} missing keys: {sorted(missing)}")
    for i, unassigned in enumerate(pass_b.get("unassigned", [])):
        missing = REQUIRED_UNASSIGNED_KEYS - unassigned.keys()
        if missing:
            errors.append(f"unassigned index {i} missing keys: {sorted(missing)}")
    return errors


# Verify every theme span lies within [1, total_lines]
def check_span_bounds(pass_b, total_lines):
    errors = []
    for theme in pass_b["themes"]:
        for span in theme["spans"]:
            s, e = span["line_start"], span["line_end"]
            if s > e:
                errors.append(f"theme {theme['id']}: span line_start {s} > line_end {e}")
            if s < 1 or e > total_lines:
                errors.append(f"theme {theme['id']}: span {s}-{e} out of document bounds (1-{total_lines})")
    return errors


# Verify spans within one theme never overlap each other
def check_no_intra_theme_overlap(pass_b):
    errors = []
    for theme in pass_b["themes"]:
        spans = sorted(theme["spans"], key=lambda s: s["line_start"])
        for a, b in zip(spans, spans[1:]):
            if a["line_end"] >= b["line_start"]:
                errors.append(
                    f"theme {theme['id']}: spans {a['line_start']}-{a['line_end']} and "
                    f"{b['line_start']}-{b['line_end']} overlap"
                )
    return errors


# Verify theme spans never intersect a Pass A trash span
def check_disjoint_from_trash(pass_b, trash_spans):
    errors = []
    for theme in pass_b["themes"]:
        for span in theme["spans"]:
            for t_start, t_end in trash_spans:
                if span["line_start"] <= t_end and t_start <= span["line_end"]:
                    errors.append(
                        f"theme {theme['id']}: span {span['line_start']}-{span['line_end']} "
                        f"overlaps trash span {t_start}-{t_end}"
                    )
    return errors


# Verify each resplit's new boundaries sit on blank lines and reconstruct the original block's range
def check_resplit_boundaries(pass_b, blocks, source_lines):
    errors = []
    for resplit in pass_b.get("resplits", []):
        block_id = resplit["pass_a_block"]
        if block_id not in blocks:
            errors.append(f"resplit references unknown Pass A block '{block_id}'")
            continue
        orig_start, orig_end = blocks[block_id]
        new_spans = sorted(resplit["new_spans"], key=lambda s: s["line_start"])
        if new_spans[0]["line_start"] != orig_start or new_spans[-1]["line_end"] != orig_end:
            errors.append(
                f"resplit {block_id}: new_spans {new_spans[0]['line_start']}-{new_spans[-1]['line_end']} "
                f"do not reconstruct original block range {orig_start}-{orig_end}"
            )
        for a, b in zip(new_spans, new_spans[1:]):
            if b["line_start"] != a["line_end"] + 1:
                errors.append(f"resplit {block_id}: gap/overlap between sub-spans ending {a['line_end']} and starting {b['line_start']}")
                continue
            boundary_line = source_lines[a["line_end"] - 1] if a["line_end"] - 1 < len(source_lines) else ""
            if boundary_line.strip() != "":
                errors.append(
                    f"resplit {block_id}: boundary at line {a['line_end']} is not a blank line "
                    f"(got: {boundary_line!r})"
                )
    return errors


# Verify every non-trash Pass A block is covered by theme spans or explicitly listed as unassigned
def check_block_coverage(pass_b, blocks):
    errors = []
    resplit_map = {r["pass_a_block"]: r["new_spans"] for r in pass_b.get("resplits", [])}
    unassigned_ids = {u["block"] for u in pass_b.get("unassigned", [])}

    theme_spans = []
    for theme in pass_b["themes"]:
        for span in theme["spans"]:
            theme_spans.append((span["line_start"], span["line_end"]))

    def covered(start, end):
        for t_start, t_end in theme_spans:
            if t_start <= start and end <= t_end:
                return True
        return False

    def touched(start, end):
        return any(t_start <= end and start <= t_end for t_start, t_end in theme_spans)

    for block_id, (b_start, b_end) in blocks.items():
        units = resplit_map[block_id] if block_id in resplit_map else [{"line_start": b_start, "line_end": b_end}]
        for unit in units:
            u_start, u_end = unit["line_start"], unit["line_end"]
            is_covered = covered(u_start, u_end)
            is_touched = touched(u_start, u_end)
            is_unassigned = block_id in unassigned_ids
            if is_covered and is_unassigned:
                errors.append(f"block {block_id}: covered by a theme span but also listed as unassigned")
            elif is_covered:
                continue
            elif is_unassigned:
                if is_touched:
                    errors.append(f"block {block_id}: listed as unassigned but partially overlaps a theme span")
                continue
            elif is_touched:
                errors.append(f"block {block_id} ({u_start}-{u_end}): partially covered by theme spans, not fully assigned, not listed as unassigned")
            else:
                errors.append(f"block {block_id} ({u_start}-{u_end}): not covered by any theme and not listed as unassigned")
    return errors


# Verify soft-member entries genuinely lie inside the owning theme's spans, and also_in ids exist
def check_soft_members(pass_b, blocks):
    errors = []
    theme_ids = {t["id"] for t in pass_b["themes"]}
    for theme in pass_b["themes"]:
        for sm in theme.get("soft_members", []):
            block_id = sm["block"]
            if block_id not in blocks:
                errors.append(f"theme {theme['id']} soft_member: unknown block '{block_id}'")
                continue
            b_start, b_end = blocks[block_id]
            own_overlap = any(
                span["line_start"] <= b_end and b_start <= span["line_end"]
                for span in theme["spans"]
            )
            if not own_overlap:
                errors.append(
                    f"theme {theme['id']} soft_member {block_id}: block range {b_start}-{b_end} "
                    f"does not actually overlap this theme's own spans"
                )
            for also_id in sm["also_in"]:
                if also_id not in theme_ids:
                    errors.append(f"theme {theme['id']} soft_member {block_id}: also_in references unknown theme '{also_id}'")
                if also_id == theme["id"]:
                    errors.append(f"theme {theme['id']} soft_member {block_id}: also_in self-references its own theme")
    return errors


# Anti-section-echo gate: assignable blocks per theme must not collapse toward 1:1
def check_blocks_per_theme(pass_b, blocks):
    n_themes = len(pass_b["themes"])
    n_unassigned = len(pass_b.get("unassigned", []))
    n_assignable = len(blocks) - n_unassigned
    ratio = n_assignable / n_themes if n_themes else 0
    if ratio < BLOCKS_PER_THEME_MIN:
        return [f"blocks/theme ratio {ratio:.2f} below {BLOCKS_PER_THEME_MIN} "
                f"({n_assignable} assignable blocks / {n_themes} themes — section echo suspected; "
                f"apply the split test's inverse: merge themes no realistic single question separates)"]
    return []


# Zero-tolerance gate: no theme may be a standalone proof (theorem statement + proof = ONE theme per R7)
def check_no_proof_themes(pass_b):
    errors = []
    for theme in pass_b["themes"]:
        if PROOF_LABEL.search(theme["label"]):
            errors.append(
                f"theme {theme['id']}: label {theme['label']!r} marks a standalone proof theme — "
                f"merge the proof into its theorem's theme as a distributed span (R7)"
            )
    return errors


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("usage: python3 eval/scripts/validate_pass_b.py <pass_b_json> <pass_a_json> <source_md>")
    validate_pass_b_workflow(sys.argv[1], sys.argv[2], sys.argv[3])
