"""AST-to-HTML conversion. Mirrors ASTRenderer's token dispatch but
emits HTML strings instead of ReportLab flowables."""

import base64
import mimetypes
import re
from html import escape, unescape
from pathlib import Path

from .highlight import highlight_html

_SAFE_SCHEMES = {"http", "https", "mailto", ""}


def _is_sup_or_sub_open(tok):
    if tok.get("type") == "inline_html":
        raw = tok.get("raw", tok.get("text", ""))
        return raw.startswith("<sup>") or raw.startswith("<sub>")
    return False


class HTMLRenderer:
    """Render mistune AST tokens to semantic HTML fragments.

    Args:
        cfg: resolved style dict (used only for front-matter field config)
        md_dir: directory of the source markdown (for image resolution)
        has_fm_title: True if front matter contains a title field
    """
    def __init__(self, cfg, md_dir, has_fm_title=False):
        self.cfg = cfg
        self.md_dir = md_dir
        self.has_fm_title = has_fm_title
        self._img_cache = {}
        self.headings = []
        self.seen_h1 = False
        self._wording_context = None
        self._in_ins = False
        self._in_del = False

    def render(self, tokens):
        """Render top-level AST tokens to an HTML string."""
        segments = []
        current = []
        in_div = None
        for tok in tokens:
            if tok.get("type") == "paragraph":
                text = self._only_text(tok)
                if text:
                    m = re.match(r'^:::\s*([\w-]+)?$', text.strip())
                    if m:
                        if current:
                            segments.append((in_div, current))
                            current = []
                        cls = m.group(1)
                        in_div = cls if (in_div is None and cls) else None
                        continue
            current.append(tok)
        if current:
            segments.append((in_div, current))

        parts = []
        for div_class, toks in segments:
            if div_class and div_class.startswith("wording"):
                self._wording_context = div_class
            inner = []
            for tok in toks:
                inner.append(self._render_token(tok))
            self._wording_context = None
            if div_class and div_class.startswith("wording"):
                parts.append(f'<div class="wording {div_class}">\n{"".join(inner)}</div>\n')
            else:
                parts.extend(inner)
        return "".join(parts)

    def render_title_block(self, title_text, hide_rule=False, logo_path=None):
        """Render the title block HTML.

        Args:
            title_text: escaped title string
            hide_rule: if True, omit the bottom border (front matter
                       box provides its own top rule, matching the PDF
                       builder which strips the HRFlowable when FM exists)
            logo_path: path to logo image, or None
        """
        cls = "title-block no-rule" if hide_rule else "title-block"
        logo_html = ""
        if logo_path:
            logo_html = f'<img class="title-logo" src="{escape(str(logo_path))}" alt="">'
        return f'<header class="{cls}">\n<h1>{title_text}</h1>\n{logo_html}</header>\n'

    def render_front_matter(self, fm):
        """Render front matter as a definition list."""
        fm_cfg = self.cfg.get("front_matter", {})
        fields = fm_cfg.get("fields", [])
        if not fields:
            return ""

        items = []
        for entry in fields:
            field = entry.get("field", "")
            label = entry.get("label", field)
            val = fm.get(field)
            if val is None:
                continue
            if isinstance(val, list):
                val_html = "<br>".join(self._fm_value(str(v)) for v in val)
            else:
                raw = str(val)
                transform = entry.get("transform", {})
                val_html = self._fm_value(transform.get(raw, raw))
            items.append(f"<dt>{escape(label)}:</dt>\n<dd>{val_html}</dd>")

        if not items:
            return ""
        return '<dl class="front-matter">\n' + "\n".join(items) + "\n</dl>\n"

    def render_toc(self):
        """Render table of contents from collected headings."""
        if not self.headings:
            return ""
        items = []
        for level, text, anchor in self.headings:
            clean = re.sub(r"<[^>]+>", "", text)
            indent = "  " * (level - 2) if level > 2 else ""
            items.append(f'{indent}<li><a href="#{anchor}">{clean}</a></li>')
        return '<nav class="toc">\n<h2>Table of Contents</h2>\n<ul>\n' + "\n".join(items) + "\n</ul>\n</nav>\n"

    def _only_text(self, tok):
        children = tok.get("children", [])
        if len(children) == 1 and children[0].get("type") == "text":
            return children[0].get("raw", children[0].get("text", ""))
        return ""

    def _render_token(self, tok):
        t = tok.get("type", "")
        handler = getattr(self, f"_render_{t}", None)
        if handler:
            return handler(tok)
        text = self._inline_children(tok.get("children", []))
        if not text:
            text = escape(tok.get("raw", tok.get("text", "")))
        return f"<p>{text}</p>\n"

    def _render_heading(self, tok):
        level = tok["attrs"]["level"]
        level = min(level, 6)
        text = self._inline_children(tok.get("children", []))

        if level == 1 and not self.seen_h1:
            self.seen_h1 = True
            if not self.has_fm_title:
                return self.render_title_block(text)

        anchor = f"h_{len(self.headings)}"
        self.headings.append((level, text, anchor))
        return f'<h{level} id="{anchor}">{text}</h{level}>\n'

    def _render_paragraph(self, tok):
        children = tok.get("children", [])
        if len(children) == 1 and children[0].get("type") == "image":
            return self._render_image(children[0])
        text = self._inline_children(children)
        if text.strip() == "\\newpage":
            return '<hr class="page-break">\n'
        return f"<p>{text}</p>\n"

    def _render_block_code(self, tok):
        raw = tok.get("raw", tok.get("text", ""))
        raw = unescape(raw)
        lang = tok.get("attrs", {}).get("info", "")
        if lang:
            lang = lang.split()[0]

        if lang == "mermaid":
            return f'<pre class="code-block mermaid"><code>{escape(raw)}</code></pre>\n'

        if lang:
            markup = highlight_html(raw, lang)
            return f'<pre class="code-block"><code class="language-{escape(lang)}">{markup}</code></pre>\n'

        return f'<pre class="code-block"><code>{escape(raw)}</code></pre>\n'

    def _render_block_quote(self, tok):
        children = tok.get("children", [])
        inner = []
        variant = None

        for child in children:
            ct = child.get("type")
            if ct == "block_quote":
                inner.append(self._render_block_quote(child))
            elif ct == "paragraph":
                text = self._inline_children(child.get("children", []))
                if not inner and variant is None:
                    m = re.match(r'^\[!(NOTE|WARNING|CAUTION)\]\s*', text)
                    if m:
                        variant = m.group(1).lower()
                        text = text[m.end():]
                        if not text.strip():
                            continue
                inner.append(f"<p>{text}</p>\n")
            else:
                inner.append(self._render_token(child))

        cls = f' class="{variant}"' if variant else ""
        return f"<blockquote{cls}>\n{''.join(inner)}</blockquote>\n"

    def _render_list(self, tok):
        ordered = tok.get("attrs", {}).get("ordered", False)
        tag = "ol" if ordered else "ul"
        items = []
        for child in tok.get("children", []):
            parts = []
            for sub in child.get("children", []):
                if sub.get("type") == "list":
                    parts.append(self._render_list(sub))
                else:
                    text = self._inline_children(sub.get("children", []))
                    parts.append(text)
            items.append(f"<li>{''.join(parts)}</li>")
        return f"<{tag}>\n" + "\n".join(items) + f"\n</{tag}>\n"

    def _render_table(self, tok):
        parts = ["<table>\n"]
        for child in tok.get("children", []):
            if child.get("type") == "table_head":
                parts.append("<thead>\n")
                head_children = child.get("children", [])
                if head_children and head_children[0].get("type") == "table_cell":
                    parts.append("<tr>")
                    for cell in head_children:
                        text = self._inline_children(cell.get("children", []))
                        parts.append(f"<th>{text}</th>")
                    parts.append("</tr>\n")
                else:
                    for row in head_children:
                        parts.append("<tr>")
                        for cell in row.get("children", []):
                            text = self._inline_children(cell.get("children", []))
                            parts.append(f"<th>{text}</th>")
                        parts.append("</tr>\n")
                parts.append("</thead>\n")
            elif child.get("type") == "table_body":
                parts.append("<tbody>\n")
                for row in child.get("children", []):
                    parts.append("<tr>")
                    for cell in row.get("children", []):
                        text = self._inline_children(cell.get("children", []))
                        parts.append(f"<td>{text}</td>")
                    parts.append("</tr>\n")
                parts.append("</tbody>\n")
        parts.append("</table>\n")
        return "".join(parts)

    def _render_thematic_break(self, tok):
        return "<hr>\n"

    def _render_blank_line(self, tok):
        return ""

    def _render_block_html(self, tok):
        raw = tok.get("raw", "")
        if re.match(r'\s*<!--.*?-->\s*$', raw, re.DOTALL):
            return ""
        return raw + "\n"

    def _img_src(self, tok):
        attrs = tok.get("attrs", {})
        return attrs.get("src", "") or attrs.get("url", "")

    def _img_alt(self, tok):
        alt = tok.get("attrs", {}).get("alt", "")
        if not alt:
            children = tok.get("children", [])
            if children and children[0].get("type") == "text":
                alt = children[0].get("raw", "")
        return alt

    def _embed_img_src(self, src):
        """Resolve image path and return a data URI, or the raw src if not found."""
        resolved = Path(src)
        if not resolved.is_absolute():
            resolved = self.md_dir / src
        key = str(resolved)
        if key in self._img_cache:
            return self._img_cache[key]
        if resolved.is_file():
            mime = mimetypes.guess_type(key)[0] or "image/png"
            data = resolved.read_bytes()
            b64 = base64.b64encode(data).decode("ascii")
            result = f"data:{mime};base64,{b64}"
        else:
            result = src
        self._img_cache[key] = result
        return result

    def _render_image(self, tok):
        src = self._embed_img_src(self._img_src(tok))
        alt = self._img_alt(tok)
        return f'<figure><img src="{escape(src)}" alt="{escape(alt)}"></figure>\n'

    def _inline_children(self, children):
        if not children:
            return ""
        parts = []
        for child in children:
            if parts and _is_sup_or_sub_open(child):
                last = parts[-1]
                stripped = last.rstrip(" \t")
                if stripped:
                    parts[-1] = stripped + " "
            parts.append(self._inline(child))
        return "".join(parts)

    def _inline(self, tok):
        t = tok.get("type", "")
        handler = getattr(self, f"_inline_{t}", None)
        if handler:
            return handler(tok)
        raw = tok.get("raw", tok.get("text", ""))
        return escape(unescape(raw))

    def _inline_text(self, tok):
        raw = tok.get("raw", tok.get("text", ""))
        return escape(unescape(raw))

    def _inline_emphasis(self, tok):
        inner = self._inline_children(tok.get("children", []))
        return f"<em>{inner}</em>"

    def _inline_strong(self, tok):
        inner = self._inline_children(tok.get("children", []))
        return f"<strong>{inner}</strong>"

    def _inline_codespan(self, tok):
        raw = tok.get("raw", tok.get("text", ""))
        return f"<code>{escape(unescape(raw))}</code>"

    def _inline_link(self, tok):
        children = self._inline_children(tok.get("children", []))
        href = tok.get("attrs", {}).get("url", "")
        scheme = href.split(":", 1)[0].lower() if ":" in href else ""
        if scheme and scheme not in _SAFE_SCHEMES:
            return children
        return f'<a href="{escape(href)}">{children}</a>'

    def _inline_image(self, tok):
        src = self._embed_img_src(self._img_src(tok))
        alt = self._img_alt(tok)
        return f'<img src="{escape(src)}" alt="{escape(alt)}">'

    def _inline_strikethrough(self, tok):
        inner = self._inline_children(tok.get("children", []))
        return f"<del>{inner}</del>"

    def _inline_softbreak(self, tok):
        return " "

    def _inline_linebreak(self, tok):
        return "<br>"

    def _inline_inline_html(self, tok):
        raw = tok.get("raw", tok.get("text", ""))
        if raw.startswith("<ins>"):
            self._in_ins = True
        elif raw.startswith("</ins>"):
            self._in_ins = False
        elif raw.startswith("<del>"):
            self._in_del = True
        elif raw.startswith("</del>"):
            self._in_del = False
        return raw

    def _fm_value(self, text):
        """Format a front-matter value, turning Name <email> into a link."""
        m = re.match(r'^(.*?)\s*<([^>]+@[^>]+)>$', text)
        if m:
            name = escape(m.group(1))
            email = m.group(2)
            link = f'<a href="mailto:{email}">{escape(email)}</a>'
            return f"{name} {link}" if name else link
        return escape(text)
