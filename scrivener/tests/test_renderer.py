"""Layer 2: Renderer token tests - ASTRenderer with registered fonts.

Each test constructs a hand-built mistune AST token, feeds it to the
renderer, and asserts on the types/properties of returned flowables.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    PageBreak,
    Paragraph,
    Spacer,
    Table,
    XPreformatted,
)

from lib.flowables import AccentBox, TitleEnd
from lib.renderer import ASTRenderer


@pytest.fixture
def renderer(font_registered, min_style, tmp_path):
    return ASTRenderer(
        min_style, body_cmap={}, fallback_chain=[],
        content_width=468, md_dir=tmp_path, has_fm_title=True)


@pytest.fixture
def renderer_no_fm_title(font_registered, min_style, tmp_path):
    return ASTRenderer(
        min_style, body_cmap={}, fallback_chain=[],
        content_width=468, md_dir=tmp_path, has_fm_title=False)


# -- Block-level rendering --

def test_render_paragraph(renderer):
    tok = {"type": "paragraph", "children": [{"type": "text", "raw": "hello"}]}
    flows = renderer._render_token(tok)
    assert len(flows) == 1
    assert isinstance(flows[0], Paragraph)


def test_render_heading_h2(renderer):
    tok = {
        "type": "heading",
        "attrs": {"level": 2},
        "children": [{"type": "text", "raw": "Section"}],
    }
    flows = renderer._render_token(tok)
    assert any(isinstance(f, Paragraph) for f in flows)
    assert len(renderer.headings) == 1
    level, text, anchor = renderer.headings[0]
    assert level == 2
    assert "Section" in text


def test_render_heading_h1_title(renderer_no_fm_title):
    tok = {
        "type": "heading",
        "attrs": {"level": 1},
        "children": [{"type": "text", "raw": "My Title"}],
    }
    flows = renderer_no_fm_title._render_token(tok)
    assert any(isinstance(f, TitleEnd) for f in flows)


def test_render_heading_registers_all_levels(renderer):
    for level in range(2, 7):
        tok = {
            "type": "heading",
            "attrs": {"level": level},
            "children": [{"type": "text", "raw": f"H{level}"}],
        }
        renderer._render_token(tok)
    assert len(renderer.headings) == 5


def test_render_code_block(renderer):
    tok = {
        "type": "block_code",
        "raw": "x = 42",
        "attrs": {"info": "python"},
    }
    flows = renderer._render_token(tok)
    assert any(isinstance(f, AccentBox) for f in flows)


def test_render_code_block_no_lang(renderer):
    tok = {"type": "block_code", "raw": "plain text", "attrs": {"info": ""}}
    flows = renderer._render_token(tok)
    assert any(isinstance(f, AccentBox) for f in flows)


def test_render_list_unordered(renderer):
    tok = {
        "type": "list",
        "attrs": {"ordered": False},
        "children": [
            {"type": "list_item", "children": [
                {"type": "paragraph", "children": [{"type": "text", "raw": "item"}]}
            ]},
        ],
    }
    flows = renderer._render_token(tok)
    assert len(flows) == 1
    assert isinstance(flows[0], ListFlowable)


def test_render_list_ordered(renderer):
    tok = {
        "type": "list",
        "attrs": {"ordered": True},
        "children": [
            {"type": "list_item", "children": [
                {"type": "paragraph", "children": [{"type": "text", "raw": "first"}]}
            ]},
        ],
    }
    flows = renderer._render_token(tok)
    assert len(flows) == 1
    lf = flows[0]
    assert isinstance(lf, ListFlowable)


def test_render_table(renderer):
    tok = {
        "type": "table",
        "children": [
            {"type": "table_head", "children": [
                {"type": "table_cell", "children": [{"type": "text", "raw": "Col A"}]},
                {"type": "table_cell", "children": [{"type": "text", "raw": "Col B"}]},
            ]},
            {"type": "table_body", "children": [
                {"type": "table_row", "children": [
                    {"type": "table_cell", "children": [{"type": "text", "raw": "1"}]},
                    {"type": "table_cell", "children": [{"type": "text", "raw": "2"}]},
                ]},
            ]},
        ],
    }
    flows = renderer._render_token(tok)
    assert any(isinstance(f, Table) for f in flows)


def test_list_in_blockquote_uses_blockquote_fg(renderer):
    from lib.colors import parse_color
    tok = {
        "type": "list",
        "attrs": {"ordered": True},
        "children": [
            {"type": "list_item", "children": [
                {"type": "paragraph", "children": [{"type": "text", "raw": "item"}]}
            ]},
        ],
    }
    expected = parse_color(renderer.style["blockquote_fg"])
    renderer._bq_fg = expected
    flows = renderer._render_list(tok)
    renderer._bq_fg = None
    para = flows[0]._flowables[0]._flowables[0]
    assert para.style.textColor == expected


def test_blockquote_bq_fg_cleaned_up(renderer):
    tok = {
        "type": "block_quote",
        "children": [
            {"type": "list", "attrs": {"ordered": True}, "children": [
                {"type": "list_item", "children": [
                    {"type": "paragraph", "children": [{"type": "text", "raw": "x"}]}
                ]},
            ]},
        ],
    }
    renderer._render_token(tok)
    assert renderer._bq_fg is None


def test_render_block_quote(renderer):
    tok = {
        "type": "block_quote",
        "children": [
            {"type": "paragraph", "children": [
                {"type": "text", "raw": "quoted text"}
            ]},
        ],
    }
    flows = renderer._render_token(tok)
    assert any(isinstance(f, AccentBox) for f in flows)


def test_render_block_quote_note(renderer):
    tok = {
        "type": "block_quote",
        "children": [
            {"type": "paragraph", "children": [
                {"type": "text", "raw": "[!NOTE] Important info"}
            ]},
        ],
    }
    flows = renderer._render_token(tok)
    boxes = [f for f in flows if isinstance(f, AccentBox)]
    assert len(boxes) == 1


def test_render_thematic_break(renderer):
    tok = {"type": "thematic_break"}
    flows = renderer._render_token(tok)
    assert len(flows) == 1
    assert isinstance(flows[0], HRFlowable)


def test_render_image_missing(renderer):
    tok = {
        "type": "image",
        "attrs": {"src": "nonexistent.png", "alt": ""},
    }
    flows = renderer._render_token(tok)
    assert len(flows) == 1
    assert isinstance(flows[0], Paragraph)


def test_render_newpage(renderer):
    tok = {
        "type": "paragraph",
        "children": [{"type": "text", "raw": "\\newpage"}],
    }
    flows = renderer._render_token(tok)
    assert len(flows) == 1
    assert isinstance(flows[0], PageBreak)


def test_render_blank_line(renderer):
    tok = {"type": "blank_line"}
    flows = renderer._render_token(tok)
    assert flows == []


# -- Wording div via full render() --

def test_render_wording_div(renderer):
    tokens = [
        {"type": "paragraph", "children": [{"type": "text", "raw": ":::wording"}]},
        {"type": "paragraph", "children": [{"type": "text", "raw": "spec text"}]},
        {"type": "paragraph", "children": [{"type": "text", "raw": ":::"}]},
    ]
    flows = renderer.render(tokens)
    assert any(isinstance(f, AccentBox) for f in flows)


def test_render_wording_add_div(renderer):
    tokens = [
        {"type": "paragraph", "children": [{"type": "text", "raw": ":::wording-add"}]},
        {"type": "paragraph", "children": [{"type": "text", "raw": "new text"}]},
        {"type": "paragraph", "children": [{"type": "text", "raw": ":::"}]},
    ]
    flows = renderer.render(tokens)
    assert any(isinstance(f, AccentBox) for f in flows)


# -- Inline rendering --

def test_inline_emphasis(renderer):
    tok = {"type": "emphasis", "children": [{"type": "text", "raw": "em"}]}
    result = renderer._inline(tok)
    assert "<i>" in result and "</i>" in result
    assert "em" in result


def test_inline_strong(renderer):
    tok = {"type": "strong", "children": [{"type": "text", "raw": "bold"}]}
    result = renderer._inline(tok)
    assert "<b>" in result and "</b>" in result


def test_inline_codespan(renderer):
    tok = {"type": "codespan", "raw": "code()"}
    result = renderer._inline(tok)
    assert 'name="Code"' in result
    assert "code()" in result


def test_inline_link(renderer):
    tok = {
        "type": "link",
        "attrs": {"url": "https://example.com"},
        "children": [{"type": "text", "raw": "click"}],
    }
    result = renderer._inline(tok)
    assert '<a href="https://example.com"' in result
    assert "click" in result


def test_inline_link_unsafe_scheme(renderer):
    tok = {
        "type": "link",
        "attrs": {"url": "javascript:alert(1)"},
        "children": [{"type": "text", "raw": "evil"}],
    }
    result = renderer._inline(tok)
    assert "javascript:" not in result
    assert "evil" in result


def test_inline_link_mailto(renderer):
    tok = {
        "type": "link",
        "attrs": {"url": "mailto:test@example.com"},
        "children": [{"type": "text", "raw": "email"}],
    }
    result = renderer._inline(tok)
    assert "mailto:test@example.com" in result


def test_inline_strikethrough(renderer):
    tok = {"type": "strikethrough", "children": [{"type": "text", "raw": "old"}]}
    result = renderer._inline(tok)
    assert "<strike>" in result and "</strike>" in result


def test_inline_html_ins(renderer):
    tok = {"type": "inline_html", "raw": "<ins>added</ins>"}
    result = renderer._inline(tok)
    assert "<u>" in result
    assert renderer.ins_color in result


def test_inline_html_del(renderer):
    tok = {"type": "inline_html", "raw": "<del>removed</del>"}
    result = renderer._inline(tok)
    assert "<strike>" in result
    assert renderer.del_color in result


def test_inline_html_sup(renderer):
    tok = {"type": "inline_html", "raw": "<sup>2</sup>"}
    result = renderer._inline(tok)
    assert "<super>" in result


def test_inline_html_br(renderer):
    tok = {"type": "inline_html", "raw": "<br/>"}
    result = renderer._inline(tok)
    assert "<br/>" in result


def test_inline_softbreak(renderer):
    tok = {"type": "softbreak"}
    assert renderer._inline(tok) == " "


def test_inline_linebreak(renderer):
    tok = {"type": "linebreak"}
    assert renderer._inline(tok) == "<br/>"


# -- _fm_value --

def test_fm_value_email(renderer):
    result = renderer._fm_value("Name <email@example.com>")
    assert "mailto:email@example.com" in result
    assert "Name" in result


def test_fm_value_plain(renderer):
    result = renderer._fm_value("plain text")
    assert result == "plain text"


def test_fm_value_special_chars(renderer):
    result = renderer._fm_value("A & B <C>")
    assert "&amp;" in result
    assert "&lt;" in result


# -- build_front_matter_flowables --

def test_build_front_matter_with_fields(font_registered, tmp_path):
    """Use cpp-al style which has front_matter.fields defined."""
    import copy
    from lib.config import load_style, resolve_style_path
    from lib.colors import resolve_colors

    style = copy.deepcopy(load_style(resolve_style_path("cpp-al")))
    resolve_colors(style, None)

    r = ASTRenderer(style, {}, [], 468, tmp_path, has_fm_title=True)
    fm = {
        "title": "Test Paper",
        "document": "P1234R0",
        "date": "2026-01-01",
        "audience": "LEWG",
        "reply-to": ["Author <a@b.com>"],
    }
    flows = r.build_front_matter_flowables(fm)
    assert len(flows) > 0
    assert any(isinstance(f, AccentBox) for f in flows)


def test_build_front_matter_empty_fields(renderer):
    flows = renderer.build_front_matter_flowables({})
    assert flows == []


# -- build_toc_flowables --

def test_build_toc_empty(renderer):
    assert renderer.build_toc_flowables() == []


def test_build_toc_with_headings(renderer):
    for i in range(3):
        tok = {
            "type": "heading",
            "attrs": {"level": 2},
            "children": [{"type": "text", "raw": f"Section {i}"}],
        }
        renderer._render_token(tok)
    flows = renderer.build_toc_flowables()
    assert len(flows) > 0
    assert any(isinstance(f, AccentBox) for f in flows)


# -- _render_mermaid tempfile cleanup --

def test_render_mermaid_cleanup_on_write_failure(renderer, monkeypatch):
    """Temp file is cleaned up even when write() raises."""
    import tempfile as tempfile_mod
    import os

    created_paths = []
    real_ntf = tempfile_mod.NamedTemporaryFile

    def tracking_ntf(**kwargs):
        f = real_ntf(**kwargs)
        created_paths.append(f.name)
        original_write = f.write
        def failing_write(data):
            raise OSError("disk full")
        f.write = failing_write
        return f

    monkeypatch.setattr(tempfile_mod, "NamedTemporaryFile", tracking_ntf)
    monkeypatch.setattr(renderer, "_mermaid_svg", lambda code: "<svg></svg>")

    result = renderer._render_mermaid("graph TD; A-->B")
    assert result is None
    for p in created_paths:
        assert not os.path.exists(p), f"temp file leaked: {p}"


# -- block_html rendering --

def test_render_block_html_comment(renderer):
    tok = {"type": "block_html", "raw": "<!-- this is a comment -->"}
    flows = renderer._render_token(tok)
    assert flows == []


def test_render_block_html_multiline_comment(renderer):
    tok = {"type": "block_html", "raw": "<!--\nmultiline\ncomment\n-->"}
    flows = renderer._render_token(tok)
    assert flows == []


def test_render_block_html_pre_code(renderer):
    tok = {"type": "block_html", "raw": "<pre><code>int x = 0;</code></pre>"}
    flows = renderer._render_token(tok)
    assert len(flows) > 0
    assert any(isinstance(f, AccentBox) for f in flows)


def test_render_block_html_plain(renderer):
    tok = {"type": "block_html", "raw": "<div>plain html</div>"}
    flows = renderer._render_token(tok)
    assert len(flows) == 1
    assert isinstance(flows[0], Paragraph)


# -- pre_code_block rendering --

def test_render_pre_code_block_ins_del(renderer):
    inner = 'void f(<ins>int x</ins>, <del>float y</del>);'
    tok = {"type": "block_html", "raw": f"<pre><code>{inner}</code></pre>"}
    flows = renderer._render_token(tok)
    assert len(flows) > 0
    xpre = None
    for f in flows:
        if isinstance(f, AccentBox):
            xpre = f._content
            break
        if isinstance(f, XPreformatted):
            xpre = f
            break
    assert xpre is not None
    assert isinstance(xpre, XPreformatted)
    assert "<u>" in xpre.text
    assert "<strike>" in xpre.text


# -- _render_mermaid coverage --

def test_render_mermaid_returns_none_when_no_svg(renderer, monkeypatch):
    monkeypatch.setattr(renderer, "_mermaid_svg", lambda code: None)
    result = renderer._render_mermaid("graph TD; A-->B")
    assert result is None


def test_render_mermaid_returns_drawing(renderer, monkeypatch):
    from unittest.mock import MagicMock, patch
    from reportlab.graphics.shapes import Drawing

    drawing = Drawing(200, 100)
    monkeypatch.setattr(renderer, "_mermaid_svg", lambda code: "<svg></svg>")

    with patch("lib.renderer.svg2rlg", create=True) as mock_svg2rlg:
        mock_svg2rlg.return_value = drawing
        import lib.renderer as renderer_mod
        original_render = renderer._render_mermaid

        def patched_render(code):
            import tempfile, os
            svg = renderer._mermaid_svg(code)
            if not svg:
                return None
            tmp = tempfile.NamedTemporaryFile(suffix=".svg", delete=False)
            try:
                tmp.write(svg.encode("utf-8"))
                tmp.close()
                d = mock_svg2rlg(tmp.name)
            finally:
                tmp.close()
                os.unlink(tmp.name)
            if d:
                return [d]
            return None

        monkeypatch.setattr(renderer, "_render_mermaid", patched_render)
        result = renderer._render_mermaid("graph TD; A-->B")
        assert result is not None
        assert isinstance(result[0], Drawing)
