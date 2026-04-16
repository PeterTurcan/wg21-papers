"""Paperworks - unified Flask server for paper management."""

import importlib.util
import json
import logging
import os
import queue
import subprocess
import sys
import time
import threading
from pathlib import Path

_log = logging.getLogger(__name__)

import yaml
from flask import Flask, Response, jsonify, render_template, request, send_file

from .server_config import load_config, save_config
from .inventory import build_inventory, compute_summary
from .isocpp import IsoCppSession

SCRIVENER_ROOT = Path(__file__).parent.parent.parent / "scrivener"

_scrivener_loaded = False

def _ensure_scrivener():
    """Make scrivener importable as 'scrivener_lib' package."""
    global _scrivener_loaded
    if _scrivener_loaded:
        return
    scr_parent = str(SCRIVENER_ROOT.parent)
    if scr_parent not in sys.path:
        sys.path.insert(0, scr_parent)
    if "scrivener_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            "scrivener_lib",
            str(SCRIVENER_ROOT / "lib" / "__init__.py"),
            submodule_search_locations=[str(SCRIVENER_ROOT / "lib")],
        )
        pkg = importlib.util.module_from_spec(spec)
        sys.modules["scrivener_lib"] = pkg
        spec.loader.exec_module(pkg)
    _scrivener_loaded = True

app = Flask(__name__, template_folder="templates")
app.config["JSON_SORT_KEYS"] = False
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

@app.after_request
def add_no_cache(response):
    if 'text/html' in response.content_type:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# -- SSE --
_sse_queues: list[queue.Queue] = []
_sse_lock = threading.Lock()

# -- Activity log --
_activity_log: list[dict] = []
_log_lock = threading.Lock()
MAX_LOG = 200

# -- Render state --
_render_queue: queue.Queue = queue.Queue()
_preview_lock = threading.Lock()
_md_pending: set[str] = set()
_md_pending_lock = threading.Lock()
_md_debounce_timer: threading.Timer | None = None
MD_DEBOUNCE = 3

# -- PDF watchdog state --
_pdf_pending: dict[str, float] = {}
_pdf_pending_lock = threading.Lock()
_pdf_debounce_timer: threading.Timer | None = None
PDF_DEBOUNCE = 2

_md_observer = None
_pdf_observer = None

_logged_warnings: set[str] = set()


def _output_pdf_path(md_path, out_dir):
    """Canonical PDF output path for a markdown source."""
    return Path(out_dir) / Path(md_path).with_suffix(".pdf").name


def _broadcast(event: str, data: dict):
    msg = f"event: {event}\ndata: {json.dumps(data)}\n\n"
    with _sse_lock:
        for q in _sse_queues:
            q.put(msg)


def _add_log(action, detail, status="ok"):
    entry = {
        "time": time.strftime("%H:%M:%S"),
        "action": action,
        "detail": detail,
        "status": status,
    }
    with _log_lock:
        _activity_log.append(entry)
        while len(_activity_log) > MAX_LOG:
            _activity_log.pop(0)
    _broadcast("log", entry)


# -- IsoCpp session with event bridge --

def _on_isocpp_event(event):
    evt = event.get("event", "")
    doc = event.get("doc_number", "")
    job_type = event.get("type", "")
    _broadcast("job", event)
    if evt == "job_queued":
        _add_log("queue", f"{doc} {job_type} queued (depth: {event.get('queue_depth', '?')})")
    elif evt == "job_started":
        _add_log("working", f"{doc} {job_type}...", status="working")
    elif evt == "job_completed":
        _add_log(job_type, f"{doc} {event.get('message', 'done')}", status="done")
    elif evt == "job_failed":
        _add_log(job_type, f"{doc} failed: {event.get('error', '?')}", status="error")
    elif evt == "queue_drained":
        _add_log("queue", "All jobs complete", status="done")

_isocpp = IsoCppSession(on_event=_on_isocpp_event)


def _load_style(style_id):
    """Load a scrivener style by ID. Ensures scrivener is importable."""
    _ensure_scrivener()
    from scrivener_lib.config import load_style, resolve_style_path
    return load_style(resolve_style_path(style_id))


# -- Render worker (from scrivener) --

def _render_worker():
    while True:
        batch = _render_queue.get()
        cfg = load_config()
        style_name = cfg.get("style", "default")
        out_dir_str = cfg.get("output_dir", "")
        if not out_dir_str:
            _add_log("render", "Output directory not configured", status="error")
            _broadcast("render_done", {"total": len(batch), "done": 0, "errors": len(batch)})
            continue
        out_dir = Path(out_dir_str)
        if not out_dir.is_dir():
            _add_log("render", f"Output directory not found: {out_dir_str}", status="error")
            _broadcast("render_done", {"total": len(batch), "done": 0, "errors": len(batch)})
            continue

        try:
            _ensure_scrivener()
            from scrivener_lib.builder import build_pdf
            style = _load_style(style_name)
        except Exception as e:
            _add_log("render", f"Scrivener init failed: {e}", status="error")
            _broadcast("render_done", {"total": len(batch), "done": 0, "errors": len(batch)})
            continue

        total = len(batch)
        _broadcast("render_start", {"total": total})
        _add_log("render", f"Rendering {total} file{'s' if total != 1 else ''}...")

        done = 0
        errors = 0
        for md_path in batch:
            out_file = _output_pdf_path(md_path, out_dir)
            fname = Path(md_path).name
            _add_log("render", f"Starting {fname}...", status="working")
            _broadcast("rendered", {
                "file": md_path, "status": "starting",
                "done": done, "total": total,
            })
            t0 = time.time()
            try:
                with _preview_lock:
                    build_pdf(md_path, out_file, {}, style)
                duration = round(time.time() - t0, 2)
                done += 1
                fname = Path(md_path).name
                _add_log("render", f"{fname} -> {out_file.name} ({duration}s)", status="done")
                _broadcast("rendered", {
                    "file": md_path, "pdf": str(out_file),
                    "status": "ok", "duration": duration,
                    "done": done, "total": total,
                })
            except Exception as e:
                import traceback
                errors += 1
                done += 1
                err_msg = str(e)
                tb = traceback.format_exc()
                _add_log("render", f"{Path(md_path).name} FAILED: {err_msg}", status="error")
                _add_log("render", tb.strip().split('\n')[-1], status="error")
                _broadcast("rendered", {
                    "file": md_path, "status": "error",
                    "error": err_msg, "done": done, "total": total,
                })

        _broadcast("render_done", {"total": total, "done": done, "errors": errors})


# -- Markdown watchdog --

def _flush_md_pending():
    global _md_debounce_timer
    _md_debounce_timer = None
    with _md_pending_lock:
        candidates = list(_md_pending)
        _md_pending.clear()
    if not candidates:
        return
    cfg = load_config()
    if not cfg.get("auto_render", True):
        return
    out_dir = cfg.get("output_dir", "")
    if not out_dir:
        _add_log("render", "Output directory not configured; skipping auto-render", status="error")
        return
    out_path = Path(out_dir)
    batch = []
    for md_path in candidates:
        try:
            if out_path.is_dir():
                pdf = _output_pdf_path(md_path, out_path)
                if pdf.is_file() and pdf.stat().st_mtime >= Path(md_path).stat().st_mtime:
                    continue
        except OSError:
            continue
        batch.append(md_path)
    if batch:
        _render_queue.put(batch)
        _add_log("watch", f"{len(batch)} markdown file{'s' if len(batch) != 1 else ''} need render")


def _on_md_changed(path: str):
    global _md_debounce_timer
    with _md_pending_lock:
        _md_pending.add(path)
    if _md_debounce_timer is not None:
        _md_debounce_timer.cancel()
    _md_debounce_timer = threading.Timer(MD_DEBOUNCE, _flush_md_pending)
    _md_debounce_timer.daemon = True
    _md_debounce_timer.start()


def _start_md_watchdog(watch_dirs):
    global _md_observer
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        return

    class MDHandler(FileSystemEventHandler):
        def _handle(self, event):
            if not event.is_directory and event.src_path.endswith(".md"):
                _on_md_changed(str(Path(event.src_path).resolve()))
        def on_modified(self, e): self._handle(e)
        def on_created(self, e): self._handle(e)

    if _md_observer:
        _md_observer.stop()
        _md_observer.join(timeout=2)

    _md_observer = Observer()
    count = 0
    for entry in watch_dirs:
        if entry.get("enabled", True) and Path(entry["path"]).is_dir():
            _md_observer.schedule(MDHandler(), entry["path"],
                                  recursive=entry.get("recursive", False))
            count += 1
    _md_observer.start()
    if count:
        print(f"  watching {count} markdown dir{'s' if count != 1 else ''}")


# -- PDF watchdog --

def _flush_pdf_pending():
    global _pdf_debounce_timer
    _pdf_debounce_timer = None
    with _pdf_pending_lock:
        changed = list(_pdf_pending.keys())
        _pdf_pending.clear()
    for filepath in changed:
        fname = Path(filepath).name
        _broadcast("file_changed", {"path": filepath, "filename": fname})
        _add_log("watch", f"PDF changed: {fname}")


def _on_pdf_changed(path: str):
    global _pdf_debounce_timer
    with _pdf_pending_lock:
        _pdf_pending[path] = time.time()
        already_scheduled = _pdf_debounce_timer is not None and _pdf_debounce_timer.is_alive()
    if not already_scheduled:
        _pdf_debounce_timer = threading.Timer(PDF_DEBOUNCE, _flush_pdf_pending)
        _pdf_debounce_timer.daemon = True
        _pdf_debounce_timer.start()


def _start_pdf_watchdog(output_dir):
    global _pdf_observer
    if not output_dir or not Path(output_dir).is_dir():
        return
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        return

    class PDFHandler(FileSystemEventHandler):
        def _handle(self, event):
            if not event.is_directory and event.src_path.endswith(".pdf"):
                _on_pdf_changed(str(Path(event.src_path).resolve()))
        def on_modified(self, e): self._handle(e)
        def on_created(self, e): self._handle(e)
        def on_deleted(self, e): self._handle(e)

    if _pdf_observer:
        _pdf_observer.stop()
        _pdf_observer.join(timeout=2)

    _pdf_observer = Observer()
    _pdf_observer.schedule(PDFHandler(), output_dir, recursive=False)
    _pdf_observer.start()
    print(f"  watching PDF dir: {output_dir}")


# -- Helpers --

def _dir_info(entry):
    path = entry["path"]
    exists = Path(path).is_dir()
    recursive = entry.get("recursive", False)
    count = 0
    if exists:
        try:
            p = Path(path)
            if recursive:
                count = sum(1 for f in p.rglob("*.md") if f.is_file())
            else:
                count = sum(1 for f in p.iterdir() if f.is_file() and f.suffix == ".md")
        except Exception:
            _log.debug("Error counting .md in %s", path, exc_info=True)
    return {
        "path": path, "recursive": recursive,
        "enabled": entry.get("enabled", True),
        "exists": exists, "md_count": count,
    }


# -- Routes: Pages --

@app.route("/")
def dashboard():
    return render_template("index.html")

# -- Routes: SSE --

@app.route("/api/events")
def sse():
    q: queue.Queue = queue.Queue()
    with _sse_lock:
        _sse_queues.append(q)
    def stream():
        try:
            yield "event: connected\ndata: {}\n\n"
            while True:
                try:
                    msg = q.get(timeout=20)
                    yield msg
                except queue.Empty:
                    yield ": keepalive\n\n"
        finally:
            with _sse_lock:
                if q in _sse_queues:
                    _sse_queues.remove(q)
    return Response(stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                             "X-Accel-Buffering": "no"})


# -- Routes: Config --

@app.route("/api/config", methods=["GET"])
def get_config():
    cfg = load_config()
    return jsonify({
        "watch_dirs": [_dir_info(d) for d in cfg.get("watch_dirs", [])],
        "output_dir": cfg.get("output_dir", ""),
        "render_output_dir": cfg.get("render_output_dir", ""),
        "style": cfg.get("style", "default"),
        "render_style": cfg.get("render_style", "default"),
        "auto_render": cfg.get("auto_render", True),
        "port": cfg.get("port", 7780),
        "isocpp_username": cfg.get("isocpp_username", ""),
        "has_password": bool(cfg.get("isocpp_password", "")),
    })

@app.route("/api/config", methods=["POST"])
def update_config():
    data = request.get_json(force=True) or {}
    cfg = load_config()
    changed = []
    for key in ("output_dir", "render_output_dir", "style", "render_style", "auto_render", "isocpp_username", "isocpp_password"):
        if key in data:
            cfg[key] = data[key]
            changed.append(key.replace("isocpp_", ""))
    if "port" in data:
        try:
            cfg["port"] = int(data["port"])
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid port number"}), 400
        changed.append("port")
    save_config(cfg)
    if "output_dir" in data:
        _start_pdf_watchdog(data["output_dir"])
    _add_log("config", f"Updated: {', '.join(changed)}")
    return jsonify({"ok": True})


# -- Routes: Watch dirs --

@app.route("/api/dirs", methods=["POST"])
def add_dir():
    data = request.get_json(force=True) or {}
    raw = data.get("dir", "").strip()
    if not raw:
        return jsonify({"error": "dir is required"}), 400
    resolved = str(Path(raw).expanduser().resolve())
    if not Path(resolved).is_dir():
        return jsonify({"error": f"not a directory: {resolved}"}), 400
    cfg = load_config()
    if resolved not in [d["path"] for d in cfg["watch_dirs"]]:
        cfg["watch_dirs"].append({"path": resolved, "recursive": False, "enabled": True})
        save_config(cfg)
    _start_md_watchdog(cfg["watch_dirs"])
    return jsonify({"watch_dirs": [_dir_info(d) for d in cfg["watch_dirs"]]})

@app.route("/api/dirs", methods=["DELETE"])
def remove_dir():
    data = request.get_json(force=True) or {}
    raw_dir = (data.get("dir", "") or "").strip()
    if not raw_dir:
        return jsonify({"error": "Missing directory"}), 400
    resolved = str(Path(raw_dir).expanduser().resolve())
    cfg = load_config()
    before = len(cfg["watch_dirs"])
    cfg["watch_dirs"] = [d for d in cfg["watch_dirs"] if d["path"] != resolved]
    if len(cfg["watch_dirs"]) == before:
        return jsonify({"error": "Directory not found"}), 404
    save_config(cfg)
    _start_md_watchdog(cfg["watch_dirs"])
    return jsonify({"watch_dirs": [_dir_info(d) for d in cfg["watch_dirs"]]})

@app.route("/api/dirs/toggle", methods=["POST"])
def toggle_dir():
    data = request.get_json(force=True) or {}
    raw_dir = (data.get("dir", "") or "").strip()
    if not raw_dir:
        return jsonify({"error": "Missing directory"}), 400
    resolved = str(Path(raw_dir).expanduser().resolve())
    field = data.get("field", "enabled")
    if field not in ("enabled", "recursive"):
        return jsonify({"error": f"Invalid field: {field}"}), 400
    value = bool(data.get("value", True))
    cfg = load_config()
    matched = False
    for entry in cfg["watch_dirs"]:
        if entry["path"] == resolved:
            entry[field] = value
            matched = True
            break
    if not matched:
        return jsonify({"error": "Directory not found"}), 404
    save_config(cfg)
    _start_md_watchdog(cfg["watch_dirs"])
    return jsonify({"watch_dirs": [_dir_info(d) for d in cfg["watch_dirs"]]})


# -- Routes: Inventory --

@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    cfg = load_config()
    remote_papers = []
    if _isocpp.authenticated:
        remote_papers, err = _isocpp.fetch_papers()
        if err:
            _add_log("sync", f"Could not fetch remote papers: {err}", status="error")

    papers = build_inventory(
        cfg.get("watch_dirs", []),
        cfg.get("output_dir", ""),
        remote_papers,
    )
    new_warnings = []
    current_keys = set()
    for p in papers:
        for w in p.get("warnings", []):
            key = f"{p['doc_number']}:{w}"
            current_keys.add(key)
            if key not in _logged_warnings:
                new_warnings.append((key, p['doc_number'], w))
    with _log_lock:
        for key, doc, w in new_warnings:
            _logged_warnings.add(key)
        _logged_warnings.intersection_update(current_keys)
    for key, doc, w in new_warnings:
        _add_log("inventory", f"{doc}: {w}", status="error")
    summary = compute_summary(papers)

    return jsonify({
        "papers": papers,
        "summary": summary,
        "authenticated": _isocpp.authenticated,
    })


# -- Routes: Auth --

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(force=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")
    if not username or not password:
        cfg = load_config()
        if not username:
            username = cfg.get("isocpp_username", "")
        if not password:
            password = cfg.get("isocpp_password", "")
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    _add_log("login", f"Logging in as {username}...")
    success, message = _isocpp.login(username, password)
    if success:
        _add_log("login", f"Authenticated as {username}")
    else:
        _add_log("login", f"Login failed: {message}", status="error")
    return jsonify({"success": success, "message": message, **_isocpp.get_status()})

@app.route("/api/logout", methods=["POST"])
def logout():
    _isocpp.logout()
    _add_log("logout", "Logged out")
    return jsonify({"ok": True})

@app.route("/api/auth-status")
def auth_status():
    return jsonify(_isocpp.get_status())


# -- Routes: Queue operations --

def _upload_audience(intent, audience):
    """Return the audience to submit for upload.

    Info papers always target All of WG21 regardless of front matter audience,
    since they inform the room without implying a scheduling request.
    """
    return "WG21" if intent == "info" else audience


@app.route("/api/upload", methods=["POST"])
def upload_paper():
    data = request.get_json(force=True) or {}
    doc_number = data.get("doc_number", "")
    form_id = data.get("form_id", "")
    pdf_path = data.get("path", "")
    if not _isocpp.authenticated:
        return jsonify({"error": "Not authenticated"}), 401
    if not form_id:
        return jsonify({"error": "No form_id"}), 400
    if not pdf_path or not Path(pdf_path).is_file():
        return jsonify({"error": "PDF not found"}), 400

    job_id = _isocpp.submit({
        "type": "upload", "form_id": form_id, "pdf_path": pdf_path,
        "doc_number": doc_number,
        "title": data.get("title", ""),
        "author": data.get("author", ""),
        "abstract": data.get("abstract", ""),
        "status": data.get("status", ""),
        "audience": _upload_audience(data.get("intent", ""), data.get("audience", "")),
    })
    return jsonify({"job_id": job_id})

@app.route("/api/upload-all", methods=["POST"])
def upload_all():
    if not _isocpp.authenticated:
        return jsonify({"error": "Not authenticated"}), 401
    cfg = load_config()
    remote_papers, err = _isocpp.fetch_papers()
    if err:
        return jsonify({"error": f"Could not fetch remote papers: {err}"}), 500
    papers = build_inventory(
        cfg.get("watch_dirs", []),
        cfg.get("output_dir", ""),
        remote_papers,
    )
    queued = 0
    for p in papers:
        if not p.get("pdf_path") or not p.get("remote"):
            continue
        if p.get("status") == "mailed":
            continue
        intent = p.get("intent", "")
        title = p.get("title", "")
        if intent:
            intent_label = {"info": "Info", "ask": "Ask"}.get(intent, intent.capitalize())
            title = f"{intent_label}: {title}"
        _isocpp.submit({
            "type": "upload",
            "form_id": p["remote"]["form_id"],
            "pdf_path": p["pdf_path"],
            "doc_number": p["doc_number"],
            "title": title,
            "author": p.get("primary_author", ""),
            "abstract": p.get("brutal_summary", ""),
            "audience": _upload_audience(p.get("intent", ""), p.get("audience", "")),
        })
        queued += 1
    if not queued:
        return jsonify({"error": "No papers to upload"}), 400
    _add_log("upload", f"Queued {queued} uploads")
    return jsonify({"queued": queued})


@app.route("/api/transition", methods=["POST"])
def transition_paper():
    data = request.get_json(force=True) or {}
    form_id = data.get("form_id", "")
    target = data.get("target", "")
    doc_number = data.get("doc_number", "")
    if not _isocpp.authenticated:
        return jsonify({"error": "Not authenticated"}), 401
    if not form_id:
        return jsonify({"error": "No form_id"}), 400
    if target not in ("draft", "review"):
        return jsonify({"error": "target must be 'draft' or 'review'"}), 400
    job_id = _isocpp.submit({
        "type": "transition", "form_id": form_id,
        "target": target, "doc_number": doc_number,
    })
    return jsonify({"job_id": job_id})


@app.route("/api/render", methods=["POST"])
def render_paper():
    """Queue a single markdown file for rendering."""
    data = request.get_json(force=True) or {}
    md_path = data.get("md_path", "")
    if not md_path or not Path(md_path).is_file():
        return jsonify({"error": "Markdown file not found"}), 400
    cfg = load_config()
    out_dir = cfg.get("output_dir", "")
    if not out_dir or not Path(out_dir).is_dir():
        _add_log("render", "Output directory not configured or missing", status="error")
        _broadcast("rendered", {
            "file": md_path, "status": "error",
            "error": "Output directory not configured or missing",
            "done": 1, "total": 1,
        })
        _broadcast("render_done", {"total": 1, "done": 0, "errors": 1})
        return jsonify({"error": "Output directory not configured or missing"}), 400
    _render_queue.put([md_path])
    _add_log("render", f"Queued: {Path(md_path).name}")
    return jsonify({"ok": True})

@app.route("/api/render-preview", methods=["POST"])
def render_preview():
    """Render a single file synchronously to a temp dir and return the PDF.

    Accepts either:
      - multipart/form-data with a "file" part and optional "style" field
      - JSON body with {"md_path": "...", "style": "..."}
    """
    import shutil
    import tempfile

    cfg = load_config()
    render_dir = cfg.get("render_output_dir", "")
    is_temp_out = False
    if render_dir and Path(render_dir).is_dir():
        out_dir = Path(render_dir)
    else:
        out_dir = Path(tempfile.mkdtemp(prefix="paperworks-preview-"))
        is_temp_out = True

    style_id = "default"
    tmp_dir = None
    ok = False

    try:
        if request.content_type and "multipart" in request.content_type:
            f = request.files.get("file")
            if not f or not f.filename:
                return jsonify({"error": "No file uploaded"}), 400
            style_id = request.form.get("style", "default")
            fname = Path(f.filename).name
            tmp_dir = Path(tempfile.mkdtemp(prefix="paperworks-upload-"))
            md_path = str(tmp_dir / fname)
            f.save(md_path)
        else:
            data = request.get_json(force=True) or {}
            md_path = data.get("md_path", "")
            style_id = data.get("style", "default")
            if not md_path or not Path(md_path).is_file():
                return jsonify({"error": "Markdown file not found"}), 400
            fname = Path(md_path).name

        with _preview_lock:
            try:
                _ensure_scrivener()
                from scrivener_lib.builder import build_pdf
                style = _load_style(style_id)
            except Exception as e:
                _add_log("preview", f"Scrivener init failed: {e}", status="error")
                return jsonify({"error": f"Scrivener init failed: {e}"}), 500

            out_file = _output_pdf_path(fname, out_dir)
            _add_log("preview", f"Rendering {fname} ({style_id})...", status="working")

            try:
                t0 = time.time()
                build_pdf(md_path, str(out_file), {}, style)
                duration = round(time.time() - t0, 2)
                _add_log("preview", f"{fname} -> {out_file.name} ({duration}s)", status="done")
                ok = True
                return jsonify({"ok": True, "pdf_path": str(out_file)})
            except Exception as e:
                _add_log("preview", f"{fname} FAILED: {e}", status="error")
                return jsonify({"error": str(e)}), 500
    finally:
        if tmp_dir and tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)
        if is_temp_out and not ok and out_dir.exists():
            shutil.rmtree(out_dir, ignore_errors=True)

@app.route("/api/render-all", methods=["POST"])
def render_all():
    """Queue markdown files for rendering. Pass force=true to re-render all."""
    force = False
    if request.is_json and request.json:
        force = request.json.get("force", False)
    cfg = load_config()
    output_dir = cfg.get("output_dir", "")
    if not output_dir or not Path(output_dir).is_dir():
        _add_log("render", "Output directory not configured or missing", status="error")
        return jsonify({"error": "Output directory not configured or missing"}), 400
    out_path = Path(output_dir)

    batch = []
    for entry in cfg.get("watch_dirs", []):
        if not entry.get("enabled", True):
            continue
        p = Path(entry["path"])
        if not p.is_dir():
            continue
        mds = p.rglob("*.md") if entry.get("recursive", False) else p.glob("*.md")
        for md in mds:
            if not md.is_file():
                continue
            if not force:
                pdf = _output_pdf_path(md, out_path)
                if pdf.is_file() and pdf.stat().st_mtime >= md.stat().st_mtime:
                    continue
            batch.append(str(md))

    if not batch:
        return jsonify({"error": "All papers are up to date"}), 400
    _render_queue.put(batch)
    return jsonify({"queued": len(batch)})

@app.route("/api/queue")
def get_queue():
    return jsonify({"depth": _isocpp.queue_depth, "active": _isocpp.active_job})


# -- Routes: Log --

@app.route("/api/log", methods=["GET"])
def get_log():
    with _log_lock:
        return jsonify(list(_activity_log))

@app.route("/api/log", methods=["DELETE"])
def clear_log():
    with _log_lock:
        _activity_log.clear()
    return jsonify({"ok": True})


# -- Routes: Scrivener catalog (fonts, images, styles) --

def _scrivener_config():
    """Load scrivener config utilities."""
    _ensure_scrivener()
    from scrivener_lib.config import FONTS_DIR, IMAGES_DIR, MANIFEST_PATH
    from scrivener_lib.catalog import list_images, list_styles
    return {
        "FONTS_DIR": FONTS_DIR,
        "IMAGES_DIR": IMAGES_DIR,
        "MANIFEST_PATH": MANIFEST_PATH,
        "list_images": list_images,
        "list_styles": list_styles,
    }


@app.route("/api/catalog")
def catalog():
    try:
        sc = _scrivener_config()
        styles = sc["list_styles"]()
        images = sc["list_images"]()

        fonts = []
        if sc["MANIFEST_PATH"].exists():
            with open(sc["MANIFEST_PATH"], encoding="utf-8") as f:
                entries = yaml.safe_load(f) or []
            for e in entries:
                fid = e.get("id", "")
                fname = e.get("file", "")
                cached = (sc["FONTS_DIR"] / fname).exists() if fname else False
                font_entry = {"id": fid, "file": fname, "cached": cached}
                preview = e.get("preview")
                if preview:
                    font_entry["preview"] = preview
                fonts.append(font_entry)

        return jsonify({"styles": styles, "images": images, "fonts": fonts})
    except Exception as e:
        return jsonify({"styles": [], "images": [], "fonts": [], "error": str(e)})


def _serve_scrivener_file(dir_key, filename, mimetype=None):
    """Serve a file from a scrivener directory (fonts or images)."""
    try:
        sc = _scrivener_config()
        root = sc[dir_key]
        path = (root / filename).resolve()
    except Exception:
        return jsonify({"error": "scrivener not found"}), 500
    if not path.is_relative_to(root.resolve()):
        return jsonify({"error": "forbidden"}), 403
    if not path.exists() or not path.is_file():
        return jsonify({"error": "not found"}), 404
    return send_file(str(path), mimetype=mimetype) if mimetype else send_file(str(path))

@app.route("/api/font")
def serve_font():
    filename = request.args.get("f", "")
    if not filename:
        return jsonify({"error": "f param required"}), 400
    return _serve_scrivener_file("FONTS_DIR", filename, mimetype="font/ttf")

@app.route("/api/image/<path:filename>")
def serve_image(filename):
    return _serve_scrivener_file("IMAGES_DIR", filename)


# -- Routes: Utility --

_tk_lock = threading.Lock()

def _pick_path(dialog_fn, **kwargs):
    """Show a tkinter file/directory picker and return the resolved path."""
    import tkinter as tk
    from tkinter import filedialog
    with _tk_lock:
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", True)
        try:
            path = dialog_fn(**kwargs)
        finally:
            root.destroy()
    return str(Path(path).resolve()) if path else None

@app.route("/api/pick-dir")
def pick_dir():
    try:
        from tkinter import filedialog
        path = _pick_path(filedialog.askdirectory, title="Choose a directory")
        return jsonify({"path": path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/pick-file")
def pick_file():
    try:
        from tkinter import filedialog
        path = _pick_path(filedialog.askopenfilename,
            title="Choose a markdown file",
            filetypes=[("Markdown", "*.md"), ("All files", "*.*")])
        return jsonify({"path": path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/assets/<path:filename>")
def serve_asset(filename):
    assets_dir = (Path(__file__).parent.parent / "assets").resolve()
    path = (assets_dir / filename).resolve()
    if not path.is_relative_to(assets_dir):
        return jsonify({"error": "forbidden"}), 403
    if not path.exists() or not path.is_file():
        return jsonify({"error": "not found"}), 404
    return send_file(str(path))


@app.route("/api/file")
def serve_local_file():
    filepath = request.args.get("path", "")
    if not filepath or not Path(filepath).is_file():
        return jsonify({"error": "File not found"}), 404
    p = Path(filepath).resolve()
    cfg = load_config()
    allowed = []
    for d in cfg.get("watch_dirs", []):
        allowed.append(Path(d["path"]).resolve())
    if cfg.get("output_dir"):
        allowed.append(Path(cfg["output_dir"]).resolve())
    if cfg.get("render_output_dir"):
        allowed.append(Path(cfg["render_output_dir"]).resolve())
    if not any(p.is_relative_to(root) for root in allowed if root.is_dir()):
        return jsonify({"error": "forbidden"}), 403
    if p.suffix.lower() in (".md", ".markdown", ".txt"):
        with open(p, encoding="utf-8") as f:
            content = f.read()
        return Response(content, mimetype="text/plain; charset=utf-8")
    return send_file(str(p))


@app.route("/api/open-folder", methods=["POST"])
def open_folder():
    data = request.get_json(force=True) or {}
    path = data.get("path", "")
    if not path or not Path(path).is_dir():
        return jsonify({"error": "Not a directory"}), 400
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except OSError as e:
        return jsonify({"error": f"Could not open folder: {e}"}), 500
    return jsonify({"ok": True})

@app.route("/api/shutdown", methods=["POST"])
def shutdown():
    def _stop():
        import signal
        time.sleep(0.3)
        os.kill(os.getpid(), signal.SIGTERM)
    threading.Thread(target=_stop, daemon=True).start()
    return jsonify({"ok": True})


# -- Server startup --

def run_server(cfg):
    port = cfg.get("port", 7780)

    t = threading.Thread(target=_render_worker, daemon=True)
    t.start()
    _add_log("startup", "Render worker started")

    _start_md_watchdog(cfg.get("watch_dirs", []))
    _add_log("startup", f"Markdown watchdog started ({len(cfg.get('watch_dirs', []))} dirs)")
    _start_pdf_watchdog(cfg.get("output_dir", ""))
    _add_log("startup", f"PDF watchdog started ({cfg.get('output_dir', '')})")

    print(f"Paperworks running at http://localhost:{port}")
    print("Press Ctrl+C to stop.")
    app.run(host="127.0.0.1", port=port, threaded=True, use_reloader=False)
