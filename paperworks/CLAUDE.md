# Paperworks - Agent Rules

## What This Is

Paperworks is the unified web dashboard for managing WG21 paper
submissions. It orchestrates two libraries:

- **Scrivener** (`../scrivener/`) - markdown to PDF rendering
- **Docketeer** (`lib/isocpp.py`) - isocpp.org authenticated client
  with internal queue

Paperworks itself handles the web UI, watchdogs, inventory
correlation, and orchestration logic.

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
      index.html      # Dashboard page (main view)
      settings.html   # Settings page (config, dirs, credentials)
```

## Source of Truth

Markdown is the source of truth for ALL paper metadata.

- **Priority**: markdown > PDF > isocpp.org. If markdown and
  PDF disagree, markdown wins. PDF is a derived artifact.
- **Metadata from markdown**: title, authors, date, audience
  (YAML front matter), abstract/brutal summary (`## Abstract`
  section in body)
- **PDF fallback**: if no markdown exists, PDF metadata is used
  but the paper shows `orphan` status
- **isocpp.org**: provides remote status (Draft/Review/Mailed)
  and form URLs only - never a metadata source
- **D/P prefixes**: interchangeable for matching. `D4007R0` and
  `P4007R0` refer to the same paper. Papers start as D (draft)
  and become P (published) when mailed. The numeric part and
  revision are what identify a paper.
- **Primary author**: only the first author from `reply-to` is
  synced to isocpp.org. Multi-author papers list all authors
  locally but only the first goes to the remote form.
- **Upload syncs everything**: there is no separate "sync
  metadata" operation. UPLOAD pushes the PDF AND syncs title,
  author, and abstract in one action. `_do_upload` skips any
  field that is None/empty - it will never overwrite good
  remote data with nothing.
- **Warnings**: if a markdown file has valid front matter but
  no `## Abstract` section, the paper gets a warning logged
  and shown in the UI. It does not block rendering or uploading.

## Three-Source Inventory

The paper inventory correlates three sources:

1. **Markdown** (source of truth) - YAML front matter provides
   doc_number, title, date, authors, audience. The `## Abstract`
   section in the body provides the brutal summary. These are
   authoritative.
2. **PDF directory** - derived artifacts. If PDF mtime < markdown
   mtime, the PDF is stale. PDF can never be newer than markdown.
3. **isocpp.org** - remote paper list with status (Draft/Review/Mailed)

### Derived Status

- `needs_render` - markdown exists, no PDF or PDF is stale
- `draft` / `review` - remote status, PDF is current
- `local` - has PDF, no remote entry
- `orphan` - has PDF but no markdown source
- `mailed` - hidden from default view

## IsoCppSession Queue (Critical)

`lib/isocpp.py` has an internal queue. ALL mutating operations
(upload, transition) go through `submit(job)`.

- Worker thread processes one job at a time
- `threading.Lock` serializes all HTTP session access
- Single `on_event` callback fires for every state change
- Events: job_queued, job_started, job_completed, job_failed, queue_drained
- NEVER bypass the queue. NEVER call the session directly.

## Two Pages

- `/` - Dashboard: top bar (auth + summary pills), paper table, log, bottom status bar
- `/settings` - Settings: output dir, watch dirs, credentials, style

Both pages use SSE (`/api/events`) for live updates. The SSE
connection is per-page - it reconnects on navigation. State is
server-side, fetched on page load via API.

## Pipeline

markdown changed -> watchdog -> render worker -> PDF created ->
PDF watchdog -> dirty flag -> user clicks Upload -> IsoCppSession
queue -> isocpp.org

## Button UX Rules (TODO - not yet fully implemented)

Buttons that submit work to the IsoCppSession queue (docketeer)
or to the render worker follow this pattern:

1. **Press** -> button enters working state immediately:
   - Disabled (no re-click)
   - Animated glowing border (badge-working style)
   - 70% opacity
2. **Log** -> IsoCppSession's on_event fires job_queued, which
   the server logs automatically. Render worker logs "Starting..."
3. **Event** -> button stays working until an SSE event confirms
   completion (job_completed, job_failed, rendered, render_done)
4. **Done** -> log entry for completion, button re-enables
5. **Log styling** -> completion entries at 50% opacity to
   distinguish from active/error entries

Buttons that go through the queue:
- Upload (IsoCppSession.submit upload - syncs title, author, abstract + PDF)
- Draft/Review transition (IsoCppSession.submit transition)
- Render per-paper (render worker)
- Render All (render worker)
- Log In (blocks on login request, not queued but same UX)

Buttons that do NOT go through the queue (instant, no working
state needed): Log Out, Clear Log, Open Folder, Shut Down,
Save (settings), tab switches.

## No Public Scraping

All remote data comes from the authenticated isocpp.org session.
Do not add public scraping of open-std.org or any other site.
