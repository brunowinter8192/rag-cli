# D_analyze report

## Sample (N = 12)

| need | stratum | intent | collection | pool chunks trimmed |
|---|---|---|---|---|
| N01 | reference | precision | wise2627-reference | 0 |
| N02 | reference | recall | goethe-bwl-reference | 0 |
| N03 | reference | precision | wise2627-reference | 0 |
| N04 | reference | precision | wise2627-reference | 0 |
| N05 | docs | precision | general-docs | 0 |
| N06 | docs | recall | canvas-docs | 0 |
| N07 | docs | recall | canvas-docs | 0 |
| N08 | docs | recall | monitor-cc-docs | 0 |
| N09 | other | recall | github_issues | 0 |
| N10 | other | precision | reddit-cli-posts | 0 |
| N11 | other | recall | reddit-cli-posts | 0 |
| N12 | other | precision | reddit-cli-posts | 0 |

## Per need (printed results: A 12, G 12, S 12, M 12, P 3 per source)

| need | intent | A@12 | G@12 | S 4x3 | M@12 | P |
|---|---|---|---|---|---|---|
| N01 | precision | hit 1 rel 7 asp 1.00 docs 1 | hit 1 rel 8 asp 1.00 docs 2 | hit 1 rel 6 asp 1.00 docs 2 | - | hit 1 rel 4 asp 1.00 docs 2 |
| N02 | recall | hit 0 rel 0 asp - docs 0 | hit 0 rel 0 asp - docs 0 | hit 0 rel 0 asp - docs 0 | hit 0 rel 0 asp - docs 0 | hit 0 rel 0 asp - docs 0 |
| N03 | precision | hit 0 rel 4 asp 1.00 docs 1 | hit 0 rel 5 asp 1.00 docs 1 | hit 0 rel 4 asp 1.00 docs 1 | - | hit 1 rel 10 asp 1.00 docs 4 |
| N04 | precision | hit 1 rel 3 asp 1.00 docs 1 | hit 1 rel 3 asp 1.00 docs 1 | hit 1 rel 2 asp 1.00 docs 1 | - | hit 0 rel 2 asp 1.00 docs 2 |
| N05 | precision | hit 1 rel 3 asp 1.00 docs 3 | hit 1 rel 4 asp 1.00 docs 4 | hit 1 rel 3 asp 1.00 docs 3 | - | - |
| N06 | recall | hit 1 rel 12 asp 1.00 docs 3 | hit 1 rel 12 asp 1.00 docs 4 | hit 1 rel 11 asp 0.75 docs 5 | hit 1 rel 12 asp 1.00 docs 4 | - |
| N07 | recall | hit 1 rel 12 asp 1.00 docs 5 | hit 1 rel 12 asp 1.00 docs 3 | hit 1 rel 7 asp 1.00 docs 3 | hit 1 rel 12 asp 1.00 docs 4 | - |
| N08 | recall | hit 1 rel 3 asp 1.00 docs 2 | hit 1 rel 3 asp 1.00 docs 2 | hit 1 rel 3 asp 1.00 docs 2 | hit 1 rel 4 asp 1.00 docs 3 | - |
| N09 | recall | hit 1 rel 12 asp 1.00 docs 5 | hit 1 rel 12 asp 1.00 docs 3 | hit 1 rel 9 asp 1.00 docs 4 | hit 1 rel 11 asp 1.00 docs 8 | - |
| N10 | precision | hit 1 rel 7 asp 1.00 docs 4 | hit 1 rel 9 asp 1.00 docs 5 | hit 1 rel 6 asp 1.00 docs 3 | - | - |
| N11 | recall | hit 1 rel 12 asp 1.00 docs 10 | hit 1 rel 12 asp 1.00 docs 10 | hit 1 rel 9 asp 1.00 docs 8 | hit 1 rel 11 asp 1.00 docs 10 | - |
| N12 | precision | hit 1 rel 6 asp 1.00 docs 3 | hit 1 rel 6 asp 1.00 docs 3 | hit 1 rel 4 asp 1.00 docs 2 | - | - |

## Default count

| list | needs with grade-2 hit (of 12) | relevant chunks (sum) | mean P |
|---|---|---|---|
| A@3 | 7 | 26 | 0.72 |
| A@4 | 9 | 33 | 0.69 |
| A@5 | 9 | 39 | 0.65 |
| A@6 | 9 | 45 | 0.62 |
| A@8 | 9 | 58 | 0.60 |
| A@12 | 10 | 81 | 0.56 |
| G@3 | 9 | 27 | 0.75 |
| G@4 | 10 | 36 | 0.75 |
| G@5 | 10 | 43 | 0.72 |
| G@6 | 10 | 50 | 0.69 |
| G@8 | 10 | 64 | 0.67 |
| G@12 | 10 | 86 | 0.60 |

Decision rule: smallest k <= 5 with Hit@k(A) >= Hit@12(A) - 1.

k* = 4; confirmed on guided queries: True

## Strategy at 12 printed results

| comparison (first vs second) | first adopted | hit first | hit second | asp first | asp second | wins/losses/ties |
|---|---|---|---|---|---|---|
| all | False | 10 | 10 | 0.98 | 1.00 | 0/1/11 |
| recall_only | False | 5 | 5 | 0.95 | 1.00 | 0/1/5 |
| precision_only | False | 5 | 5 | 1.00 | 1.00 | 0/0/6 |
| multiplicity_control | False | 10 | 10 | 0.98 | 1.00 | 0/1/11 |
| shape_control | False | 10 | 10 | 1.00 | 1.00 | 0/0/12 |

Rows: all and the intent splits compare S (4x3) with A (12). multiplicity_control compares S with G (12). shape_control compares G (12) with A (12).

## Per-source search

Needs with per-source arm: ['N01', 'N02', 'N03', 'N04']. Hit sum P 2 vs A 2. Relevant documents P [2, 0, 4, 2] vs A [1, 0, 1, 1].

Known-item rank in the 30-deep ranking for N01: A:A=22, G:G=4, S:s2=16, S:s3=2, S:s4=12, F:kw=5, F:nl=2, F:bool=8, P:Welge=-, P:Grundei=1, P:Seibert=-, R:R=-

## Querybau claims
- Form, guided vs kw: verdict supported (P@3 wins/losses/ties 3/1/2, mean P 0.72 vs 0.72, hit 4 vs 4)
- Form, guided vs nl: verdict inconclusive (P@3 wins/losses/ties 2/2/2, mean P 0.72 vs 0.67, hit 4 vs 5)
- Form, guided vs bool: verdict inconclusive (P@3 wins/losses/ties 1/1/4, mean P 0.72 vs 0.78, hit 4 vs 5)
- Multi-concept failure, siblings vs one merged query on recall needs: verdict not supported (asp wins/losses/ties 0/1/5, mean 0.95 vs 1.00)
- Anchor effect, precision: verdict supported (wins/losses/ties 2/0/10, mean 0.78 vs 0.72)
- Anchor effect, recall: verdict inconclusive (wins/losses/ties 0/0/12, mean 0.95 vs 0.95)
- Anchor effect, reldocs: verdict supported (wins/losses/ties 3/1/8, mean 2.00 vs 1.83)
- Sibling agreement: P(relevant | returned by 2+ siblings) 0.68 (n 38) vs by 1 0.62 (n 61); supported: False

## Rank and score profile of the logged queries (arm A)

| rank | n | P(relevant) |
|---|---|---|
| 1 | 12 | 0.67 |
| 2 | 12 | 0.67 |
| 3 | 12 | 0.83 |
| 4 | 12 | 0.58 |
| 5 | 12 | 0.50 |
| 6 | 12 | 0.50 |
| 7 | 12 | 0.42 |
| 8 | 12 | 0.67 |
| 9 | 12 | 0.58 |
| 10 | 12 | 0.33 |
| 11 | 12 | 0.50 |
| 12 | 12 | 0.50 |

| score band | n | P(relevant) |
|---|---|---|
| 0.9-1.01 | 102 | 0.63 |
| 0.5-0.9 | 7 | 0.43 |
| 0.1-0.5 | 16 | 0.62 |
| 0.0-0.1 | 19 | 0.21 |

Score cutoff supported by data: False

## Exploratory (added after the stage 1 results were known, not pre-registered)

- Guided vs logged query at k=3: hit wins/losses/ties 3/1/8, P wins/losses/ties 2/2/8, mean P 0.75 vs 0.72
- Guided vs logged query at k=4: hit wins/losses/ties 1/0/11, P wins/losses/ties 4/2/6, mean P 0.75 vs 0.69

Four printed results, needs: all

| list | needs | hit | relevant | asp | relevant docs | mean P |
|---|---|---|---|---|---|---|
| A@4 | 12 | 9 | 33 | 0.95 | 20 | 0.69 |
| G@4 | 12 | 10 | 36 | 0.95 | 22 | 0.75 |
| M@4 | 6 | 5 | 19 | 0.95 | 16 | 0.79 |
| S@1 | 12 | 10 | 29 | 0.95 | 21 | 0.75 |

Four printed results, needs: recall

| list | needs | hit | relevant | asp | relevant docs | mean P |
|---|---|---|---|---|---|---|
| A@4 | 6 | 5 | 19 | 0.88 | 12 | 0.79 |
| G@4 | 6 | 5 | 18 | 0.88 | 11 | 0.75 |
| M@4 | 6 | 5 | 19 | 0.95 | 16 | 0.79 |
| S@1 | 6 | 5 | 16 | 0.88 | 13 | 0.71 |

Rank of the first answer-bearing chunk (within the judged depth of 12; - means none)

| need | logged query | guided query |
|---|---|---|
| N01 | 9 | 1 |
| N02 | - | - |
| N03 | - | - |
| N04 | 1 | 4 |
| N05 | 4 | 1 |
| N06 | 1 | 1 |
| N07 | 1 | 1 |
| N08 | 1 | 1 |
| N09 | 1 | 2 |
| N10 | 1 | 1 |
| N11 | 4 | 1 |
| N12 | 1 | 2 |

Distinct share of the 12 printed results of the four sibling queries: 0.69

## Judge self-agreement

n = 22, kappa relevant 1.00, kappa grade 1.00
