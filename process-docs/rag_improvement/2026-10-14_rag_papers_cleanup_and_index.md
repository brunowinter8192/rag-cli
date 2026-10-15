# Cleaning and indexing three RAG papers into rag-cli-reference (2026-10-14)

Papers: Gao2023RagForLlmsSurvey, Wang2024RagBestPractices, Barnett2024SevenFailurePoints. Source PDFs are archived in `data/pdf/RAG/`, the MinerU conversion output lived in `data/documents/rag-cli-reference/`. `data/` is gitignored and exists only in the main checkout; the cleaned files and the index sidecars therefore are not part of this commit.

## The task referred to a phase 2 that does not exist

The task text said the papers should be cleaned "per the websearch-pdf skill phase 2". `websearch/skills/websearch-pdf/SKILL.md` contains no phase 2. It describes a Haiku-worker pipeline (extract, workers, assemble, sample, index, report) for PDFs that have not been converted yet. For MinerU output only two parts apply: the Step 4 sampling criteria (missing paragraphs, invented text, broken tables and formulas, figures without description) and the Step 5 index call. The actual cleanup class catalogue (classes A to J, MinerU mlx output) lives in the websearch area under pdf_pipeline and was handed over by the orchestrator mid-session. The definitions of classes A to D were not available; the classes that were applied are E (strip final reference lists), F (HTML tables to pipe text), G (strip image tags), H (fence and separator noise, count was 0 here) and I (run-on tokens, longest token 104 characters, nothing to do).

## Method

1. `pdftotext` (raw reading order) of each PDF, word-level `difflib` between the PDF text and the markdown. Page numbers, running headers, table cell order and figure labels show up as noise; everything else is a real difference. This found the content defects below that a read-through alone would have missed (for example the OCR error "rewritten" for "rewriter").
2. A cleaning script (kept in /tmp, not pinned) that works on blocks: strip, merge, convert tables, replace, then compare again against the PDF.
3. Result check: word diff original markdown vs cleaned markdown, so that every difference is an intended one.

Sibling papers in the collection were the convention reference: single `#` headings are kept (they all use only `#`), tables are pipe text, there are no reference lists, no image tags.

## Defect classes with observed examples

### Sentences split by floats and page breaks (all three papers)

MinerU emits tables, figure captions and boilerplate at the physical page position, in the middle of a sentence. The embedder then sees two half sentences.

- Barnett: "...give software engineers new capabilities to" + ACM permission notice + "CAIN 2024, April 2024, Lisbon" + copyright + ISBN + DOI + "build new HCI solutions". Barnett: "The generated questions were then evaluated using the" + Table 1 + "OpenEvals technique implemented by OpenAI". Barnett: "you need to" + Table 2 + "sort out the security/privacy".
- Wang: "selecting the appro" + Figure 2 caption + "priate algorithm" (word cut in half, joined without space). "Concatenating multiple pseudo-documents with the original query can significantly" + Table 8 + Table 9 + "enhance retrieval performance". "Finally, cloud" + Table 5 + "native capabilities" (PDF has "cloud-native"). 19 merges in total.
- Gao: "...paradigms including naive RAG," + Figure 1 caption + "advanced RAG, and modular RAG". "...how to harness both parameterized" + Table IV + the table footnote "† represents a benchmark..." + "and non-parameterized advantages". 18 merges in total.

Fix: the paragraph is rejoined, the float (caption plus table) is moved behind the rejoined paragraph. The Gao table footnote starting with the dagger sign had to be treated as part of the float, otherwise the merge attached the wrong block. One legitimate non-merge: Wang "One notable implement is HyDE [10]," is followed by a new paragraph in the PDF itself, so the "no terminal punctuation" rule must not merge it (explicit exclusion).

### Truncated content (Wang)

Appendix A.5 "Metrics" ended with "...the generation length of the model is sometimes" and the PDF continues "hard to limit." (the converter lost the line when Table 13 was inserted). Restored before the merge step, otherwise the next paragraph would have been glued onto the unfinished sentence.

### OCR substitutions found only by the PDF diff

- Barnett: "rewritten" for "rewriter" in three places ("retriever, data generation, rewritten, and reader", "includes a rewritten to generalise queries", "The rewritten considers this context"). Table 1 of the same paper correctly says "Rewriter".
- Barnett: email "mohamed. Abdelrazek}" for "mohamed.abdelrazek}".
- Wang: "Faisss" for "Faiss" in the text before Table 5. "LongLLMlingua" for "LongLLMLingua" in six places (bullet, text, Table 10, Table 11, A.6). "RA-GAs" for "RAGAs". Table 5 check marks: PDF "✗" came out as "X".
- Gao Table I: "KnewedGPT" (PDF "KnowledGPT"), "Filter-erank" (PDF "Filter-rerank"), "Rog" (PDF "RoG"), "G-R retriever" (PDF "G-Retriever"). Text: "KnowledgeGPT" for "KnowledGPT", "SemanticRouter" for "Semantic Router", "Cuonasu" for "Cuconasu".
- Gao missing spaces: "chunks.Chunks", "Proposition,Chunks", "Metadata Attachments:Chunks", "[7]model", "[30]proposed". Fixed with an explicit list plus a generic rule for `]` directly followed by a letter.
- Reference list errors (moot after stripping, noted for the record): `api_semanticscholar.org`, `apisemantic scholar.org`, `api-semanticscholar.org`, `api(semanticscholar.org` for `api.semanticscholar.org`; "Wikiasm" for "Wikiasp"; "Nomiraci" for "Nomiracl"; "tec 2019" for "trec 2019"; "Lmlingua" for "Llmlingua".

### Math

Spaced LaTeX from the converter: `S _ {h} = \alpha \cdot S _ {s} + S _ {d} \tag {1}`, `\text {c o n t e x t r e l e v a n c y}`, `\frac {| S |}{| T o t a l |}`. Now `S_{h} = \alpha \cdot S_{s} + S_{d} \tag{1}`, `\text{context relevancy}`, `\frac{|S|}{|Total|}`. Barnett `$\rightarrow$` became the arrow character. Inline spacing such as `$S_{s}$ , $S_{d}$`, `top- $k$` and `$D_g$ :` was tightened.

### Tables

HTML `<table>` blocks (Barnett 2, Wang 14, Gao 4) converted to pipe tables. Decisions that came from observed tables:

- Two-row headers with colspan and rowspan (Wang Tables 1, 3, 4, 6 to 11) are flattened into one header row with the group label as prefix, for example "TREC DL19 nDCG@10".
- Wang Table 11: MinerU gave RAG and Avg. a colspan of 2 each, which produced two columns named "RAG Score"; the PDF has RAG with one column and Avg. with three (Score, F1, Latency). The header is set explicitly to the PDF structure.
- Section rows ("unsupervised", "w/o Reranking") are kept as rows with empty cells.
- Rowspan cells are repeated in every covered row (Gao Table II task and sub task, Table IV framework, Wang Table 12 context). Each row is then self contained for retrieval. The Gao Table II layout (including "Recommendation" in the sub task column, and "StrategyQA" under "Language Modeling") matches the PDF layout text.
- Wang Table 14 (two row key value template) is written as two plain lines.
- Original typos kept: Wang Table 13 "SQuAD 67,00", Gao "Natural Qustion(NQ)", Gao "Multi-time".

### Footnotes

Markers came in three forms (`$^{2}$`, `$^{5}$`, `<sup>6</sup>`) and the footnote texts were gone. The texts are in the PDF text layer and were put inline in parentheses behind the marked word: Barnett 6, Wang 8, Gao 10 plus two that the converter had dropped entirely (Gao footnote 1 "resources available at https://github.com/Tongji-KGLLM/RAG-Survey" at the end of the abstract, footnote 8 for TruLens). The Gao footnote 8 URL is reconstructed: the PDF text layer prints `trulens eval/core concepts rag triad/` with spaces where the underscores are, so the URL in the file is `trulens_eval/core_concepts_rag_triad` by inference. The corresponding author line of Gao was restored as a plain line. Affiliation markers `$^{a}$` became `(a)`.

### Images, captions, reference lists

- `![](images/...)` tags removed (the `images/` directory does not exist). Captions are kept, no figure descriptions were invented. Figure labels that were pure diagram residue ("Text2image Retrieval" before Wang Figure 4) were removed.
- Reference lists removed: Barnett and Gao at the end, Wang between "References" and "A Experimental Details" (the appendix is content and stays). Convention of the siblings and the earlier class E decision. The in-text citation numbers stay.
- Acknowledgments stay.

### Kept on purpose (original paper defects)

Gao "On the contrary, it requires additional effort to build, validate, and maintain structured databases." appears twice in the PDF text layer itself. Gao "severing a dual purpose" and "aslo" (both are in the PDF). The converter did not keep all PDF typos either: the PDF has "apprach" where the converted file says "approach". The file is therefore not a letter-exact copy of the PDF, only free of conversion defects that were found. Barnett "Our results confirm this The unique aspects". Do not "fix" these in a later pass; the PDF has them.

## Indexing

One `rag-cli index --collection rag-cli-reference --document <file>.md` per paper. The guard of the shell tool blocks a second single-document index call to the same collection within 10 minutes; the calls were spaced accordingly: Barnett 23:02, Wang 23:50, Gao after 00:45 (all CEST). A `sleep`, an `until` loop or a background `sleep` to wait out the 10 minutes is blocked or killed by the shell tool after 2 minutes, so a second call right after the first cannot be scheduled by the agent itself; the wait has to be bridged by going idle and being re-triggered. A collection-wide `rag-cli index --collection rag-cli-reference` is the suggested alternative of the guard; whether it skips documents that already have a sidecar was not tested, so it was not used.

| Paper | Chunks | Sidecar |
|---|---|---|
| Barnett2024SevenFailurePoints | 19 | written |
| Wang2024RagBestPractices | 49 | written |
| Gao2023RagForLlmsSurvey | 60 | written |

The search command takes `search <query> <collection>` as positional arguments; `--collection` and `--top-k` do not exist for it (top_k is fixed at 12), and a wrong flag makes the shell tool print a refusal instead of a usage text. Calling `--help` on rag-cli is refused by the shell tool as well; the usage is in `cli.py` of the repo.

## Verification

`rag-cli list_documents rag-cli-reference --filter <name>`:

- Barnett2024SevenFailurePoints.md (19 chunks)
- Wang2024RagBestPractices.md (49 chunks)
- Gao2023RagForLlmsSurvey.md (60 chunks)

The three sidecars `Barnett2024SevenFailurePoints.json`, `Wang2024RagBestPractices.json` and `Gao2023RagForLlmsSurvey.json` now exist next to the markdown files.

`rag-cli search`:

- "seven failure points when engineering a RAG system" returned 11 Barnett chunks (rank 1 to 11, scores 0.9999 to 0.9928, chunk 0 is the title and abstract, chunk 12 contains FP1 and FP2) and one Wang chunk at rank 12.
- "best RAG practice: Hybrid with HyDE retrieval, monoT5 reranking, reverse repacking, Recomp summarization" returned 12 Wang chunks; rank 1 is the "Best Performance Practice" paragraph of section 5.1 (score 0.9997), rank 5 is the cleaned Table 11 rows, rank 6 and 11 show the rejoined sentences.
- "Naive RAG, Advanced RAG and Modular RAG paradigms" returned Gao chunks at rank 1 to 9 and 11 to 12 (rank 1 chunk 9 "B. Advanced RAG" with the Fig. 3 caption, score 0.9996; rank 2 and 4 the Modular RAG section; rank 7 the conclusion) and one FlashRAG_Modular_Toolkit chunk at rank 10. Rank 8 (chunk 20) shows the cleaned Table I with "KnowledGPT", "RoG" and "G-Retriever"; rank 12 shows the inline footnote URLs "LlamaIndex (https://www.llamaindex.ai), LangChain (https://www.langchain.com/)"; rank 9 (chunk 0) shows the restored corresponding author line and the resources URL at the end of the abstract.

Check on the cleaning itself via the search output: the Barnett chunk 3 shows the footnote URL inline ("OpenAI evals (https://github.com/openai/evals)"), Wang chunk 2 shows the rejoined sentence "...the choice of vector databases to efficiently store feature representations" followed by the Figure 1 caption, Wang chunk 33 shows the pipe table with the corrected Table 11 header, and Barnett chunk 4 contains "rewriter".

## Hints for a successor

- Do the PDF word diff first. Reading the markdown cannot find "rewritten" for "rewriter".
- `grep` in the shell is a broken function in this environment (it printed nothing for patterns that exist); `/usr/bin/grep` works.
- Do not restructure headings. All siblings use only `#`.
- If another RAG paper from `data/pdf/RAG/` is indexed later, expect the same four defect families: split sentences, footnotes without text, spaced LaTeX, collapsed table headers.

## Recap (after review)

Inventory of the branch against `integration`: this process-docs file is the only changed file. No DOCS.md describes it, so no DOCS.md was updated. The cleaned markdown files and the three sidecars are in the gitignored `data/documents/rag-cli-reference/` of the main checkout and are not part of any commit.

Details of the cleaning script that a successor would need if the same cleanup has to be repeated for another MinerU paper (the script itself was in /tmp and is not pinned, so this is the spec):

- Block level processing: split on blank lines, drop image-only lines and boilerplate blocks, strip the reference section, then merge split sentences, then convert tables, then string replacements, then LaTeX de-spacing.
- Merge rule: a prose block (or a bullet item) that does not end in `. ? ! : ; ) ] "` is joined with the next prose block; floats between them (caption lines starting with "Table N", "TABLE X", "Fig. N." or "Figure N:", the dagger table note, HTML tables) are moved behind the merged paragraph. Merging only starts after the abstract heading, otherwise the author and affiliation lines of the title block are merged. Every merge was printed and read before the output was installed (Barnett 6, Wang 19, Gao 18); one false positive was caught by that review (Gao Table IV footnote) and one is excluded explicitly (Wang "HyDE [10],").
- Replacements that must run before the merge: restored truncated text (Wang "hard to limit.").
- Table headers: header row count is 1, plus one more for every row above it that contains a rowspan cell. Colspan headers are repeated per column and joined to one header cell. Wang Table 11 needed a manual header because MinerU's colspans were wrong.
- Footnote regexes must use `[ \t]*` and not `\s*` before the marker; `\s*` swallowed the newline between the Gao author line and the affiliation line.
- Verification that carried the work: word diff PDF vs markdown before, word diff original vs cleaned markdown after, and a numeric token count per paper (PDF-only and markdown-only numbers) to see that table values were not lost. The markdown-only numbers were image file hashes and footnote numbers, the PDF-only numbers page numbers and reference page ranges.

Observed environment limits during this session, 2026-10-14: a second `--document` index call to the same collection within 10 minutes is blocked; waiting with `sleep`, `until` loops or background sleeps is blocked or cut off after 2 minutes; `rag-cli <cmd> --help` is refused. All three were bridged by working on other things and by going idle.
