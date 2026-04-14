# Paperworks

Web dashboard for managing WG21 paper submissions. Orchestrates
markdown-to-PDF rendering (via Scrivener) and authenticated
isocpp.org operations into a single-page UI with live updates.

## Installation

Requires Python 3.10+.

Install dependencies (includes everything Scrivener needs):

```
pip install -r requirements.txt
```

Scrivener must be present at `../scrivener/` relative to this
directory. No separate install step is needed - Paperworks
imports it at runtime.

## Quick Start

```
python paperworks.py serve
```

Open http://localhost:7780 in a browser. Use `--port` to change:

```
python paperworks.py serve --port 8080
```

On first launch, go to the **Settings** tab to configure:

1. **Output Directory** - where rendered PDFs are written
2. **Watch Directories** - folders containing your `.md` source files
3. **Credentials** - your isocpp.org username and password (stored locally in `~/.paperworks/config.json`)

Then click **Log In** in the top bar to connect to isocpp.org.

## Configuration

Settings are stored in `~/.paperworks/config.json`:

- `watch_dirs` - list of directories to scan for markdown papers
- `output_dir` - where rendered PDFs are written
- `render_output_dir` - where Render tab preview PDFs are written (falls back to temp dir)
- `style` - render style name (default: `wg21`)
- `auto_render` - automatically render stale PDFs when markdown files change (default: `true`)
- `port` - server port (default: `7780`)
- `isocpp_username` - isocpp.org login
- `isocpp_password` - isocpp.org password (stored locally, never transmitted except to isocpp.org)

If `~/.scrivener/config.json` exists, Paperworks inherits its
settings as defaults on first run.

## Tabs

### Folio

The main paper inventory. Shows a table of all papers correlated
from three sources: local markdown, rendered PDFs, and isocpp.org.

Each row shows:

- **Document number** (e.g. P4007R1) in monospace
- **MD** button - opens the markdown source in a new tab
- **PDF** button - opens the rendered PDF in a new tab
- **Title**, **Date**, **Status badge**

Click a row to expand its detail panel:

- Document, title, authors, audience
- Markdown and PDF file paths
- Abstract (first sentence of the `## Abstract` section)
- isocpp.org link (if the paper has a remote entry)
- Prior revision buttons (R0, R1, R2, etc.) linking to isocpp.org
- Warnings (e.g. "Missing abstract") in amber
- Action buttons:
  - **RENDER** - queue the paper for PDF rendering
  - **UPLOAD** - push the PDF to isocpp.org and sync all metadata (title, author, abstract)

**Status badges** on each row:

- **render** (blue, clickable) - markdown exists but PDF is missing or stale
- **draft** (amber, clickable) - paper is in draft status on isocpp.org; click to mark for review
- **review** (green, clickable) - paper is in review on isocpp.org; click to revert to draft
- **local** (gray) - has a PDF but no isocpp.org entry
- **orphan** (gray) - has a PDF but no markdown source

Use the filter bar to search by document number, title, or audience.

The **RENDER** button in the header renders all papers that need it.

### Render

One-off preview rendering. A table shows one row per available
style (loaded from Scrivener's style catalog).

Two ways to render:

1. **Drag and drop** - drag a `.md` file from your file explorer
   onto a style row. The file is uploaded to the server, rendered
   in that style, and the PDF opens in a new browser tab.

2. **Browse or type** - use the path input at the top to browse
   for a file or type a path, then click RENDER on the desired
   style row.

Output goes to a temporary directory (not the folio output dir).
This is for quick previews, not the publishing workflow.

### Settings

- **Output Directory** - where the folio render worker writes PDFs
- **Watch Directories** - folders to scan for `.md` files. Each
  can be toggled active/paused and set to recursive. The count
  shows how many `.md` files are in each directory.
- **Render Style** - default style for folio rendering
- **Fonts** - shows cached font status with live previews
- **Images** - shared images available to styles
- **Credentials** - isocpp.org username and password

### Log

Activity log showing all server events: renders, uploads, status
transitions, watchdog events, login/logout, errors.

- Active entries (rendering, uploading) show at full brightness
- Completed entries dim to 50% opacity
- Errors show in red

Click the bottom status bar from any tab to jump to the log.

## Source of Truth

Markdown is authoritative for all paper metadata.

**Priority**: markdown > PDF > isocpp.org

- **Markdown provides**: title, authors, date, audience (from YAML
  front matter), abstract (from the `## Abstract` section in the body)
- **PDF is a fallback**: used only when no markdown exists. Papers
  without markdown show as `orphan` status.
- **isocpp.org provides**: remote status (Draft/Review/Mailed) and
  form URLs. Never used as a metadata source.

D/P prefixes are interchangeable for matching. `D4007R0` and
`P4007R0` refer to the same paper - D is the working draft prefix,
P is the published prefix.

Only the first author from `reply-to` is synced to isocpp.org.

Upload is safe: fields that are empty locally are skipped, never
overwriting good remote data with nothing.

## Architecture

```
paperworks/
  paperworks.py          CLI entry point
  requirements.txt       Python dependencies
  CLAUDE.md              Agent rules (not for humans)
  README.md              This file
  assets/                SVG icons for MD/PDF buttons
  lib/
    server.py            Flask app, SSE, routes, watchdogs, render worker
    server_config.py     ~/.paperworks/config.json management
    inventory.py         Three-source paper correlation
    isocpp.py            IsoCppSession - queued authenticated client
    pdf_reader.py        PDF metadata extraction (PyMuPDF)
    templates/
      index.html         Single-page dashboard (all four tabs)
```

### Three-Source Inventory

`inventory.py` merges data from three sources into a unified
paper list:

1. `scan_markdown_dirs()` - reads YAML front matter and extracts
   the abstract from `## Abstract` sections
2. `scan_pdf_dir()` - reads metadata from rendered PDFs via PyMuPDF
3. Remote papers from isocpp.org (fetched when authenticated)

`build_inventory()` correlates these by document number, applies
the source-of-truth priority, derives status, groups by base
number (keeping only the latest revision), and attaches prior
revision links.

### IsoCpp Queue

`isocpp.py` serializes all mutating operations to isocpp.org
through a single-threaded queue:

- Upload (PDF + metadata sync)
- Draft/Review status transitions

The queue prevents CSRF token conflicts and rate limiting.
A callback fires SSE events for every state change (queued,
started, completed, failed, drained).

### Render Worker

A background thread processes render batches from a queue.
Uses the configured style and output directory. Broadcasts
SSE events per file (starting, completed, failed) and per
batch (render_start, render_done).

The Render tab uses a separate synchronous endpoint
(`/api/render-preview`) that renders to a temp directory
and returns the PDF path immediately.

### Watchdogs

Two file system watchers run in background threads:

- **Markdown watchdog** - watches configured directories for
  `.md` file changes. Debounces (3s) then queues stale files
  for rendering.
- **PDF watchdog** - watches the output directory for PDF
  changes. Broadcasts file_changed events so the UI can
  mark papers as dirty (needing upload).

### SSE (Server-Sent Events)

The UI maintains a persistent connection to `/api/events`.
All state changes are pushed in real time: log entries, job
progress, file changes, render progress. The UI never polls -
it reacts to events.

## Markdown Format

Papers must have YAML front matter:

```yaml
---
title: "Paper Title"
document: P4007R1
date: 2026-04-08
reply-to:
  - "Author Name <email@example.com>"
audience: LEWG
---
```

The `## Abstract` section in the body is parsed for the brutal
summary (first sentence, with markdown links and HTML tags
stripped). Papers without an abstract get a warning in the UI
and log.

## API Reference

All endpoints are on `localhost` at the configured port.

### Pages

- `GET /` - dashboard (single page with all tabs)

### Data

- `GET /api/inventory` - full paper list with summary counts
- `GET /api/config` - current configuration
- `POST /api/config` - update configuration fields
- `GET /api/catalog` - available styles, fonts, images
- `GET /api/auth-status` - authentication state
- `GET /api/log` - activity log entries
- `DELETE /api/log` - clear the log
- `GET /api/queue` - isocpp queue depth and active job

### Actions

- `POST /api/login` - authenticate with isocpp.org
- `POST /api/logout` - end session
- `POST /api/render` - queue a file for rendering (folio workflow)
- `POST /api/render-preview` - synchronous render to temp dir (accepts multipart file upload or JSON path)
- `POST /api/render-all` - queue all stale files for rendering
- `POST /api/upload` - upload PDF and sync metadata to isocpp.org
- `POST /api/transition` - change paper status (draft/review)

### Files and Directories

- `GET /api/file?path=...` - serve a local file (markdown or PDF)
- `POST /api/open-folder` - open a directory in the OS file manager
- `GET /api/pick-dir` - OS directory picker dialog
- `GET /api/pick-file` - OS file picker dialog (.md filter)
- `POST /api/shutdown` - stop the server

### Watch Directories

- `POST /api/dirs` - add a watch directory
- `DELETE /api/dirs` - remove a watch directory
- `POST /api/dirs/toggle` - toggle enabled/recursive on a directory

### Live Updates

- `GET /api/events` - SSE stream (events: connected, log, job, file_changed, render_start, rendered, render_done)
