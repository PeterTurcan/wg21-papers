# Code Review: tomd

- **Date:** 2026-04-14
- **Model:** Opus 4.6

Clean pipeline architecture with well-separated modules; a nested-list text duplication bug in HTML rendering, a dehyphenation duplicate-text bug in PDF cleanup, and cross-module author-parsing drift are the most actionable findings across 10 flagged issues.

## Executive Summary

tomd is a ~3,800-line Python PDF/HTML-to-Markdown converter organized around a dual-extraction architecture that produces confidence-scored structural classifications. The 14-stage PDF pipeline flows cleanly from extraction through cleanup, normalization, comparison, structuring, and emission, with each stage owning a distinct responsibility. The HTML path mirrors the PDF pipeline's output contract using BeautifulSoup with generator-specific strategies for mpark, Bikeshed, hand-written, and HackMD papers.

The review found 10 flagged issues across 18 source files (216 total checks: 152 clean, 54 advisory, 10 flag). The most critical issues are: a nested-list text duplication bug in the HTML renderer that doubles nested item content; a dehyphenation state-machine bug in PDF cleanup that can leave duplicate words in output; character sort order in spatial extraction that relies on unstable iteration order; cross-module duplication of the author-parsing state machine between PDF and HTML paths; and a `Block.font_size` docstring that claims character-count weighting while the implementation uses line-count voting. Test coverage is uneven - core algorithms like heading confidence, monospace classification, and TOC detection are well-tested, while header/footer detection, hidden region stripping, position-based list detection, and several HTML generator-specific paths have no direct coverage.

## Synthesis

### API Grouping

Ten logical API groups emerge from the inventory:

- **Pipeline entry:** `convert_pdf`, `convert_html`, `main` - three entry points, clean and narrow
- **Text extraction:** `extract_mupdf`, `extract_spatial`, `collect_links`, `attach_links` - dual-path PDF extraction with link annotation
- **Classification:** `classify_monospace`, `heading_confidence`, `classify_wording`, `detect_tables` - single-concern classifiers with multi-signal designs
- **Text cleanup:** `cleanup_text`, `normalize_whitespace`, `normalize_spans` - whitespace, dehyphenation, cross-page joining, style boundary snapping
- **Header/footer detection:** `get_edge_items`, `detect_repeating`, `strip_repeating` - repeating content identification and removal
- **Structure analysis:** `compare_extractions`, `structure_sections` - dual-path comparison and structural classification
- **Metadata:** `extract_metadata_from_blocks` (PDF), `extract_metadata` (HTML), `format_front_matter` - WG21-specific metadata parsing and YAML output
- **Output:** `emit_markdown`, `emit_prompts` - Markdown generation and companion prompts file
- **Support:** `similar`, `find_toc_indices`, `is_readable`, `propagate_monospace` - format-agnostic utilities
- **Data model:** `Span`, `Line`, `Block`, `Section`, `PageEdgeItem`, `Confidence`, `SectionKind` - shared types and enums

These groups are well-separated with minimal coupling between them. The data model types are the primary integration surface.

### Cohesion

The codebase pulls in the same direction consistently. The dual-extraction architecture is the organizing principle, and every module respects it. Data flows through a clean `Block` -> `Section` -> markdown string pipeline. The shared `lib/__init__.py` provides cross-cutting utilities without creating unwanted coupling.

Three fracture points exist. First, the author-parsing state machine (pending name + email accumulation) is implemented independently in `wg21.py` (`_parse_authors`) and `html/extract.py` (`_parse_mpark_authors`) with minor surface differences but identical structure - changes to the pattern must be synchronized in two places. Second, metadata extraction is split between `wg21.py` (block-level parsing for PDF), `structure.py` (`_extract_metadata` as a second pass), and `lib/__init__.py` (`format_front_matter` for output) with no shared schema tying them together. Third, `structure.py` uses inconsistent mutation strategy - `_merge_paragraphs` creates copies via `replace()` while `_extract_metadata` mutates Section objects in place, so callers cannot predict whether their input survives unchanged.

### Scope

The tool does exactly what it claims and no more. The v2 LLM integration is cleanly deferred via the prompts file mechanism. The dual-extraction confidence approach is ambitious but justified by the problem domain. The HTML path is leaner but covers the four major WG21 paper generators adequately.

One scope concern: `structure.py` at 832 lines handles seven distinct concerns (dual-path comparison, metadata extraction, heading classification, list detection, paragraph merging, code block detection, wording reclassification, and nesting validation). This is the module most likely to accumulate bugs as the codebase evolves. Breaking it into `compare.py` + `classify.py` would reduce the blast radius of changes.

### Responsibility Leakage

- `structure.py` owns both dual-path comparison (pipeline step 10) AND structural classification (step 12) - distinct pipeline stages bundled in one file
- Author parsing implemented twice: `wg21.py/_parse_authors` and `html/extract.py/_parse_mpark_authors` with the same state machine
- Metadata extraction bleeds across `wg21.py`, `structure.py/_extract_metadata`, and `lib/__init__.py/format_front_matter` - three modules touching the same data with no shared schema
- `cleanup.py` handles both header/footer detection (a detection concern) and text cleanup (a transformation concern)
- `render.py` calls `decompose()` on DOM nodes during rendering, bleeding mutation into what callers expect to be a read operation, making `render_body` non-idempotent
- `classify_wording` in `wording.py` both mutates `span.wording_role` and returns diagnostic strings - mixed side-effect and return-value contract

### Cross-File Coherence

Naming conventions are consistent across all 18 files. The `_private` prefix convention is followed everywhere. Constants are well-named and centralized in `types.py`. The data model types are used uniformly across the pipeline.

Three coherence gaps: (1) regex patterns for document numbers appear in both `lib/__init__.py` (`DOC_NUM_RE`) and `lib/pdf/types.py` (`DOC_FIELD_RE`) with overlapping but distinct patterns, creating drift risk and violating the project's own rule that patterns live in one place; (2) font size computation uses span-level weighting in `_detect_body_size` but line-level `font_size` property in `_rank_font_sizes`, both in `structure.py` - mixed granularity for the same concept; (3) the `"\n\n".join(parts) + rstrip + "\n"` output assembly pattern appears in both `lib/pdf/emit.py` and `lib/html/__init__.py` with no shared helper.

## File Profiles

### main.py

CLI entry point (~124 lines). Parses arguments (input files/globs, output path, output directory, verbose flag), dispatches to either `convert_pdf` or `convert_html` based on file extension, writes `.md` and optional `.prompts.md` output files.

#### Findings

10/12 checks clean.

- **Bugs (advisory):** If a glob pattern has no matches, the raw pattern string is appended and later skipped as "not found" - delays user feedback. `sys.exit(0)` on no input is arguable.
- **Error handling (advisory):** `except Exception` is broad but logs full traceback and prints to stderr. No silent swallowing.

### lib/\_\_init\_\_.py

Shared utilities and constants (~112 lines). Provides `ascii_escape`, `strip_format_chars`, `format_front_matter`, `ALLOWED_LINK_SCHEMES`, and shared regex patterns.

#### Findings

8/12 checks clean.

- **Bugs (advisory):** `FORMAT_CHARS` iterates all 1,114,112 Unicode code points at import time. One-time cost but ~150-300ms on cold start.
- **Duplication (advisory):** `SECTION_NUM_PREFIX_RE` overlaps with `SECTION_NUM_RE` in `lib/pdf/types.py`. Project rules require patterns defined in one place.
- **Error handling (advisory):** `_yaml_escape` handles `\`, `"`, `\n` but not tab characters. A tab in a metadata value would produce invalid YAML.
- **Security (advisory):** YAML escaping covers the critical injection characters. Adequate for the WG21 metadata domain.

### lib/similarity.py

Dual-algorithm string similarity (~62 lines). SequenceMatcher + Jaccard with per-algorithm thresholds and 200-character circuit breaker.

#### Findings

9/12 checks clean.

- **Bugs (flag, medium):** The 200-char circuit breaker returns `False` for identical strings over 200 characters. Two identical long heading strings (e.g., a verbose section title repeated in the TOC) will not be recognized as similar. The docstring does not warn callers.
- **Contract fidelity (advisory):** Docstring embeds caller knowledge ("the caller (TOC detection) provides a second guard") in a format-agnostic module.
- **API design (advisory):** Thresholds are fixed module constants, not overridable by callers.

### lib/toc.py

Table of Contents detection (~133 lines). Matches section texts against known headings using fuzzy similarity. Detects runs of 3+ consecutive matches, bridges small gaps.

#### Findings

9/12 checks clean.

- **Bugs (advisory):** `_matches_heading` passes an already-first-lined string into `_normalize_toc_entry` which calls `_first_line` again. Redundant but idempotent.
- **Duplication (advisory):** The double `_first_line` call noted above.
- **Readability (advisory):** The gap-bridging loop requires careful reading. The retroactive inclusion of gap entries is the least obvious part.

### lib/pdf/\_\_init\_\_.py

Pipeline orchestrator (~194 lines). Exports `convert_pdf()`, coordinating the full 14-step pipeline.

#### Findings

7/12 checks clean.

- **Bugs (advisory):** `if page_count > 0` guard at line 106 is redundant - the function returns earlier for empty PDFs. Table section insertion uses O(n*m) linear scan per table.
- **Duplication (advisory):** `cleanup_text` and `normalize_spans` applied identically to both block paths. `strip_repeating` / `strip_hidden_blocks` similarly duplicated.
- **Single responsibility (advisory):** `convert_pdf` is ~140 lines. Table-insertion block could be extracted into a named helper.
- **Error handling (advisory):** Empty `dominant_font` string passed to `propagate_monospace` is handled but implicit.
- **Readability (advisory):** Step-number comments matching the CLAUDE.md pipeline numbering would improve scanability.

### lib/pdf/types.py

Core data model (~231 lines). Defines `Span`, `Line`, `Block`, `Section`, `PageEdgeItem` dataclasses; `Confidence` and `SectionKind` enums; named constants; precompiled regex; and `is_readable()`.

#### Findings

7/12 checks clean.

- **Bugs (flag, low):** `Block.font_size` docstring says "Most common font size among lines (by character count)" but the implementation counts by line count (one vote per line regardless of character count).
- **Contract fidelity (flag, low):** Same docstring/implementation mismatch as above.
- **Duplication (advisory):** `SECTION_NUM_RE` overlaps with `SECTION_NUM_PREFIX_RE` in `lib/__init__.py`.
- **Single responsibility (advisory):** `Span.wording_role` is typed as `str | None` rather than an enum. Allows typos to pass silently.
- **API design (advisory):** `Section` has 11 fields with defaults. `Section.font_size` defaults to `0.0` which is indistinguishable from "not set" vs "actually zero."

### lib/pdf/extract.py

Dual-path PDF text extraction (~256 lines). `extract_mupdf()` uses MuPDF's dict API; `extract_spatial()` uses rawdict with four spatial rules. Link collection and attachment.

#### Findings

9/12 checks clean.

- **Bugs (flag, medium):** `extract_spatial` sorts chars by rounded y-position only, with no secondary sort by x-coordinate. Python's stable sort preserves the original rawdict iteration order within equal y-buckets, but rawdict block order is not guaranteed left-to-right. Two blocks at the same y with reversed x-ranges would produce characters in wrong reading order.
- **Readability (advisory):** `extract_spatial` is 135 lines with three nested `_flush_*` closures mutating outer-scope lists. Character tuples use positional indexing (`c[0]`, `c[1]`, `c[4]`) - a named tuple would improve readability.
- **API design (advisory):** `attach_links` is O(links x blocks x lines x spans). An R-tree or y-bucketed index would scale better for large documents.

### lib/pdf/mono.py

Triple-signal monospace detection (~188 lines). Font name keyword decomposition, glyph width uniformity, glyph spacing uniformity. Also `propagate_monospace()`.

#### Findings

11/12 checks clean.

- **API design (advisory):** `propagate_monospace` requires `dominant_font` to be pre-lowercased. Callers who forget get silent mismatches. Consider lowercasing inside the function defensively.

### lib/pdf/cleanup.py

Header/footer detection and text cleanup (~329 lines). Edge items, repeating strip, NBSP normalization, dehyphenation, cross-page joining, hidden region detection.

#### Findings

5/12 checks clean.

- **Bugs (flag, medium):** `cleanup_text` dehyphenation: when `pending_trim` is empty string (next line's first span entirely consumed by dehyphenation) and the line has exactly 1 span, the consumed word remains in output as a duplicate. Example: `["imple-"]` + `["mentation"]` produces `"implementation"` on line 1 and `"mentation"` still present on line 2.
- **Bugs (flag, medium):** `find_hidden_regions` calls `page.get_texttrace()` which is not a standard PyMuPDF API method across all versions. Raises `AttributeError` at runtime with no fallback on incompatible versions.
- **Duplication (advisory):** Per-span NBSP replacement + multi-space collapsing in `cleanup_text` duplicates the logic in `normalize_whitespace`. Consider having one call the other.
- **Documentation (advisory):** `find_hidden_regions` is named generically but behavior is Google Docs-specific.
- **Single responsibility (advisory):** `cleanup_text` does whitespace normalization, cross-page joining, and dehyphenation. The dehyphenation state machine could be extracted.
- **Resource management (advisory):** Deferred `import fitz` inside `strip_hidden_blocks` is inconsistent with the rest of the project.
- **Error handling (advisory):** `find_hidden_regions` accesses character data by positional index with no guard. Format changes would raise `IndexError` with no context.
- **Readability (advisory):** The dehyphenation state machine uses `pending_trim` as a nullable string with three states (None, truthy, falsy-but-not-None). An explicit enum would clarify intent.

### lib/pdf/spans.py

Span normalization (~143 lines). Snaps bold/italic style boundaries to word edges between adjacent non-monospace spans.

#### Findings

11/12 checks clean.

- **Duplication (advisory):** The forward pass and backward pass share the same guard structure (monospace check, style check, touch check, boundary find, text move). A shared `_try_snap(result, i, direction)` helper could reduce the ~60 lines of near-parallel logic.

### lib/pdf/table.py

Table detection (~153 lines). Identifies columnar layout by x-gap between lines, groups consecutive matching blocks into table sections.

#### Findings

11/12 checks clean.

- **Bugs (advisory):** `_block_column_positions` checks each line's x-start against the first line's x-start, not against its predecessor. Lines at [50, 300, 200] would pass even though columns aren't in ascending x-order.

### lib/pdf/structure.py

The largest module (~832 lines). Dual-path comparison, metadata extraction, heading classification, list detection, paragraph merging, code block detection, wording reclassification, nesting validation.

#### Findings

5/12 checks clean.

- **Bugs (flag, low):** `_extract_metadata` mutates input `Section` objects via `sec.text = "\n".join(leftover)`, unlike `_merge_paragraphs` which uses `replace()`. If `structure_sections` is ever called twice on the same sections, metadata fields would already be stripped. Short all-uppercase text (<=3 words) in the metadata zone is silently consumed as a category label; a 3-word all-caps title would be discarded before title detection.
- **Duplication (advisory):** `compare_extractions` repeats the filter-rebuild-append promotion pattern in pairwise and bulk passes. A `_promote_pages` helper would eliminate ~30 lines.
- **Documentation (advisory):** `_extract_metadata` does not document the "metadata zone" concept or that short all-uppercase text is consumed as category labels. `_detect_code_blocks` doesn't document the two-phase language-label removal.
- **Contract fidelity (advisory):** `compare_extractions` docstring claims "region by region" comparison; implementation is whole-page multiset word similarity plus promotions. `structure_sections` silently drops language-label sections without documenting this behavior.
- **Single responsibility (advisory):** `_extract_metadata` mixes key-value metadata extraction with category label filtering.
- **Readability (advisory):** 832 lines, deep pipeline in `structure_sections`. `_detect_code_blocks` manages `fence_lang` and `pending_label_idx` as function-level state alongside a `flush_mono` closure with `nonlocal` - subtle interaction.
- **API design (advisory):** `structure_sections` mutates input sections in-place inconsistently (some helpers copy, some mutate directly). Callers cannot assume their sections are unchanged.

### lib/pdf/emit.py

Markdown generation (~381 lines). Renders headings, paragraphs, code blocks, tables, lists, wording sections. Generates companion prompts file.

#### Findings

9/12 checks clean.

- **Bugs (advisory):** A span with both `wording_role` and `monospace=True` takes only the wording path, silently dropping backtick formatting. `_render_heading_spans` only renders the first line of a heading section; multi-line headings silently drop subsequent lines.
- **Duplication (advisory):** `_render_paragraph_spans` and `_render_wording_section` both perform `normalize_whitespace(joined_lines)` followed by `" ".join(stripped_lines)`.
- **Error handling (advisory):** `_estimate_char_width` silently returns a module-level default with no log message indicating the fallback was used.

### lib/pdf/wording.py

Wording section detection (~217 lines). HSV color analysis, drawing decoration correlation, body color identification.

#### Findings

7/12 checks clean.

- **Contract fidelity (advisory):** `_build_body_color` is documented as "retained for planned v2 integration" but is dead code - never called. Should be removed or gated behind a TODO.
- **Single responsibility (advisory):** `classify_wording` performs classification, mutates `span.wording_role`, and returns problem descriptions. The mixed side-effect and return-value contract limits testability.
- **Error handling (advisory):** `collect_line_drawings` catches bare `Exception`. Catching `RuntimeError` (MuPDF's exception type) would be tighter.
- **Readability (advisory):** Candidate tuples `(span, role, confidence)` would benefit from a `NamedTuple` or named unpacking.
- **API design (advisory):** Mutation-plus-return pattern means callers unaware of the side effect may observe unexpected span changes.

### lib/pdf/wg21.py

WG21-specific metadata extraction (~213 lines). Parses document number, date, audience, reply-to from page 0 blocks. Handles Scrivener and Google Docs formats.

#### Findings

9/12 checks clean.

- **Duplication (flag, medium):** `_parse_authors` is structurally near-identical to `_parse_mpark_authors` in `lib/html/extract.py`. Both implement the same pending-name + email state machine with minor variations. Changes to the pattern must be synchronized in two places. Should be consolidated into a shared helper in `lib/__init__.py`.
- **Single responsibility (advisory):** `extract_metadata_from_blocks` handles title detection, label-value parsing, and author overflow in a single 107-line function. The author overflow block nests four levels deep.
- **Readability (advisory):** The author-overflow block nests `for > if > for > if`. Extracting it into `_collect_extra_authors` would reduce nesting.

### lib/html/\_\_init\_\_.py

HTML converter entry point (~60 lines). Exports `convert_html()`, orchestrating parsing, generator detection, metadata extraction, boilerplate stripping, and body rendering.

#### Findings

10/12 checks clean.

- **Duplication (advisory):** The `"\n\n".join(parts)` + `rstrip() + "\n"` output assembly pattern duplicates `emit_markdown` in `lib/pdf/emit.py`.
- **Error handling (advisory):** `ascii_escape` is applied to markdown output but not to prompts. If problem descriptions ever contain non-ASCII, the prompts file would have raw non-ASCII while markdown is escaped. Currently latent.

### lib/html/extract.py

HTML parsing and metadata extraction (~330 lines). Generator detection, WG21 metadata extraction with generator-specific strategies, boilerplate stripping.

#### Findings

7/12 checks clean.

- **Bugs (flag, low):** `_extract_handwritten_metadata` evaluates `DATE_RE.search(line)` twice - once in the `elif` condition and once to extract the match group. Not a correctness bug but wasteful and fragile under refactoring.
- **Duplication (flag, medium):** `_parse_mpark_authors` duplicates the pending-name/email state machine from `lib/pdf/wg21._parse_authors`. Same cross-module issue as wg21.py finding. Additionally, the `authors = metadata.get("reply-to", [])` / `authors.append(...)` / `metadata["reply-to"] = authors` pattern appears at three separate locations.
- **Resource management (advisory):** `_parse_mpark_authors` creates a new `BeautifulSoup` instance to re-parse a single cell's HTML after string-level `<br>` replacement. Iterating `cell.children` would be more robust.
- **Readability (advisory):** `line.strip().strip("<>").strip()` - triple chained strip with angle brackets. An explicit `re.sub(r"[<>]", "", line).strip()` would be clearer.
- **API design (advisory):** `strip_boilerplate` mutates its soup argument in-place with no return-value indication of what was removed (only problem strings).

### lib/html/render.py

DOM-to-Markdown rendering engine (~376 lines). Recursively traverses HTML elements producing headings, paragraphs, code blocks, tables, lists, blockquotes, wording divs, inline formatting.

#### Findings

8/12 checks clean.

- **Bugs (flag, medium):** `_render_list` calls `_inline_text(li)` which recurses into nested `<ul>`/`<ol>` children, capturing their text. Lines 208-213 then extract and re-render those same sublists. This produces duplicated text - nested list item content appears both in the parent item's text and in the indented child rendering. The existing `test_nested` test masks this because it only asserts substring presence.
- **Bugs (flag, low):** `_render_table` uses `el.find_all("tr")` with default `recursive=True`, which flattens nested `<table>` rows into the parent table.
- **Duplication (advisory):** The pattern `parts = []; _render_children(el, parts, generator); "\n\n".join(...)` appears in six functions. A `_render_container(el, generator) -> str` helper would eliminate the repetition.
- **Contract fidelity (advisory):** `render_body` docstring says it "may mutate the soup tree" but due to the ordering bug in `_render_list`, the mutation happens after text is already captured, so it doesn't achieve its intended purpose.
- **Readability (advisory):** `_inline_text` is 80 lines handling 15+ tag types via cascading if-continue. `_render_element` handles 20+ tag types in 56 lines with the same pattern.

## API Surface

### main.py

- public | `main` | function | CLI entry: argument parsing, file dispatch, output writing

### lib/\_\_init\_\_.py

- public | `ascii_escape` | function | Encode non-ASCII chars as HTML character references
- public | `FORMAT_CHARS` | constant | Frozenset of all Unicode format characters (Cf category)
- public | `strip_format_chars` | function | Remove Unicode format characters from text
- public | `FRONT_MATTER_ORDER` | constant | Ordered list of YAML front matter field names
- public | `format_front_matter` | function | Format metadata dict as YAML front matter string
- public | `ALLOWED_LINK_SCHEMES` | constant | Frozenset of allowed URL schemes
- public | `EMAIL_RE` | regex | Matches email addresses
- public | `DATE_RE` | regex | Matches ISO dates
- public | `DOC_NUM_RE` | regex | Matches WG21 document numbers
- public | `SECTION_NUM_PREFIX_RE` | regex | Matches dotted-decimal section number prefixes

### lib/similarity.py

- public | `similar` | function | True if either algorithm scores above threshold | `(a, b)` -> `bool`

### lib/toc.py

- public | `find_toc_indices` | function | Return indices of entries forming a TOC | `(texts, headings)` -> `set[int]`

### lib/pdf/\_\_init\_\_.py

- public | `convert_pdf` | function | Convert PDF file to Markdown with optional prompts | `(path)` -> `tuple[str, str|None]`

### lib/pdf/types.py

- public | `Confidence` | enum | HIGH, MEDIUM, LOW, UNCERTAIN
- public | `SectionKind` | enum | TITLE, METADATA, HEADING, PARAGRAPH, LIST, CODE, TABLE, UNCERTAIN, WORDING, WORDING_ADD, WORDING_REMOVE
- public | `Span` | dataclass | A run of text with uniform font properties
- public | `Line` | dataclass | A sequence of spans forming a single line
- public | `Block` | dataclass | A group of lines forming a paragraph-level unit
- public | `Section` | dataclass | A classified region of the document
- public | `PageEdgeItem` | dataclass | Text item near page top/bottom for header/footer detection
- public | `WORD_GAP_RATIO` | constant | Spatial rule threshold (0.3)
- public | `LINE_SPACING_RATIO` | constant | Spatial rule threshold (1.8)
- public | `PARA_SPACING_RATIO` | constant | Spatial rule threshold (2.5)
- public | `Y_TOLERANCE` | constant | Header/footer y-matching tolerance (2.0)
- public | `REPEATING_THRESHOLD` | constant | Minimum page fraction for repeating (0.5)
- public | `EDGE_ITEMS_PER_PAGE` | constant | Edge items to capture per page (3)
- public | `SIMILARITY_THRESHOLD` | constant | Word-level similarity threshold (0.85)
- public | `MIN_UNCERTAIN_WORDS` | constant | Minimum words to keep uncertain status (10)
- public | `FALLBACK_FONT_SIZE` | constant | Default font size (12.0)
- public | `FALLBACK_BODY_SIZE` | constant | Default body size (11.0)
- public | `SECTION_NUM_RE` | regex | Dotted-decimal section numbers
- public | `DOC_FIELD_RE` | regex | Document Number/# patterns
- public | `REPLY_TO_RE` | regex | Reply-to/Author patterns
- public | `AUDIENCE_RE` | regex | Audience patterns
- public | `PAGE_NUM_RE` | regex | Page number patterns
- public | `BULLET_CHARS` | constant | Unicode bullet characters
- public | `BULLET_RE` | regex | Lines starting with bullets
- public | `NUMBERED_LIST_RE` | regex | Lines starting with numbered markers
- public | `COMPOUND_PREFIXES` | constant | Compound-word prefixes for dehyphenation skip
- public | `KNOWN_SECTIONS` | constant | Known WG21 section names
- public | `TERMINAL_PUNCTUATION` | constant | Sentence-ending punctuation
- public | `is_readable` | function | Heuristic readability check | `(text)` -> `bool`

### lib/pdf/extract.py

- public | `extract_mupdf` | function | Extract text via MuPDF dict API | `(page, page_num)` -> `list[Block]`
- public | `extract_spatial` | function | Extract text via spatial rules | `(page, page_num)` -> `list[Block]`
- public | `collect_links` | function | Collect hyperlink annotations | `(page)` -> `list[dict]`
- public | `attach_links` | function | Match links to spans by bbox overlap | `(blocks, links)` -> `None`

### lib/pdf/mono.py

- public | `classify_monospace` | function | Accept/reject monospace from available signals | `(font_name, char_widths, char_x_origins, chars)` -> `bool`
- public | `propagate_monospace` | function | Apply spatial path decisions to MuPDF spans | `(mupdf_blocks, spatial_blocks, dominant_font)` -> `None`

### lib/pdf/cleanup.py

- public | `get_edge_items` | function | Get top/bottom text items by y-coordinate | `(blocks, page_num, page_height)` -> `list[PageEdgeItem]`
- public | `detect_repeating` | function | Identify repeating header/footer items | `(all_edge_items, total_pages)` -> `set[tuple]`
- public | `strip_repeating` | function | Remove lines matching repeating patterns | `(blocks, repeating)` -> `list[Block]`
- public | `normalize_whitespace` | function | Collapse spaces, replace NBSP, strip trailing | `(text)` -> `str`
- public | `find_hidden_regions` | function | Find hidden text regions | `(page, body_fonts)` -> `set[tuple]`
- public | `strip_hidden_blocks` | function | Remove blocks in hidden regions | `(blocks, hidden_bboxes)` -> `list[Block]`
- public | `cleanup_text` | function | Apply all text cleanup operations | `(blocks)` -> `list[Block]`

### lib/pdf/spans.py

- public | `normalize_spans` | function | Snap bold/italic boundaries to word edges | `(blocks)` -> `list[Block]`

### lib/pdf/table.py

- public | `detect_tables` | function | Detect table regions from block structure | `(blocks)` -> `tuple[list[Section], list[Block]]`
- public | `exclude_table_regions` | function | Remove blocks overlapping table regions | `(blocks, table_sections)` -> `list[Block]`

### lib/pdf/structure.py

- public | `compare_extractions` | function | Compare two extraction paths via word similarity | `(mupdf_blocks, spatial_blocks)` -> `list[Section]`
- public | `structure_sections` | function | Apply heading/list/paragraph classification | `(sections, has_title)` -> `tuple[dict, list[Section]]`
- public | `heading_confidence` | function | Determine heading level and confidence | `(has_number, number_level, font_level, is_bold, is_known)` -> `tuple[int, Confidence]`

### lib/pdf/emit.py

- public | `emit_markdown` | function | Generate Markdown from structured sections | `(metadata, sections)` -> `str`
- public | `emit_prompts` | function | Generate prompts file for uncertain regions | `(sections)` -> `str|None`

### lib/pdf/wording.py

- public | `classify_wording` | function | Classify spans as ins/del/context | `(blocks, page_drawings)` -> `list[str]`
- public | `collect_line_drawings` | function | Collect horizontal line drawings from page | `(page)` -> `list[tuple]`

### lib/pdf/wg21.py

- public | `extract_metadata_from_blocks` | function | Extract WG21 metadata from page 0 blocks | `(blocks, text_colors)` -> `tuple[dict, set[int]]`

### lib/html/\_\_init\_\_.py

- public | `convert_html` | function | Convert HTML file to Markdown | `(path)` -> `tuple[str, str|None]`

### lib/html/extract.py

- public | `parse_html` | function | Parse HTML text into BeautifulSoup | `(text)` -> `BeautifulSoup`
- public | `detect_generator` | function | Identify generator tool | `(soup)` -> `str`
- public | `extract_metadata` | function | Extract WG21 metadata from HTML | `(soup, generator)` -> `dict`
- public | `strip_boilerplate` | function | Remove non-content elements in-place | `(soup, generator)` -> `list[str]`

### lib/html/render.py

- public | `render_body` | function | Render HTML body to Markdown | `(soup, generator)` -> `str`
