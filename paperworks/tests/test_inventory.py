"""Tests for inventory.build_inventory merge logic."""

import unittest
from unittest.mock import patch


def _md(doc, title="Test", rev=0, base="P9999"):
    return {
        "doc_number": doc, "base": base, "revision": rev,
        "title": title, "authors": "A", "date": "2026-01-01",
        "audience": "LEWG", "intent": "ask", "brutal_summary": "Test.",
        "md_path": f"/src/{doc.lower()}.md", "md_mtime": 1000.0,
        "folder_idx": 1,
    }


def _pdf(doc, rev=0, base="P9999"):
    return {
        "doc_number": doc, "base": base, "revision": rev,
        "title": "", "authors": "", "date": "", "audience": "",
        "brutal_summary": None,
        "pdf_path": f"/out/{doc.lower()}.pdf", "pdf_mtime": 2000.0,
    }


class TestBuildInventory(unittest.TestCase):

    def _build(self, md_papers, pdf_papers, remote_papers=None):
        with patch("lib.inventory.scan_markdown_dirs", return_value=md_papers), \
             patch("lib.inventory.scan_pdf_dir", return_value=pdf_papers):
            from lib.inventory import build_inventory
            return build_inventory([], "/out", remote_papers)

    def _find(self, papers, base):
        return next((p for p in papers if p["base"] == base), None)

    def test_pdf_matches_markdown_at_r0(self):
        """Baseline: R0 markdown + R0-keyed PDF merge correctly."""
        md = {"D4035R0": _md("D4035R0", rev=0, base="P4035")}
        pdf = {"D4035R0": _pdf("D4035R0", rev=0, base="P4035")}
        result = self._build(md, pdf)
        p = self._find(result, "P4035")
        self.assertIsNotNone(p)
        self.assertIsNotNone(p["md_path"])
        self.assertIsNotNone(p["pdf_path"])

    def test_pdf_matches_markdown_at_r2(self):
        """The bug: filename-derived R0 PDF must match R2 markdown."""
        md = {"P4003R2": _md("P4003R2", rev=2, base="P4003")}
        # PDF keyed as R0 (filename fallback: d4003-io-awaitables.pdf -> D4003 -> R0)
        pdf = {"D4003R0": _pdf("D4003R0", rev=0, base="P4003")}
        result = self._build(md, pdf)
        p = self._find(result, "P4003")
        self.assertIsNotNone(p)
        self.assertEqual(p["revision"], 2)
        self.assertIsNotNone(p["md_path"])
        self.assertIsNotNone(p["pdf_path"])

    def test_orphan_pdf_still_appears(self):
        """PDF with no markdown or remote is still in the inventory."""
        pdf = {"D4099R0": _pdf("D4099R0", rev=0, base="P4099")}
        result = self._build({}, pdf)
        p = self._find(result, "P4099")
        self.assertIsNotNone(p)
        self.assertIsNotNone(p["pdf_path"])
        self.assertIsNone(p["md_path"])

    def test_pdf_plus_remote_at_non_r0(self):
        """PDF matched by base when remote provides the authoritative revision."""
        pdf = {"D4007R0": _pdf("D4007R0", rev=0, base="P4007")}
        remote = [{"doc_number": "P4007R2", "title": "Open Issues",
                    "author": "A", "status": "Draft", "date": "2026-04-08",
                    "form_id": "99", "form_url": "https://isocpp.org/papers/form/99"}]
        result = self._build({}, pdf, remote)
        p = self._find(result, "P4007")
        self.assertIsNotNone(p)
        self.assertEqual(p["revision"], 2)
        self.assertIsNotNone(p["pdf_path"])


if __name__ == "__main__":
    unittest.main()
