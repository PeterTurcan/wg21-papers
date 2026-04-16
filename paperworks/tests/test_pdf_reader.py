"""Tests for pdf_reader._extract_doc_number."""
import unittest

from lib.pdf_reader import _extract_doc_number


class TestExtractDocNumber(unittest.TestCase):
    def test_structured_field_wins(self):
        text = "Document Number: P4096R0\nCoroutine Executors and P2464R0"
        assert _extract_doc_number(text) == "P4096R0"

    def test_title_paper_number_ignored(self):
        """A paper number in the title must not be returned."""
        text = "Coroutine Executors and P2464R0\nSome other content"
        assert _extract_doc_number(text) is None

    def test_no_field_returns_none(self):
        text = "Just some text with no document number field."
        assert _extract_doc_number(text) is None

    def test_case_insensitive_field(self):
        text = "document number: d4007r0\nSome title"
        assert _extract_doc_number(text) == "D4007R0"

    def test_n_paper_structured(self):
        text = "Document Number: N4950\nWorking Draft"
        assert _extract_doc_number(text) == "N4950"

    def test_single_word_document_label(self):
        """Scrivener wg21 style renders 'Document:' not 'Document Number:'."""
        text = "Document: P4003R2\nDate: 2026-04-05"
        assert _extract_doc_number(text) == "P4003R2"

    def test_single_word_document_label_no_revision(self):
        text = "Document: D4035\nDate: 2026-03-20"
        assert _extract_doc_number(text) == "D4035"
