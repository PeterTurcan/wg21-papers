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


# -- _resolve_fallback --

def _make_renderer(body_cmap=None, fallback_chain=None):
    """Minimal ASTRenderer with synthetic cmap data (no font registration)."""
    style = {
        "body_size": 10, "line_height": 1.85,
        "code_fg": "#333", "blockquote_fg": "#4a4a4a",
        "front_matter_label_color": "#888",
        "link_color": "#a91c21", "heading_rule_color": "#e0ddd8",
        "code_block": {"font_scale": 0.82, "leading_scale": 1.55,
                       "bar_width": 3, "left_padding": 15,
                       "right_padding": 15, "vertical_padding": 15},
        "page_size": "a4", "page_number_color": "#888",
    }
    r = object.__new__(ASTRenderer)
    r.body_cmap = body_cmap or set()
    r.fallback_chain = fallback_chain or []
    return r


def test_resolve_fallback_cjk():
    chain = [("CJK", {0x2713, 0x26A0}), ("Emoji", {0x2705, 0x274C})]
    r = _make_renderer(fallback_chain=chain)
    assert r._resolve_fallback(0x2713) == "CJK"


def test_resolve_fallback_emoji():
    chain = [("CJK", {0x2713, 0x26A0}), ("Emoji", {0x2705, 0x274C})]
    r = _make_renderer(fallback_chain=chain)
    assert r._resolve_fallback(0x2705) == "Emoji"


def test_resolve_fallback_none():
    chain = [("CJK", {0x2713}), ("Emoji", {0x2705})]
    r = _make_renderer(fallback_chain=chain)
    assert r._resolve_fallback(0x1F600) is None


def test_resolve_fallback_cjk_first():
    """When both fonts have the glyph, CJK wins (it's first in chain)."""
    chain = [("CJK", {0x26A0}), ("Emoji", {0x26A0})]
    r = _make_renderer(fallback_chain=chain)
    assert r._resolve_fallback(0x26A0) == "CJK"


# -- _inject_fallback_fonts --

def test_inject_fallback_fonts_mixed():
    chain = [("CJK", {0x2713}), ("Emoji", {0x2705})]
    body = set(range(0x20, 0x7F))
    r = _make_renderer(body_cmap=body, fallback_chain=chain)
    text = "ok\u2713\u2705?"
    result = r._inject_fallback_fonts(text)
    assert '<font name="CJK">\u2713</font>' in result
    assert '<font name="Emoji">\u2705</font>' in result
    assert result.startswith("ok")


def test_inject_fallback_fonts_unknown():
    chain = [("CJK", {0x2713})]
    body = set(range(0x20, 0x7F))
    r = _make_renderer(body_cmap=body, fallback_chain=chain)
    result = r._inject_fallback_fonts("x\u274Cy")
    assert "x?y" == result


def test_inject_fallback_fonts_empty_cmap():
    r = _make_renderer(body_cmap=set(), fallback_chain=[])
    assert r._inject_fallback_fonts("hello") == "hello"


# -- _keep_short_before_boxes --

def test_keep_short_before_boxes_one_line():
    ps = ParagraphStyle("body", fontSize=10, leading=18.5)
    para = Paragraph("Short label:", ps)
    spacer = Spacer(1, 5)
    spacer.keepWithNext = True
    box = Spacer(1, 100)

    r = _make_renderer()
    r.style = {"body_size": 10, "line_height": 1.85}
    r.content_width = 468
    from lib.config import PAGE_CONFIGS
    pc = PAGE_CONFIGS["a4"]
    r._page_h = pc["size"][1] - 2 * pc["margin"]

    flows = [para, spacer, box]
    r._keep_short_before_boxes(flows)
    assert getattr(para, "keepWithNext", False) is True


def test_keep_short_before_boxes_multi_line():
    ps = ParagraphStyle("body", fontSize=10, leading=18.5)
    long_text = "This is a much longer paragraph that should wrap to multiple lines " * 5
    para = Paragraph(long_text, ps)
    spacer = Spacer(1, 5)
    spacer.keepWithNext = True
    box = Spacer(1, 100)

    r = _make_renderer()
    r.style = {"body_size": 10, "line_height": 1.85}
    r.content_width = 468
    from lib.config import PAGE_CONFIGS
    pc = PAGE_CONFIGS["a4"]
    r._page_h = pc["size"][1] - 2 * pc["margin"]

    flows = [para, spacer, box]
    r._keep_short_before_boxes(flows)
    assert not getattr(para, "keepWithNext", False)
