# Code Review: Paperworks

- **Date:** 2026-04-13
- **Model:** claude-4.6-opus

A well-structured local dashboard with sound layering and a clear data model, undermined by an overstuffed server module, absent path validation on file-serving routes, and innerHTML XSS vectors in the client.

## Executive Summary

Paperworks is a local-first WG21 paper dashboard that correlates markdown sources, rendered PDFs, and isocpp.org remote state into a single browser UI. The architecture is clean: a thin CLI boots a Flask server that hosts a single-page client, JSON APIs, SSE push, filesystem watchdogs, and a background PDF render pipeline. Data flows through well-separated modules - `inventory.py` assembles the paper model, `pdf_reader.py` extracts metadata from PDFs, `isocpp.py` handles authenticated remote operations, and `server_config.py` persists user settings.

The review found 7 flags across 4 files, with the most consequential being path traversal vectors in `server.py`'s file-serving routes, XSS via unescaped `innerHTML` in the client, and a style-override bug in config loading that can silently overwrite intentional user settings. The codebase has no tests. Error handling is inconsistent - some modules swallow all exceptions silently, others surface them. The server module carries too many responsibilities (880 lines spanning routes, SSE, watchdogs, render orchestration, Tk dialogs, and asset serving).

## Synthesis

**API Grouping.** Six logical API groups exist within the codebase:

1. **CLI** - `paperworks.py`: `main`
2. **Configuration** - `server_config.py`: `load_config`, `save_config`, `CONFIG_DIR`, `CONFIG_PATH`, `DEFAULTS`, `SCRIVENER_CONFIG`
3. **Data Assembly** - `inventory.py`: `scan_markdown_dirs`, `scan_pdf_dir`, `build_inventory`, `compute_summary`; `pdf_reader.py`: `read_pdf`
4. **Remote Integration** - `isocpp.py`: `IsoCppSession` (login, logout, fetch_papers, submit, get_status, properties)
5. **Server Orchestration** - `server.py`: Flask `app`, 25+ route handlers, `run_server`, SSE hub, watchdogs, render pipeline
6. **Client UI** - `index.html`: 40+ global JS functions, SSE consumer, drag-and-drop, tab management

Groups 1-4 are well-bounded. Group 5 is the problem - it is a single 880-line module carrying HTTP routing, SSE broadcasting, activity logging, filesystem watching with debounce, background PDF rendering, Tk file dialogs, and scrivener asset serving. Group 6 mirrors this breadth on the client side.

**Cohesion.** The files pull in the same direction. The data model flows cleanly: markdown YAML is source of truth, PDFs provide rendered-state confirmation, remote rows add isocpp.org status. `inventory.py` assembles these into a unified view that the server exposes and the client renders. The layering is sound.

**Scope.** `server.py` does too much. It owns the HTTP surface, the event bus, two independent filesystem watchers with debounce timers, a background render worker, dynamic `sys.path` manipulation for scrivener import, Tk dialog spawning, and static asset serving. These are at least four distinct concerns (web API, filesystem observation, render orchestration, scrivener integration) packed into one module. Similarly, `index.html` at 775 lines puts CSS, HTML structure, and all client JavaScript into a single file with no module boundary.

**Responsibility Leakage.** Document-number normalization appears twice with different regex patterns: `_DOC_RE` and `_parse_doc_number` in `inventory.py` versus `_DOC_NUM_RE` and `_DOC_FIELD_RE` in `pdf_reader.py`. These could diverge silently. The server reaches into scrivener internals via dynamic path manipulation and direct module import. The config module's style-inheritance logic is coupled to the default string value rather than a sentinel, creating a fragile detection mechanism.

**Cross-file Coherence.** Naming conventions are consistent. All modules use the same dict-passing style with no typed boundaries (no TypedDict, no dataclass, no schema). Error handling varies significantly: `isocpp.py` uses broad `except Exception` that returns tuples, `pdf_reader.py` silently falls back to filename-only metadata, `server_config.py` silently returns defaults, and `inventory.py` silently drops unreadable papers. None of these log the original exception. Documentation quality is uneven - `isocpp.py` has the best class-level docs, while most route handlers in `server.py` have none.

## Files With Findings

### paperworks.py

Entry script for the Paperworks WG21 dashboard. Parses CLI arguments so `serve` starts the Flask stack after loading or updating `~/.paperworks/config.json` (optional `--port`). Python, roughly 50 lines.

- **Bugs** (advisory): `--port` persists to `config.json` via `save_config`; if intent is one-shot override, this silently changes stored config
- **Documentation** (advisory): module docstring references "docketeer" while the implemented client module is `isocpp.py` (naming drift); `main` has no docstring
- **Contract fidelity** (advisory): module docstring and usage epilog use inconsistent names; `--port` persistence is undocumented
- **API design** (advisory): dual argparse paths (in-function parser vs top-level parser) widen CLI surface; lazy imports inside `serve` branch hide import failures until runtime

### lib/isocpp.py

Python client for authenticated isocpp.org flows using `requests`, HTML parsing, a background worker queue, and a session lock. About 405 lines.

- **Contract fidelity** (flag): class docstring states all events include `job_id`, `doc_number`, `type`; the `queue_drained` event only carries `event`, breaking the documented contract (high)
- **Bugs** (advisory): `_run_worker` never calls `task_done` on the queue; `_read_form` does not check HTTP status before parsing; `active_job` property read without the lock used for writes
- **Duplication** (advisory): login form scraping and `_read_form` input-walking repeat the same dict-building pattern
- **Documentation** (advisory): public properties lack docstrings; private methods with non-obvious behavior (`_run_worker`, `_emit`, `_do_upload`) undocumented
- **Resource management** (advisory): `logout` replaces `requests.Session` without `close()` on the old session
- **Error handling** (advisory): `_emit` swallows all callback exceptions with no logging; broad `except Exception` in login/fetch returns strings that hide error kind
- **Security** (advisory): `submit` trusts `pdf_path` from caller without validation; login success detection uses substring heuristics on response body
- **Concurrency** (advisory): `_active_job` updates visible across threads without documented memory barrier
- **API design** (advisory): `get_status`/`active_job` expose live dict references; callers can mutate shared state

### lib/server.py

Large Flask application: REST-ish JSON APIs, Server-Sent Events hub, activity log, dynamic scrivener import, markdown and PDF watchdogs, and a background render worker. About 880 lines.

- **Security** (flag): `serve_local_file` returns any readable file by query path with no allowlist (medium on localhost, critical if bind address widens); `_serve_scrivener_file`/`serve_font`/`serve_image` join filename to base dir without rejecting `..` segments (path traversal); unauthenticated `shutdown` POST terminates the process (high/medium)
- **Resource management** (flag): `render_preview` creates `tempfile.mkdtemp` that is never cleaned up (disk growth on repeated previews); observer `join(timeout=2)` may return while old thread still running (medium/low)
- **Bugs** (advisory): `int(data["port"])` in `update_config` unhandled `ValueError` becomes 500; `remove_dir` with empty string resolves to cwd; `render_all` returns 400 for "nothing to do" (normal outcome)
- **Duplication** (advisory): watchdog startup pattern repeated between md and pdf watchers; output-dir validation repeated in flush, render_paper, and render_all; scrivener bootstrap duplicated in render_worker and render_preview
- **Documentation** (advisory): most route handlers have no docstrings; module docstring is a single line
- **Contract fidelity** (advisory): `render_all` docstring implies success but returns 400 on empty batch
- **Single responsibility** (advisory): 880 lines combining HTTP, SSE, logging, watchdogs, render orchestration, Tk pickers, and asset serving
- **Error handling** (advisory): `_dir_info` uses `except Exception: pass` hiding permission and I/O failures
- **Readability** (advisory): `render_preview` nests try/with/inner-try with mixed multipart/JSON branches
- **Formatting** (advisory): mixed quote style; `render_preview` uses six-space indentation while rest uses four
- **API design** (advisory): wide HTTP surface with module-level globals; tight coupling to scrivener layout via dynamic import

### lib/inventory.py

Pure Python correlation of markdown trees, PDF output folder, and optional remote paper rows into one sorted list per paper family with derived status, warnings, and revision links. About 369 lines.

- **Bugs** (advisory): `scan_markdown_dirs` uses `entry["path"]` with no default (KeyError risk); duplicate normalized `doc_number` silently overwrites; `_read_markdown_paper` reads only 8000 bytes risking missed front-matter closure; `_parse_doc_number` non-match path sets base to raw string; `compute_summary` does not count all statuses so `total` can diverge from bucket sum
- **Duplication** (advisory): rekey loop for `md_by_base`/`pdf_by_base` repeated; doc-number normalization overlaps with `pdf_reader.py` using different regexes
- **Documentation** (advisory): `build_inventory` docstring says remote provides "status only" but implementation also uses remote title, author, and date as fallbacks
- **Contract fidelity** (advisory): documented "status only" contract contradicts metadata-fallback behavior; sort order does not distinguish D vs P prefixes
- **Single responsibility** (advisory): `build_inventory` at ~150 lines mixes source merging, status derivation, warning generation, revision grouping, filtering, and sorting
- **Error handling** (advisory): `_read_markdown_paper` broad except returns `(None, None)` with no logging
- **Readability** (advisory): status derivation branch ordering encodes implicit product rules without a mapping comment
- **API design** (advisory): untyped dict returns with string keys; `scan_markdown_dirs` assumes dict-shaped entries with required keys

### lib/pdf_reader.py

Python module that opens PDFs with PyMuPDF when available and heuristically extracts document number, title, authors, date, audience, and abstract from early pages or the filename. About 165 lines.

- **Bugs** (advisory): `_extract_abstract_from_doc` for multi-page PDFs starts at page 1, skipping page 0 where abstract may appear; title extraction can skip valid titles matching doc-number pattern; `_STOP_RE` can cut abstract early on false matches
- **Documentation** (advisory): `read_pdf` docstring omits behavior when PyMuPDF is missing; private helpers have no docstrings; page-index choice in abstract extraction is non-obvious
- **Contract fidelity** (advisory): return dict always has all keys, but many stay `None` without signaling why (import failure vs corrupt PDF vs empty text)
- **Error handling** (advisory): `except Exception` maps all failures to filename-only `doc_number` with no logging or distinction between error types
- **Readability** (advisory): magic numbers (20 lines for title, 5 pages, thresholds 10/20/30/200/1000) unexplained at call sites
- **Security** (advisory): opens path as given; fine for local trust model but no normalization if path were ever user-controlled
- **API design** (advisory): untyped dict return; broad exception handling exposes no error type to callers

### lib/server_config.py

JSON-backed user config under `~/.paperworks/config.json` with defaults and merge from `~/.scrivener/config.json` for output dirs, watch dirs, and style when unset. About 75 lines.

- **Bugs** (flag): `load_config` treats `style == DEFAULTS["style"]` as "unset" and overwrites with scrivener's style - an intentional `wg21` setting gets silently replaced when it matches the default (medium); `save_config` direct in-place JSON write can leave truncated/invalid `config.json` on crash (low-medium); `_normalize_dir` does not handle `None` or non-dict/non-str entries (low)
- **Contract fidelity** (flag): `save_config` described as atomic persistence but uses no temp-file-plus-replace pattern (medium)
- **Duplication** (advisory): watch-dir normalization pattern appears twice in `load_config`
- **Documentation** (advisory): `load_config` and `save_config` have no docstrings; no documentation of which keys inherit from scrivener
- **Error handling** (advisory): broad `except Exception` in config loading discards all error types with no signal
- **Security** (advisory): credentials stored as plain JSON under user home
- **Concurrency** (advisory): no file lock or atomic replace between concurrent `save_config`/`load_config` calls
- **API design** (advisory): "unset" detection for style is coupled to default string value (fragile); `render_output_dir`/`render_style` never inherit from scrivener while `output_dir`/`style` do (asymmetric)

### lib/templates/index.html

Single-page dashboard: embedded CSS for a dark UI, HTML for Folio/Render/Settings/Log tabs, and a large inline JavaScript client for fetch APIs, EventSource, drag-and-drop preview cards, and directory management. About 775 lines.

- **Security** (flag): `toggleDetail` interpolates `furl`/`r.form_url` into `innerHTML`/`href` without escaping - XSS vector from hostile or malformed server data (high); `renderDirs` emits `d.path` raw in HTML; `populateStyleSelect` emits `s.name` raw; images grid emits `i` raw (medium)
- **Bugs** (flag): `connectSSE` handlers call `JSON.parse(e.data)` with no guard - malformed SSE payloads throw and can break the EventSource callback chain (high); `submitJob` has no timeout or fallback if `job_completed`/`job_failed` SSE events never arrive, leaving `_workingSet` and badges stuck (medium); same stuck risk in `renderSingle` (medium)
- **Duplication** (advisory): fetch-json-toast pattern repeated across many functions; working/disabled/pulse styling duplicated across CSS selectors
- **Documentation** (advisory): globals and server field expectations undocumented; `setStatus` parameter meaning non-obvious
- **Contract fidelity** (advisory): `submitJob` name implies complete transaction but success completion is delegated to SSE
- **Single responsibility** (advisory): `renderPapers` mixes filtering, row HTML, empty state, global button, and detail restoration; `loadCatalog` mixes styles, font-face injection, font table, image grid, and select population
- **Resource management** (advisory): `_statusTimer` can stack across callers; debounce timers not cleared on shutdown
- **Error handling** (advisory): `removeDir`/`toggleDir` on `!r.ok` do not surface errors to user
- **Readability** (advisory): long single-line functions hurt scanability; large template literals in `renderPapers` and `toggleDetail` increase nesting
- **Formatting** (advisory): inconsistent density between expanded and minified functions; CSS uses long single-line rules throughout
- **Concurrency** (advisory): shared globals updated from SSE, timers, and overlapping `loadInventory` calls; last completion wins
- **API design** (advisory): inline `onclick` ties DOM to global function names; client assumes fixed JSON shapes with no runtime checks
