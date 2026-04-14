# Code Review: Scrivener

- **Date:** 2026-04-14
- **Model:** claude-4.6-opus

Well-layered Markdown-to-PDF pipeline held together by an untyped dict and zero tests.

## Executive Summary

Scrivener is a Python toolchain that converts Markdown with YAML front matter into styled PDFs using ReportLab, Mistune v3, and external YAML style definitions with downloadable variable fonts. The architecture is clean: `scrivener.py` handles CLI, `builder.py` orchestrates per-document conversion, `config.py` manages styles and inheritance, and `renderer.py` (the bulk of the codebase at 1120 lines) translates Mistune AST tokens into ReportLab flowables for headings, lists, tables, code blocks, mermaid diagrams, wording divs, and more.

The review found 5 flags, 83 advisories, and 68 clean checks across 13 source files. The flags concentrate in `renderer.py` (temp file leak in mermaid rendering, fragile variable scoping) and `logo.py` (likely double-scaling bug in SVG handling, undocumented None return). The systemic issues are not in any single file but in the architecture's seams: the `style` dict flows through every module as an untyped, partially-documented contract, mutation conventions are inconsistent across the API surface, and no test suite exists to catch regressions.

## Synthesis

### API Grouping

The codebase organizes into six logical API groups:

**CLI Surface** - `scrivener.py`: `main`

**Pipeline Orchestration** - `builder.py`: `build_pdf`

**Configuration & Styles** - `config.py`: `PROJECT_ROOT`, `STYLES_DIR`, `IMAGES_DIR`, `FONTS_DIR`, `MANIFEST_PATH`, `PAGE_CONFIGS`, `sp`, `deep_merge`, `resolve_style_path`, `load_style`, `apply_options`, `resolve_palette`, `extract_front_matter`, `merge_config`; `catalog.py`: `IMAGE_EXTS`, `list_images`, `list_styles`

**Font Management** - `font_manifest.py`: `load_font_manifest`, `resolve_font_files`, `ensure_fonts_downloaded`; `fonts.py`: `set_fonts_dir`, `ensure_font`, `get_cmap`, `ensure_lazy`, `register_fonts`, `register_families`, `ensure_code_family`, `build_body_cmap`

**Color & Theme** - `colors.py`: `parse_color`, `hex_to_hsl`, `hsl_to_hex`, `dominant_chromatic_color`, `resolve_accent`, `derive_mid`, `resolve_colors`

**Document Rendering** - `renderer.py`: `ASTRenderer`; `flowables.py`: `AccentBox`, `TitleEnd`, `AccentRule`, `PageChrome`; `highlight.py`: `highlight`, `HAS_PYGMENTS`; `inline_patch.py`: `RADIUS`; `logo.py`: `load_logo`; `__init__.py`: `escape_xml`

### Cohesion

The pipeline is directional and well-layered: CLI -> orchestration -> (config + assets) -> rendering. Modules pull in the same direction and do not fight each other. The one file that serves a different audience is `catalog.py`, which exists for web UI integration and sits orthogonally to the CLI tool.

The cohesion problem is the `style` dict. It acts as a god-object that threads through every module. Each module reads a different subset of keys, some modules mutate it, and the full set of required keys is discoverable only by reading every method of every file. This makes the dependency graph invisible.

### Scope

Appropriate for a single-developer document toolchain. `renderer.py` is the only file that pushes the size boundary (1120 lines), but its responsibilities are internally cohesive - every method converts one AST token type to flowables. The natural extraction boundary, if growth continues, is splitting block-level handlers, inline handlers, and structural builders (title/FM/TOC) into separate modules.

### Responsibility Leakage

Mutation conventions are inconsistent. `resolve_colors`, `resolve_palette`, and `apply_options` mutate the `style` dict in place. `merge_config` returns a new dict. `resolve_font_files` mutates `style` in place. Callers must remember which functions mutate and which copy. A consistent convention (always mutate, or always return new) would reduce surprise.

`font_manifest.py` and `fonts.py` both walk font configuration entries with similar patterns but at different abstraction levels. The duplication is tolerable at current size but would benefit from a shared iterator if either module grows.

`build_pdf` in `builder.py` sequences config merging, asset resolution, parsing, rendering, and document construction in a single 164-line function. The initialization order is implicit - calling helpers out of sequence (e.g., `build_toc_flowables` before `render`) produces silent wrong results rather than errors.

### Cross-File Coherence

Naming conventions are consistent: snake_case throughout, clear function names, private underscore prefix used correctly. Import ordering and formatting are uniform. The codebase reads as single-author work with a consistent aesthetic.

The consistency extends to gaps: no type hints in any file, no docstrings on most public functions, no test files anywhere. Error handling is uniformly raw - exceptions propagate without domain-specific wrapping or user-facing messages. The `style` dict is accessed with bare dictionary indexing (`s["key"]`) in every module, so a missing key produces a generic `KeyError` with no indication of which style file or field is wrong.

## File Profiles

### lib/__init__.py

Package bootstrap (~8 lines). Imports `inline_patch` for side-effect ReportLab patching and exposes `escape_xml` for minimal XML escaping used across render/highlight paths.

#### Findings

6/12 checks clean.

- **Bugs (advisory):** `escape_xml` accepts any type without validation. Only escapes `&`, `<`, `>` - does not escape `"` or `'`, which matters when values are interpolated into XML attributes elsewhere.
- **Documentation (advisory):** `escape_xml` has no docstring or type hints. Module docstring does not mention the import-time ReportLab patch side effect.
- **Contract fidelity (advisory):** Name `escape_xml` suggests general XML safety but behavior is a three-character subset. Adequate for text content; insufficient for attribute values.
- **Error handling (advisory):** No validation; invalid input surfaces as normal exceptions from `str.replace`.
- **Security (advisory):** Incomplete XML escaping for attribute contexts is a markup-injection vector when inputs are interpolated into quoted attributes.
- **API design (advisory):** No `__all__`; `inline_patch` leaks as a public name on the package namespace.

### lib/logo.py

Loads a logo path as a ReportLab flowable: SVG via svglib scaling to height, raster via `Image` (~19 lines).

#### Findings

7/12 checks clean.

- **Bugs (flag, high):** SVG path adjusts `drawing.width` and `drawing.height` by `scale`, then calls `drawing.scale(scale, scale)` which applies the same factor again to the graphic. Likely double-scaling or width/height inconsistency with the transform. Division by zero possible if `drawing.height` is 0.
- **Contract fidelity (flag, medium):** Docstring implies a flowable is always returned; `None` is returned for failed SVG parse. Callers must handle `None` without API documentation of this case.
- **Documentation (advisory):** No parameter descriptions, no return type annotation, no units for `height`.

### lib/inline_patch.py

Monkey-patches ReportLab's paragraph post-text hook so inline `backColor` spans draw merged rounded rectangles with padding from font metrics (~59 lines).

#### Findings

7/12 checks clean.

- **Bugs (advisory):** If `leading < asc + desc`, `gap` goes negative and `bot`/`top`/`h` can invert or distort height. `getFont(fn)` can raise for unknown font names with no guard.
- **Duplication (advisory):** `reportlab.pdfbase.pdfmetrics` imported at module level and again inside `_patched`.
- **Documentation (advisory):** Module docstring covers behavior but public `RADIUS` constant has no documentation.
- **Error handling (advisory):** Errors from `getFont`, missing `face`, or bad `xs.style` propagate uncaught.
- **API design (advisory):** Global replacement of `_mod._do_post_text` is a wide side effect by design; import-time effect should be documented for callers.

### lib/catalog.py

JSON-oriented helpers for web UI or tooling: lists images under `images/` and scans `styles/*.yaml` into a merged, serializable catalog (~61 lines).

#### Findings

5/12 checks clean.

- **Bugs (advisory):** Non-mapping YAML at top level makes `raw.get` fail. Scalar elements in `options` list break `opt.get`.
- **Duplication (advisory):** When `inherits` is truthy, the file is read and parsed with `safe_load`, then `load_style` opens and parses the same path again.
- **Documentation (advisory):** `IMAGE_EXTS` has no description. Docstrings do not describe return element shapes.
- **Contract fidelity (advisory):** Claims JSON-serializable output but YAML values can be non-JSON types.
- **Single responsibility (advisory):** `list_styles` mixes directory scan, pre-parse, merged style loading, palette resolution side effects, and response shaping.
- **Error handling (advisory):** Any `yaml.safe_load` or `load_style` failure fails the whole catalog build with no per-file skip.
- **API design (advisory):** `IMAGE_EXTS` is a mutable `set`; catalog entries attach the full global images list per style.

### lib/font_manifest.py

Reads root `fonts.yaml` into an id-to-file/url map, resolves logical `font:` ids in style entries to filenames, and downloads missing files into `.fonts/` (~70 lines).

#### Findings

4/12 checks clean.

- **Bugs (advisory):** `safe_load` result not validated as a list of mappings. Manifest values assumed to carry `file` when built internally.
- **Duplication (advisory):** Same walk over `style["fonts"]` with `isinstance(entry, dict)` and field extraction in both `resolve_font_files` and `ensure_fonts_downloaded`.
- **Documentation (advisory):** One-line docstrings exist but parameters, in-place mutation, and return value are not spelled out.
- **Contract fidelity (advisory):** `ensure_fonts_downloaded` prints to stdout, not implied by the name or docstring.
- **Single responsibility (advisory):** `ensure_fonts_downloaded` combines dependency discovery, reverse manifest lookup, filesystem setup, network fetch, and user-facing logging.
- **Security (advisory):** Font filenames joined to `FONTS_DIR` without path normalization. URLs from manifest/style have no scheme restriction.
- **Concurrency (advisory):** Existence check before download allows races between processes.
- **API design (advisory):** Relies on in-place mutation, global paths, and stdout printing from library code.

### lib/colors.py

Color parsing and theme logic: hex/named colors for ReportLab, HSL helpers, dominant-color extraction from logos via Pillow, and `resolve_colors` to fill accent, mid-tone, and link colors from style + logo (~74 lines).

#### Findings

4/12 checks clean.

- **Bugs (advisory):** Hex helpers assume well-formed six-digit hex. Malformed strings surface as exceptions.
- **Documentation (advisory):** Only `parse_color` has a docstring. Other public helpers lack API-level description. No type hints.
- **Contract fidelity (advisory):** `parse_color` has undocumented pass-through behavior for non-string inputs. `resolve_colors` mutates in place without stating the contract.
- **Single responsibility (advisory):** One module covers ReportLab parsing, HSL math, logo-driven sampling, and style resolution. Acceptable at current size.
- **Error handling (advisory):** Missing files, invalid images, bad hex propagate as raw exceptions.
- **Readability (advisory):** Magic numbers for chromatic thresholds, lightness bounds, and `derive_mid` scaling lack names or comments.
- **Security (advisory):** `dominant_chromatic_color` opens paths from configuration. Untrusted YAML could point at sensitive paths or huge images.
- **API design (advisory):** In-place mutation of `style` in `resolve_colors` surprises some callers. `parse_color` dual behavior widens the type surface.

### lib/highlight.py

Optional Pygments integration: maps token types to style syntax color keys and emits ReportLab-friendly XML via a custom formatter. Falls back to escaped plain text if Pygments is missing or lexer fails (~82 lines).

#### Findings

6/12 checks clean.

- **Security (flag, medium):** Color strings from the style dict are interpolated into double-quoted XML attributes without validation or escaping. A value containing `"` can break the attribute boundary. Severity depends on whether YAML style inputs are trusted.
- **Bugs (advisory):** `get_lexer_by_name` uses `stripall=True` but `guess_lexer` does not, creating inconsistent behavior.
- **Documentation (advisory):** `colors` dict key/value shape undocumented.
- **Contract fidelity (advisory):** "Language not recognized" understates "any lexer-related failure."
- **Error handling (advisory):** `except Exception` around lexer setup hides programming errors alongside genuine failures. No logging.
- **API design (advisory):** Opaque `colors` dict couples callers to undocumented key names matching `_TOKEN_MAP` values.

### lib/flowables.py

Reusable ReportLab drawing primitives: `AccentBox` (boxed content with accent bar, splittable), `TitleEnd` sentinel, `AccentRule`, and `PageChrome` callback for centered page numbers (~127 lines).

#### Findings

5/12 checks clean.

- **Bugs (advisory):** `AccentBox.split` ignores fragments beyond the second if inner content splits into more than two parts. `AccentRule.draw` uses configured width regardless of `wrap` result, causing potential geometry disagreement. `PageChrome` will raise on invalid `page_size` key.
- **Documentation (advisory):** `AccentRule` has no class docstring. Parameter semantics (units, coordinate assumptions) undocumented.
- **Contract fidelity (advisory):** `TitleEnd` docstring says "zero-height" but it is also zero-width. `AccentRule` drawn width may not match wrapped width.
- **Error handling (advisory):** Invalid `page_size` or missing style keys surface as generic exceptions.
- **Readability (advisory):** Magic vertical offset for page number (`margin - 20`) and fixed line baseline in `AccentRule` are unexplained constants.
- **API design (advisory):** `AccentBox` exposes many mutable public attributes. `PageChrome` takes a loose `style` mapping with undiscoverable required keys.

### scrivener.py

CLI entry point: parses arguments via argparse, resolves and loads YAML styles, merges JSON `--options`, expands globs, and loops inputs through `build_pdf` (~143 lines).

#### Findings

7/12 checks clean.

- **Bugs (advisory):** Invalid or non-object JSON for `--options` (null, array) can yield confusing failures.
- **Documentation (advisory):** Rich module docstring exists but no dedicated docstring on the public `main` function.
- **Contract fidelity (advisory):** Usage blurb emphasizes inline JSON for `--options` while behavior also treats paths as files, which is only in the flag help text.
- **Single responsibility (advisory):** `main` bundles parsing, validation, glob expansion, output path planning, and the per-file loop.
- **Error handling (advisory):** Per-file failures use broad catch and only print the string form, losing traceback context.

### lib/fonts.py

ReportLab font registration: global fonts dir, variable-font instantiation via fontTools with disk cache under `.fonts/cache/`, lazy vs eager registration, font family registration for Body/Code, and body cmap for CJK fallback detection (~150 lines).

#### Findings

3/12 checks clean.

- **Bugs (advisory):** If `set_fonts_dir` was never called, `_resolve` fails. Crash during cache `save` can leave a truncated file that passes mtime freshness check on next run.
- **Duplication (advisory):** Same cache-key shape (variable path + sorted axes) appears in multiple places. Same `axes` copy pattern across entry points.
- **Documentation (advisory):** No docstrings on public functions. Preconditions (fonts dir set, style shape, lazy dict populated before family registration) undocumented.
- **Contract fidelity (advisory):** `ensure_lazy` silently no-ops when a name is absent from `_lazy`. Family registration may declare faces that were never registered.
- **Single responsibility (advisory):** One module covers cache paths, instantiation, registration, family wiring, and CJK cmap.
- **Error handling (advisory):** Font load, instancing, disk I/O, and ReportLab registration errors propagate raw.
- **Security (advisory):** Font filenames joined without path normalization.
- **Concurrency (advisory):** Module-level caches not synchronized. Two processes building same cache path can race.
- **API design (advisory):** Global mutable module state and required call order complicate testing and reuse. No reset path.

### lib/builder.py

Orchestrates one document: reads Markdown, extracts front matter, merges config, resolves logo/colors/fonts, parses with Mistune AST, renders flowables via `ASTRenderer`, optionally inserts TOC and front-matter blocks, then builds a `BaseDocTemplate` with `PageChrome` (~164 lines).

#### Findings

6/12 checks clean.

- **Documentation (advisory):** `build_pdf` has a narrative docstring but no parameter or return type annotations.
- **Contract fidelity (advisory):** Docstring says `style` may be mutated but `merge_config` deep-copies into `cfg` and only `cfg` is mutated. `cli_cfg` description lists only a subset of keys.
- **Single responsibility (advisory):** One function sequences config merging, asset resolution, parsing, rendering, and document construction.
- **Readability (advisory):** Linear overall but logo block and title-versus-body split increase branching and state in one place.
- **Security (advisory):** Full-file `read_text` on caller-supplied path enables memory pressure from large files. No validation of path or size.
- **API design (advisory):** `cli_cfg` and `style` are untyped dicts. Contracts are informal.

### lib/config.py

Project paths, page-size presets, proportional spacing, YAML style loading with `inherits` and circularity checks, palette `@` reference resolution, front-matter split/merge, and validated option application. Configuration backbone (~167 lines).

#### Findings

6/12 checks clean.

- **Bugs (advisory):** Front-matter regex demands a newline after closing `---`, so some valid fences may not split. `apply_options` assumes every schema entry has an `id` key. `deep_merge` only shallow-copies the top level so unchanged nested dicts stay aliased.
- **Documentation (advisory):** Short docstrings exist. Path constants and `PAGE_CONFIGS` semantics not documented.
- **Contract fidelity (advisory):** `merge_config` reads like a full merge but front matter only applies `_FM_STYLE_KEYS` plus selective CLI flags.
- **Error handling (advisory):** `yaml.safe_load` failures propagate as library exceptions. Malformed `options` entries raise `KeyError`.
- **Readability (advisory):** `_in` reads like the keyword `in`. `sp` parameters `cfg`/`r` are terse.
- **API design (advisory):** Mix of mutating APIs (`apply_options`, `resolve_palette`) and copying merge (`merge_config`). Callers must remember which mutate.

### lib/renderer.py

The largest module: `ASTRenderer` turns Mistune AST tokens into ReportLab flowables for headings, lists, tables, blockquotes, code blocks, mermaid diagrams, wording divs, images, HTML blocks, and builds title block, front-matter table, and TOC (~1120 lines).

#### Findings

2/12 checks clean.

- **Bugs (flag, low-medium):** `_render_heading` uses `anchor` outside its defining `if` scope - structurally fragile if a heading ever arrives with `level < 1`. `_inject_cjk_fallback` has a dead code path. `_inline_codespan` uses `getattr` with default for an attribute that is always set. `_bold_italic_size` is computed in `__init__` but never referenced (dead attribute).
- **Resource management (flag, low):** `_render_mermaid` temp file leak: `try/finally` for `os.unlink` only wraps `svg2rlg`, not the preceding `tmp.write()` and `tmp.close()`. If either throws, `NamedTemporaryFile(delete=False)` persists on disk and the file descriptor leaks.
- **Duplication (advisory):** Zero-padding `TableStyle` applied verbatim in three locations. Code-block-in-`AccentBox` construction duplicated between `_render_block_code` and `_render_pre_code_block`. `tok.get("raw", tok.get("text", ""))` idiom appears five times. Table header cell rendering duplicated between flat and nested paths.
- **Documentation (advisory):** Public methods `render`, `title_block`, `build_front_matter_flowables`, `build_toc_flowables` lack docstrings. `__init__` parameters undocumented. The `style` dict's required keys are discoverable only by reading every method.
- **Contract fidelity (advisory):** `_render_mermaid` docstring says "render to SVG flowable" but returns `Optional[list]`. `build_toc_flowables` depends on `self.headings` populated by `render()` - calling out of order silently produces empty TOC.
- **Single responsibility (advisory):** `ASTRenderer` at 1080 lines is cohesive but monolithic. Three natural extraction boundaries: inline handlers, block handlers, structural builders. `_render_block_code` handles both mermaid dispatch and code rendering. `_inline_inline_html` is a 36-line if/elif chain that could be a dispatch dict.
- **Error handling (advisory):** Style dict keys accessed bare throughout - missing key produces generic `KeyError` with no context. Broad `except Exception` catches in mermaid, logo, and image loading. `_in_table_header` flag not reset on exception.
- **Readability (advisory):** Multiple magic numbers (heading-codespan scale `0.85`, cap-shift `0.5`, mermaid height ratio `0.8`, smart-col-widths padding fudge `2`). Redundant `import re` inside `_smart_col_widths` when `re` is already module-level. `_build_styles` mixes three concerns in 80 lines.
- **Security (advisory):** `_fm_value` interpolates email into `href="mailto:{email}"` without XML-escaping `"`. Mermaid passes user-supplied code to external JS engines.
- **API design (advisory):** `style` parameter is an untyped dict with dozens of required and optional keys. Temporal coupling between `render()` and `build_toc_flowables()`. Mutable instance flags make `ASTRenderer` non-reentrant. Dead imports: `Indenter`, `KeepTogether`, `Preformatted`.

## API Surface

### scrivener.py

- public | main | function | CLI entrypoint; parses args, runs conversions, sets exit code

### lib/__init__.py

- public | escape_xml | function | Escapes &, <, > for XML-ish markup

### lib/builder.py

- public | build_pdf | function | Full pipeline from Markdown path to PDF

### lib/catalog.py

- public | IMAGE_EXTS | constant (set) | Allowed image extensions for listing
- public | list_images | function | Lists image basenames in IMAGES_DIR
- public | list_styles | function | Builds style catalog entries for JSON

### lib/colors.py

- public | parse_color | function | Parses hex or ReportLab color name to color object
- public | hex_to_hsl | function | Converts #rrggbb to HSL tuple
- public | hsl_to_hex | function | Converts HSL to #rrggbb
- public | dominant_chromatic_color | function | Estimates saturated accent hex from image
- public | resolve_accent | function | Resolves accent spec including from_logo
- public | derive_mid | function | Derives mid accent from saturated hex
- public | resolve_colors | function | Mutates style dict with resolved accent/link colors
- private | _FALLBACK_ACCENT | constant | Default accent hex when logo path missing

### lib/config.py

- public | PROJECT_ROOT | variable | Path to scrivener project root
- public | STYLES_DIR | variable | Path to styles/
- public | IMAGES_DIR | variable | Path to images/
- public | FONTS_DIR | variable | Path to .fonts/
- public | MANIFEST_PATH | variable | Path to fonts.yaml
- public | PAGE_CONFIGS | variable | Dict mapping page size name to size and margin
- public | sp | function | Spacing scaled by body_size
- public | deep_merge | function | Recursive dict merge
- public | resolve_style_path | function | Resolves CLI style arg to YAML path
- public | load_style | function | Loads YAML with inheritance
- public | apply_options | function | Applies validated option overrides
- public | resolve_palette | function | Expands @palette refs in style dict
- public | extract_front_matter | function | Splits YAML front matter from markdown text
- public | merge_config | function | Merges CLI, front matter, and style
- private | _in, _mm20, _mm15, _mm10 | variables | Margin helpers
- private | _FM_STYLE_KEYS | constant | Front-matter keys merged into style

### lib/flowables.py

- public | AccentBox | class | Splittable boxed flowable with accent bar and optional top rule
- public | TitleEnd | class | Zero-size sentinel flowable
- public | AccentRule | class | Horizontal rule flowable
- public | PageChrome | class | onPage callable drawing page number

### lib/font_manifest.py

- public | load_font_manifest | function | Loads fonts.yaml as id map
- public | resolve_font_files | function | Fills file from manifest
- public | ensure_fonts_downloaded | function | Downloads missing fonts to cache dir

### lib/fonts.py

- public | set_fonts_dir | function | Sets global fonts directory path
- public | ensure_font | function | Registers TTF (variable or cached instance)
- public | get_cmap | function | Unicode codepoints available for font/axes
- public | ensure_lazy | function | Registers a lazily deferred font
- public | register_fonts | function | Registers fonts from style config
- public | register_families | function | Registers Body font family links
- public | ensure_code_family | function | Registers Code font family if needed
- public | build_body_cmap | function | Cmap for body font entry
- private | _cache, _cmap_cache, _lazy, _families, _fonts_dir | variables | Module caches/state
- private | _resolve | function | Resolves filename under fonts dir
- private | _axes_key | function | Stable key for axis dict
- private | _cache_path | function | Cache file path for instantiated font

### lib/highlight.py

- public | HAS_PYGMENTS | variable | Bool whether Pygments imported
- public | highlight | function | Returns highlighted XML markup or escaped text
- private | _TOKEN_MAP | constant | Pygments token to key mapping
- private | _resolve | function | Token to color resolution
- private | _RLFormatter | class | Pygments formatter subclass

### lib/inline_patch.py

- public | RADIUS | constant | Corner radius for inline code backgrounds
- private | _orig | variable | Original _do_post_text reference
- private | _patched | function | Replacement post-text handler

### lib/logo.py

- public | load_logo | function | Loads image/SVG as flowable scaled to height

### lib/renderer.py

- public | log | variable | Module logging.Logger
- public | ASTRenderer | class | Mistune AST to ReportLab flowables
- public | ASTRenderer.__init__ | method | Params: style, body_cmap, content_width, md_dir, has_fm_title
- public | ASTRenderer.render | method | Params: tokens. Returns: list of flowables
- public | ASTRenderer.title_block | method | Params: title_markup. Returns: list
- public | ASTRenderer.build_front_matter_flowables | method | Params: fm. Returns: list
- public | ASTRenderer.build_toc_flowables | method | Returns: list
- private | ASTRenderer._build_styles | method | Constructs ParagraphStyles from config
- private | ASTRenderer._inject_cjk_fallback | method | Wraps CJK runs in fallback font
- private | ASTRenderer._propagate_keep | staticmethod | Sets keepWithNext on flowables
- private | ASTRenderer._only_text | method | Extracts plain text from token tree
- private | ASTRenderer._wrap_wording | method | Wraps flowables in wording-div styling
- private | ASTRenderer._render_token | method | Dispatches to per-type render method
- private | ASTRenderer._render_heading | method | Heading with anchor and TOC entry
- private | ASTRenderer._render_paragraph | method | Paragraph with inline markup
- private | ASTRenderer._render_block_code | method | Fenced code block or mermaid dispatch
- private | ASTRenderer._render_block_quote | method | Recursive blockquote with AccentBox
- private | ASTRenderer._render_list | method | Ordered/unordered list with nesting
- private | ASTRenderer._render_table | method | Table with smart column widths
- private | ASTRenderer._render_thematic_break | method | Horizontal rule
- private | ASTRenderer._render_blank_line | method | Vertical spacing
- private | ASTRenderer._render_block_html | method | Raw HTML block handling
- private | ASTRenderer._render_pre_code_block | method | Pre/code HTML blocks
- private | ASTRenderer._render_image | method | Image flowable
- private | ASTRenderer._render_mermaid | method | Mermaid diagram to SVG flowable
- private | ASTRenderer._inline_children | method | Renders inline child tokens to markup
- private | ASTRenderer._inline | method | Dispatches inline token types
- private | ASTRenderer._inline_text | method | Plain text with escaping
- private | ASTRenderer._inline_emphasis | method | Italic markup
- private | ASTRenderer._inline_strong | method | Bold markup
- private | ASTRenderer._inline_codespan | method | Inline code with backColor
- private | ASTRenderer._inline_link | method | Hyperlink with scheme validation
- private | ASTRenderer._inline_image | method | Inline image (rendered as link)
- private | ASTRenderer._inline_strikethrough | method | Strikethrough markup
- private | ASTRenderer._inline_softbreak | method | Soft line break
- private | ASTRenderer._inline_linebreak | method | Hard line break
- private | ASTRenderer._inline_inline_html | method | Inline HTML tag handling
- private | ASTRenderer._smart_col_widths | method | Proportional column width calculation
- private | ASTRenderer._fm_value | method | Front-matter value with email detection
- private | ASTRenderer._wording_text_color | method | Text color for wording divs
- private | ASTRenderer._wording_wrap | method | Text wrapping for wording context
- private | ASTRenderer._DEFAULT_BULLETS | class attribute | Bullet glyph strings
- private | ASTRenderer._SAFE_SCHEMES | class attribute | Allowed URL schemes for links
