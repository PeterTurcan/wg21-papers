# Paperworks UI Operations Audit

Every interactive element in the UI, what it does, whether it
goes through the queue, and its current working-state compliance.

Legend:
- **Queue**: goes through IsoCppSession queue or render worker
- **Instant**: completes immediately, no working state needed
- **Compliant**: follows the button UX rules in CLAUDE.md
- **Non-compliant**: needs the working state pattern added

---

## Top Bar

### Tab Buttons (Papers, Settings, Log)
- **Action**: switches visible tab panel
- **Type**: instant
- **Backend**: none (pure JS show/hide)
- **Compliant**: yes (no working state needed)

### LOG IN
- **Action**: authenticates with isocpp.org using saved credentials
- **Type**: queue-like (blocks on HTTP request to isocpp.org)
- **Backend**: POST /api/login -> IsoCppSession.login()
- **SSE event**: none (login is synchronous, not queued)
- **Exit working state**: when fetch response returns
- **Compliant**: partially - has working class and disabled state,
  but login is not queued through IsoCppSession.submit(), it calls
  login() directly which acquires the lock. No SSE event on completion.
- **Log**: yes - "Logging in..." and "Authenticated as ..."

### LOG OUT
- **Action**: clears isocpp.org session
- **Type**: instant
- **Backend**: POST /api/logout -> IsoCppSession.logout()
- **Compliant**: yes (instant, no working state needed)
- **Log**: yes - "Logged out"

### SHUT DOWN (X button)
- **Action**: kills the server process
- **Type**: instant (one-way, no recovery)
- **Backend**: POST /api/shutdown -> os.kill(SIGTERM)
- **Compliant**: yes (no working state needed)
- **Log**: no (server dies immediately)

---

## Papers Tab

### Summary Pills
- **Action**: display only, no interaction
- **Type**: n/a

### RENDER N (header button)
- **Action**: queues all stale markdown files for rendering
- **Type**: queue (render worker)
- **Backend**: POST /api/render-all -> _render_queue.put(batch)
- **SSE events**: render_start, rendered (per file), render_done
- **Exit working state**: render_done SSE event
- **Compliant**: partially - has disabled + glow animation on press,
  re-enables on render_done. But the button itself uses custom JS
  (_rendering flag), not the standard badge-working pattern.
- **Log**: yes - "Rendering N files...", per-file "Starting...",
  per-file success/fail, "Rendered N files"

### SYNC N (header button)
- **Action**: for each paper: render if stale, upload if dirty,
  sync meta if title/abstract differs
- **Type**: queue (both render worker and IsoCppSession)
- **Backend**: mixed - calls renderPaper(), submitUpload(),
  submitSyncMeta() per paper
- **SSE events**: rendered, job_queued/started/completed/failed,
  queue_drained
- **Exit working state**: per-paper via SSE events
- **Compliant**: non-compliant - the Sync button itself has no
  working state. Individual papers get _workingSet treatment but
  the button doesn't disable or glow.
- **Log**: yes (via individual operations)

### Filter Input
- **Action**: filters paper table by text match
- **Type**: instant
- **Backend**: none (pure JS filter)
- **Compliant**: yes (no working state needed)

### Paper Row Click
- **Action**: expands/collapses detail panel
- **Type**: instant
- **Backend**: none (pure JS DOM manipulation)
- **Compliant**: yes (no working state needed)

### MD Icon (per row)
- **Action**: opens markdown file in new browser tab
- **Type**: instant
- **Backend**: GET /api/file?path=... (serves file as text/plain)
- **Compliant**: yes (no working state needed, it's a link)

### PDF Icon (per row)
- **Action**: opens PDF file in new browser tab
- **Type**: instant
- **Backend**: GET /api/file?path=... (serves file as application/pdf)
- **Compliant**: yes (no working state needed, it's a link)

### Status Badge: DRAFT (per row)
- **Action**: transitions paper to Review on isocpp.org
- **Type**: queue (IsoCppSession.submit transition)
- **Backend**: POST /api/transition -> IsoCppSession.submit()
- **SSE events**: job_queued, job_started, job_completed/failed,
  queue_drained
- **Exit working state**: job_completed or job_failed SSE event
  for this doc_number
- **Compliant**: yes - adds to _workingSet, badge shows
  badge-working animation, clears on SSE event, inventory reloads
  on queue_drained
- **Log**: yes - "P4100R0 transition queued", "P4100R0 transition...",
  "P4100R0 -> review"

### Status Badge: REVIEW (per row)
- **Action**: transitions paper to Draft on isocpp.org
- **Type**: queue (IsoCppSession.submit transition)
- **Backend**: POST /api/transition -> IsoCppSession.submit()
- **SSE events**: same as DRAFT
- **Exit working state**: same as DRAFT
- **Compliant**: yes - same pattern as DRAFT
- **Log**: yes

### Status Badge: RENDER (per row)
- **Action**: renders this paper's markdown to PDF
- **Type**: queue (render worker)
- **Backend**: POST /api/render -> _render_queue.put([md_path])
- **SSE events**: rendered (for this file), render_done
- **Exit working state**: rendered SSE event matching this file
- **Compliant**: partially - adds to _workingSet and shows
  badge-working, but the rendered event match uses md_path
  comparison which may not always clear correctly
- **Log**: yes - "Starting ...", "file -> file.pdf (Ns)"

---

## Detail Row (expanded paper)

### RENDER (detail button)
- **Action**: renders this paper's markdown to PDF
- **Type**: queue (render worker)
- **Backend**: POST /api/render -> renderSingle(idx)
- **SSE events**: rendered, render_done
- **Exit working state**: rendered SSE event
- **Compliant**: non-compliant - the detail row button itself does
  not disable or glow. It calls renderSingle which updates
  _workingSet for the badge, but the button in the detail row is
  rebuilt from scratch on each renderPapers() call.
- **Log**: yes

### EDIT ON ISOCPP.ORG (detail link)
- **Action**: opens isocpp.org paper form in new tab
- **Type**: instant (external link)
- **Backend**: none
- **Compliant**: yes (no working state needed)

### UPLOAD PDF (detail button)
- **Action**: uploads local PDF to isocpp.org paper entry,
  syncing title and abstract
- **Type**: queue (IsoCppSession.submit upload)
- **Backend**: POST /api/upload -> IsoCppSession.submit()
- **SSE events**: job_queued, job_started, job_completed/failed,
  queue_drained
- **Exit working state**: job_completed/failed SSE event
- **Compliant**: partially - adds to _workingSet, badge shows
  working. But the detail row button itself doesn't disable.
  Detail row is rebuilt on renderPapers() which may close it.
- **Log**: yes

### SYNC META (detail button)
- **Action**: syncs title/abstract to isocpp.org without uploading PDF
- **Type**: queue (IsoCppSession.submit sync_meta)
- **Backend**: POST /api/sync-meta -> IsoCppSession.submit()
- **SSE events**: job_queued, job_started, job_completed/failed,
  queue_drained
- **Exit working state**: job_completed/failed SSE event
- **Compliant**: partially - same issues as UPLOAD PDF
- **Log**: yes

---

## Log Tab

### CLEAR
- **Action**: clears all log entries
- **Type**: instant
- **Backend**: DELETE /api/log
- **Compliant**: yes (no working state needed)
- **Log**: clears itself

---

## Settings Tab

### Output Directory: BROWSE
- **Action**: opens native folder picker dialog
- **Type**: instant (blocks on tkinter dialog)
- **Backend**: GET /api/pick-dir
- **Compliant**: yes (no working state needed)

### Output Directory: SAVE
- **Action**: saves output directory path to config
- **Type**: instant
- **Backend**: POST /api/config
- **Compliant**: yes (no working state needed)
- **Log**: yes - "Updated: output_dir"

### Output Directory: OPEN
- **Action**: opens directory in OS file explorer
- **Type**: instant
- **Backend**: POST /api/open-folder
- **Compliant**: yes (no working state needed)

### Watch Dirs: BROWSE
- **Action**: opens native folder picker dialog
- **Type**: instant
- **Backend**: GET /api/pick-dir
- **Compliant**: yes

### Watch Dirs: ADD
- **Action**: adds a directory to watch list
- **Type**: instant
- **Backend**: POST /api/dirs
- **Compliant**: yes
- **Log**: yes - "Updated: paper_dir"

### Watch Dirs: ACTIVE/PAUSED badge (per dir)
- **Action**: toggles directory enabled/disabled
- **Type**: instant
- **Backend**: POST /api/dirs/toggle
- **Compliant**: yes (no working state needed)

### Watch Dirs: recursive checkbox (per dir)
- **Action**: toggles recursive scanning
- **Type**: instant
- **Backend**: POST /api/dirs/toggle
- **Compliant**: yes

### Watch Dirs: X remove (per dir)
- **Action**: removes directory from watch list
- **Type**: instant
- **Backend**: DELETE /api/dirs
- **Compliant**: yes

### Style Dropdown
- **Action**: changes render style
- **Type**: instant
- **Backend**: POST /api/config
- **Compliant**: yes
- **Log**: yes - "Updated: style"

### Credentials: SAVE
- **Action**: saves username/password to config
- **Type**: instant
- **Backend**: POST /api/config
- **Compliant**: yes
- **Log**: yes - "Updated: username, password"

---

## Compliance Status (Updated)

All queued-action buttons now use the unified `startWork`/`endWork`
pattern. The `submitJob` function handles all IsoCppSession
submissions. The `.btn.working` and `.badge-working` CSS classes
provide consistent glow animation.

All buttons: COMPLIANT

- LOG IN: startWork/endWork on fetch lifecycle
- RENDER N: startWork/endWork via render_done SSE
- SYNC N: startWork/endWork via queue_drained + render_done SSE
- Draft/Review badges: _workingSet via submitJob, cleared by job SSE
- Render badge: _workingSet via renderSingle, cleared by rendered SSE
- Detail row buttons: disabled+working class driven by _workingSet
- Log entries: completion events dimmed at 50% via .la-done class
