# Scrivener - Agent Rules

## No Style in Code

Every visual value - colors, sizes, spacing, padding - comes from a style YAML file (e.g. `styles/default.yaml`) or is proportional to body_size via `sp()`. Zero hardcoded appearance numbers in Python. Use `cfg["key"]` not `cfg.get("key", "#hex")` for values that exist in the style. No color hex strings as fallback defaults. If a key is missing, let it crash - the style is incomplete. Styles are flat YAML files in `styles/`; derived styles use `inherits: base` for cascade.

## All Spacing is Proportional

Use `sp(cfg, r)` for every spacing value. Never bare `Spacer(1, 4)` or `spaceAfter=6`. The function is in `lib/config.py`:

```python
def sp(cfg, r):
    """Spacing proportional to body_size."""
    return cfg.get("body_size", 11) * r
```

Ratios use the form `N/11` so the original value is visible: `sp(cfg, 4/11)` produces 4pt at body_size 11.

Values already in style.yaml (heading spacing, list indent, etc.) are absolute and stay as-is - the user controls them directly.

## No Duplicated Drawing Logic

The accent-bar-plus-background-box pattern lives in `AccentBox` (`lib/flowables.py`). Both front-matter and blockquotes use it. Do not recreate this pattern elsewhere.

## Do Not Add YAML Keys Without Asking

Adding new keys to style.yaml is a last resort. Before adding a key, ask the user. Derive values from existing keys whenever possible. Example: the title uses headings.h1.scale - it does not get its own font_scale key.

## Short Variable Names

Prefer `bs`, `cfg`, `fm`, `lh`, `cb`, `bq`, `s`, `r`, `w`, `h`. Spell out only when meaning is unclear from context.

## File Map

- `scrivener.py` - CLI entry point. Argparse, help text, main(). No rendering logic.
- `lib/__init__.py` - Package marker. `escape_xml()` utility.
- `lib/builder.py` - `build_pdf()` orchestration. Wires config, fonts, renderer, and ReportLab document.
- `lib/flowables.py` - `AccentBox`, `PageChrome`, `TitleEnd`. Stable drawing primitives.
- `lib/fonts.py` - Font cache, variable-font instantiation, ReportLab registration. `ensure_lazy()`, `ensure_code_family()`.
- `lib/colors.py` - Color math. `hex_to_hsl`, `resolve_accent`, `derive_mid`, `resolve_colors`.
- `lib/config.py` - Style loading with `inherits:` cascade, `deep_merge()`, option handling, front-matter extraction, config merge, `sp()`.
- `lib/font_manifest.py` - Font manifest loading, `resolve_font_files()`, `ensure_fonts_downloaded()`.
- `lib/catalog.py` - `list_styles()`, `list_images()`.
- `lib/logo.py` - `load_logo()` for raster and SVG.
- `lib/highlight.py` - Syntax highlighting via Pygments. Single `highlight()` function returns ReportLab XML markup.
- `lib/renderer.py` - `ASTRenderer`. AST-to-flowable conversion. The largest module.

## keepWithNext Is Broken

ReportLab's `keepWithNext` silently fails when `KeepTogether` splits across pages — see `KEEPWITHNEXT-BUG.md` for the full explanation. Use `CondPageBreak` before headings instead of relying on `keepWithNext` alone.

## Flowable Split Correctness

When a flowable's `split()` constructs continuation fragments, it must forward every constructor parameter that affects drawing. If a parameter is intentionally dropped on split (e.g. `radius` for geometric reasons), add a comment explaining why.

## Links and Security

Links in generated PDFs must restrict URI schemes to `http`, `https`, and `mailto`. Reject `javascript:` and unknown schemes.

## Testing

Run `python -m pytest tests/ -v` after every code change. All tests must pass before considering a change complete. The test suite has four layers:

1. **Pure-function unit tests** - config, colors, escape, highlight, renderer utilities. No font registration needed.
2. **Renderer token tests** - feed AST tokens to ASTRenderer, assert on flowable types and properties. Requires fonts.
3. **Builder integration tests** - full `build_pdf` pipeline against markdown fixtures in `tests/fixtures/`. Verifies PDF output exists and has valid header.
4. **Style/catalog tests** - style loading, inheritance, palette resolution, catalog JSON output.

`test-kitchen-sink.md` is the visual regression fixture. Render it and inspect the PDF after significant visual changes. See `TESTING.md` for details on each layer and the future layer 5 (automated visual regression).

## Scrivener-Specific Extensions

These extend general rules in the root CLAUDE.md with project-specific instances.

- Functions named `resolve_*` or `load_*` must not mutate their arguments unless the docstring explicitly says so. Use `copy.deepcopy` or recursive merge when callers must not see mutations.
- Every style key referenced in code must either exist in the schema with a default or be accessed with an explicit fallback. Never emit `color="None"` or `value=None` into markup.
- Do not use any specific flowable type as a structural sentinel for splitting logic. Use an explicit marker or return a structured object.
- Font registration is global process state.
