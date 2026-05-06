"""Layer 2: HTMLRenderer token tests.

No fonts or ReportLab needed - the HTML renderer has no font dependency.
Tests feed hand-built mistune AST tokens and assert on HTML output.
"""

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.config import load_style, resolve_style_path
from lib.html_renderer import HTMLRenderer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conftest import MINIMAL_PNG


@pytest.fixture
def style():
    path = resolve_style_path(None)
    return copy.deepcopy(load_style(path))


@pytest.fixture
def renderer(style, tmp_path):
    return HTMLRenderer(style, tmp_path, has_fm_title=True)


class TestBlockTokens:
    def test_paragraph(self, renderer):
        tok = {"type": "paragraph", "children": [
            {"type": "text", "raw": "Hello world"}]}
        html = renderer._render_token(tok)
        assert "<p>Hello world</p>" in html

    def test_heading_h2(self, renderer):
        tok = {"type": "heading", "attrs": {"level": 2}, "children": [
            {"type": "text", "raw": "Section"}]}
        html = renderer._render_token(tok)
        assert '<h2 id="h_0">Section</h2>' in html

    def test_heading_h1_title_block(self, style, tmp_path):
        r = HTMLRenderer(style, tmp_path, has_fm_title=False)
        tok = {"type": "heading", "attrs": {"level": 1}, "children": [
            {"type": "text", "raw": "Title"}]}
        html = r._render_token(tok)
        assert '<header class="title-block">' in html
        assert "<h1>Title</h1>" in html

    def test_heading_collects_anchors(self, renderer):
        for i in range(3):
            tok = {"type": "heading", "attrs": {"level": 2}, "children": [
                {"type": "text", "raw": f"H{i}"}]}
            renderer._render_token(tok)
        assert len(renderer.headings) == 3
        assert renderer.headings[0][2] == "h_0"
        assert renderer.headings[2][2] == "h_2"

    def test_code_block(self, renderer):
        tok = {"type": "block_code", "raw": "x = 1", "attrs": {"info": "python"}}
        html = renderer._render_token(tok)
        assert '<pre class="code-block">' in html
        assert 'class="language-python"' in html

    def test_code_block_no_lang(self, renderer):
        tok = {"type": "block_code", "raw": "hello", "attrs": {"info": ""}}
        html = renderer._render_token(tok)
        assert "<pre" in html
        assert "hello" in html

    def test_code_block_mermaid(self, renderer):
        tok = {"type": "block_code", "raw": "graph TD\n  A-->B",
               "attrs": {"info": "mermaid"}}
        html = renderer._render_token(tok)
        assert "mermaid" in html

    def test_block_quote(self, renderer):
        tok = {"type": "block_quote", "children": [
            {"type": "paragraph", "children": [
                {"type": "text", "raw": "Quote text"}]}]}
        html = renderer._render_token(tok)
        assert "<blockquote>" in html
        assert "Quote text" in html

    def test_block_quote_note_variant(self, renderer):
        tok = {"type": "block_quote", "children": [
            {"type": "paragraph", "children": [
                {"type": "text", "raw": "[!NOTE] Important info"}]}]}
        html = renderer._render_token(tok)
        assert 'class="note"' in html

    def test_unordered_list(self, renderer):
        tok = {"type": "list", "attrs": {"ordered": False}, "children": [
            {"type": "list_item", "children": [
                {"type": "paragraph", "children": [
                    {"type": "text", "raw": "Item 1"}]}]},
            {"type": "list_item", "children": [
                {"type": "paragraph", "children": [
                    {"type": "text", "raw": "Item 2"}]}]}]}
        html = renderer._render_token(tok)
        assert "<ul>" in html
        assert "<li>" in html
        assert "Item 1" in html

    def test_ordered_list(self, renderer):
        tok = {"type": "list", "attrs": {"ordered": True}, "children": [
            {"type": "list_item", "children": [
                {"type": "paragraph", "children": [
                    {"type": "text", "raw": "First"}]}]}]}
        html = renderer._render_token(tok)
        assert "<ol>" in html

    def test_table(self, renderer):
        tok = {"type": "table", "children": [
            {"type": "table_head", "children": [
                {"type": "table_cell", "children": [
                    {"type": "text", "raw": "Col1"}]},
                {"type": "table_cell", "children": [
                    {"type": "text", "raw": "Col2"}]}]},
            {"type": "table_body", "children": [
                {"type": "table_row", "children": [
                    {"type": "table_cell", "children": [
                        {"type": "text", "raw": "A"}]},
                    {"type": "table_cell", "children": [
                        {"type": "text", "raw": "B"}]}]}]}]}
        html = renderer._render_token(tok)
        assert "<table>" in html
        assert "<thead>" in html
        assert "<th>Col1</th>" in html
        assert "<td>A</td>" in html

    def test_thematic_break(self, renderer):
        tok = {"type": "thematic_break"}
        html = renderer._render_token(tok)
        assert "<hr>" in html

    def test_blank_line(self, renderer):
        tok = {"type": "blank_line"}
        html = renderer._render_token(tok)
        assert html == ""

    def test_newpage(self, renderer):
        tok = {"type": "paragraph", "children": [
            {"type": "text", "raw": "\\newpage"}]}
        html = renderer._render_token(tok)
        assert 'class="page-break"' in html

    def test_image(self, renderer):
        tok = {"type": "image", "attrs": {"src": "photo.png", "alt": "A photo"}}
        html = renderer._render_token(tok)
        assert "<figure>" in html
        assert "photo.png" in html

    def test_image_embed_found(self, style, tmp_path):
        png = tmp_path / "test.png"
        png.write_bytes(MINIMAL_PNG)
        r = HTMLRenderer(style, tmp_path, has_fm_title=True)
        tok = {"type": "image", "attrs": {"url": "test.png"},
               "children": [{"type": "text", "raw": "alt text"}]}
        html = r._render_token(tok)
        assert "data:image/png;base64," in html
        assert "test.png" not in html

    def test_image_embed_missing(self, renderer):
        tok = {"type": "image", "attrs": {"url": "nope.png"},
               "children": [{"type": "text", "raw": ""}]}
        html = renderer._render_token(tok)
        assert "nope.png" in html

    def test_block_html_comment(self, renderer):
        tok = {"type": "block_html", "raw": "<!-- comment -->"}
        html = renderer._render_token(tok)
        assert html == ""

    def test_block_html_passthrough(self, renderer):
        tok = {"type": "block_html", "raw": "<div>custom</div>"}
        html = renderer._render_token(tok)
        assert "<div>custom</div>" in html


class TestInlineTokens:
    def test_emphasis(self, renderer):
        tok = {"type": "emphasis", "children": [
            {"type": "text", "raw": "italic"}]}
        assert renderer._inline(tok) == "<em>italic</em>"

    def test_strong(self, renderer):
        tok = {"type": "strong", "children": [
            {"type": "text", "raw": "bold"}]}
        assert renderer._inline(tok) == "<strong>bold</strong>"

    def test_codespan(self, renderer):
        tok = {"type": "codespan", "raw": "x"}
        assert renderer._inline(tok) == "<code>x</code>"

    def test_codespan_escapes(self, renderer):
        tok = {"type": "codespan", "raw": "<T>"}
        result = renderer._inline(tok)
        assert "&lt;T&gt;" in result

    def test_link(self, renderer):
        tok = {"type": "link", "attrs": {"url": "https://example.com"},
               "children": [{"type": "text", "raw": "click"}]}
        result = renderer._inline(tok)
        assert '<a href="https://example.com">click</a>' == result

    def test_link_unsafe_scheme(self, renderer):
        tok = {"type": "link", "attrs": {"url": "javascript:alert(1)"},
               "children": [{"type": "text", "raw": "bad"}]}
        result = renderer._inline(tok)
        assert "href" not in result
        assert "bad" in result

    def test_link_mailto(self, renderer):
        tok = {"type": "link", "attrs": {"url": "mailto:a@b.com"},
               "children": [{"type": "text", "raw": "email"}]}
        result = renderer._inline(tok)
        assert "mailto:a@b.com" in result

    def test_strikethrough(self, renderer):
        tok = {"type": "strikethrough", "children": [
            {"type": "text", "raw": "removed"}]}
        assert renderer._inline(tok) == "<del>removed</del>"

    def test_softbreak(self, renderer):
        tok = {"type": "softbreak"}
        assert renderer._inline(tok) == " "

    def test_linebreak(self, renderer):
        tok = {"type": "linebreak"}
        assert renderer._inline(tok) == "<br>"

    def test_inline_html_passthrough(self, renderer):
        tok = {"type": "inline_html", "raw": "<sup>2</sup>"}
        assert renderer._inline(tok) == "<sup>2</sup>"

    def test_inline_image(self, renderer):
        tok = {"type": "image", "attrs": {"src": "img.png", "alt": "pic"}}
        result = renderer._inline(tok)
        assert "img.png" in result

    def test_inline_image_embed_found(self, style, tmp_path):
        png = tmp_path / "inline.png"
        png.write_bytes(MINIMAL_PNG)
        r = HTMLRenderer(style, tmp_path, has_fm_title=True)
        tok = {"type": "image", "attrs": {"url": "inline.png"},
               "children": [{"type": "text", "raw": "pic"}]}
        result = r._inline(tok)
        assert "data:image/png;base64," in result
        assert "inline.png" not in result

    def test_image_embed_svg(self, style, tmp_path):
        svg = tmp_path / "icon.svg"
        svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
        r = HTMLRenderer(style, tmp_path, has_fm_title=True)
        tok = {"type": "image", "attrs": {"url": "icon.svg"},
               "children": [{"type": "text", "raw": ""}]}
        html = r._render_token(tok)
        assert "data:image/svg+xml;base64," in html

    # -- entity-encoded tags stay literal --

    def test_text_encoded_sup_stays_literal(self, renderer):
        tok = {"type": "text", "raw": "mc<sup>2</sup>"}
        assert renderer._inline_text(tok) == "mc&lt;sup&gt;2&lt;/sup&gt;"

    def test_text_encoded_sub_stays_literal(self, renderer):
        tok = {"type": "text", "raw": "H<sub>2</sub>O"}
        assert renderer._inline_text(tok) == "H&lt;sub&gt;2&lt;/sub&gt;O"

    # -- sup/sub implied space --

    def test_sup_implied_space(self, renderer):
        children = [
            {"type": "text", "raw": "mc"},
            {"type": "inline_html", "raw": "<sup>2</sup>"},
        ]
        assert renderer._inline_children(children) == "mc <sup>2</sup>"

    def test_sup_no_double_space(self, renderer):
        children = [
            {"type": "text", "raw": "mc "},
            {"type": "inline_html", "raw": "<sup>2</sup>"},
        ]
        assert renderer._inline_children(children) == "mc <sup>2</sup>"

    def test_sup_collapse_multi_space(self, renderer):
        children = [
            {"type": "text", "raw": "mc   "},
            {"type": "inline_html", "raw": "<sup>2</sup>"},
        ]
        assert renderer._inline_children(children) == "mc <sup>2</sup>"

    def test_sub_implied_space(self, renderer):
        children = [
            {"type": "text", "raw": "H"},
            {"type": "inline_html", "raw": "<sub>2</sub>"},
        ]
        assert renderer._inline_children(children) == "H <sub>2</sub>"

    def test_sub_no_double_space(self, renderer):
        children = [
            {"type": "text", "raw": "H "},
            {"type": "inline_html", "raw": "<sub>2</sub>"},
        ]
        assert renderer._inline_children(children) == "H <sub>2</sub>"

    def test_sup_at_start_no_space(self, renderer):
        children = [
            {"type": "inline_html", "raw": "<sup>2</sup>"},
        ]
        assert renderer._inline_children(children) == "<sup>2</sup>"

    def test_sub_at_start_no_space(self, renderer):
        children = [
            {"type": "inline_html", "raw": "<sub>2</sub>"},
        ]
        assert renderer._inline_children(children) == "<sub>2</sub>"


class TestRender:
    def test_render_returns_string(self, renderer):
        tokens = [
            {"type": "paragraph", "children": [
                {"type": "text", "raw": "Hello"}]}]
        html = renderer.render(tokens)
        assert isinstance(html, str)
        assert "Hello" in html

    def test_wording_div(self, renderer):
        tokens = [
            {"type": "paragraph", "children": [
                {"type": "text", "raw": "::: wording-add"}]},
            {"type": "paragraph", "children": [
                {"type": "text", "raw": "Added text"}]},
            {"type": "paragraph", "children": [
                {"type": "text", "raw": ":::"}]}]
        html = renderer.render(tokens)
        assert 'class="wording wording-add"' in html
        assert "Added text" in html


class TestFrontMatter:
    def test_render_front_matter(self, renderer):
        fm = {"document": "P1234R0", "date": "2026-04-25"}
        html = renderer.render_front_matter(fm)
        assert '<dl class="front-matter">' in html
        assert "P1234R0" in html
        assert "Document" in html

    def test_render_front_matter_empty(self, renderer):
        html = renderer.render_front_matter({})
        assert html == ""

    def test_render_front_matter_email(self, renderer):
        fm = {"reply-to": ["Author <author@example.com>"]}
        html = renderer.render_front_matter(fm)
        assert "mailto:author@example.com" in html

    def test_render_toc(self, renderer):
        for i in range(3):
            tok = {"type": "heading", "attrs": {"level": 2}, "children": [
                {"type": "text", "raw": f"Section {i}"}]}
            renderer._render_token(tok)
        html = renderer.render_toc()
        assert '<nav class="toc">' in html
        assert "Section 0" in html
        assert 'href="#h_0"' in html

    def test_render_toc_empty(self, renderer):
        assert renderer.render_toc() == ""
