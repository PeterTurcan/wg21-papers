"""Authenticated session with isocpp.org for paper management.

All mutating operations (upload, transition) go through an internal
queue processed by a single worker thread. This serializes requests
to isocpp.org which shares CSRF tokens across a single session.

Consumers receive progress via a single on_event callback.
"""

import queue
import re
import threading
import uuid

import requests
from bs4 import BeautifulSoup

LOGIN_URL = "https://isocpp.org/member/login"
PAPERS_URL = "https://isocpp.org/papers"
BASE_URL = "https://isocpp.org"


class IsoCppSession:
    """Manages an authenticated, queue-serialized session with isocpp.org.

    Args:
        on_event: callback(dict) invoked for every queue state change.
            Events: job_queued, job_started, job_completed, job_failed,
            queue_drained. All events include job_id, doc_number, type.
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
                login_page = self._session.get(LOGIN_URL, timeout=15)
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
                r = self._session.post(action, data=fields, timeout=15,
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
                return [], "Not authenticated"

            try:
                r = self._session.get(PAPERS_URL, timeout=15)
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

            with self._pending_lock:
                if job_id not in self._pending:
                    continue

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
            pass

    # -- Internal executors (run inside worker thread, hold session lock) --

    def _read_form(self, form_id):
        """Fetch a paper form page and parse its fields.

        Returns (fields_dict, checked_audiences, submit_buttons) or
        (None, None, None) if the form is not found.
        submit_buttons is a list of (name, value) for all submit inputs.
        """
        page = self._session.get(f"{BASE_URL}/papers/form/{form_id}", timeout=15)
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

    def _post_form(self, form_id, fields, checked, files=None, timeout=15):
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
                return False, "Not authenticated"

            form_id = job["form_id"]
            pdf_path = job["pdf_path"]
            title = job.get("title")
            author = job.get("author")
            abstract = job.get("abstract")

            fields, checked, submits = self._read_form(form_id)
            if fields is None:
                return False, "Could not find upload form"

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
                fname = pdf_path.split("/")[-1].split("\\")[-1]
                files = {"document": (fname, f, "application/pdf")}
                r = self._post_form(form_id, fields, checked, files=files, timeout=30)

            if r.status_code < 400:
                extra = f" (synced {', '.join(synced)})" if synced else ""
                warn = ", no save button found on form" if no_btn else ""
                return True, f"uploaded{extra}{warn}"
            return False, f"status {r.status_code}"

    def _do_transition(self, job):
        with self._lock:
            if not self._authenticated:
                return False, "Not authenticated"

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

