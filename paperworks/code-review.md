# Code Review: Paperworks

- **Date:** 2026-04-15
- **Model:** Opus 4.6 (orchestrator) + fast sub-agents (analysis)
- **Scope:** `paperworks/` - all Python modules, HTML dashboard, and configuration

Useful WG21 glue with a clean isocpp queue boundary, but path handling, threaded I/O, and SPA completion contracts are not yet trustworthy for multi-tree or failure-heavy use.

## Executive Summary

Paperworks correctly centralizes render serialization, SSE fanout, and the IsoCppSession queue, while `inventory.py` plus `pdf_reader.py` implement the advertised three-source merge with clear priority rules. The weak spots are systemic rather than cosmetic: PDF outputs are keyed only by basename in several server paths while the inventory model assumes one canonical PDF per doc id, debounced and SSE-driven client flows violate the project's own async invariants, and several routes accept ambiguous path inputs or return misleading success.

Cross-cutting duplication of "stale skip" math across the markdown watchdog, batch render, and the render worker increases the risk of subtle drift, and the UI's working-state model is split between HTTP responses and SSE events without a reconciliation path when identifiers do not match exactly. Tightening path normalization, surfacing errors instead of silent no-ops, and making remote form reads distinguish network failures from missing markup would materially improve reliability without re-architecting the app.

## Codebase Profile

### Entry and persisted settings

CLI only boots `serve` and optionally persists a port override. JSON config loading merges defaults, optional scrivener fallback, and atomic save semantics for watch dirs, output dirs, styles, and credentials.

**`paperworks.py`** - Minimal argparse entry point: `serve` loads config, optionally overwrites `port`, and calls `run_server`; no other commands, so almost all behavior lives under `lib.server`.

**`lib/server_config.py`** - Small, focused module: defaults, scrivener fallback for empty fields, watch-dir shape normalization, and atomic `save_config` via temp file plus `os.replace`. Broad `except Exception` on optional reads is intentional degradation to defaults.

### Server, orchestration, and live transport

Flask hosts the SPA, REST APIs, SSE streams, filesystem watchdogs, a background render queue worker, and bridges isocpp.org job events into logs and broadcasts.

**`lib/server.py`** - The system's gravity well: SSE registry, activity log, markdown and PDF watchdog timers, render queue worker calling scrivener `build_pdf`, inventory and upload/transition routes, catalog and constrained file serving, tkinter pickers, and shutdown. Threading is pervasive (`threaded=True`, timer threads, worker thread, isocpp worker), which amplifies any non-thread-safe or racy filesystem use.

### Inventory and PDF-derived metadata

Correlates markdown scans, a flat PDF output directory, and remote rows into per-paper records with derived status, warnings, and revision history.

**`lib/inventory.py`** - Implements the three-source merge and status derivation, with `_parse_doc_number` as the linchpin for keys across markdown, PDF, and remote. Markdown reads are capped early in the file, which interacts directly with YAML front-matter parsing and abstract extraction.

**`lib/pdf_reader.py`** - PyMuPDF-backed metadata extraction with regex-based doc number, title, authors, and a heuristic abstract scanner; feeds `scan_pdf_dir` when markdown is missing. Abstract handling is intentionally bounded but the public docstring over-promises relative to the truncation applied in code.

### Authenticated remote client

Serializes all mutating isocpp.org traffic on a worker thread behind `submit`, with lock-protected immediate reads.

**`lib/isocpp.py`** - Well-scoped remote adapter: queue plus `_emit` guards, clear job types, and lock-held `_do_upload` / `_do_transition`. `_read_form` is the main weak link for HTTP error semantics because it never validates status before parsing HTML.

### Single-page dashboard

Self-contained HTML/CSS/JS implements tabs, inventory table, settings, render cards, log view, fetch wrappers, and EventSource handling.

**`lib/templates/index.html`** - Large inline SPA: renders folio from `_papers`, wires badges to queue-backed actions, debounces inventory refresh, posts settings without uniform response checking, and couples row working state to SSE payloads and string-normalized path equality.

## Cross-cutting Analysis

Module boundaries are mostly sensible on paper: `server_config` owns persistence, `inventory` plus `pdf_reader` own local corpus semantics, `isocpp` owns remote mutation serialization, and `server` owns orchestration and transport. In practice `server` still absorbs policy that belongs with inventory output invariants (for example, how rendered PDF paths relate to markdown paths across multiple watch roots), because the render worker, markdown debounce flush, batch `render_all`, and preview endpoint all independently choose output filenames using only `Path(md).with_suffix('.pdf').name` under a single configured output directory. That duplicates the same structural assumption in three places, so any fix to collision behavior must be coordinated across those call sites and retested against `scan_pdf_dir`, which only globs one flat directory.

Naming is coherent around `doc_number`, `base`, and `revision`, and the D/P normalization idea is consistently documented in `inventory` and project rules. Responsibility leakage appears where HTTP-layer routes accept raw strings that are later treated as authoritative paths (`remove_dir`, `toggle_dir`, `update_config` port parsing, `open_folder`) without the same validation rigor as `add_dir`, and where the SPA embeds filesystem paths into HTML attributes and inline `onclick` strings instead of keeping opaque server-side ids or data attributes with safe encoding.

The isocpp queue is the clearest positive boundary in the codebase: the server never calls mutating session methods directly, and events bridge cleanly to SSE. The weakest boundary is error semantics from `_read_form` into `_do_upload` / `_do_transition`, because the same `(None, None, None)` tuple represents both "HTML did not contain a form" and "request returned an error page", which forces misleading user-visible messages upstream.

Duplication worth calling out: stale-PDF detection logic mirrors between `_flush_md_pending` and `render_all` (and overlaps the per-item logic in `_render_worker`), and the client re-implements completion heuristics (HTTP for some actions, SSE `rendered` path matching for single render) that the server already partially signals through `render_done`. A single canonical "output path for markdown source" helper used by server and documented for inventory would reduce drift. Finally, `server_config`'s permissive JSON merge and `inventory`'s tolerant `_parse_doc_number` combine so that mildly malformed `document` fields in YAML can still create surprising merge keys; tightening validation at markdown ingest would keep the rest of the pipeline honest.

## Findings

### Must fix

1. `lib/server.py:render_worker`, `lib/server.py:_flush_md_pending`, `lib/server.py:render_all`, `lib/inventory.py:scan_pdf_dir` - derive PDF output paths from a stable key (resolved markdown path or doc id), not basename-only names
   (basename-only outputs make different `foo.md` trees collide in one output folder, so inventory's flat scan can attach the wrong PDF to the wrong paper)

2. `lib/server.py:remove_dir:443`, `lib/server.py:toggle_dir:453` - reject empty `dir` like `add_dir` does and compare using same normalization as stored config entries
   (blank `dir` resolves to the process current working directory, which is an unsafe default and makes DELETE/toggle a misleading no-op)

3. `lib/server.py:_flush_md_pending:229` - wrap stat() / existence checks in try/except and treat missing files as skip-or-requeue
   (timer-thread stat() on paths that may be deleted can raise and kill the debounce flush path, stalling auto-render)

4. `lib/inventory.py:_parse_doc_number`, `lib/inventory.py:scan_markdown_dirs`, `lib/inventory.py:build_inventory` - treat non-matching `document` field as invalid (warn and skip) instead of fabricating merge keys from arbitrary strings
   (non-matching values become collision-prone dict keys and corrupt cross-source correlation)

5. `lib/templates/index.html:loadInventory:564` - implement debounce so prior Promises reject or resolve before replacing the timer
   (rapid calls strand earlier `await loadInventory()` chains, leaving callers waiting forever while UI state moves on)

6. `lib/templates/index.html:renderSingle`, `lib/templates/index.html:connectSSE rendered handler` - clear `_workingSet` for the doc on `render_done` or match using normalized paths, not only strict string equality
   (`endWork` depends on SSE `d.file` matching `p.md_path`; a mismatch strands the row in a perpetual working badge)

### Should fix

7. `lib/server.py:update_config:413` - validate port with try/except around int() and return 400 JSON
   (bad client input becomes a 500 instead of a controlled validation error)

8. `lib/server.py:remove_dir:443`, `lib/server.py:toggle_dir:459` - return explicit 404 or `{changed:false}` when no entry matches
   (silent list replacement makes mismatched paths look like success)

9. `lib/server.py:open_folder:909` - catch OSError from os.startfile / subprocess.Popen and return JSON error
   (desktop integration failures surface as generic 500 without structured response)

10. `lib/inventory.py:_read_markdown_paper:60` - read through end of front matter reliably (bounded full read, or incremental read until closing `---`)
    (8k cap can truncate front matter on large papers, causing valid markdown to be discarded)

11. `lib/isocpp.py:_read_form:281` - call raise_for_status() before BeautifulSoup parsing and return distinct errors for transport vs missing form
    (HTTP failures parse like an absent form, producing the wrong failure mode for uploads and transitions)

12. `lib/templates/index.html:postConfig:605`, `lib/templates/index.html:saveOutputDirs`, `lib/templates/index.html:saveCreds`, `lib/templates/index.html:toggleAutoRender` - check r.ok and only toast success when the POST actually persisted
    (users get positive confirmation even when /api/config failed)

13. `lib/server.py:_pick_path:836`, `lib/server.py:pick_dir`, `lib/server.py:pick_file` - marshal Tk calls onto a dedicated thread because Flask serves with threaded=True
    (tkinter is not designed for concurrent use from arbitrary worker threads)

### Nice to have

14. `lib/pdf_reader.py:_extract_abstract_from_doc` - align docstring with actual truncation policy or remove the 1000-char cap
    (callers treat abstract as complete, but the implementation silently truncates)

15. `lib/templates/index.html:renderDirs` - replace inline onclick built from escaped paths with data-path attributes plus addEventListener
    (manual escaping of Windows paths into JS string literals is brittle for special characters)

16. `lib/templates/index.html:toggleDetail` - set link URLs via URL/encodeURI for href after parsing, rather than relying on esc() alone
    (esc() is HTML escaping, not URL safety; odd schemes or characters in remote URLs are safer through URL APIs)

7 files / ~105 functions reviewed. 89 functions reviewed clean.
