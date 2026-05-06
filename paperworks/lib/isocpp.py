"""Authenticated session with isocpp.org for paper management.

All mutating operations (upload, transition) go through an internal
queue processed by a single worker thread. This serializes requests
to isocpp.org which shares CSRF tokens across a single session.

Consumers receive progress via a single on_event callback.
"""

import logging
import queue
import re
import threading
import uuid

from pathlib import Path as _Path

import requests
from bs4 import BeautifulSoup

_log = logging.getLogger(__name__)

LOGIN_URL = "https://isocpp.org/member/login"
PAPERS_URL = "https://isocpp.org/papers"
BASE_URL = "https://isocpp.org"
DEFAULT_TIMEOUT = 15
UPLOAD_TIMEOUT = 30
_NOT_AUTHENTICATED = "Not authenticated"

_ALL_OF_WG21 = "All of WG21"

# Maps markdown front-matter audience shorthand (uppercased) to the exact
# checkbox values used by the isocpp.org paper submission form.
_AUDIENCE_MAP = {
    "SG1":       "SG1 Concurrency and Parallelism",
    "SG2":       "SG2 Modules",
    "SG4":       "SG4 Networking",
    "SG5":       "SG5 Transactional Memory",
    "SG6":       "SG6 Numerics",
    "SG7":       "SG7 Reflection",
    "SG9":       "SG9 Ranges",
    "SG10":      "SG10 Feature Test",
    "SG12":      "SG12 Undefined and Unspecified Behavior",
    "SG13":      "SG13 I/O",
    "SG14":      "SG14 Low Latency",
    "SG15":      "SG15 Tooling",
    "SG16":      "SG16 Unicode",
    "SG17":      "EWGI SG17: EWG Incubator",
    "EWGI":      "EWGI SG17: EWG Incubator",
    "SG18":      "LEWGI SG18: LEWG Incubator",
    "LEWGI":     "LEWGI SG18: LEWG Incubator",
    "SG19":      "SG19 Machine Learning",
    "SG20":      "SG20 Education",
    "SG21":      "SG21 Contracts",
    "SG22":      "SG22 Compatibility",
    "SG23":      "SG23 Safety and Security",
    "EWG":       "EWG Evolution",
    "LEWG":      "LEWG Library Evolution",
    "CWG":       "CWG Core",
    "LWG":       "LWG Library",
    "WG21":      _ALL_OF_WG21,
    "ALL":       _ALL_OF_WG21,
    "DG":        "Direction Group",
    "DIRECTION": "Direction Group",
    "ARG":       "ARG ABI Review Group",
}


def resolve_audience(audience_str):
    """Map a markdown audience string to remote checkbox values.

    Splits the comma-separated audience_str, maps each token via
    _AUDIENCE_MAP, and enforces the WG21 form exclusivity rule:
    if "All of WG21" is present, all other checkboxes are cleared
    (mirrors fixCheckBoxes() in papers.js).

    Unknown tokens are logged as warnings and skipped.
    Returns a list of remote checkbox value strings.
    """
    if not audience_str:
        return []
    values = []
    for raw in audience_str.split(","):
        token = raw.strip().upper()
        if not token:
            continue
        mapped = _AUDIENCE_MAP.get(token)
        if mapped:
            values.append(mapped)
        else:
            _log.warning("Unknown audience token %r - skipped", token)
    if _ALL_OF_WG21 in values:
        return [_ALL_OF_WG21]
    return values


class IsoCppSession:
    """Manages an authenticated, queue-serialized session with isocpp.org.

    Args:
        on_event: callback(dict) invoked for every queue state change.
            Events: job_queued, job_started, job_completed, job_failed,
            queue_drained. Job-level events include job_id, doc_number,
            type. queue_drained is a queue-level event with only the
            event field.
    """

    def __init__(self, on_event=None):
        self._session = requests.Session()
        self._lock = threading.Lock()
        self._authenticated = False
        self._username = None
        self._on_event = on_event or (lambda e: None)

        self._queue = queue.Queue()
        self._pending = {}
        self._pending_lock = threading.Lock()
        self._active_job = None

        self._worker = threading.Thread(target=self._run_worker, daemon=True)
        self._worker.start()

    # -- Properties --

    @property
    def authenticated(self):
        return self._authenticated

    @property
    def username(self):
        return self._username

    @property
    def queue_depth(self):
        with self._pending_lock:
            return len(self._pending)

    @property
    def active_job(self):
        return self._active_job

    def get_status(self):
        return {
            "authenticated": self._authenticated,
            "username": self._username,
            "queue_depth": self.queue_depth,
            "active_job": self._active_job,
        }

    # -- Immediate operations (lock-serialized, not queued) --

    def login(self, username, password):
        """Log in to isocpp.org. Acquires session lock.

        Returns (success: bool, message: str).
        """
        with self._lock:
            self._authenticated = False
            self._username = None

            try:
                login_page = self._session.get(LOGIN_URL, timeout=DEFAULT_TIMEOUT)
                login_page.raise_for_status()
            except Exception as e:
                return False, f"Failed to reach login page: {e}"

            soup = BeautifulSoup(login_page.text, "html.parser")

            form = None
            for f in soup.find_all("form"):
                if f.find("input", {"type": "password"}):
                    form = f
                    break
            if not form:
                return False, "Could not find login form"

            action = form.get("action", LOGIN_URL)
            if action.startswith("/"):
                action = BASE_URL + action

            fields = {}
            for inp in form.find_all("input"):
                name = inp.get("name")
                if name:
                    fields[name] = inp.get("value", "")

            fields["username"] = username
            fields["password"] = password

            try:
                r = self._session.post(action, data=fields, timeout=DEFAULT_TIMEOUT,
                                       allow_redirects=True)
            except Exception as e:
                return False, f"Login request failed: {e}"

            text = r.text.lower()
            if ("logout" in text or "sign out" in text
                    or "you are now logged in" in text):
                self._authenticated = True
                self._username = username
                return True, "Logged in successfully"

            if "invalid" in text or "incorrect" in text:
                return False, "Invalid username or password"

            return False, "Unexpected response - login may have failed"

    def logout(self):
        with self._lock:
            self._session = requests.Session()
            self._authenticated = False
            self._username = None

    def fetch_papers(self):
        """Fetch the list of your papers from isocpp.org. Acquires session lock.

        Returns (papers: list[dict], error: str or None).
        """
        with self._lock:
            if not self._authenticated:
                return [], _NOT_AUTHENTICATED

            try:
                r = self._session.get(PAPERS_URL, timeout=DEFAULT_TIMEOUT)
                r.raise_for_status()
            except Exception as e:
                return [], str(e)

            soup = BeautifulSoup(r.text, "html.parser")
            table = soup.find("table")
            if not table:
                return [], "No papers table found - login may have expired"

            papers = []
            for row in table.find_all("tr")[1:]:
                cells = row.find_all("td")
                if len(cells) < 5:
                    continue

                link = cells[0].find("a")
                form_url = link.get("href", "") if link else ""
                form_id = ""
                m = re.search(r"/papers/form/(\d+)", form_url)
                if m:
                    form_id = m.group(1)

                papers.append({
                    "doc_number": cells[0].get_text(strip=True),
                    "title": cells[1].get_text(strip=True),
                    "author": cells[2].get_text(strip=True),
                    "status": cells[3].get_text(strip=True),
                    "date": cells[4].get_text(strip=True),
                    "form_id": form_id,
                    "form_url": BASE_URL + form_url if form_url.startswith("/") else form_url,
                })

            return papers, None

    # -- Queued operations --

    def submit(self, job):
        """Submit a job to the queue. Returns job_id immediately.

        Job types:
            {"type": "upload", "form_id": "...", "pdf_path": "...",
             "doc_number": "...", "title": "...", "author": "...",
             "abstract": "..."}
            {"type": "transition", "form_id": "...", "target": "draft|review",
             "doc_number": "..."}
        """
        job_id = str(uuid.uuid4())[:8]
        job = dict(job, job_id=job_id)

        with self._pending_lock:
            self._pending[job_id] = job

        self._emit({
            "event": "job_queued",
            "job_id": job_id,
            "doc_number": job.get("doc_number", ""),
            "type": job.get("type", ""),
            "queue_depth": self.queue_depth,
        })

        self._queue.put(job)
        return job_id

    # -- Worker thread --

    def _run_worker(self):
        while True:
            job = self._queue.get()
            job_id = job["job_id"]
            self._active_job = job
            self._emit({
                "event": "job_started",
                "job_id": job_id,
                "doc_number": job.get("doc_number", ""),
                "type": job.get("type", ""),
            })

            try:
                if job["type"] == "upload":
                    success, message = self._do_upload(job)
                elif job["type"] == "transition":
                    success, message = self._do_transition(job)
                else:
                    success, message = False, f"Unknown job type: {job['type']}"
            except Exception as e:
                success, message = False, str(e)

            with self._pending_lock:
                self._pending.pop(job_id, None)
                drained = len(self._pending) == 0

            self._active_job = None

            event_name = "job_completed" if success else "job_failed"
            payload = {
                "event": event_name,
                "job_id": job_id,
                "doc_number": job.get("doc_number", ""),
                "type": job.get("type", ""),
            }
            if success:
                payload["message"] = message
            else:
                payload["error"] = message
            self._emit(payload)

            if drained:
                self._emit({"event": "queue_drained"})

    def _emit(self, event):
        try:
            self._on_event(event)
        except Exception:
            logging.getLogger(__name__).exception("_emit callback failed")

    # -- Internal executors (run inside worker thread, hold session lock) --

    def _read_form(self, form_id):
        """Fetch a paper form page and parse its fields.

        Returns (fields_dict, checked_audiences, submit_buttons) or
        (None, None, None) if the form is not found.
        submit_buttons is a list of (name, value) for all submit inputs.
        """
        page = self._session.get(f"{BASE_URL}/papers/form/{form_id}", timeout=DEFAULT_TIMEOUT)
        if not page.ok:
            _log.warning("Form %s returned HTTP %d", form_id, page.status_code)
            return None, None, None
        soup = BeautifulSoup(page.text, "html.parser")

        form = None
        for f in soup.find_all("form"):
            if f.find("input", {"name": "document"}):
                form = f
                break
        if not form:
            return None, None, None

        fields = {}
        submits = []
        for inp in form.find_all("input"):
            itype = (inp.get("type") or "").lower()
            if itype == "file":
                continue
            if itype == "submit":
                submits.append((inp.get("name", ""), inp.get("value", "")))
                continue
            name = inp.get("name")
            if not name:
                continue
            if name == "audience[]":
                continue
            fields[name] = inp.get("value", "")

        for ta in form.find_all("textarea"):
            name = ta.get("name")
            if name:
                fields[name] = ta.get_text()

        checked = []
        for inp in form.find_all("input", {"name": "audience[]"}):
            if inp.get("checked"):
                checked.append(inp.get("value", ""))

        return fields, checked, submits

    def _pick_save_button(self, submits):
        """Pick the submit button that saves without changing status.

        Prefers the plain "Save" button (no name, no status transition).
        Falls back to the first available button.
        Returns (name, value) or None.
        """
        for name, value in submits:
            val = value.lower()
            if "save" in val and "draft" not in val and "review" not in val and "delete" not in val:
                return (name, value)
        return submits[0] if submits else None

    def _post_form(self, form_id, fields, checked, files=None, timeout=DEFAULT_TIMEOUT):
        """Post form fields to the form-update endpoint.

        Builds the data list, appends audience checkboxes, and posts.
        Returns the response object.
        """
        url = f"{BASE_URL}/papers/form-update/{form_id}"
        data = list(fields.items())
        for aud in checked:
            data.append(("audience[]", aud))
        if files:
            return self._session.post(url, data=data, files=files, timeout=timeout)
        return self._session.post(url, data=data, timeout=timeout)

    def _do_upload(self, job):
        with self._lock:
            if not self._authenticated:
                return False, _NOT_AUTHENTICATED

            form_id = job["form_id"]
            pdf_path = job["pdf_path"]
            title = job.get("title")
            author = job.get("author")
            abstract = job.get("abstract")

            fields, checked, submits = self._read_form(form_id)
            if fields is None:
                return False, "Could not find upload form"

            audience_str = job.get("audience")
            if audience_str is not None:
                checked = resolve_audience(audience_str)

            synced = []
            if title and fields.get("title") != title:
                fields["title"] = title
                synced.append("title")
            if author and fields.get("author") != author:
                fields["author"] = author
                synced.append("author")
            if abstract and fields.get("abstract") != abstract:
                fields["abstract"] = abstract
                synced.append("abstract")

            save_btn = self._pick_save_button(submits)
            no_btn = False
            if save_btn:
                if save_btn[0]:
                    fields[save_btn[0]] = save_btn[1]
            else:
                no_btn = True

            with open(pdf_path, "rb") as f:
                fname = _Path(pdf_path).name
                files = {"document": (fname, f, "application/pdf")}
                r = self._post_form(form_id, fields, checked, files=files, timeout=UPLOAD_TIMEOUT)

            if r.status_code < 400:
                extra = f" (synced {', '.join(synced)})" if synced else ""
                warn = ", no save button found on form" if no_btn else ""
                return True, f"uploaded{extra}{warn}"
            return False, f"status {r.status_code}"

    def _do_transition(self, job):
        with self._lock:
            if not self._authenticated:
                return False, _NOT_AUTHENTICATED

            form_id = job["form_id"]
            target = job["target"]

            fields, checked, _ = self._read_form(form_id)
            if fields is None:
                return False, "Could not find paper form"

            if target == "review":
                fields["update_status_review"] = "Save and Mark for Review"
            else:
                fields["update_status_review"] = "Save and Revert to Draft"

            r = self._post_form(form_id, fields, checked)

            if r.status_code < 400:
                return True, f"-> {target}"
            return False, f"status {r.status_code}"

