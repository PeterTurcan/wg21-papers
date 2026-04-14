# Code Review: Paperworks

- **Date:** 2026-04-14
- **Model:** claude-4.6-opus

Sound three-source data model and clean layering, undermined by path-traversal exposure in file-serving routes, a debounce race that can strand client promises, and a 910-line server module that owns five distinct concerns.

## Executive Summary

Paperworks is a local-first WG21 paper dashboard that correlates markdown sources, rendered PDFs, and isocpp.org remote state into a browser UI. A thin CLI boots a Flask server hosting a single-page client, JSON APIs, SSE push, filesystem watchdogs, and a background PDF render pipeline. Data flows through well-separated modules - `inventory.py` assembles the paper model, `pdf_reader.py` extracts metadata from PDFs, `isocpp.py` handles authenticated remote operations, and `server_config.py` persists user settings.

The review found 8 flags across 5 files, with the most consequential being path traversal vectors in `server.py`'s file-serving routes, a debounce/promise race in the client's `loadInventory`, and contract mismatches between `isocpp.py`'s documented event schema and its actual behavior. The codebase has no tests. Error handling is inconsistent - some modules swallow all exceptions silently, others surface them. `server.py` carries too many responsibilities (910 lines spanning routes, SSE, watchdogs, render orchestration, Tk dialogs, and asset serving). `index.html` mirrors this breadth on the client side.

## Synthesis

**API Grouping.** Six logical API groups exist:

1. **CLI** - `paperworks.py`: `main`
2. **Configuration** - `server_config.py`: `load_config`, `save_config`, `CONFIG_DIR`, `CONFIG_PATH`, `DEFAULTS`, `SCRIVENER_CONFIG`
3. **Data Assembly** - `inventory.py`: `scan_markdown_dirs`, `scan_pdf_dir`, `build_inventory`, `compute_summary`; `pdf_reader.py`: `read_pdf`
4. **Remote Integration** - `isocpp.py`: `IsoCppSession` (login, logout, fetch_papers, submit, get_status, properties)
5. **Server Orchestration** - `server.py`: Flask `app`, 25+ route handlers, `run_server`, SSE hub, watchdogs, render pipeline
6. **Client UI** - `index.html`: 40+ global JS functions, SSE consumer, drag-and-drop, tab management

Groups 1-4 are well-bounded. Group 5 is the problem - it is a single 910-line module carrying HTTP routing, SSE broadcasting, activity logging, filesystem watching with debounce, background PDF rendering, Tk file dialogs, and scrivener asset serving. Group 6 mirrors this breadth on the client side at 800 lines.

**Cohesion.** The files pull in the same direction. The data model flows cleanly: markdown YAML is source of truth, PDFs provide rendered-state confirmation, remote rows add isocpp.org status. `inventory.py` assembles these into a unified view that the server exposes and the client renders. The layering is sound.

**Scope.** `server.py` does too much. It owns the HTTP surface, the event bus, two independent filesystem watchers with debounce timers, a background render worker, dynamic `sys.path` manipulation for scrivener import, Tk dialog spawning, and static asset serving. These are at least five distinct concerns (web API, filesystem observation, render orchestration, scrivener integration, OS dialogs) packed into one module. `index.html` puts CSS, HTML structure, and all client JavaScript into a single file with no module boundary.

**Responsibility Leakage.** Document-number normalization appears twice with different regex patterns: `_DOC_RE` and `_parse_doc_number` in `inventory.py` versus `_DOC_NUM_RE` and `_DOC_FIELD_RE` in `pdf_reader.py`. These can diverge silently. The server reaches into scrivener internals via dynamic path manipulation and direct module import. The config module's style-inheritance logic uses value equality with the default string rather than a sentinel, creating a fragile detection mechanism. CLAUDE.md states isocpp.org is "never a metadata source" but `build_inventory` uses remote title, author, and date as fallbacks - a contract gap between project documentation and implementation.

**Cross-file Coherence.** Naming conventions are consistent. All modules use the same dict-passing style with no typed boundaries (no TypedDict, no dataclass, no schema). Error handling varies significantly: `isocpp.py` uses broad `except Exception` returning tuples, `pdf_reader.py` silently falls back to filename-only metadata, `server_config.py` silently returns defaults, `inventory.py` silently drops unreadable papers. None log the original exception. Documentation quality is uneven - `isocpp.py` has the best class-level docs, most route handlers in `server.py` have none.

## Files With Findings

### paperworks.py

Entry script for the Paperworks CLI. Parses `serve` (optional `--port`), loads or updates config via `server_config`, then starts the Flask app via `run_server`. About 50 lines, Python.

6/12 checks clean.

- **Bugs** (advisory): `--port` persists to `config.json` via `save_config`; if intent is one-shot override, this silently changes stored config
- **Documentation** (advisory): module docstring references "docketeer" while the implemented client module is `isocpp.py`; `main` has no docstring; unused import `Path`
- **Contract fidelity** (advisory): module docstring and usage epilog use inconsistent invocation names
- **Single responsibility** (advisory): `main` both dispatches CLI and applies persistent config when `--port` is set; bind behavior and config persistence are two policies in one function
- **Formatting** (advisory): unused import `Path` from `pathlib`
- **API design** (advisory): `sys.argv[1] == "serve"` pre-check is narrow compared to `argparse` subparsers if more commands are planned

### lib/server.py

Large Flask application (~910 lines) wiring the dashboard: SSE fan-out, activity log, queued PDF rendering with scrivener's `build_pdf`, markdown and PDF filesystem watchdogs, REST JSON APIs, and an `IsoCppSession` bridge.

0/12 checks clean.

- **Bugs** (advisory): `int(data["port"])` in `update_config` unhandled `ValueError` becomes 500; `remove_dir` with empty string resolves to cwd; warning de-duplication outside `_log_lock` can produce inconsistent log lines under concurrent requests
- **Duplication** (advisory): `MDHandler` vs `PDFHandler` repeat the same handler/on_modified/on_created pattern; watchdog startup pattern repeated between md and pdf watchers; `pick_dir`/`pick_file` identical wiring
- **Documentation** (advisory): module docstring is one line; most route handlers and helpers have no docstrings; public constants undocumented
- **Contract fidelity** (advisory): startup log says watchdog "started" even when `watchdog` module is missing and observer is not created; `render_preview` does not document temp-directory behavior
- **Single responsibility** (advisory): 910 lines combining HTTP, SSE, logging, watchdogs, render orchestration, Tk pickers, and asset serving
- **Resource management** (flag): `render_preview` creates `tempfile.mkdtemp` for output that is never cleaned up (disk growth on repeated previews); observer `join(timeout=2)` may leave threads alive on shutdown (medium)
- **Error handling** (advisory): `_dir_info` uses `except Exception: pass` hiding permission and I/O failures; broad exception handling in several routes
- **Readability** (advisory): `render_preview` nests try/with/inner-try with inconsistent indentation; `_render_worker` is long with multiple responsibilities
- **Formatting** (advisory): `render_preview` body uses 6-space indentation while rest uses 4-space; one-liner handler methods differ from expanded style elsewhere
- **Security** (flag): `serve_local_file` returns any readable file by query path with no allowlist; `serve_asset`, `_serve_scrivener_file`, `serve_font`, `serve_image` join filename to base dir without rejecting `..` segments (path traversal); unauthenticated `shutdown` POST terminates the process (medium on localhost, high if bind widens)
- **Concurrency** (advisory): `_preview_lock` serialization is correct; debounce timers have minor residual races from timer scheduling outside locks; `_activity_log` access is properly locked
- **API design** (advisory): config/dir routes mutate process-global observers as side effects; `shutdown` is unauthenticated; wide module surface couples tests and callers to globals

### lib/server_config.py

JSON config layer for `~/.paperworks/config.json` with defaults, merge-on-load, watch-dir normalization, and fallback fields from `~/.scrivener/config.json`. About 76 lines, Python.

5/12 checks clean.

- **Bugs** (advisory): `_normalize_dir` raises `AttributeError` on `None`, number, or list entries in `watch_dirs`; `load_config` treats `style == DEFAULTS["style"]` as "unset" and overwrites with scrivener's style - an intentional `wg21` setting gets silently replaced when it matches the default
- **Documentation** (advisory): `load_config` and `save_config` have no docstrings describing merge rules, scrivener fallback, or which keys are persisted
- **Contract fidelity** (advisory): style fallback behavior does not match a strict reading of "only fill missing from scrivener" because default value is treated as missing
- **Error handling** (advisory): broad `except Exception` in config loading and scrivener reading swallows all error types with no signal; `save_config` uses no temp-file-plus-replace for atomic writes
- **Security** (advisory): `isocpp_password` stored as plain JSON under user home
- **Concurrency** (advisory): non-atomic read-modify-write on `config.json` can yield torn JSON under parallel processes
- **API design** (advisory): `save_config` writes the full dict with no key whitelist; "unset" detection for style is coupled to default string value

### lib/inventory.py

Pure Python correlation of markdown trees, PDF output folder, and optional remote paper rows into one sorted list per paper family with derived status, warnings, and revision links. About 370 lines.

2/12 checks clean.

- **Bugs** (advisory): `scan_markdown_dirs` uses `entry["path"]` with no default (KeyError risk); duplicate normalized `doc_number` silently overwrites; `_read_markdown_paper` reads only 8000 bytes risking missed front-matter closure; `_parse_doc_number` non-match path yields inconsistent key format; `stat()` after `is_file()` can race on file removal
- **Duplication** (advisory): doc-number normalization overlaps with `pdf_reader.py` using different regexes
- **Documentation** (advisory): `compute_summary` docstring does not state which statuses contribute to per-bucket counts; `scan_markdown_dirs` does not document required entry shape or overwrite behavior
- **Contract fidelity** (flag): CLAUDE.md states isocpp.org is "never a metadata source" but `build_inventory` uses remote title, author, and date as fallbacks when markdown and PDF are absent; behavior matches the module's own docstring but contradicts the project-level contract (medium)
- **Single responsibility** (advisory): `build_inventory` at ~150 lines mixes source merging, status derivation, warning generation, revision grouping, filtering, and sorting
- **Error handling** (advisory): `_read_markdown_paper` broad except masks `UnicodeDecodeError`, disk errors, and YAML issues indistinguishably
- **Readability** (advisory): `build_inventory` has high local complexity with nested status conditionals; `_sort_key` has no separating blank line
- **Security** (advisory): paths not validated beyond `is_dir()`; `yaml.safe_load` is appropriate
- **Concurrency** (advisory): filesystem races during scan can cause skipped papers or uncaught `OSError`
- **API design** (advisory): untyped dict returns with string keys; easy for callers to mis-key `author` vs `authors` on remote vs local merge paths

### lib/isocpp.py

Python client using `requests` and BeautifulSoup: `IsoCppSession` holds a session, lock, and background worker queue so uploads and draft/review transitions serialize. About 410 lines.

3/12 checks clean.

- **Bugs** (flag): `_do_transition` treats any `target` other than `"review"` as draft revert including typos or missing keys (medium); `_run_worker` never calls `task_done()` on the queue, breaking `join()` semantics; `_read_form` does not check HTTP status before parsing; `active_job` read across threads without lock (low)
- **Duplication** (advisory): login form scraping and `_read_form` input-walking repeat the same BeautifulSoup pattern
- **Documentation** (advisory): class docstring claims all events include `job_id`, `doc_number`, `type` but `queue_drained` does not; `logout` and `get_status` have no docstrings; module-level constants undocumented
- **Contract fidelity** (flag): "all events include job_id, doc_number, type" contradicted by `queue_drained` payload; `_read_form` documented as running inside lock but does not take it itself (relies on caller holding `_lock`) (low)
- **Resource management** (advisory): `logout` replaces `requests.Session` without `close()` on old session; daemon worker has no join or shutdown hook
- **Error handling** (advisory): `_emit` swallows all callback exceptions; broad `except Exception` in login and worker with string-only messages; `_read_form` has no timeout or status handling
- **Security** (advisory): `_do_upload` trusts `pdf_path` from caller without validation; standard TLS defaults should be verified
- **Concurrency** (advisory): `_lock` correctly serializes session use but long uploads block concurrent reads; `_active_job` cross-thread visibility without copying
- **API design** (advisory): `get_status`/`active_job` expose live mutable dict references; `submit` validates nothing up front

### lib/pdf_reader.py

Uses PyMuPDF (`fitz`) when available to open a WG21 PDF and regex-scan the first pages for document number, title, authors, date, audience, and abstract. Filename fallback when text extraction fails. About 165 lines, Python.

5/12 checks clean.

- **Bugs** (flag): broad `except` in `read_pdf` drops already-extracted title, authors, date, audience on any late failure and returns filename-only metadata (medium); `_extract_title` rejects lines starting with a doc-number token, skipping titles prefixed by paper id; `_extract_abstract_from_doc` requires exact `abstract` match, missing variants like `Abstract:` (medium)
- **Duplication** (advisory): doc-number parsing overlaps `inventory._DOC_RE`/`_parse_doc_number` with different regex patterns
- **Documentation** (advisory): `read_pdf` docstring omits behavior when PyMuPDF is missing; private helpers have no docstrings
- **Contract fidelity** (advisory): any `Exception` yields nearly empty metadata without signaling failure to callers; `authors` reflects first match only without documentation
- **Error handling** (advisory): broad `except Exception` conflates missing PyMuPDF, corrupt PDFs, and logic bugs with no logging
- **API design** (advisory): untyped dict return; broad exception handling exposes no error type to callers

### lib/templates/index.html

Single-page dashboard with embedded CSS and JavaScript (~800 lines). Dark-themed UI: tabs (Folio, Render, Settings, Log), inventory table, SSE client, fetch wrappers, render drop-zone cards, settings forms, and bottom status bar.

0/12 checks clean.

- **Bugs** (flag): `loadInventory` debounce clears the pending timer but does not resolve or supersede earlier Promises - a second call within the window can strand a prior `await loadInventory()` forever (high); `JSON.parse(e.data)` in SSE handlers is uncaught - malformed payloads throw and break further handling (medium)
- **Duplication** (advisory): fetch-then-json-then-toast pattern repeated across many functions; working/disabled/pulse styling duplicated across CSS selectors
- **Documentation** (advisory): no file-level or per-function documentation of the global onclick/SSE contract
- **Contract fidelity** (advisory): `submitJob`/`renderSingle` defer clearing busy state to SSE, fragile if events are missed; `showTab` couples to `onclick` attribute text
- **Single responsibility** (advisory): single script mixes tabs, inventory, settings, drag-drop preview, SSE, logging, and auth; `fillCard` wires UI, state, and kicks `renderCard`
- **Resource management** (advisory): no explicit EventSource teardown on page unload; debounce timers can overlap logically
- **Error handling** (advisory): many fetch paths rely on `r.ok` without normalizing non-JSON error bodies
- **Readability** (advisory): large inlined template strings in `renderPapers`, `toggleDetail`, `loadCatalog` raise cognitive load; mixed density between compressed one-liners and expanded blocks
- **Formatting** (advisory): inconsistent brace/spacing style between early globals and later functions; inline `style=` attributes coexist with centralized CSS
- **Security** (advisory): `innerHTML` used widely; `toggleDetail` injects `furl` and revision links with less uniform escaping than other paths; `renderDirs` embeds directory paths into `onclick` strings with partial escaping (medium under untrusted config)
- **Concurrency** (flag): `loadInventory` debounce plus shared `_papers`/`_workingSet`/`_dirtySet` means overlapping async refreshes produce stranded promises and unpredictable ordering relative to SSE-driven `loadInventory()` calls (high)
- **API design** (advisory): very wide global surface with no encapsulation module; DOM ids double as a narrow API to `startWork`/`endWork`

## API Surface

### paperworks.py

- public | `main` | function | CLI entry: `serve` with optional `--port` or help

### lib/server.py

- public | `SCRIVENER_ROOT` | constant | Path to sibling scrivener tree
- public | `app` | variable | Flask application instance
- public | `MAX_LOG` | constant | Max retained activity log entries
- public | `MD_DEBOUNCE` | constant | Markdown watchdog debounce seconds
- public | `PDF_DEBOUNCE` | constant | PDF watchdog debounce seconds
- public | `run_server` | function | Start render thread, watchdogs, app.run (cfg)
- public | `add_no_cache` | function | after_request: no-cache headers for HTML
- public | `dashboard` | function | GET /: render index.html
- public | `sse` | function | GET /api/events: SSE stream
- public | `get_config` | function | GET /api/config: safe config snapshot
- public | `update_config` | function | POST /api/config: merge and save
- public | `add_dir` | function | POST /api/dirs: add watch directory
- public | `remove_dir` | function | DELETE /api/dirs: remove watch directory
- public | `toggle_dir` | function | POST /api/dirs/toggle: toggle dir field
- public | `get_inventory` | function | GET /api/inventory: merged papers + summary
- public | `login` | function | POST /api/login: isocpp login
- public | `logout` | function | POST /api/logout: clear session
- public | `auth_status` | function | GET /api/auth-status: auth snapshot
- public | `upload_paper` | function | POST /api/upload: queue one upload job
- public | `upload_all` | function | POST /api/upload-all: queue many uploads
- public | `transition_paper` | function | POST /api/transition: queue draft/review
- public | `render_paper` | function | POST /api/render: queue one markdown render
- public | `render_preview` | function | POST /api/render-preview: sync preview PDF
- public | `render_all` | function | POST /api/render-all: queue stale renders
- public | `get_queue` | function | GET /api/queue: isocpp queue depth/active
- public | `get_log` | function | GET /api/log: activity log list
- public | `clear_log` | function | DELETE /api/log: clear log
- public | `catalog` | function | GET /api/catalog: styles, images, fonts
- public | `serve_font` | function | GET /api/font: serve font file
- public | `serve_image` | function | GET /api/image/filename: serve image
- public | `pick_dir` | function | GET /api/pick-dir: tkinter directory picker
- public | `pick_file` | function | GET /api/pick-file: tkinter file picker
- public | `serve_asset` | function | GET /assets/filename: static assets
- public | `serve_local_file` | function | GET /api/file: read local file by path
- public | `open_folder` | function | POST /api/open-folder: OS open folder
- public | `shutdown` | function | POST /api/shutdown: terminate process
- private | `_broadcast` | function | Push SSE message to all queues
- private | `_add_log` | function | Append log entry and SSE event
- private | `_on_isocpp_event` | function | Bridge IsoCpp events to SSE and log
- private | `_ensure_scrivener` | function | Add scrivener to sys.path
- private | `_load_style` | function | Load scrivener style dict by id
- private | `_render_worker` | function | Background loop draining render queue
- private | `_flush_md_pending` | function | Debounced enqueue of stale renders
- private | `_start_md_watchdog` | function | Start/restart markdown Observer
- private | `_flush_pdf_pending` | function | Emit file_changed for PDF updates
- private | `_start_pdf_watchdog` | function | Start/restart PDF directory observer
- private | `_dir_info` | function | Enrich watch dir entry with counts
- private | `_scrivener_config` | function | Import scrivener paths/helpers
- private | `_serve_scrivener_file` | function | send_file from fonts/images dir
- private | `_pick_path` | function | Tk root + filedialog helper
- private | `MDHandler` | class | FileSystemEventHandler for .md
- private | `PDFHandler` | class | FileSystemEventHandler for .pdf

### lib/server_config.py

- public | `CONFIG_DIR` | constant | Path ~/.paperworks
- public | `CONFIG_PATH` | constant | Path to config.json
- public | `DEFAULTS` | constant | Default config dict
- public | `SCRIVENER_CONFIG` | constant | Path ~/.scrivener/config.json
- public | `load_config` | function | Load, normalize, merge with scrivener fallback
- public | `save_config` | function | Persist config to disk (cfg)
- private | `_normalize_dir` | function | Coerce watch dir entry to structured dict
- private | `_read_scrivener_config` | function | Read optional scrivener JSON

### lib/inventory.py

- public | `scan_markdown_dirs` | function | Scan watch dirs for papers from markdown (watch_dirs)
- public | `scan_pdf_dir` | function | Scan output dir for PDF metadata (output_dir)
- public | `build_inventory` | function | Merge markdown, PDF, remote; derive status (watch_dirs, output_dir, remote_papers)
- public | `compute_summary` | function | Count papers by status for dashboard (papers)
- private | `_DOC_RE` | constant | Compiled doc number regex
- private | `_MD_STRIP_RE` | constant | Abstract cleanup regex
- private | `_parse_doc_number` | function | Parse D/P/N to full/base/rev (raw)
- private | `_read_markdown_paper` | function | Read front matter + abstract (path)
- private | `_extract_markdown_abstract` | function | First sentence from ## Abstract (body)

### lib/isocpp.py

- public | `LOGIN_URL` | constant | isocpp login URL
- public | `PAPERS_URL` | constant | isocpp papers list URL
- public | `BASE_URL` | constant | Site origin
- public | `IsoCppSession` | class | Queued authenticated HTTP session to isocpp
- public | `IsoCppSession.__init__` | method | Start worker thread and session state (on_event)
- public | `IsoCppSession.authenticated` | property | Whether login succeeded
- public | `IsoCppSession.username` | property | Current username or None
- public | `IsoCppSession.queue_depth` | property | Pending job count
- public | `IsoCppSession.active_job` | property | Current job dict or None
- public | `IsoCppSession.get_status` | method | Snapshot for API
- public | `IsoCppSession.login` | method | POST login form (username, password)
- public | `IsoCppSession.logout` | method | Reset session and flags
- public | `IsoCppSession.fetch_papers` | method | Parse papers table HTML
- public | `IsoCppSession.submit` | method | Enqueue upload or transition job (job)
- private | `IsoCppSession._run_worker` | method | Worker loop
- private | `IsoCppSession._emit` | method | Safe callback invoke
- private | `IsoCppSession._read_form` | method | GET and parse paper form
- private | `IsoCppSession._pick_save_button` | method | Choose non-transition save submit
- private | `IsoCppSession._post_form` | method | POST form-update with optional file
- private | `IsoCppSession._do_upload` | method | Execute upload job under lock
- private | `IsoCppSession._do_transition` | method | Execute transition job under lock

### lib/pdf_reader.py

- public | `read_pdf` | function | Extract metadata dict from one PDF path (path)
- private | `_DOC_NUM_RE` | constant | Doc number pattern regex
- private | `_DOC_FIELD_RE` | constant | Document Number: line regex
- private | `_REPLY_TO_RE` | constant | Author line regex
- private | `_AUDIENCE_RE` | constant | Audience line regex
- private | `_DATE_RE` | constant | ISO date regex
- private | `_STOP_RE` | constant | Abstract termination pattern regex
- private | `_extract_doc_number` | function | Resolve doc number from text (text)
- private | `_doc_number_from_filename` | function | Parse doc number from PDF stem (path)
- private | `_extract_title` | function | Heuristic title from first lines (lines)
- private | `_extract_authors` | function | Authors from reply-to line (text)
- private | `_extract_abstract_from_doc` | function | Scan pages for abstract block (doc)
