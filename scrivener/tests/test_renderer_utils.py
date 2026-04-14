"""Layer 1: Unit tests for ASTRenderer static/utility methods."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle

from lib.renderer import ASTRenderer


# -- _nobr_numbers --

def test_nobr_numbers_basic():
    assert ASTRenderer._nobr_numbers("foo 42 bar") == "foo <nobr>42</nobr> bar"


def test_nobr_numbers_with_comma():
    result = ASTRenderer._nobr_numbers("count: 1,234")
    assert "<nobr>1,234</nobr>" in result


def test_nobr_numbers_preserves_tags():
    text = '<font color="#123">42</font>'
    result = ASTRenderer._nobr_numbers(text)
    assert '<font color="#123">' in result
    assert "<nobr>42</nobr>" in result


def test_nobr_numbers_no_numbers():
    text = "hello world"
    assert ASTRenderer._nobr_numbers(text) == text


def test_nobr_numbers_range():
    result = ASTRenderer._nobr_numbers("pages 10-20")
    assert "<nobr>10-20</nobr>" in result


# -- _only_text (instance method, tested via unbound call with self=None) --

class _Dummy:
    """Minimal stand-in so _only_text can be called as unbound."""
    pass


def _only_text(tok):
    """Call _only_text as an unbound method."""
    return ASTRenderer._only_text(_Dummy(), tok)


def test_only_text_single():
    tok = {"children": [{"type": "text", "raw": "hello"}]}
    assert _only_text(tok) == "hello"


def test_only_text_single_text_key():
    tok = {"children": [{"type": "text", "text": "hello"}]}
    assert _only_text(tok) == "hello"


def test_only_text_multiple():
    tok = {"children": [
        {"type": "text", "raw": "a"},
        {"type": "emphasis", "children": []},
    ]}
    assert _only_text(tok) == ""


def test_only_text_no_children():
    tok = {}
    assert _only_text(tok) == ""


def test_only_text_empty_children():
    tok = {"children": []}
    assert _only_text(tok) == ""


# -- _propagate_keep --

def test_propagate_keep_through_spacer():
    ps = ParagraphStyle("test", fontSize=10, leading=12)
    heading = Paragraph("Title", ps)
    heading.keepWithNext = True
    spacer = Spacer(1, 10)
    body = Paragraph("Content", ps)

    flows = [heading, spacer, body]
    ASTRenderer._propagate_keep(flows)
    assert spacer.keepWithNext is True


def test_propagate_keep_no_keep():
    ps = ParagraphStyle("test", fontSize=10, leading=12)
    p1 = Paragraph("A", ps)
    spacer = Spacer(1, 10)
    p2 = Paragraph("B", ps)

    flows = [p1, spacer, p2]
    ASTRenderer._propagate_keep(flows)
    assert not getattr(spacer, "keepWithNext", False)


def test_propagate_keep_non_spacer():
    ps = ParagraphStyle("test", fontSize=10, leading=12)
    p1 = Paragraph("A", ps)
    p1.keepWithNext = True
    p2 = Paragraph("B", ps)

    flows = [p1, p2]
    ASTRenderer._propagate_keep(flows)
    assert not getattr(p2, "keepWithNext", False)
