# Committed Pass Validator Scripts, Bollerslev Cross-Check (2026-07-26)

The four-pass chain (segmentation A/B, summary C, query D) had been validated end-to-end on
`Bollerslev1986GARCH.md` only via throwaway `/tmp` scripts (e.g. the Pass D head-concept
checker referenced in the 2026-07-25 entry) — lost between sessions, re-derived from scratch
each time. Ahead of the 20-paper batch, five scripts were committed to `eval/scripts/`:
`validate_pass_a.py`, `validate_pass_b.py`, `validate_pass_c.py`, `validate_pass_d.py`,
`audit_leakage.py`. All five ran clean against the committed Bollerslev artifact set
(`eval/queries/pass_{a,b,c,d}_runs/Bollerslev1986GARCH.pass_*.json`) as of this date.

## Design choice: collect-and-report-all, not fail-fast

Content checks (span overlap, word budget, digit ban, head-concept lead, ...) accumulate into
one error list and exit once at the end; only schema-shape checks fail immediately (a malformed
shape would crash every downstream check). Chosen over fail-fast-on-first-error because at
20-paper scale, seeing every defect in one run beats a fix-rerun-fix loop per document.

## Word budget: whitespace-token count, not alpha-only

First attempt counted only `[A-Za-z][A-Za-z-']*` regex matches as "words" for Pass C's 60-90
budget (R12). This put t06 at 59 words — one under the floor — while manual whitespace-`split()`
counting put it at exactly 60. The `field` slot's convention (`"financial econometrics /
volatility modeling"`) treats the `/` as a budget-counted token; switched `count_words` to plain
`text.split()` (`wc -w` semantics). All 8 themes landed 60-69 under this counting, comfortably
inside budget — the alpha-only regex had been silently under-counting every summary by the
number of `/`-separated field labels and stray punctuation tokens.

## Soft-member cross-theme overlap does not hold on real data

Pass B's `soft_members` entries (`t02→b011→also_in:[t05]`, `t05→b020→also_in:[t03]`) do NOT
show actual line-range overlap between the block and its `also_in` target theme's spans — e.g.
b011 (lines 80-99) sits nowhere near t05's span (171-232), despite being flagged as also
relevant there. A strict "block overlaps the also_in theme's spans" check would fail this
committed, presumably-accepted artifact. Implemented instead as: (1) block genuinely overlaps
its *owning* theme's own spans (sanity that the primary assignment is real), (2) `also_in`
theme ids are non-dangling and non-self-referential. This is a real check (catches a bogus block
id or a self-reference) without asserting a spatial-overlap property the pipeline apparently
never intended to hold — soft membership here reads as "this content is topically relevant
elsewhere," not "this line range is duplicated into another theme's span list."

## Inflection-tolerant matching: prefix-capped stemmer

R16b (Pass D primary_concept lead) and Pass C's information_need-carries-primary_concept check
both need "same concept, different inflection" matching. Suffix-stripping alone (`-s`, `-es`,
`-ing`, `-ed`) fails t06: `information_need` says "maximum likelihood **estimator**" while
`primary_concept` is "maximum likelihood **estimation**" — different suffixes entirely, no
shared plural/gerund pattern. Fixed by capping the stemmed token at 7 characters after
suffix-stripping (`estimator`/`estimation` → `estimat`), a common cheap trick for exactly this
family of derivational (not just inflectional) variance. Verified by hand against all 8 themes'
keyword_bag/natural_question/field_sentence/information_need before relying on it.

## Review round: digit ban scope, new trash type, unassigned schema

A review pass caught three gaps against the prompt's actual rules:
- Pass C's digit ban (R14: "no numbers") had only been checked on `sub_concepts` (with the
  `GARCH(1,1)`-style parenthetical exemption); `field`, `information_need`, `answer_type` allow
  no digits at all and were unchecked. Fixed — those three fields now reject any digit, no
  exemption; `sub_concepts` keeps the parenthetical exemption.
- `segmentation_prompt_pass_a.md` gained a `navigation_meta` trash type (roadmap/structure
  meta-text) not yet in `VALID_TRASH_TYPES`. Added.
- `segmentation_prompt_pass_b.md`'s `unassigned` entries ({block, reason}) had no schema check.
  Added `REQUIRED_UNASSIGNED_KEYS`.

All three re-verified with a targeted negative case (digit injected into `information_need`,
type relabeled to `navigation_meta` and accepted, `reason` key stripped from an `unassigned`
entry) before the fix was considered done.

## What's not covered

Every check was hand-verified against the single Bollerslev artifact set only — no second
document exists yet to confirm the checks generalize (e.g. whether the resplit-boundary check,
never exercised since this run's `resplits` list is empty, behaves correctly on a document that
actually re-splits a block). Batch iteration and cross-document runs are separate follow-up
work.
