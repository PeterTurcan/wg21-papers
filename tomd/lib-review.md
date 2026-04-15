# Dual-Extraction Intelligence With Uneven Test Armor

**A WG21 paper converter whose multi-signal architecture advances the state of rule-based PDF conversion, carrying active bugs in the paths its tests do not reach.**

April 2026, by Vinnie Falco

---

## 1. Executive Summary

tomd's core design remains the most structurally honest approach to PDF-to-Markdown conversion in the open-source field. Dual extraction with confidence scoring, companion prompt files for targeted LLM escalation, and WG21-specific metadata intelligence represent capabilities no competitor matches in the deterministic converter space.<sup>1</sup> Since the prior evaluation, the project has added HTML conversion support covering four WG21 paper generators (mpark, Bikeshed, hand-written, HackMD) and a 12-file pytest suite covering core classification algorithms.<sup>2</sup>

The dominant dynamic shaping tomd's current design quality is an uneven test armor that protects core classifiers while leaving pipeline integration paths - and their active bugs - exposed. A code review across all 18 source files found 10 flagged issues, the most severe being a nested-list text duplication bug in the HTML renderer<sup>3</sup>, a dehyphenation state machine that can leave duplicate words in output<sup>4</sup>, and an unstable character sort order in spatial extraction<sup>5</sup>. The existing test suite masks the nested-list bug by asserting substring presence rather than absence of duplication<sup>3</sup>. Header/footer detection, hidden region stripping, position-based list detection, and several HTML generator-specific paths have no test coverage at all.<sup>2</sup>

The competitive position is strong. The only direct competitor for WG21 paper conversion - CppDigest/wg21-paper-markdown-converter<sup>6</sup> - delegates all structural analysis to upstream libraries and an LLM vision fallback, performs no metadata extraction, and ships no tests. tomd's purpose-built pipeline outclasses it on every structural dimension. Against the broader PDF-to-Markdown field (Marker, Docling, MinerU), tomd differentiates on explicit confidence composition, WG21 targeting, and minimal dependencies - but cannot match their vision/VLM capabilities for scanned or image-heavy documents.

The verdict is **Promising** - the same category as the prior evaluation, now on stronger footing. The algorithmic core is proven by use. The remaining work is conventional engineering: closing test coverage gaps, fixing the identified bugs, adding CI, and writing a user-facing README.

---

## 2. The Project

tomd is a Python CLI tool that converts WG21 committee papers from PDF and HTML to Markdown.<sup>1</sup> Written by Vinnie Falco, it lives as a subdirectory within the `wg21-papers` repository. The tool targets WG21 papers specifically: it recognizes committee metadata fields (Document Number, Date, Reply-to, Audience), parses known section names (Abstract, Wording, References), extracts YAML front matter, and detects table-of-contents regions for removal.<sup>1</sup>

The PDF pipeline is a 14-stage sequence: per-page dual extraction (MuPDF dict + spatial coordinate rules), link collection, header/footer detection and stripping, monospace propagation via triple-signal analysis, wording detection (HSV color + drawing correlation for ins/del markup), text cleanup (dehyphenation, cross-page joining, whitespace normalization), span normalization, table detection from columnar geometry, dual-path comparison with confidence scoring, structural classification (headings, lists, code, paragraphs), TOC stripping, and Markdown emission with optional companion prompts file.<sup>1</sup> The HTML pipeline uses BeautifulSoup with generator-specific strategies, extracting metadata, stripping boilerplate, and rendering DOM-to-Markdown through a recursive traversal engine.<sup>7</sup>

The codebase spans 18 Python source files (~4,300 non-test lines) organized in a pipeline-shaped layout: `main.py` (CLI), `lib/` (format-agnostic utilities including similarity and TOC detection), `lib/pdf/` (PDF-specific pipeline stages), and `lib/html/` (HTML conversion).<sup>2</sup> Two external dependencies: PyMuPDF and BeautifulSoup4, both unpinned.<sup>8</sup> Twelve pytest files provide ~1,400 lines of test coverage.<sup>2</sup> Three commits, one contributor, born April 14, 2026.<sup>9</sup> No LICENSE file, no CI, no user-facing README.

---

## 3. The Domain

Converting standards-committee papers to Markdown serves a specific operational need: making dense technical documents reviewable in Git-based workflows where line-level diffs, pull request annotations, and plain-text search are the native tools. Five stress points shape any tool operating in this space.

**Structural fidelity.** Committee papers mix prose, code blocks, tables, wording markup (insertions/deletions), and nested lists where layout carries normative meaning. Flattening or reordering during conversion loses information that implementers and reviewers rely on. This elevates Tests 6-9, 19, 22.

**Diff-stable output.** Markdown emitted for version control must stay stable across repeated runs and minor source edits so that PR diffs reflect real content changes, not converter noise. This elevates Tests 30-32, 34.

**Explicit failure visibility.** Normative and pre-normative text is audited for accidental edits. Silent omission or corruption during conversion is a known class of incident in document pipelines. The tool must report what it could not convert, not silently drop content. This elevates Tests 8, 10, 11.

**Heterogeneous upstreams.** WG21 paper corpora span years of generator and stylesheet variation - mpark, Bikeshed, hand-written HTML, HackMD, Google Docs, Scrivener, LaTeX-based tools. A converter must isolate parser and renderer logic so fixes for one upstream template do not break another. This elevates Tests 21, 23, 30.

**Automation contracts.** Batch processing of large paper corpora demands predictable CLI behavior - stable exit semantics, machine-friendly diagnostics, batch-safe operation. This elevates Tests 10, 12, 28.

---

## 4. The Landscape

No other open-source tool occupies tomd's exact niche: deterministic, multi-signal WG21 paper conversion with explicit confidence scoring. The competitive field spans general-purpose PDF-to-Markdown converters and one direct WG21-targeted competitor.

**CppDigest/wg21-paper-markdown-converter**<sup>6</sup> (Python, no license, 0 stars, 1 contributor) is the only other tool specifically targeting WG21 paper conversion. It is a URL-oriented batch processor with CI integration. HTML conversion runs through Pandoc with committee-specific preprocessing and ~200 lines of regex post-processing. PDF conversion uses a three-tier fallback: docling (ML-based), then pdfplumber (rule-based), then OpenRouter Vision API (LLM-based OCR). The tool performs no custom structural analysis on PDFs - output quality depends entirely on upstream libraries or the LLM. No WG21 metadata extraction, no heading classification, no dehyphenation, no header/footer stripping, no confidence signaling. No tests. Heavy dependency footprint (docling pulls in PyTorch). ~1,035 lines of Python. Its strengths are CI workflow integration, URL fetching, and artifact management - operational capabilities tomd currently lacks. Its weakness is structural: it trades conversion precision for breadth and convenience.<sup>10</sup>

The broader field includes:

- **Marker** (Python, GPL-3.0, ~33k stars) - hybrid pipeline with learned layout models and optional LLM assist. Closest in ambition to tomd's structural analysis but uses ML where tomd uses geometry and font signals.
- **Docling** (Python, MIT, ~50k-58k stars) - IBM-backed layout-model-centric parser. The CppDigest converter's primary PDF engine. Strong on reading order and table detection through ML, but no WG21 awareness.
- **MinerU** (Python, AGPL-3.0, ~50k stars) - multi-backend pipeline emphasizing complex PDFs (tables, math, scans) for LLM-ready output.
- **PyMuPDF4LLM** (Python, AGPL-3.0, ~1-2k stars) - lightweight MuPDF-native Markdown extraction. Shares tomd's MuPDF foundation but lacks dual-extraction, confidence scoring, or domain-specific intelligence.
- **Nougat** (Python, MIT, ~10k stars) - Meta's pure vision model for PDF-to-Markdown with math emphasis. Different philosophy: neural end-to-end rather than rule-based.

| Feature | tomd | CppDigest | Marker | Docling | PyMuPDF4LLM |
|---|---|---|---|---|---|
| Structural analysis | Multi-signal, custom | None | ML-based | ML-based | Basic |
| Confidence scoring | Four-level enum | None | None | Partial | None |
| WG21 metadata | YAML front matter | None | None | None | None |
| HTML support | Yes (4 generators) | Yes (Pandoc) | No | Multi-format | No |
| Vision/OCR fallback | None | OpenRouter | Optional | Optional | None |
| Dependencies | 2 | 10+ | Heavy | Heavy | 1 |
| Tests | 12 files | None | Yes | Yes | Partial |
| CI integration | None | GitHub Actions | Yes | Yes | Partial |

tomd's gaps relative to the field: no vision/VLM capability for scanned pages, no CI, no batch URL fetching, no package installation path. Its differentiators: the only rule-and-geometry-first converter with explicit dual-path confidence composition, the only tool with WG21-specific targeting across both PDF and HTML inputs, and the lightest dependency footprint in the field.

---

## 5. Design Assessment

### 5.1 Bugs the Tests Do Not Catch

The most actionable compound dynamic is the interaction between tomd's uneven test coverage and its active bugs. A code review across all 18 source files found 10 flagged issues.<sup>2</sup> The three most severe bugs live in paths the test suite does not exercise - or actively masks.

The nested-list text duplication bug in `lib/html/render.py` is the clearest example. `_render_list` calls `_inline_text(li)` which recurses into nested `<ul>`/`<ol>` children, capturing their text into the parent item. The code then extracts and re-renders those same sublists, producing duplicated content - nested list item text appears both in the parent and in the indented child rendering.<sup>3</sup> The existing `test_nested` test masks this because it asserts substring presence (`"nested item" in output`) rather than asserting absence of duplication (`output.count("nested item") == 1`).<sup>2</sup> For WG21 papers, which frequently contain nested lists in wording sections, this produces silently corrupted output - precisely the failure mode the domain demands be made visible.

The dehyphenation state machine in `lib/pdf/cleanup.py` has a symmetric bug. When a next-line span is entirely consumed by dehyphenation joining (`pending_trim` becomes empty string) and the line has exactly one span, the consumed word remains in the output as a duplicate.<sup>4</sup> No test exercises this single-span edge case. The dehyphenation logic is nested within the 329-line `cleanup.py` module which mixes header/footer detection with text transformation - two distinct concerns whose coupling makes targeted testing harder (Lakos 1996).

The spatial extraction path in `lib/pdf/extract.py` sorts characters by rounded y-position only, with no secondary sort by x-coordinate.<sup>5</sup> Python's stable sort preserves rawdict iteration order within equal y-buckets, but rawdict block order is not guaranteed left-to-right across blocks. Two blocks at the same y-coordinate with reversed x-ranges would produce characters in wrong reading order. No test exercises multi-block same-y scenarios.

These bugs share a structural pattern. tomd's test suite covers core classifiers well - heading confidence, monospace detection, TOC matching, structure classification, and similarity all have dedicated test files with meaningful assertions.<sup>2</sup> But pipeline integration paths - where data flows through multiple stages and edge-case interactions emerge - are undertested. Header/footer detection, hidden region stripping, position-based list detection, and HTML generator-specific rendering paths have no direct coverage.<sup>2</sup> The bugs cluster in exactly these gaps.

### 5.2 Cross-Module Duplication and Mutation Drift

The author-parsing state machine is implemented independently in `lib/pdf/wg21.py` (`_parse_authors`) and `lib/html/extract.py` (`_parse_mpark_authors`) with identical structure but minor surface differences.<sup>2</sup> Both accumulate pending names and match email patterns using the same state transitions. Changes to the pattern must be synchronized in two places - a violation of the project's own rule that patterns live in one module (Bloch 2006).

This duplication is part of a broader pattern. Metadata extraction is split across three modules - `wg21.py` (block-level parsing for PDF), `structure.py` (`_extract_metadata` as a second pass), and `lib/__init__.py` (`format_front_matter` for output) - with no shared schema tying them together.<sup>2</sup> Regex patterns for document numbers appear in both `lib/__init__.py` (`DOC_NUM_RE`) and `lib/pdf/types.py` (`DOC_FIELD_RE`) with overlapping but distinct patterns.<sup>2</sup>

The mutation discipline compounds the duplication risk. `structure.py` uses inconsistent mutation strategy: `_merge_paragraphs` creates copies via `replace()` while `_extract_metadata` mutates Section objects in place.<sup>2</sup> The HTML renderer's `render_body` calls `decompose()` on DOM nodes during rendering, making the function non-idempotent - callers cannot predict whether their soup tree survives unchanged.<sup>3</sup> `classify_wording` in `wording.py` both mutates `span.wording_role` and returns diagnostic strings - a mixed side-effect and return-value contract that limits testability (Bloch 2006).

None of these mutation patterns are documented or tested for their side effects. The combination of duplicated logic across modules and undocumented mutation contracts means that a fix to one path can silently break the other.

### 5.3 The Operational Void

Three infrastructure gaps form a compound that prevents the algorithmic sophistication from translating into operational trust.

`requirements.txt` lists two dependencies (`pymupdf`, `beautifulsoup4`) without version pins.<sup>8</sup> PyMuPDF has undergone API changes between major versions, and tomd's dual-extraction architecture depends on specific output structures from `page.get_text("dict")` and `page.get_text("rawdict")`.<sup>5</sup> `find_hidden_regions` calls `page.get_texttrace()`, a method that is not available across all PyMuPDF versions.<sup>4</sup> A version upgrade could break extraction silently.

No CI pipeline exists.<sup>9</sup> The parent repository's `render.yml` workflow handles paper rendering with Pandoc but does not run tomd's pytest suite. The 12 test files must be run manually. Without CI, the unpinned dependency problem compounds: there is no version matrix to expose incompatibilities, no automated gate to catch regressions, and no evidence of cross-platform behavior (OpenSSF Scorecard).

No user-facing README exists. The project has invested substantial documentation effort in `CLAUDE.md` (a 125-line architecture contract) and two `ARCHITECTURE.md` files in the `lib/pdf/` and `lib/html/` subdirectories.<sup>1</sup> This documentation is thoughtful and detailed - but targets AI agents, not human operators. A developer encountering tomd for the first time has no explanation of what the tool does, how to install it, or what its limitations are. The `main.py` CLI help string exists but is discoverable only by reading the source. The documentation inversion is specific: the author can clearly document; the audience is misallocated.

The project also has no LICENSE file, no `pyproject.toml` or entry point declaration, and no packaging infrastructure.<sup>9</sup> It must be invoked as `python tomd/main.py` from the parent directory - a fragile path for batch-processing integration.

---

## 6. Design Maturity

**Promising.** tomd's core architecture - dual-extraction with multi-signal confidence scoring, companion prompt files for selective LLM escalation, pipeline-shaped physical modularity, and WG21-specific intelligence across both PDF and HTML inputs - represents genuine design sophistication that no competitor matches in the deterministic converter space. The API surface is maximally minimal (`convert_pdf`, `convert_html`, CLI), naming is consistent across all 18 files, and the two-dependency approach keeps the supply chain clean (Pike 2015).

The project has improved since its prior evaluation. HTML conversion support now covers four WG21 paper generators where none existed before. A 12-file pytest suite covers core classification algorithms where no tests existed before. The tool has been exercised against a corpus of real WG21 papers with outputs preserved in `.out/`.<sup>2</sup>

The gaps are addressable without redesign. The nested-list and dehyphenation bugs are localized fixes. The cross-module duplication consolidates into shared helpers. The test coverage gaps follow the existing test architecture - adding files for header/footer detection, hidden regions, and HTML rendering edge cases requires no new patterns. CI, dependency pinning, packaging, and a README are conventional infrastructure.

The project's trajectory is upward. The hard problem - structural analysis of ambiguous PDF and HTML content with explicit uncertainty signaling - is solved with care. The remaining work is operational discipline catching up to algorithmic ambition. The compound dynamics identified in Section 5 all trace to infrastructure gaps, not to architectural flaws.

---

## 7. Audit Trail

**Subject:** `wg21-papers/tomd/` (local, inspected April 14, 2026)

**Supplementary imports:**

- Code review (`review.md`): 10 flagged issues across 18 files, 152 clean checks, 54 advisory. Most critical: nested-list duplication, dehyphenation duplicate, spatial sort order, cross-module author parsing, docstring/implementation mismatch.

**Governing specification:** None identified.

**Cache status:** Prior domain brief and competitive map from `doc/tomd-eval.md` (April 2026). Refreshed for current analysis with updated project state (HTML support added, tests added, competitor added).

**Prior reports imported:** `doc/tomd-eval.md` (April 2026, Opus 4.6). Prior verdict: Promising. Prior state: no tests, no HTML support, PDF-only.

**Reconnaissance:** Full source read of all 18 Python source files, 12 test files, `requirements.txt`, `CLAUDE.md`, `lib/pdf/ARCHITECTURE.md`, `lib/html/ARCHITECTURE.md`.

**Domain brief:** 5 stress points identified. Elevated tests: 6-12, 19, 21-23, 28, 30-32, 34.

**Competitive map:** 6 competitors evaluated (CppDigest/wg21-paper-markdown-converter, Marker, Docling, MinerU, PyMuPDF4LLM, Nougat). CppDigest noted as direct WG21-targeted competitor per user input.

**Diagnosis:** 38 tests run. 10 findings produced. 28 clean results.

**Challenge outcomes:**

- 8 findings survived all applicable challenge tests (Tests 8, 10, 16, 17, 21, 26, 30, 32)
- 2 candidate findings killed: Test 36 (License - personal tool, not distributed; Challenge Test 2), Test 38 (Maintenance health - expected for personal tool maturity; Challenge Test 6)

**Coupling analysis:** 5 compound dynamics proposed. 4 survived coupling challenge. 1 killed (Documentation inversion blocks test authoring - Challenge Test 1, co-present but not genuinely amplifying).

**Surviving compounds:**

- Bugs in untested paths (Tests 30+8+21) - uneven coverage exposes mutation pattern bugs in the most complex module
- Duplicated logic with undocumented mutation contracts (Tests 8+21) - cross-module duplication compounds with inconsistent mutation discipline
- Unpinned, unverified dependency stack (Tests 26+32) - no pins plus no CI means extraction API contract is defended by nothing
- Coverage gaps in integration paths (Tests 30+32) - absent CI means test gaps cannot be detected by automated gates

---

## 8. References

<sup>1</sup> `CLAUDE.md` - tomd architecture and design rules

<sup>2</sup> `review.md` - code review, April 14, 2026 (supplementary import)

<sup>3</sup> `lib/html/render.py` - DOM-to-Markdown rendering engine, `_render_list` nested-list bug

<sup>4</sup> `lib/pdf/cleanup.py` - dehyphenation state machine, `find_hidden_regions` API compatibility

<sup>5</sup> `lib/pdf/extract.py` - dual extraction implementation, spatial character sort order

<sup>6</sup> CppDigest/wg21-paper-markdown-converter. GitHub repository. https://github.com/CppDigest/wg21-paper-markdown-converter

<sup>7</sup> `lib/html/__init__.py`, `lib/html/extract.py`, `lib/html/render.py` - HTML conversion pipeline

<sup>8</sup> `requirements.txt` - dependency declaration (pymupdf, beautifulsoup4, unpinned)

<sup>9</sup> Git history: 3 commits, 1 contributor, April 14, 2026. No LICENSE, no CI workflow, no README.

<sup>10</sup> `doc/wg21-paper-markdown-converter-eval.md` - prior evaluation of competitor, April 2026

---

Bloch, J. "How to Design a Good API and Why it Matters." *Companion to OOPSLA*, 2006.

Lakos, J. *Large-Scale C++ Software Design.* Addison-Wesley, 1996.

OpenSSF Scorecard. Open Source Security Foundation.

Pike, R. "Go Proverbs." Gopherfest, November 2015.

---

*April 2026 - Opus 4.6*
