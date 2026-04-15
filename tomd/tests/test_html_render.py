"""Tests for lib.html.render."""

from lib.html.extract import parse_html
from lib.html.render import render_body


class TestHeading:
    def test_atx_level(self):
        soup = parse_html("<h2>Introduction</h2>")
        md = render_body(soup, "mpark")
        assert "## Introduction" in md

    def test_strips_section_number_span(self):
        soup = parse_html(
            '<h1><span class="header-section-number">1</span> Abstract</h1>')
        md = render_body(soup, "mpark")
        assert "# Abstract" in md
        assert "1 " not in md.split("Abstract")[0]

    def test_strips_leading_dotted_number(self):
        soup = parse_html("<h3>2.1.3 Details</h3>")
        md = render_body(soup, "mpark")
        assert "### Details" in md

    def test_bold_suppressed(self):
        soup = parse_html("<h2><strong>Bold Heading</strong></h2>")
        md = render_body(soup, "mpark")
        assert "## Bold Heading" in md
        assert "**" not in md


class TestParagraph:
    def test_collapses_whitespace(self):
        soup = parse_html("<p>Hello   \n  world</p>")
        md = render_body(soup, "mpark")
        assert "Hello world" in md

    def test_inline_code(self):
        soup = parse_html("<p>Use <code>std::vector</code> here.</p>")
        md = render_body(soup, "mpark")
        assert "`std::vector`" in md


class TestCodeBlock:
    def test_fenced(self):
        soup = parse_html('<pre class="sourceCode cpp"><code>int x = 1;</code></pre>')
        md = render_body(soup, "mpark")
        assert "```cpp" in md
        assert "int x = 1;" in md

    def test_language_from_class(self):
        soup = parse_html(
            '<div class="sourceCode"><pre class="sourceCode python">'
            '<code class="sourceCode python">print("hi")</code></pre></div>')
        md = render_body(soup, "mpark")
        assert "```python" in md

    def test_default_cpp_for_mpark(self):
        soup = parse_html("<pre><code>void f();</code></pre>")
        md = render_body(soup, "mpark")
        assert "```cpp" in md

    def test_no_default_for_unknown(self):
        soup = parse_html("<pre><code>void f();</code></pre>")
        md = render_body(soup, "unknown")
        assert "```\n" in md


class TestTable:
    def test_pipe_table(self):
        soup = parse_html("""
        <table>
          <tr><th>A</th><th>B</th></tr>
          <tr><td>1</td><td>2</td></tr>
        </table>
        """)
        md = render_body(soup, "mpark")
        assert "| A | B |" in md
        assert "| --- | --- |" in md
        assert "| 1 | 2 |" in md

    def test_pipe_escaped(self):
        soup = parse_html("""
        <table><tr><td>a|b</td><td>c</td></tr></table>
        """)
        md = render_body(soup, "mpark")
        assert r"a\|b" in md


class TestList:
    def test_unordered(self):
        soup = parse_html("<ul><li>One</li><li>Two</li></ul>")
        md = render_body(soup, "mpark")
        assert "- One" in md
        assert "- Two" in md

    def test_ordered(self):
        soup = parse_html("<ol><li>First</li><li>Second</li></ol>")
        md = render_body(soup, "mpark")
        assert "1. First" in md
        assert "2. Second" in md

    def test_nested(self):
        soup = parse_html("""
        <ul>
          <li>Parent
            <ul><li>Child</li></ul>
          </li>
        </ul>
        """)
        md = render_body(soup, "mpark")
        assert "- Parent" in md
        assert "  - Child" in md


class TestWording:
    def test_wording_add_fence(self):
        soup = parse_html('<div class="wording-add"><p>New text</p></div>')
        md = render_body(soup, "mpark")
        assert ":::wording-add" in md
        assert ":::" in md.split(":::wording-add")[1]

    def test_wording_remove_fence(self):
        soup = parse_html('<div class="wording-remove"><p>Old text</p></div>')
        md = render_body(soup, "mpark")
        assert ":::wording-remove" in md

    def test_wording_mixed_fence(self):
        soup = parse_html('<div class="wording"><p>Spec text</p></div>')
        md = render_body(soup, "mpark")
        assert ":::wording\n" in md

    def test_ins_del_passthrough(self):
        soup = parse_html("<p><ins>added</ins> and <del>removed</del></p>")
        md = render_body(soup, "mpark")
        assert "<ins>added</ins>" in md
        assert "<del>removed</del>" in md


class TestBlockquote:
    def test_blockquote(self):
        soup = parse_html("<blockquote><p>Quoted text</p></blockquote>")
        md = render_body(soup, "mpark")
        assert "> Quoted text" in md


class TestInlineFormatting:
    def test_bold(self):
        soup = parse_html("<p><strong>bold</strong></p>")
        md = render_body(soup, "mpark")
        assert "**bold**" in md

    def test_italic(self):
        soup = parse_html("<p><em>italic</em></p>")
        md = render_body(soup, "mpark")
        assert "*italic*" in md

    def test_link(self):
        soup = parse_html('<p><a href="https://example.com">link</a></p>')
        md = render_body(soup, "mpark")
        assert "[link](https://example.com)" in md

    def test_anchor_link_plain(self):
        soup = parse_html('<p><a href="#section">section</a></p>')
        md = render_body(soup, "mpark")
        assert "section" in md
        assert "[" not in md

    def test_sub_sup_passthrough(self):
        soup = parse_html("<p>x<sub>2</sub> + y<sup>3</sup></p>")
        md = render_body(soup, "mpark")
        assert "<sub>2</sub>" in md
        assert "<sup>3</sup>" in md


class TestCollapseWhitespace:
    def test_collapses_spaces(self):
        md = render_body(parse_html("<p>hello   world</p>"), "mpark")
        assert "hello world" in md

    def test_strips_format_chars(self):
        md = render_body(parse_html("<p>hello\u200bworld</p>"), "mpark")
        assert "helloworld" in md

    def test_strips_and_trims(self):
        md = render_body(parse_html("<p>  hi  </p>"), "mpark")
        assert md.strip() == "hi"
