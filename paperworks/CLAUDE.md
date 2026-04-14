# Paperworks - Agent Rules

## What This Is

Paperworks is the unified web dashboard for managing WG21 paper submissions. It orchestrates two libraries:

- **Scrivener** (`../scrivener/`) - markdown to PDF rendering
- **Docketeer** (`lib/isocpp.py`) - isocpp.org authenticated client with internal queue

Paperworks itself handles the web UI, watchdogs, inventory correlation, and orchestration logic.

## Architecture

```
paperworks/
  paperworks.py       # CLI: python paperworks.py serve
  lib/
    server.py         # Flask app, SSE, routes, both watchdogs, render worker
    server_config.py  # ~/.paperworks/config.json, falls back to scrivener
    inventory.py      # Three-source paper database (markdown + PDF + isocpp.org)
    isocpp.py         # IsoCppSession - queued, lock-serialized, event-emitting
    pdf_reader.py     # PDF metadata extraction via PyMuPDF
    templates/
      index.html      # Single-page dashboard (folio, render, settings, log tabs)
```

## Source of Truth

Markdown is the source of truth for ALL paper metadata.

- **Priority**: markdown > PDF > isocpp.org. If markdown and PDF disagree, markdown wins. PDF is a derived artifact.
- **Metadata from markdown**: title, authors, date, audience (YAML front matter), abstract/brutal summary (`## Abstract` section in body)
- **PDF fallback**: if no markdown exists, PDF metadata is used but the paper shows `orphan` status
- **isocpp.org**: provides remote status (Draft/Review/Mailed) and form URLs only - never a metadata source
- **D/P prefixes**: interchangeable for matching. `D4007R0` and `P4007R0` refer to the same paper. Papers start as D (draft) and become P (published) when mailed. The numeric part and revision are what identify a paper.
- **Primary author**: only the first author from `reply-to` is synced to isocpp.org. Multi-author papers list all authors locally but only the first goes to the remote form.
- **Upload syncs everything**: there is no separate "sync metadata" operation. UPLOAD pushes the PDF AND syncs title, author, and abstract in one action. `_do_upload` skips any field that is None/empty - it will never overwrite good remote data with nothing.
- **Warnings**: if a markdown file has valid front matter but no `## Abstract` section, the paper gets a warning logged and shown in the UI. It does not block rendering or uploading.

## Three-Source Inventory

The paper inventory correlates three sources:

1. **Markdown** (source of truth) - YAML front matter provides doc_number, title, date, authors, audience. The `## Abstract` section in the body provides the brutal summary. These are authoritative.
2. **PDF directory** - derived artifacts. If PDF mtime < markdown mtime, the PDF is stale. PDF can never be newer than markdown.
3. **isocpp.org** - remote paper list with status (Draft/Review/Mailed)

### Derived Status

- `needs_render` - markdown exists, no PDF or PDF is stale
- `draft` / `review` - remote status, PDF is current
- `local` - has PDF, no remote entry
- `orphan` - has PDF but no markdown source
- `mailed` - hidden from default view

## IsoCppSession Queue (Critical)

`lib/isocpp.py` has an internal queue. ALL mutating operations (upload, transition) go through `submit(job)`.

- Worker thread processes one job at a time
- `threading.Lock` serializes all HTTP session access
- Single `on_event` callback fires for every state change
- Events: job_queued, job_started, job_completed, job_failed, queue_drained
- NEVER bypass the queue. NEVER call the session directly.

## Tabs

- **Folio** - paper inventory table with status badges, detail rows, upload
- **Render** - card-based drop targets for one-off preview rendering
- **Settings** - output dirs (folio + render), watch dirs, style, fonts, credentials
- **Log** - activity log with dimming

Both pages use SSE (`/api/events`) for live updates. The SSE connection is per-page - it reconnects on navigation. State is server-side, fetched on page load via API.

## Pipeline

markdown changed -> watchdog -> render worker -> PDF created -> PDF watchdog -> dirty flag -> user clicks Upload -> IsoCppSession queue -> isocpp.org

## SSE Command Lifecycle

A control that enters working state is guaranteed to exit working state on every code path. There are no stuck controls.

1. **Single gate** - `startWork`/`endWork` are the only way to enter/exit working state. No manual `disabled`, `classList`, or `_workingSet` manipulation outside these functions.
2. **Lock before submit** - `startWork` executes before the network call, never after or conditionally.
3. **Two completion modes, never mixed** - An operation is either synchronous (HTTP response is the result - unlock in `finally`) or queue-backed (HTTP merely enqueues - unlock comes from SSE). The HTTP response of a queue-backed operation is not a completion signal.
4. **HTTP failure unlocks immediately** - If the POST to enqueue fails (`!r.ok` or catch), no SSE event will arrive. The error handler must `endWork`.
5. **Server guarantees a terminal event** - Every enqueued operation emits exactly one terminal event (completed or failed). Worker threads enforce this via try/except. `_broadcast` uses unbounded queues - no maxsize, no `put_nowait`, no silent discard. Callback exceptions in event emitters must be logged, never swallowed.
6. **Reconnection reconciles** - After SSE reconnects, client state must be reconciled against server state. Events missed during the gap are gone; the only recovery is to query current state and clear stale locks.
7. **Failures are visible** - Every error-path unlock produces user feedback (toast or log entry). Silent unlocks hide bugs.

## Render Serialization

All `build_pdf` calls are serialized through `_preview_lock`. The batch render worker acquires it per file. The preview endpoint acquires it for the full render. This prevents concurrent ReportLab font registration corruption.

`build_pdf` is self-contained: it loads the font manifest, downloads missing fonts, registers them, and builds the PDF. Callers only need to provide a style dict. Variable fonts are instantiated on first use and cached as static TTFs in `.fonts/cache/` - subsequent renders skip fontTools entirely.

## No Public Scraping

All remote data comes from the authenticated isocpp.org session. Do not add public scraping of open-std.org or any other site.

## Path and File Safety

Never serve a file by joining a user-supplied filename to a base directory without rejecting `..` segments or normalizing the path first. File-serving routes must validate paths against an explicit allowlist of permitted root directories. Resolve relative paths with `Path.resolve()` and confirm the result is still under the intended root before opening.

## Client Security

`innerHTML` assignments must escape all server-supplied strings through `esc()` or equivalent. No exceptions for "trusted" fields - the escaping function is cheap, the XSS is not.

## Paperworks-Specific Extensions

These extend general rules in the root CLAUDE.md with project-specific instances.

- Always check HTTP response status before parsing the response body. Wrap `JSON.parse()` in a try/catch when processing external data (SSE payloads, fetch responses).
- A debounced async function must resolve or reject any previously returned Promise before replacing it. Stranded Promises break `await` callers.
- `queue.Queue.get()` must be paired with `task_done()` if any code path ever calls `queue.join()`.
