# Scrivener Gap Report

Remaining gaps between scrivener (ReportLab + mistune) and
paperkiller (Pandoc + Chromium). Items already implemented in
scrivener are excluded.

## Rendering Pipeline

| | Paperkiller | Scrivener |
|---|---|---|
| Parser | Pandoc (full CommonMark + extensions) | Mistune v3 (AST, strikethrough + table plugins) |
| Layout engine | Chromium print-to-PDF | ReportLab platypus |
| Mermaid | mermaid-filter (official CLI, full syntax) | merm (pure Python, limited syntax) with optional mermaido fallback |
| Deployment | Docker microservice (Flask + REST API) | Standalone Python script, also usable as library via Paperworks |

## Gaps

| # | Feature | Priority | Notes |
|---|---------|----------|-------|
| 1 | Mermaid full syntax | Medium | `merm` fails on chained arrows and named task IDs. Workaround: rewrite Mermaid source to use explicit edge pairs. Installing `mermaido` (optional, requires Node) gives full mermaid-cli support. |
| 2 | PDF bookmarks/outline | Medium | Neither tool creates a bookmark tree from headings. ReportLab supports this via `bookmarkPage` + `addOutlineEntry`. Named anchors exist for TOC links but no outline tree. |
| 3 | Footnotes | Medium | Pandoc handles footnotes natively. Mistune has no footnote plugin. Rendering footnotes at page bottom in ReportLab is non-trivial. |
| 4 | Figure captions | Medium | Paperkiller supports `<figure>` + `<figcaption>`. Scrivener inserts block images with no caption. |
| 5 | Running headers | Low | Paperkiller has "WG21 Proposal" static strip. Scrivener has page numbers only in `PageChrome`. Adding text to the header bar would be straightforward. |
| 6 | Classification watermark | Low | Paperkiller has diagonal watermark and colored header/footer bars for C/S/TS. Not needed for current use cases. |
| 7 | Definition lists | Low | Pandoc supports natively. Mistune has no plugin. Rarely used in WG21 papers. |
| 8 | Inline images | Low | Scrivener renders alt text only for inline images. Block images work. |
| 9 | Raw HTML rendering | Low | Scrivener escapes raw HTML into text. Paperkiller renders it via Chromium. |
| 10 | Math/LaTeX | Low | Neither tool has it wired. ReportLab would need an external renderer. |
| 11 | Citations/bibliography | Low | Pandoc has `--citeproc`. ReportLab would need a full citation engine. |
| 12 | Cross-references | Low | Neither tool has explicit anchor/ref support beyond heading links. |
| 13 | Task lists | Low | Neither tool supports `- [ ]` / `- [x]` checkboxes. Mistune has no task-list plugin. |

## Scrivener Advantages

Features scrivener has that paperkiller does not:

- Style cascade with `inherits:` and deep merge
- Logical font manifest with on-demand download (auto-fetched by `build_pdf`)
- Variable font axis instantiation (arbitrary width/weight)
- JSON style catalog API (`--list-styles`) with images array
- CLI option overrides with schema validation
- Smart table column sizing with header repeat on multipage tables
- Proportional spacing system (`sp()`)
- Shared image asset directory
- Standalone script (no Docker/Node/Chromium dependency)
- Library API usable by Paperworks and other callers
- Per-character CJK cmap fallback detection
- Configurable front matter fields per style
- GitHub-style blockquote callouts (`[!NOTE]`, `[!WARNING]`, `[!CAUTION]`)
- Heading widow/orphan control with keepWithNext propagation
- Inline code rounded background rectangles
- Wording divs (`:::wording`, `:::wording-add`, `:::wording-remove`) with colored accent bars
- Superscript and subscript via `<sup>` / `<sub>` HTML
- Syntax highlighting in fenced code blocks (Pygments)
- TOC with internal anchor links
- Title auto-shrink for long titles
- Unsupported token markers (`[unsupported: ...]`) for debugging
- Page breaks via `\newpage`
- PDF metadata (title, author) from front matter

## Summary

The highest-impact gaps are Mermaid full syntax (1), PDF bookmarks (2),
footnotes (3), and figure captions (4). Mermaid is partially addressed
by the optional `mermaido` fallback but the default pure-Python parser
remains limited. Bookmarks would make long papers navigable in PDF
readers. Footnotes are blocked on a mistune plugin plus non-trivial
page-bottom placement in ReportLab. Everything else is low priority.
