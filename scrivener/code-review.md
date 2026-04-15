# Code Review: scrivener

- **Date:** 2026-04-15
- **Model:** claude opus 4.6
- **Scope:** `scrivener/` - 13 source files, 9 test files, 3 YAML configs

Clean pipeline architecture with a well-factored core, held back by undocumented mutation contracts across the resolve_* boundary and font lifecycle state scattered across three modules.

## Executive Summary

Scrivener is a well-structured 2,300-line rendering pipeline. The division of responsibility is sound: config.py owns style loading, colors.py owns color math, fonts.py owns registration, and renderer.py (1,156 lines) owns AST-to-flowable conversion. The codebase follows its own CLAUDE.md rules with reasonable discipline - spacing goes through sp(), visual values come from style YAML, and AccentBox is the sole shared drawing primitive.

The systemic weakness is a three-module mutation chain: resolve_palette (config.py), resolve_colors (colors.py), and resolve_font_files (font_manifest.py) all mutate the same style dict in-place without documenting it, violating the project's own resolve_* immutability rule. This is compounded by the font lifecycle being split across font_manifest.py, fonts.py, and builder.py with no enforcement of call ordering. These are design-level issues, not bugs - the pipeline works because builder.py calls everything in the right order - but they make the system fragile to refactoring. The individual file findings (tempfile leak in mermaid, hardcoded offset in PageChrome, missing test coverage) are real but lower risk.

## Codebase Profile

### Pipeline Orchestration

CLI entry point and build orchestrator. scrivener.py handles argument parsing and batch iteration; builder.py wires config, fonts, parsing, and rendering into a single build_pdf call.

**scrivener.py** - Clean CLI entry point. Argparse, glob expansion, batch loop with success/failure tracking. No rendering logic leaks in. The only issue is the batch error handler printing just the exception message without traceback.

**lib/builder.py** - The 165-line orchestrator is the most cross-cutting module. It calls resolve_colors, load_font_manifest, resolve_font_files, ensure_fonts_downloaded, set_fonts_dir, register_fonts, register_families, build_body_cmap, and build_fallback_cmaps in a specific order that constitutes an implicit contract. The logo resolution block is the only place builder does substantive logic rather than delegation. The function's docstring correctly warns that style may be mutated.

### Configuration & Color

Style loading with YAML inheritance cascade, front-matter extraction, config merge, proportional spacing, and color math.

**lib/config.py** - Style loading is well-factored: load_style handles inheritance with cycle detection, deep_merge is a clean recursive dict merge, and sp() is the proportional spacing primitive. resolve_palette (line 117) mutates the style dict via clear()/update() without documenting it.

**lib/colors.py** - Small, focused color math module. hex_to_hsl/hsl_to_hex are pure. dominant_chromatic_color correctly uses a with-block for Image.open. resolve_colors mutates its argument without a docstring and uses cfg.get with a hardcoded hex fallback, violating the no-fallback-hex rule.

### Font Management

Two-phase font system: font_manifest.py resolves logical IDs to filenames and downloads missing files; fonts.py handles variable-font instantiation, caching, and ReportLab registration via global process state.

**lib/fonts.py** - Five module-level caches make this the most stateful module. The variable-font instantiation and disk caching logic is solid with mtime-based invalidation. get_cmap re-instantiates fonts that ensure_font already cached, which is wasteful but not incorrect.

**lib/font_manifest.py** - Clean download-and-resolve module. Download loop correctly cleans up partial files on failure. resolve_font_files mutates nested style entries without documenting it.

### Rendering Engine

Core rendering: renderer.py converts AST tokens to flowables; flowables.py provides drawing primitives; inline_patch.py monkey-patches ReportLab for rounded inline code backgrounds.

**lib/renderer.py** - At 1,156 lines this is the project's center of gravity. The handler-dispatch pattern (_render_{type}, _inline_{type}) is consistent and extensible. _build_styles pre-computes ParagraphStyles from config, keeping per-token methods focused on structure. _render_mermaid has a tempfile leak if write/close fails before the try/finally. The _inline_inline_html handler is a long if/elif chain for HTML tag dispatch - functional but brittle if new tags are added.

**lib/flowables.py** - Three clean drawing primitives. AccentBox.split correctly forwards constructor params to continuation fragments; the bottom fragment intentionally drops top_rule without the comment required by CLAUDE.md. PageChrome.__call__ has a bare `- 20` offset that should use sp().

**lib/inline_patch.py** - Import-time monkey-patch of ReportLab internals. The patch is clean - it merges consecutive same-color spans and draws rounded rects. No version guard means a ReportLab update could silently break it.

### Utilities

**lib/highlight.py** - Clean Pygments adapter with graceful degradation when Pygments is unavailable.

**lib/logo.py** - Minimal 19-line module. Correctly dispatches SVG vs raster. Clean.

**lib/catalog.py** - Style catalog for the JSON API. Clean.

**lib/__init__.py** - Package init triggering the ReportLab monkey-patch. Exports escape_xml for text-content escaping.

## Cross-cutting Analysis

**Module Boundaries.** The dependency graph is a clean DAG rooted at builder.py. No circular dependencies. The one boundary concern is renderer.py's direct import of PAGE_CONFIGS from config.py to compute page height - this duplicates a lookup that builder.py already performed and passed implicitly via content_width but not page_height.

**The Mutation Chain.** The most significant cross-cutting issue. builder.py calls three functions in sequence that all mutate the same dict: resolve_palette (config.py) clears and rewrites the entire dict, resolve_colors (colors.py) writes accent/mid/link keys, and resolve_font_files (font_manifest.py) writes file keys into nested font entries. All three are named resolve_* which per CLAUDE.md means they must not mutate unless documented. None documents it. This is a systemic violation, not three independent findings.

**Font Lifecycle Fragmentation.** The invariant "fonts are downloaded and registered before rendering" is maintained by builder.py's 8-call sequence: load_font_manifest, resolve_font_files, ensure_fonts_downloaded, set_fonts_dir, register_fonts, register_families, build_body_cmap, build_fallback_cmaps. No single module enforces this ordering.

**Naming Coherence.** After merge_config() in builder.py, the result is called `cfg`. But every downstream function that receives it calls the parameter `style`. The dict has been transformed from a raw style into a fully resolved configuration - the name `style` is misleading post-merge. Additionally, `_resolve` appears in both fonts.py (path resolution) and highlight.py (token-to-color resolution) with different semantics.

**AccentBox Construction.** renderer.py constructs AccentBox in six places, each extracting padding/color values from the style dict slightly differently. The code-block sites (_render_block_code and _render_pre_code_block) are nearly identical in their style extraction.

## Findings

### Should fix

1. `config.py:117`, `colors.py:61`, `font_manifest.py:20`, `builder.py:69-74` - document the resolve_* mutation chain and add explicit mutation disclosure to each docstring
   (three resolve_* functions mutate the config dict in-place without disclosure, violating the project's own immutability convention)

2. `colors.py:62` - use `cfg["accent_saturated"]` not `cfg.get("accent_saturated", _FALLBACK_ACCENT)`
   (hex string as .get() fallback default violates "no color hex strings as fallback defaults" rule)

3. `renderer.py:570` - widen try/finally in _render_mermaid to cover write/close, not just svg2rlg
   (NamedTemporaryFile(delete=False) leaks if write or close raises before the finally block)

4. `flowables.py:106` - replace bare `self.margin - 20` with sp() or a style key
   (hardcoded 20pt offset violates "zero hardcoded appearance numbers in Python" rule)

5. `test_renderer.py` - add tests for _render_block_html and _render_pre_code_block
   (substantive render paths with HTML comment stripping, ins/del color injection, and entity handling have zero test coverage)

6. `test_catalog.py:137` - write temp style files to tmp_path, not into the real STYLES_DIR
   (test artifacts left in production directory on failure)

### Nice to have

7. `builder.py:80`, `renderer.py:130`, `flowables.py:97` - pass pre-computed page geometry instead of triple PAGE_CONFIGS lookup
   (page dimensions derived independently in three modules)

8. `builder.py:55`, `colors.py:61`, `font_manifest.py:20`, `fonts.py:94`, `renderer.py:36` - pick one name: `cfg` post-merge, `style` pre-merge
   (same dict called `cfg` in builder but `style` in every downstream parameter)

9. `fonts.py` - consider a single ensure_fonts_ready() entry point to replace the 8-call protocol
   (font subsystem exposes internal lifecycle as a sequencing contract that builder must execute in exact order)

10. `flowables.py:59` - add comment explaining why top_rule is intentionally dropped on the bottom split fragment
    (CLAUDE.md split-correctness rule requires comments on intentionally dropped parameters)

11. `renderer.py:795` - remove redundant `import re` inside _smart_col_widths
    (re is already imported at module level; the local import shadows it for no benefit)

12. `inline_patch.py:58` - add ReportLab version assertion or try/except around the monkey-patch assignment
    (deep coupling to undocumented ReportLab internals could silently break on upgrade)

13. `fonts.py:26` - add a guard in _resolve for _fonts_dir=None with a clear RuntimeError
    (TypeError from NoneType / str is opaque when set_fonts_dir was not called)

14. `fonts.py:69` - read the cached static TTF from disk in get_cmap when it exists
    (re-instantiates variable fonts that ensure_font already cached, duplicating expensive work)

15. `scrivener.py:130` - log full traceback to stderr, not just str(e)
    (KeyError or AttributeError deep in the pipeline produces a useless one-word message)

16. `lib/__init__.py:6` - document that escape_xml is for text content only, not attribute values
    (omits `"` and `'` escaping which would be needed in attribute contexts)

17. `test_catalog.py:103` - extract the recursive @-reference checker into a shared helper
    (identical 10-line check() closure duplicated between two test functions)

18. `test_config.py:220` - remove duplicate circular-inheritance test
    (identical to test_catalog.py::test_circular_inheritance)

19. `test_highlight.py:61` - strengthen test_highlight_escapes_xml assertion
    (or-condition `"<" not in result or "<font" in result` always passes when font tags exist)

20. `renderer.py:562` - add a test for _render_mermaid mocking svglib.svg2rlg
    (tempfile + two optional libraries have no direct test coverage)

22 files / 91 functions reviewed. 78 functions reviewed clean.
