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
    Image as RLImage,
    ListFlowable,
    PageBreak,
    Paragraph,
    Spacer,
    Table,
    XPreformatted,
)

from lib.flowables import AccentBox, TitleEnd
from lib.renderer import ASTRenderer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conftest import MINIMAL_PNG, make_png


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


# ---------------------------------------------------------------------------
# title_block sizing regression tests.
#
# title_block has three regimes for the title font size:
#   1. Title fits at h1 nominal size -> render at h1, single line.
#   2. Title needs shrinking but the proportional shrink stays >= h2 size
#      -> render at the shrunk size, single line.
#   3. Proportional shrink would land below h2 size -> clamp at h2 and let
#      the Paragraph wrap to multiple lines using ReportLab's default
#      whitespace-based wrapping.
# ---------------------------------------------------------------------------


def _title_paragraph(renderer, title_text):
    """Return the Paragraph that title_block produces for *title_text*.

    Strips out the surrounding logo/table wrapper so tests can assert on the
    title Paragraph's style directly.
    """
    flows = renderer.title_block(title_text)
    for f in flows:
        if isinstance(f, Paragraph):
            return f
        if isinstance(f, Table):
            for row in f._cellvalues:
                for cell in row:
                    if isinstance(cell, Paragraph):
                        return cell
    raise AssertionError("no title Paragraph found in title_block output")


def test_title_short_uses_h1_size(renderer_no_fm_title):
    """A title that fits at the nominal h1 size renders at h1 with no shrink."""
    from reportlab.pdfbase.pdfmetrics import getFont

    bs = renderer_no_fm_title.style["body_size"]
    h1_scale = renderer_no_fm_title.style["headings"]["h1"]["scale"]
    expected_h1 = bs * h1_scale

    face = getFont("Body-Bold").face
    metric_scale = (face.ascent + abs(face.descent)) / 1000

    para = _title_paragraph(renderer_no_fm_title, "Short Title")
    assert para.style.fontSize == pytest.approx(expected_h1)
    assert para.style.leading == pytest.approx(expected_h1 * metric_scale)


def test_title_medium_shrinks_to_fit_single_line(renderer_no_fm_title):
    """A title that overflows h1 but stays >= h2 after shrink is single-line."""
    from reportlab.pdfbase.pdfmetrics import stringWidth

    r = renderer_no_fm_title
    bs = r.style["body_size"]
    h1_scale = r.style["headings"]["h1"]["scale"]
    h2_scale = r.style["headings"]["h2"]["scale"]
    expected_h1 = bs * h1_scale
    expected_h2 = bs * h2_scale

    # Without a loaded logo, avail_w = content_width. Construct a title whose
    # h1-width lands squarely in the medium band: just over avail_w (so shrink
    # fires) but well under avail_w * (h1/h2) (so the shrunk size stays
    # comfortably above h2).
    avail_w = r.content_width
    target_w = avail_w * 1.05  # ~5% over -> mild shrink, well above h2 floor
    token = "Word "
    title = token
    while stringWidth(title.strip(), "Body-Bold", expected_h1) < target_w:
        title += token
    title = title.strip()

    para = _title_paragraph(r, title)

    assert para.style.fontSize < expected_h1, "should have shrunk below h1"
    assert para.style.fontSize > expected_h2, "should have stayed above h2"
    # Single-line regime: leading spans the full font metric height.
    from reportlab.pdfbase.pdfmetrics import getFont as _gf
    _face = _gf("Body-Bold").face
    _ms = (_face.ascent + abs(_face.descent)) / 1000
    assert para.style.leading == pytest.approx(para.style.fontSize * _ms)


def test_title_too_long_clamps_to_h2_and_wraps(renderer_no_fm_title):
    """A pathologically long title clamps at h2 size and wraps to multiple lines."""
    bs = renderer_no_fm_title.style["body_size"]
    h2_scale = renderer_no_fm_title.style["headings"]["h2"]["scale"]
    h2_lead_scale = renderer_no_fm_title.style["headings"]["h2"].get(
        "leading_scale", 1.3)
    expected_h2 = bs * h2_scale
    expected_lead = expected_h2 * h2_lead_scale

    # Long enough that the proportional shrink would fall below h2.
    title = (
        "An Unreasonably Long Title Deliberately Constructed To Demonstrate "
        "That The Title Renderer Wraps Long Titles Across Multiple Lines "
        "Instead Of Shrinking Below The H2 Heading Size Forever")
    para = _title_paragraph(renderer_no_fm_title, title)

    assert para.style.fontSize == pytest.approx(expected_h2), (
        f"expected fontSize {expected_h2} (h2), got {para.style.fontSize}")
    assert para.style.leading == pytest.approx(expected_lead), (
        f"expected leading {expected_lead}, got {para.style.leading}")

    # Confirm the Paragraph actually wraps to more than one line at the
    # available width. content_width=468; subtract a generous logo column
    # to be conservative.
    avail_w = renderer_no_fm_title.content_width - 75
    _, height = para.wrap(avail_w, 10000)
    assert height > expected_lead * 1.5, (
        f"expected multi-line wrap (height > {expected_lead * 1.5}), "
        f"got single-line height {height}")


def test_title_at_h2_floor_boundary_uses_single_line(renderer_no_fm_title):
    """A title whose shrink lands exactly at h2 size still renders single-line."""
    from reportlab.pdfbase.pdfmetrics import stringWidth

    bs = renderer_no_fm_title.style["body_size"]
    h1_scale = renderer_no_fm_title.style["headings"]["h1"]["scale"]
    h2_scale = renderer_no_fm_title.style["headings"]["h2"]["scale"]
    h1_font = bs * h1_scale
    h2_font = bs * h2_scale

    # Construct a title whose plain-text width at h1 exactly fills
    # avail_w * (h1_font / h2_font), so the proportional shrink lands at h2.
    avail_w = renderer_no_fm_title.content_width - 75
    target_w_at_h1 = avail_w * (h1_font / h2_font)

    # Repeat a known token until we just exceed target_w_at_h1.
    token = "Word "
    title = token
    while stringWidth(title.strip(), "Body-Bold", h1_font) < target_w_at_h1:
        title += token
    # Trim back one token so the shrink stays just above the h2 floor.
    title = title[: -len(token)].strip()

    para = _title_paragraph(renderer_no_fm_title, title)
    assert para.style.fontSize >= h2_font, (
        f"fontSize {para.style.fontSize} must not fall below h2 floor {h2_font}")
    # Above-floor case stays single-line: leading spans the full font metric height.
    from reportlab.pdfbase.pdfmetrics import getFont as _gf2
    _face2 = _gf2("Body-Bold").face
    _ms2 = (_face2.ascent + abs(_face2.descent)) / 1000
    assert para.style.leading == pytest.approx(para.style.fontSize * _ms2)


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


def test_render_image_found(font_registered, min_style, tmp_path):
    png = tmp_path / "test.png"
    png.write_bytes(MINIMAL_PNG)
    r = ASTRenderer(
        min_style, body_cmap={}, fallback_chain=[],
        content_width=468, md_dir=tmp_path, has_fm_title=True)
    tok = {
        "type": "paragraph",
        "children": [{"type": "image", "attrs": {"url": "test.png"},
                      "children": [{"type": "text", "raw": "alt"}]}],
    }
    flows = r._render_token(tok)
    assert len(flows) == 3
    assert isinstance(flows[0], Spacer)
    assert isinstance(flows[1], RLImage)
    assert isinstance(flows[2], Spacer)


def test_render_image_scales_to_fit(font_registered, min_style, tmp_path):
    png = tmp_path / "wide.png"
    png.write_bytes(make_png(200, 200))

    narrow_width = 100.0
    r = ASTRenderer(
        min_style, body_cmap={}, fallback_chain=[],
        content_width=narrow_width, md_dir=tmp_path, has_fm_title=True)
    tok = {
        "type": "paragraph",
        "children": [{"type": "image", "attrs": {"url": "wide.png"},
                      "children": [{"type": "text", "raw": ""}]}],
    }
    flows = r._render_token(tok)
    img = flows[1]
    assert isinstance(img, RLImage)
    assert img.drawWidth <= narrow_width + 0.01
    assert img.drawHeight <= r._page_h + 0.01


def test_render_image_url_attr(font_registered, min_style, tmp_path):
    png = tmp_path / "v3.png"
    png.write_bytes(MINIMAL_PNG)
    r = ASTRenderer(
        min_style, body_cmap={}, fallback_chain=[],
        content_width=468, md_dir=tmp_path, has_fm_title=True)
    tok = {
        "type": "paragraph",
        "children": [{"type": "image", "attrs": {"url": "v3.png"},
                      "children": [{"type": "text", "raw": ""}]}],
    }
    flows = r._render_token(tok)
    assert isinstance(flows[1], RLImage)


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


# -- entity-encoded tags stay literal --

def test_text_encoded_sup_stays_literal(renderer):
    tok = {"type": "text", "raw": "mc<sup>2</sup>"}
    assert renderer._inline_text(tok) == "mc&lt;sup&gt;2&lt;/sup&gt;"


def test_text_encoded_sub_stays_literal(renderer):
    tok = {"type": "text", "raw": "H<sub>2</sub>O"}
    assert renderer._inline_text(tok) == "H&lt;sub&gt;2&lt;/sub&gt;O"


# -- sup/sub implied space --

def test_sup_implied_space(renderer):
    children = [
        {"type": "text", "raw": "mc"},
        {"type": "inline_html", "raw": "<sup>2</sup>"},
    ]
    assert renderer._inline_children(children) == "mc <super>2</super>"


def test_sup_no_double_space(renderer):
    children = [
        {"type": "text", "raw": "mc "},
        {"type": "inline_html", "raw": "<sup>2</sup>"},
    ]
    assert renderer._inline_children(children) == "mc <super>2</super>"


def test_sup_collapse_multi_space(renderer):
    children = [
        {"type": "text", "raw": "mc   "},
        {"type": "inline_html", "raw": "<sup>2</sup>"},
    ]
    assert renderer._inline_children(children) == "mc <super>2</super>"


def test_sup_collapse_tabs(renderer):
    children = [
        {"type": "text", "raw": "mc\t\t"},
        {"type": "inline_html", "raw": "<sup>2</sup>"},
    ]
    assert renderer._inline_children(children) == "mc <super>2</super>"


def test_sup_at_start_no_space(renderer):
    children = [
        {"type": "inline_html", "raw": "<sup>2</sup>"},
    ]
    assert renderer._inline_children(children) == "<super>2</super>"


def test_sup_split_tag_implied_space(renderer):
    children = [
        {"type": "text", "raw": "mc"},
        {"type": "inline_html", "raw": "<sup>"},
    ]
    assert renderer._inline_children(children) == "mc <super>"


def test_sub_implied_space(renderer):
    children = [
        {"type": "text", "raw": "H"},
        {"type": "inline_html", "raw": "<sub>"},
        {"type": "text", "raw": "2"},
        {"type": "inline_html", "raw": "</sub>"},
    ]
    assert renderer._inline_children(children) == "H <sub>2</sub>"


def test_sub_no_double_space(renderer):
    children = [
        {"type": "text", "raw": "H "},
        {"type": "inline_html", "raw": "<sub>"},
        {"type": "text", "raw": "2"},
        {"type": "inline_html", "raw": "</sub>"},
    ]
    assert renderer._inline_children(children) == "H <sub>2</sub>"


def test_sub_collapse_multi_space(renderer):
    children = [
        {"type": "text", "raw": "H   "},
        {"type": "inline_html", "raw": "<sub>"},
        {"type": "text", "raw": "2"},
        {"type": "inline_html", "raw": "</sub>"},
    ]
    assert renderer._inline_children(children) == "H <sub>2</sub>"


def test_sub_at_start_no_space(renderer):
    children = [
        {"type": "inline_html", "raw": "<sub>"},
        {"type": "text", "raw": "2"},
        {"type": "inline_html", "raw": "</sub>"},
    ]
    assert renderer._inline_children(children) == "<sub>2</sub>"


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


def _fm_cell_values(flows):
    """Extract (label_text, value_text) pairs from front matter flowables."""
    pairs = []
    for f in flows:
        if isinstance(f, AccentBox):
            tbl = f._content
            if isinstance(tbl, Table):
                for row in tbl._cellvalues:
                    if len(row) >= 2:
                        label = getattr(row[0], "text", "")
                        value = getattr(row[1], "text", "")
                        pairs.append((label, value))
    return pairs


def test_intent_transform_info(font_registered, tmp_path):
    """intent: info renders as 'Inform' via transform."""
    import copy
    from lib.config import load_style, resolve_style_path
    from lib.colors import resolve_colors

    style = copy.deepcopy(load_style(resolve_style_path("cpp-al")))
    resolve_colors(style, None)

    r = ASTRenderer(style, {}, [], 468, tmp_path, has_fm_title=True)
    fm = {"document": "P9999R0", "date": "2026-01-01", "intent": "info"}
    flows = r.build_front_matter_flowables(fm)
    pairs = _fm_cell_values(flows)
    intent_values = [v for l, v in pairs if "Intent" in l]
    assert len(intent_values) == 1
    assert "Inform" in intent_values[0]
    assert "info" not in intent_values[0]


def test_intent_transform_ask(font_registered, tmp_path):
    """intent: ask renders as 'Ask' via transform."""
    import copy
    from lib.config import load_style, resolve_style_path
    from lib.colors import resolve_colors

    style = copy.deepcopy(load_style(resolve_style_path("cpp-al")))
    resolve_colors(style, None)

    r = ASTRenderer(style, {}, [], 468, tmp_path, has_fm_title=True)
    fm = {"document": "P9999R0", "date": "2026-01-01", "intent": "ask"}
    flows = r.build_front_matter_flowables(fm)
    pairs = _fm_cell_values(flows)
    intent_values = [v for l, v in pairs if "Intent" in l]
    assert len(intent_values) == 1
    assert "Ask" in intent_values[0]


def test_front_matter_field_order_matches_style(font_registered, tmp_path):
    """Fields render in style YAML order regardless of fm dict insertion order."""
    import copy
    from lib.config import load_style, resolve_style_path
    from lib.colors import resolve_colors

    style = copy.deepcopy(load_style(resolve_style_path("cpp-al")))
    resolve_colors(style, None)

    r = ASTRenderer(style, {}, [], 468, tmp_path, has_fm_title=True)
    # Insert in reverse of expected style order
    fm = {
        "reply-to": ["Author <a@b.com>"],
        "audience": "LEWG",
        "intent": "info",
        "date": "2026-01-01",
        "document": "P0001R0",
    }
    flows = r.build_front_matter_flowables(fm)
    pairs = _fm_cell_values(flows)
    label_names = [l.rstrip(":") for l, _ in pairs]
    expected_order = ["Document Number", "Date", "Intent", "Audience", "Reply-to"]
    assert label_names == expected_order


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

def test_render_mermaid_returns_flowables(renderer):
    """Valid mermaid code produces flowables via native renderer."""
    result = renderer._render_mermaid("flowchart TD\n    A[Start] --> B[End]")
    assert result is not None
    assert len(result) >= 1


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

def test_render_mermaid_returns_none_on_bad_input(renderer):
    result = renderer._render_mermaid("not valid mermaid at all")
    assert result is None


def test_render_block_code_mermaid_bad_input_warns_and_returns_empty(renderer):
    tok = {"type": "block_code", "raw": "gantt\n    title A Schedule\n    section Work\n    Task :a1, 2024-01-01, 30d", "attrs": {"info": "mermaid"}}
    result = renderer._render_block_code(tok)
    assert result == []


def test_render_mermaid_contains_drawing(renderer):
    from reportlab.graphics.shapes import Drawing
    result = renderer._render_mermaid("flowchart TD\n    A[Start] --> B[End]")
    assert result is not None
    drawings = [f for f in result if isinstance(f, Drawing)]
    assert len(drawings) == 1


# -- Table word-wrap and shrink-retry --

def _make_table_tok(headers, rows):
    """Build a mistune AST table token from lists of strings."""
    head_cells = [
        {"type": "table_cell", "children": [{"type": "text", "raw": h}]}
        for h in headers
    ]
    body_rows = []
    for row in rows:
        cells = [
            {"type": "table_cell", "children": [{"type": "text", "raw": c}]}
            for c in row
        ]
        body_rows.append({"type": "table_row", "children": cells})
    return {
        "type": "table",
        "children": [
            {"type": "table_head", "children": head_cells},
            {"type": "table_body", "children": body_rows},
        ],
    }


def _extract_table(flows):
    """Return the first Table flowable from a list."""
    for f in flows:
        if isinstance(f, Table):
            return f
    return None



def test_table_cells_no_split_long_words(renderer):
    """Table cell paragraphs must have splitLongWords disabled."""
    tok = _make_table_tok(
        ["Header"],
        [["AutomatedEvaluation"]],
    )
    flows = renderer._render_token(tok)
    tbl = _extract_table(flows)
    assert tbl is not None
    for row in tbl._cellvalues:
        for cell in row:
            if isinstance(cell, Paragraph):
                assert cell.style.splitLongWords == 0


def test_smart_col_widths_returns_min_word_widths(renderer):
    """_smart_col_widths returns min-word-width floors alongside column widths."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    tok = _make_table_tok(
        ["Short", "LongHeaderWord"],
        [["a", "Extremely"]],
    )
    flows = renderer._render_token(tok)
    tbl = _extract_table(flows)
    assert tbl is not None
    # Build rows the same way _build_table_flowable does
    hdr = [
        Paragraph("Short", renderer.ps["table_body"]),
        Paragraph("LongHeaderWord", renderer.ps["table_body"]),
    ]
    body = [
        Paragraph("a", renderer.ps["table_body"]),
        Paragraph("Extremely", renderer.ps["table_body"]),
    ]
    col_widths, min_word = renderer._smart_col_widths([hdr, body], 2)
    assert len(min_word) == 2
    pad = renderer.style["table"]["cell_padding"]
    h_pad = pad["left"] + pad["right"] + 2
    fs = renderer.style["body_size"]
    expected_min = stringWidth("LongHeaderWord", "Body", fs) + h_pad
    assert min_word[1] >= expected_min - 1


def test_table_shrink_retry(font_registered, min_style, tmp_path):
    """When columns are too narrow for their words, font size shrinks."""
    import copy
    style = copy.deepcopy(min_style)
    r = ASTRenderer(
        style, body_cmap={}, fallback_chain=[],
        content_width=120, md_dir=tmp_path, has_fm_title=True)
    tok = _make_table_tok(
        ["Date", "Move", "Register", "Description"],
        [["July 2026", "Agora21 Launch", "Automated Evaluation",
          "An AI-generated analysis of every paper"]],
    )
    flows = r._render_token(tok)
    tbl = _extract_table(flows)
    assert tbl is not None
    base_fs = style["body_size"] * style.get("table", {}).get("font_scale", 1.0)
    cmds = getattr(tbl, '_cmds', [])
    if not cmds and hasattr(tbl, 'style') and hasattr(tbl.style, '_cmds'):
        cmds = tbl.style._cmds
    for cmd in cmds:
        if cmd[0] == 'FONTSIZE':
            assert cmd[3] < base_fs


def test_table_shrink_caps_at_three_retries(font_registered, min_style, tmp_path):
    """Font size never shrinks below base * SHRINK_FACTOR^MAX_SHRINK_RETRIES."""
    import copy
    style = copy.deepcopy(min_style)
    r = ASTRenderer(
        style, body_cmap={}, fallback_chain=[],
        content_width=60, md_dir=tmp_path, has_fm_title=True)
    tok = _make_table_tok(
        ["A", "B", "C", "D", "E", "F"],
        [["Incomprehensibilities", "Supercalifragilistic",
          "Extraordinarily", "Internationalization",
          "Counterrevolutionary", "Deinstitutionalization"]],
    )
    flows = r._render_token(tok)
    tbl = _extract_table(flows)
    assert tbl is not None
    base_fs = style["body_size"] * style.get("table", {}).get("font_scale", 1.0)
    min_allowed = base_fs * (ASTRenderer.SHRINK_FACTOR ** ASTRenderer.MAX_SHRINK_RETRIES)
    cmds = getattr(tbl, '_cmds', [])
    if not cmds and hasattr(tbl, 'style') and hasattr(tbl.style, '_cmds'):
        cmds = tbl.style._cmds
    for cmd in cmds:
        if cmd[0] == 'FONTSIZE':
            assert cmd[3] >= min_allowed - 0.01
