"""Tests for paperworks upload endpoint."""

import json
import pathlib
import tempfile
import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, PropertyMock, patch


def _auth(authenticated):
    """Context manager that patches IsoCppSession.authenticated as a property."""
    from lib import server
    return patch.object(type(server._isocpp), "authenticated",
                        new_callable=PropertyMock, return_value=authenticated)


class TestUploadEndpoint(unittest.TestCase):
    """Tests for POST /api/upload."""

    def setUp(self):
        from lib import server
        server.app.config["TESTING"] = True
        self.client = server.app.test_client()
        self._server = server

        self._tmpfile = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        self._tmpfile.write(b"%PDF-1.4 fake")
        self._tmpfile.flush()
        self._pdf_path = self._tmpfile.name

    def tearDown(self):
        self._tmpfile.close()
        pathlib.Path(self._pdf_path).unlink(missing_ok=True)

    def _post(self, body):
        return self.client.post(
            "/api/upload",
            data=json.dumps(body),
            content_type="application/json",
        )

    def test_upload_rejected_when_not_authenticated(self):
        """Returns 401 when not logged in to isocpp.org."""
        with _auth(False):
            r = self._post({"form_id": "42", "doc_number": "D1234R0", "path": self._pdf_path})
        self.assertEqual(r.status_code, 401)
        self.assertIn("error", json.loads(r.data))

    def test_upload_rejected_with_missing_form_id(self):
        """Returns 400 when form_id is absent."""
        with _auth(True):
            r = self._post({"doc_number": "D1234R0", "path": self._pdf_path})
        self.assertEqual(r.status_code, 400)
        self.assertIn("error", json.loads(r.data))

    def test_upload_rejected_with_missing_pdf(self):
        """Returns 400 when pdf path does not exist on disk."""
        with _auth(True):
            r = self._post({"form_id": "42", "doc_number": "D1234R0", "path": "/nonexistent/paper.pdf"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("error", json.loads(r.data))

    def test_upload_queues_job_and_returns_job_id(self):
        """Returns 200 with job_id and submits correct fields to the queue."""
        captured = []
        def _capture(j):
            captured.append(j)
            return "test-job-id"
        with _auth(True), \
             patch.object(self._server._isocpp, "submit",
                          side_effect=_capture):
            r = self._post({
                "form_id": "42",
                "doc_number": "D1234R0",
                "path": self._pdf_path,
                "title": "My Paper",
                "author": "A. Author",
                "abstract": "Does stuff.",
            })
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertEqual(data["job_id"], "test-job-id")

        self.assertEqual(len(captured), 1)
        job = captured[0]
        self.assertEqual(job["type"], "upload")
        self.assertEqual(job["form_id"], "42")
        self.assertEqual(job["pdf_path"], self._pdf_path)
        self.assertEqual(job["doc_number"], "D1234R0")
        self.assertEqual(job["title"], "My Paper")
        self.assertEqual(job["author"], "A. Author")
        self.assertEqual(job["abstract"], "Does stuff.")


class TestResolveAudience(unittest.TestCase):
    """Tests for resolve_audience() in lib/isocpp.py."""

    def setUp(self):
        from lib.isocpp import resolve_audience
        self._resolve = resolve_audience

    def test_empty_string_returns_empty(self):
        self.assertEqual(self._resolve(""), [])

    def test_none_equivalent_empty_string(self):
        self.assertEqual(self._resolve(""), [])

    def test_basic_mapping(self):
        result = self._resolve("SG14, EWG")
        self.assertEqual(result, ["SG14 Low Latency", "EWG Evolution"])

    def test_lewg_mapping(self):
        result = self._resolve("SG14, EWG, LEWG")
        self.assertEqual(result, ["SG14 Low Latency", "EWG Evolution", "LEWG Library Evolution"])

    def test_all_of_wg21_exclusivity_clears_others(self):
        """WG21 token displaces all other checked boxes (papers.js fixCheckBoxes rule)."""
        result = self._resolve("SG14, WG21")
        self.assertEqual(result, ["All of WG21"])

    def test_all_token_exclusivity(self):
        result = self._resolve("ALL, EWG, LEWG")
        self.assertEqual(result, ["All of WG21"])

    def test_unknown_token_skipped(self):
        result = self._resolve("SG14, UNKNOWN_GROUP")
        self.assertEqual(result, ["SG14 Low Latency"])

    def test_arg_only_when_explicit(self):
        """ARG ABI Review Group is only included when front matter explicitly says ARG."""
        with_arg = self._resolve("ARG")
        self.assertIn("ARG ABI Review Group", with_arg)
        without_arg = self._resolve("SG14, EWG")
        self.assertNotIn("ARG ABI Review Group", without_arg)

    def test_ewgi_alias(self):
        self.assertEqual(self._resolve("EWGI"), ["EWGI SG17: EWG Incubator"])

    def test_sg17_alias(self):
        self.assertEqual(self._resolve("SG17"), ["EWGI SG17: EWG Incubator"])

    def test_lewgi_alias(self):
        self.assertEqual(self._resolve("LEWGI"), ["LEWGI SG18: LEWG Incubator"])

    def test_case_insensitive(self):
        self.assertEqual(self._resolve("sg14, ewg"), ["SG14 Low Latency", "EWG Evolution"])

    def test_whitespace_tolerance(self):
        self.assertEqual(self._resolve("  SG14 ,  EWG  "), ["SG14 Low Latency", "EWG Evolution"])


if __name__ == "__main__":
    unittest.main()
