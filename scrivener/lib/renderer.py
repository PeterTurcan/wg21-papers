"""AST-to-flowable conversion. The largest module - contains all
rendering logic for converting mistune AST tokens into ReportLab
flowables."""

import re
from html import unescape
from pathlib import Path

from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    Indenter,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
    XPreformatted,
)

from . import escape_xml
from .colors import parse_color
from .config import sp, load_logo
from .flowables import AccentBox, AccentRule
from .fonts import ensure_lazy, ensure_code_family
from .highlight import highlight


class ASTRenderer:
    def __init__(self, style, body_cmap, content_width, md_dir,
                 has_fm_title=False):
        self.style = style
        self.body_cmap = body_cmap
        self.content_width = content_width
        self.md_dir = md_dir
        self.headings = []
        self.seen_h1 = False
        self._in_heading = False
        self._wording_context = None
        self._in_ins = False
        self._in_del = False
        self.has_fm_title = has_fm_title
        self._build_styles()

    def _build_styles(self):
        s = self.style
        bs = s["body_size"]
        lh = bs * s["line_height"]
        code_fg = s["code_fg"]
        bq_fg = s["blockquote_fg"]
        self.fm_label_color = s["front_matter_label_color"]
        headings_cfg = s.get("headings", {})

        fm_cfg = s.get("front_matter", {})

        self.ps = {
            "body": ParagraphStyle(
                "body", fontName="Body", fontSize=bs, leading=lh,
                spaceAfter=sp(s, 0.8), spaceBefore=0),
            "code_block": ParagraphStyle(
                "code_block", fontName="Code",
                fontSize=bs * s["code_block"]["font_scale"],
                leading=bs * s["code_block"]["leading_scale"],
                textColor=parse_color(code_fg)),
            "blockquote": ParagraphStyle(
                "blockquote", fontName="Body-Italic", fontSize=bs,
                leading=lh, textColor=parse_color(bq_fg)),
            "front_value": ParagraphStyle(
                "front_value", fontName="Body",
                fontSize=bs * fm_cfg.get("font_scale", 0.9),
                leading=bs * fm_cfg.get("leading_scale", 1.2)),
        }

        self.gap = self.ps["body"].spaceAfter
        self.gap_sm = self.gap * 2 / 3
        self.ps["blockquote"].spaceAfter = self.gap
        self.ps["front_value"].spaceAfter = self.ps["body"].spaceBefore
        self.ps["list_item"] = ParagraphStyle(
            "list_item", parent=self.ps["body"],
            spaceAfter=0, spaceBefore=0)

        for level in range(1, 7):
            key = f"h{level}"
            hcfg = headings_cfg.get(key, {})
            scale = hcfg.get("scale", 1.0)
            lead_scale = hcfg.get("leading_scale", 1.45)
            h_fs = bs * scale
            sb = hcfg.get("space_before", 1.5) * h_fs
            sa = hcfg.get("space_after", 0.6) * h_fs
            self.ps[key] = ParagraphStyle(
                key, fontName="Body-Bold", fontSize=h_fs,
                leading=bs * lead_scale, spaceBefore=sb, spaceAfter=sa,
                keepWithNext=True)

        toc_fs = bs * 0.9
        toc_lh = toc_fs * s["line_height"]
        for level in range(2, 4):
            key = f"toc_h{level}"
            indent = s.get("toc_indent", 18) * (level - 2)
            self.ps[key] = ParagraphStyle(
                key, fontName="Body",
                fontSize=toc_fs,
                leading=toc_lh, leftIndent=indent)

        self.link_color = s["link_color"]
        self.heading_rule_color = s["heading_rule_color"]

        from reportlab.pdfbase.pdfmetrics import getFont
        face = getFont("Body").face
        asc, desc = face.ascent, abs(face.descent)
        em = asc + desc
        cap_vc = (desc + asc * 0.5) / em
        self.cap_shift = (cap_vc - 0.5) * lh

        wcfg = s.get("wording", {})
        self.ins_color = wcfg.get("ins_color")
        self.del_color = wcfg.get("del_color")
        self.code_inline_fg = s.get("code_inline_fg", s["code_fg"])
        self.code_inline_bg = s.get("code_inline_bg", s["code_bg"])

    def _inject_cjk_fallback(self, text):
        if not self.body_cmap:
            return text
        # Decode numeric character references (&#NNNNN; and &#xHHHH;)
        # so CJK characters become actual Unicode for glyph checking.
        # Named entities (&amp; &lt; etc.) stay intact for ReportLab.
        decoded = re.sub(
            r'&#(\d+);', lambda m: chr(int(m.group(1))), text)
        decoded = re.sub(
            r'&#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)), decoded)
        result = []
        cjk_run = []
        cjk_available = None
        for ch in decoded:
            cp = ord(ch)
            if cp > 127 and cp not in self.body_cmap:
                if cjk_available is None:
                    ensure_lazy("CJK")
                    from reportlab.pdfbase.pdfmetrics import getFont
                    try:
                        getFont("CJK")
                        cjk_available = True
                    except KeyError:
                        cjk_available = False
                if cjk_available:
                    cjk_run.append(ch)
                else:
                    if cjk_run:
                        result.append('<font name="CJK">')
                        result.append("".join(cjk_run))
                        result.append("</font>")
                        cjk_run = []
                    result.append("?")
            else:
                if cjk_run:
                    result.append('<font name="CJK">')
                    result.append("".join(cjk_run))
                    result.append("</font>")
                    cjk_run = []
                result.append(ch)
        if cjk_run:
            result.append('<font name="CJK">')
            result.append("".join(cjk_run))
            result.append("</font>")
        return "".join(result)

    def render(self, tokens):
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
                        if in_div is None and cls:
                            in_div = cls
                        else:
                            in_div = None
                        continue
            current.append(tok)
        if current:
            segments.append((in_div, current))

        flowables = []
        for div_class, toks in segments:
            if div_class and div_class.startswith("wording"):
                self._wording_context = div_class
            flows = []
            for tok in toks:
                flows.extend(self._render_token(tok))
            self._wording_context = None
            if div_class and div_class.startswith("wording"):
                flowables.extend(self._wrap_wording(div_class, flows))
            else:
                flowables.extend(flows)
        self._propagate_keep(flowables)
        return flowables

    @staticmethod
    def _propagate_keep(flowables):
        """Propagate keepWithNext through spacers so headings
        chain past decorative gaps to the real content."""
        for i in range(len(flowables) - 1):
            cur = flowables[i]
            if getattr(cur, 'keepWithNext', False):
                nxt = flowables[i + 1]
                if isinstance(nxt, Spacer):
                    nxt.keepWithNext = True

    def _only_text(self, tok):
        """Return raw text if paragraph has exactly one text child, else ''."""
        children = tok.get("children", [])
        if len(children) == 1 and children[0].get("type") == "text":
            return children[0].get("raw", children[0].get("text", ""))
        return ""

    def _wrap_wording(self, div_class, flows):
        """Wrap flowables in a wording AccentBox."""
        wcfg = self.style.get("wording", {})
        variant = wcfg.get(div_class, wcfg.get("wording", {}))
        bg = parse_color(variant["bg"])
        bar = parse_color(variant["bar_color"])
        bar_w = wcfg["bar_width"]
        pad = wcfg["padding"]
        radius = wcfg["radius"]

        if not flows:
            return []

        left_pad = bar_w + pad
        right_pad = pad
        inner_w = self.content_width - left_pad - right_pad

        tbl = Table([[f] for f in flows], colWidths=[inner_w])
        tbl.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))

        box = AccentBox(
            tbl, bg, bar, bar_w,
            left_pad, right_pad, pad,
            width=self.content_width, radius=radius,
            cap_shift=self.cap_shift)

        return [
            Spacer(1, self.gap_sm),
            box,
            Spacer(1, self.gap_sm),
        ]

    def _render_token(self, tok):
        t = tok.get("type", "")
        handler = getattr(self, f"_render_{t}", None)
        if handler:
            return handler(tok)
        text = self._inline_children(tok.get("children", []))
        if not text:
            text = escape_xml(tok.get("raw", tok.get("text", "")))
        return [Paragraph(f"[unsupported: {t}] {text}", self.ps["body"])]

    def _render_heading(self, tok):
        level = tok["attrs"]["level"]
        self._in_heading = True
        self._heading_level = min(level, 6)
        text = self._inline_children(tok.get("children", []))
        self._in_heading = False
        style_key = f"h{min(level, 6)}"
        flows = []

        if level == 1 and not self.seen_h1:
            self.seen_h1 = True
            if not self.has_fm_title:
                return self._title_block(text)

        if level >= 1:
            anchor = f"h_{len(self.headings)}"
            self.headings.append((level, text, anchor))

        flows.append(Paragraph(f'<a name="{anchor}"/>{text}', self.ps[style_key]))

        hcfg = self.style.get("headings", {}).get(style_key, {})
        if hcfg.get("rule"):
            rule = HRFlowable(
                width="100%", thickness=1,
                color=parse_color(self.heading_rule_color),
                spaceBefore=self.gap_sm,
                spaceAfter=self.gap,
                lineCap='butt')
            rule.keepWithNext = True
            flows.append(rule)
        return flows

    def _title_block(self, title_markup):
        from reportlab.pdfbase.pdfmetrics import stringWidth

        flows = []
        logo_path = self.style.get("logo")
        title_cfg = self.style.get("title", {})
        thickness = title_cfg.get("rule_thickness", 3)
        space_after = title_cfg.get("space_after_rule", 6)
        logo_h = title_cfg.get("logo_height", 55)
        logo_col_w = title_cfg.get("logo_column_width", 75)

        bs = self.style["body_size"]
        h1_cfg = self.style.get("headings", {}).get("h1", {})
        font_size = bs * h1_cfg.get("scale", 2.2)

        logo_img = None
        if logo_path:
            try:
                logo_img = load_logo(logo_path, logo_h)
                if logo_img:
                    logo_img.hAlign = "RIGHT"
            except Exception:
                logo_img = None

        avail_w = self.content_width - logo_col_w if logo_img else self.content_width
        plain = re.sub(r'<[^>]+>', '', title_markup)
        text_w = stringWidth(plain, "Body-Bold", font_size)
        if text_w > avail_w:
            font_size = font_size * avail_w / text_w

        title_style = ParagraphStyle(
            "title", fontName="Body-Bold",
            fontSize=font_size, leading=font_size,
            spaceBefore=0, spaceAfter=0)
        title_para = Paragraph(title_markup, title_style)

        rule_color = parse_color(self.style["heading_rule_color"])

        if logo_img:
            actual_logo_w = logo_img.width if hasattr(logo_img, 'width') else logo_col_w
            tbl = Table(
                [[title_para, logo_img]],
                colWidths=[self.content_width - actual_logo_w, actual_logo_w])
            tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), self.gap_sm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), self.gap),
            ]))
            flows.append(tbl)
        else:
            flows.append(title_para)

        if thickness:
            flows.append(HRFlowable(
                width="100%", thickness=thickness,
                color=rule_color,
                spaceBefore=0,
                spaceAfter=space_after,
                lineCap='butt'))
        else:
            flows.append(Spacer(1, space_after))
        return flows

    def build_front_matter_flowables(self, fm):
        flows = []
        fm_cfg = self.style.get("front_matter", {})
        fields = fm_cfg.get("fields", [])
        if not fields:
            return flows

        label_style = ParagraphStyle(
            "fm_label", fontName="Body",
            fontSize=self.ps["front_value"].fontSize,
            leading=self.ps["front_value"].leading)
        val_style = self.ps["front_value"]

        table_rows = []
        for entry in fields:
            field = entry.get("field", "")
            label = entry.get("label", field)
            val = fm.get(field)
            if val is None:
                continue
            if isinstance(val, list):
                val = "<br/>".join(self._fm_value(str(v)) for v in val)
            else:
                val = self._fm_value(str(val))
            table_rows.append([
                Paragraph(f"{escape_xml(label)}:", label_style),
                Paragraph(val, val_style),
            ])

        if not table_rows:
            return flows

        bg = parse_color(fm_cfg["bg"])
        bar_w = fm_cfg["bar_width"]
        accent = parse_color(self.style["accent_saturated"])
        inner_pad = fm_cfg["inner_pad"]
        label_col = fm_cfg["label_col"]
        cell_v = fm_cfg["cell_v_pad"]
        fm_space = fm_cfg["space_after"]

        left_pad = bar_w + inner_pad
        right_pad = inner_pad
        inner_width = self.content_width - left_pad - right_pad

        tbl = Table(table_rows, colWidths=[label_col, inner_width - label_col])
        tbl.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), cell_v),
            ("BOTTOMPADDING", (0, 0), (-1, -1), cell_v),
        ]))

        rule_color = parse_color(self.style["heading_rule_color"])
        rule_thickness = self.style.get("title", {}).get("rule_thickness", 3)
        flows.append(AccentBox(
            tbl, bg, accent, bar_w,
            left_pad, right_pad, inner_pad,
            width=self.content_width,
            cap_shift=self.cap_shift,
            top_rule=rule_color,
            top_rule_thickness=rule_thickness))
        flows.append(Spacer(1, fm_space))
        return flows

    def build_toc_flowables(self):
        if not self.headings:
            return []

        fm_cfg = self.style.get("front_matter", {})
        bg = parse_color(fm_cfg.get("bg", self.style["blockquote_bg"]))
        bar_w = fm_cfg.get("bar_width", 3)
        accent = parse_color(self.style["accent_saturated"])
        inner_pad = fm_cfg.get("inner_pad", 12)
        rule_color = parse_color(self.heading_rule_color)
        rule_thickness = self.style.get("title", {}).get("rule_thickness", 3)

        toc_fg = parse_color(self.style["page_number_color"])
        toc_title_style = ParagraphStyle(
            "toc_title", parent=self.ps["body"],
            fontName="Body-Bold",
            textColor=toc_fg,
            spaceAfter=0)
        toc_rule = HRFlowable(
            width="100%", thickness=2,
            color=parse_color(self.heading_rule_color),
            spaceBefore=self.gap_sm,
            spaceAfter=self.gap * 2,
            lineCap='butt')
        inner_flows = [
            Paragraph("Table of Contents", toc_title_style),
            toc_rule,
            Spacer(1, self.gap),
        ]
        for level, text, anchor in self.headings:
            clean = re.sub(r"<[^>]+>", "", text)
            base = self.ps.get(f"toc_h{level}", self.ps["toc_h3"])
            dimmed = ParagraphStyle(f"toc_h{level}_dim", parent=base,
                                    textColor=toc_fg)
            linked = f'<a href="#{anchor}" color="{self.style["page_number_color"]}">{clean}</a>'
            inner_flows.append(Paragraph(linked, dimmed))

        inner_w = self.content_width - inner_pad * 2
        tbl = Table([[f] for f in inner_flows], colWidths=[inner_w])
        tbl.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))

        box = AccentBox(
            tbl, bg, bg, 0,
            inner_pad, inner_pad, inner_pad,
            width=self.content_width,
            cap_shift=self.cap_shift)

        h1_h = self.ps["h1"].fontSize
        return [Spacer(1, h1_h), box, Spacer(1, self.gap * 2)]

    def _wording_text_color(self):
        """Return the text color for the current wording context, or None."""
        ctx = self._wording_context
        if ctx == "wording-add":
            return self.ins_color
        if ctx == "wording-remove":
            return self.del_color
        return None

    def _wording_wrap(self, text):
        """Apply wording-context color and strikethrough to inline markup."""
        color = self._wording_text_color()
        if color:
            text = f'<font color="{color}">{text}</font>'
        wcfg = self.style.get("wording", {})
        variant = wcfg.get(self._wording_context, {})
        if variant.get("strikethrough"):
            text = f"<strike>{text}</strike>"
        return text

    def _render_paragraph(self, tok):
        text = self._inline_children(tok.get("children", []))
        if text.strip() == "\\newpage":
            return [PageBreak()]
        text = self._inject_cjk_fallback(text)
        if self._wording_context:
            text = self._wording_wrap(text)
        return [Paragraph(text, self.ps["body"])]

    def _render_mermaid(self, code):
        """Render mermaid code to an SVG flowable."""
        svg = self._mermaid_svg(code)
        if not svg:
            return None
        try:
            from svglib.svglib import svg2rlg
            import tempfile, os
            tmp = tempfile.NamedTemporaryFile(suffix=".svg", delete=False)
            tmp.write(svg.encode("utf-8"))
            tmp.close()
            drawing = svg2rlg(tmp.name)
            os.unlink(tmp.name)
            if drawing:
                from .config import PAGE_CONFIGS
                pc = PAGE_CONFIGS[self.style.get("page_size", "letter")]
                max_h = (pc["size"][1] - 2 * pc["margin"]) * 0.8
                s = self.content_width / drawing.width
                if drawing.height * s > max_h:
                    s = max_h / drawing.height
                drawing.width *= s
                drawing.height *= s
                drawing.scale(s, s)
                return [Spacer(1, self.gap_sm), drawing,
                        Spacer(1, self.ps["h1"].fontSize)]
        except Exception:
            pass
        return None

    def _mermaid_svg(self, code):
        """Try merm (pure Python), fall back to mermaido (official mermaid-cli)."""
        try:
            from merm import render_diagram
            return render_diagram(code)
        except Exception:
            pass
        try:
            import mermaido
            return mermaido.render_to_string(code)
        except Exception:
            pass
        return None

    def _render_block_code(self, tok):
        ensure_code_family()
        raw = tok.get("raw", tok.get("text", ""))
        raw = unescape(raw)
        lang = tok.get("attrs", {}).get("info", "")
        if lang:
            lang = lang.split()[0]
        if lang == "mermaid":
            result = self._render_mermaid(raw)
            if result:
                return result

        if self._wording_context:
            ctx = self._wording_context
            if ctx in ("wording-add", "wording-remove"):
                markup = escape_xml(raw)
            else:
                syntax = self.style.get("syntax", {})
                markup = highlight(raw, lang, syntax)
            color = self._wording_text_color()
            style = ParagraphStyle(
                "code_block_wording", parent=self.ps["code_block"],
                textColor=parse_color(color) if color else self.ps["code_block"].textColor)
            pre = XPreformatted(markup, style)
            return [Spacer(1, self.gap_sm), pre, Spacer(1, self.gap_sm)]

        syntax = self.style.get("syntax", {})
        markup = highlight(raw, lang, syntax)
        cb = self.style["code_block"]
        bg = parse_color(self.style["code_bg"])
        accent = parse_color(self.style["accent_saturated"])
        bar_w = cb["bar_width"]
        lpad = cb["left_padding"]
        rpad = cb["right_padding"]
        vpad = cb["vertical_padding"]

        pre = XPreformatted(markup, self.ps["code_block"])
        box = AccentBox(
            pre, bg, accent, bar_w,
            lpad, rpad, vpad, radius=0,
            cap_shift=self.cap_shift)
        return [Spacer(1, self.gap_sm), box, Spacer(1, self.ps["h1"].fontSize)]

    def _render_block_quote(self, tok, depth=0):
        ensure_lazy("Body-Italic")
        children = tok.get("children", [])
        inner = []
        variant = None

        for child in children:
            ct = child.get("type")
            if ct == "block_quote":
                nested = self._render_block_quote(child, depth=depth + 1)
                inner.extend(nested)
            elif ct == "paragraph":
                text = self._inline_children(child.get("children", []))
                if not inner and variant is None:
                    m = re.match(r'^\[!(NOTE|WARNING|CAUTION)\]\s*', text)
                    if m:
                        variant = m.group(1).lower()
                        text = text[m.end():]
                        if not text.strip():
                            continue
                markup = self._inject_cjk_fallback(text)
                inner.append(Paragraph(f"<i>{markup}</i>", self.ps["blockquote"]))
            else:
                inner.extend(self._render_token(child))

        if not inner:
            return []

        bq = self.style["blockquote"]
        if variant:
            v = bq["variants"][variant]
            bg = parse_color(v["bg"])
            accent = parse_color(v["bar_color"])
        else:
            bg = parse_color(self.style["blockquote_bg"])
            accent = parse_color(self.style["accent_saturated"])

        left_pad = bq["left_padding"]
        right_pad = bq["right_padding"]
        inner_w = self.content_width - left_pad - right_pad
        if depth > 0:
            inner_w -= depth * left_pad

        tbl = Table([[f] for f in inner], colWidths=[inner_w])
        tbl.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -2), self.gap),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 0),
        ]))

        box = AccentBox(
            tbl, bg, accent,
            bar_w=bq["bar_width"],
            left_pad=left_pad,
            right_pad=right_pad,
            v_pad=bq["vertical_padding"],
            radius=bq["corner_radius"],
            cap_shift=self.cap_shift)

        flows = [box]
        if depth == 0:
            flows.insert(0, Spacer(1, self.gap_sm))
            flows.append(Spacer(1, self.ps["h1"].fontSize))
        return flows

    def _fm_value(self, text):
        """Format a front-matter value, turning Name <email> into a link."""
        m = re.match(r'^(.*?)\s*<([^>]+@[^>]+)>$', text)
        if m:
            name = escape_xml(m.group(1))
            email = m.group(2)
            link = f'<a href="mailto:{email}" color="{self.link_color}">{escape_xml(email)}</a>'
            return f"{name} {link}" if name else link
        return escape_xml(text)

    _DEFAULT_BULLETS = ["\u2022", "\u2013", "\u00B7"]

    def _render_list(self, tok, depth=0):
        ordered = tok.get("attrs", {}).get("ordered", False)
        list_cfg = self.style["list"]
        items = []
        for child in tok.get("children", []):
            item_parts = []
            nested_lists = []
            for sub in child.get("children", []):
                if sub.get("type") == "list":
                    nested_lists.extend(self._render_list(sub, depth=depth + 1))
                else:
                    text = self._inline_children(sub.get("children", []))
                    text = self._inject_cjk_fallback(text)
                    item_parts.append(Paragraph(text, self.ps["list_item"]))
            if item_parts and nested_lists:
                items.append(item_parts + nested_lists)
            elif item_parts:
                items.append(ListItem(item_parts))
            elif nested_lists:
                for nl in nested_lists:
                    items.append(nl)
        if not items:
            return []

        if ordered:
            bullet_type = "1"
            bullet_fmt = "%s."
        else:
            bullet_type = "bullet"
            bullet_fmt = None

        indent = list_cfg["left_indent"]
        kwargs = dict(
            bulletType=bullet_type,
            bulletFontName="Body",
            bulletFontSize=self.style["body_size"],
            leftIndent=indent,
            bulletDedent=list_cfg["bullet_dedent"],
            spaceBefore=list_cfg["space_before"] if depth == 0 else 0,
            spaceAfter=list_cfg["space_after"] if depth == 0 else 0,
        )
        if bullet_fmt:
            kwargs["bulletFormat"] = bullet_fmt
        if not ordered:
            bullets = list_cfg.get("bullets", self._DEFAULT_BULLETS)
            kwargs["start"] = bullets[depth % len(bullets)]

        return [ListFlowable(items, **kwargs)]

    def _smart_col_widths(self, all_rows, ncols):
        """Two-pass column sizing: measure minimum width per column,
        give short columns their natural width and share the rest
        proportionally among wide columns."""
        from reportlab.pdfbase.pdfmetrics import stringWidth
        import re

        natural = [0.0] * ncols
        for row in all_rows:
            for i, cell in enumerate(row):
                if i >= ncols:
                    break
                if hasattr(cell, 'text'):
                    txt = re.sub(r'<[^>]+>', '', cell.text)
                    fn = cell.style.fontName if hasattr(cell, 'style') else "Body"
                    fs = cell.style.fontSize if hasattr(cell, 'style') else 10
                else:
                    txt = str(cell)
                    fn = "Body"
                    fs = 10
                w = stringWidth(txt, fn, fs)
                tbl_cfg = self.style.get("table", {})
                pad = tbl_cfg.get("cell_padding", {})
                w += pad.get("left", 10) + pad.get("right", 10)
                if w > natural[i]:
                    natural[i] = w

        total_natural = sum(natural)
        if total_natural <= self.content_width:
            scale = self.content_width / total_natural
            return [w * scale for w in natural]

        threshold = self.content_width / ncols
        fixed = [(i, w) for i, w in enumerate(natural) if w <= threshold]
        flex = [(i, w) for i, w in enumerate(natural) if w > threshold]

        fixed_total = sum(w for _, w in fixed)
        flex_total = sum(w for _, w in flex)
        remaining = self.content_width - fixed_total

        result = [0.0] * ncols
        for i, w in fixed:
            result[i] = w
        for i, w in flex:
            result[i] = remaining * (w / flex_total) if flex_total > 0 else remaining / len(flex)
        return result

    def _render_table(self, tok):
        tbl_cfg = self.style.get("table", {})
        pad = tbl_cfg.get("cell_padding", {})
        hdr_fg = self.style.get("table_header_fg")
        rows = []
        headers = []
        for child in tok.get("children", []):
            if child.get("type") == "table_head":
                if hdr_fg and "table_header" not in self.ps:
                    self.ps["table_header"] = ParagraphStyle(
                        "table_header", parent=self.ps["body"],
                        textColor=parse_color(hdr_fg),
                        fontName="Body-Bold",
                        spaceBefore=0, spaceAfter=0)
                hdr_style = self.ps.get("table_header", self.ps["body"])
                head_children = child.get("children", [])
                if head_children and head_children[0].get("type") == "table_cell":
                    # mistune v3: table_head > table_cell (flat)
                    cells = []
                    for cell in head_children:
                        text = self._inline_children(cell.get("children", []))
                        if not hdr_fg:
                            text = f"<b>{text}</b>"
                        cells.append(Paragraph(text, hdr_style))
                    headers.append(cells)
                else:
                    # table_head > table_row > table_cell (nested)
                    for row in head_children:
                        cells = []
                        for cell in row.get("children", []):
                            text = self._inline_children(
                                cell.get("children", []))
                            if not hdr_fg:
                                text = f"<b>{text}</b>"
                            cells.append(Paragraph(text, hdr_style))
                        headers.append(cells)
            elif child.get("type") == "table_body":
                for row in child.get("children", []):
                    cells = []
                    for cell in row.get("children", []):
                        text = self._inline_children(cell.get("children", []))
                        text = self._inject_cjk_fallback(text)
                        cells.append(Paragraph(text, self.ps["body"]))
                    rows.append(cells)

        all_rows = headers + rows
        if not all_rows:
            return []

        ncols = max(len(r) for r in all_rows)
        for r in all_rows:
            while len(r) < ncols:
                r.append(Paragraph("", self.ps["body"]))

        if tbl_cfg.get("smart_columns", True):
            col_widths = self._smart_col_widths(all_rows, ncols)
        else:
            col_widths = [self.content_width / ncols] * ncols
        tbl = Table(all_rows, colWidths=col_widths)

        rule_color = parse_color(self.style["table_rule_color"])
        nhead = len(headers)
        style_cmds = []

        if nhead > 0:
            hdr_bg = parse_color(self.style["table_header_bg"])
            style_cmds.append(("BACKGROUND", (0, 0), (-1, nhead - 1), hdr_bg))

        stripe = self.style.get("table_stripe_bg")
        if stripe:
            sc = parse_color(stripe)
            for i in range(nhead, len(all_rows)):
                if (i - nhead) % 2 == 1:
                    style_cmds.append(("BACKGROUND", (0, i), (-1, i), sc))

        tbl_fs = self.style["body_size"] * tbl_cfg.get("font_scale", 1.0)
        top_pad = pad["top"] + self.cap_shift
        bot_pad = pad["bottom"] - self.cap_shift
        style_cmds.extend([
            ("FONTNAME", (0, 0), (-1, -1), "Body"),
            ("FONTSIZE", (0, 0), (-1, -1), tbl_fs),
            ("TOPPADDING", (0, 0), (-1, -1), top_pad),
            ("BOTTOMPADDING", (0, 0), (-1, -1), bot_pad),
            ("LEFTPADDING", (0, 0), (-1, -1), pad["left"]),
            ("RIGHTPADDING", (0, 0), (-1, -1), pad["right"]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])

        if nhead > 0:
            style_cmds.append(("LINEBELOW", (0, nhead), (-1, -1),
                               tbl_cfg["body_rule_width"], rule_color))
            style_cmds.append(("LINEBELOW", (0, nhead - 1), (-1, nhead - 1),
                               tbl_cfg["header_rule_width"], rule_color))
        else:
            style_cmds.append(("LINEBELOW", (0, 0), (-1, -1),
                               tbl_cfg["body_rule_width"], rule_color))

        tbl.setStyle(TableStyle(style_cmds))
        if nhead > 0:
            tbl.repeatRows = nhead
        spacer_before = Spacer(1, self.gap_sm)
        spacer_before.keepWithNext = True
        return [
            spacer_before,
            tbl,
            Spacer(1, self.ps["h1"].fontSize),
        ]

    def _render_thematic_break(self, tok):
        return [HRFlowable(
            width="100%", thickness=1,
            color=parse_color(self.style["heading_rule_color"]),
            spaceBefore=self.gap,
            spaceAfter=self.gap,
            lineCap='butt')]

    def _render_blank_line(self, tok):
        return []

    def _render_block_html(self, tok):
        raw = tok.get("raw", "")
        pre_m = re.match(
            r'<pre><code>(.*?)</code></pre>\s*$', raw, re.DOTALL)
        if pre_m:
            return self._render_pre_code_block(pre_m.group(1))
        text = escape_xml(raw)
        if self._wording_context:
            text = self._wording_wrap(text)
        return [Paragraph(text, self.ps["body"])]

    def _render_pre_code_block(self, inner):
        """Render a <pre><code>...</code></pre> HTML block as monospace,
        with <ins>/<del> converted to ReportLab color markup. HTML entities
        like &lt; &gt; &amp; pass through as valid XML."""
        ensure_code_family()
        markup = inner
        markup = re.sub(
            r'<ins>(.*?)</ins>',
            lambda m: f'<u><font color="{self.ins_color}">{m.group(1)}</font></u>',
            markup, flags=re.DOTALL)
        markup = re.sub(
            r'<del>(.*?)</del>',
            lambda m: f'<strike><font color="{self.del_color}">{m.group(1)}</font></strike>',
            markup, flags=re.DOTALL)

        if self._wording_context:
            color = self._wording_text_color()
            style = ParagraphStyle(
                "pre_code_wording", parent=self.ps["code_block"],
                textColor=parse_color(color) if color else self.ps["code_block"].textColor)
        else:
            style = self.ps["code_block"]

        pre = XPreformatted(markup, style)
        if self._wording_context:
            return [Spacer(1, self.gap_sm), pre, Spacer(1, self.gap_sm)]

        cb = self.style["code_block"]
        bg = parse_color(self.style["code_bg"])
        accent = parse_color(self.style["accent_saturated"])
        box = AccentBox(
            pre, bg, accent, cb["bar_width"],
            cb["left_padding"], cb["right_padding"],
            cb["vertical_padding"], radius=0,
            cap_shift=self.cap_shift)
        return [Spacer(1, self.gap_sm), box, Spacer(1, self.ps["h1"].fontSize)]

    def _inline_children(self, children):
        if not children:
            return ""
        parts = []
        for child in children:
            parts.append(self._inline(child))
        return "".join(parts)

    def _inline(self, tok):
        t = tok.get("type", "")
        handler = getattr(self, f"_inline_{t}", None)
        if handler:
            return handler(tok)
        raw = tok.get("raw", tok.get("text", ""))
        return escape_xml(unescape(raw))

    def _inline_text(self, tok):
        raw = tok.get("raw", tok.get("text", ""))
        text = escape_xml(unescape(raw))
        text = re.sub(r'&lt;sup&gt;(.*?)&lt;/sup&gt;', r'<super>\1</super>', text)
        text = text.replace('&lt;sup&gt;', '<super>').replace('&lt;/sup&gt;', '</super>')
        text = re.sub(r'&lt;sub&gt;(.*?)&lt;/sub&gt;', r'<sub>\1</sub>', text)
        text = text.replace('&lt;sub&gt;', '<sub>').replace('&lt;/sub&gt;', '</sub>')
        return text

    def _inline_emphasis(self, tok):
        inner = self._inline_children(tok.get("children", []))
        return f"<i>{inner}</i>"

    def _inline_strong(self, tok):
        inner = self._inline_children(tok.get("children", []))
        return f"<b>{inner}</b>"

    def _inline_codespan(self, tok):
        ensure_code_family()
        raw = tok.get("raw", tok.get("text", ""))
        raw = escape_xml(unescape(raw))
        if getattr(self, '_in_heading', False):
            sz = self.ps[f"h{self._heading_level}"].fontSize * 0.85
            return f'<font name="Code-Bold" size="{sz}">{raw}</font>'
        sz = self.ps["code_block"].fontSize
        if self._wording_context or self._in_ins or self._in_del:
            return f'<font name="Code" size="{sz}">{raw}</font>'
        return (f'<font name="Code" size="{sz}" color="{self.code_inline_fg}">'
                f'<span backColor="{self.code_inline_bg}">{raw}</span></font>')

    def _inline_link(self, tok):
        children = self._inline_children(tok.get("children", []))
        href = tok.get("attrs", {}).get("url", "")
        return f'<a href="{escape_xml(href)}" color="{self.link_color}">{children}</a>'

    def _inline_image(self, tok):
        src = tok.get("attrs", {}).get("src", "")
        alt = tok.get("attrs", {}).get("alt", "")
        return escape_xml(alt or f"[image: {src}]")

    def _inline_strikethrough(self, tok):
        inner = self._inline_children(tok.get("children", []))
        return f"<strike>{inner}</strike>"

    def _inline_softbreak(self, tok):
        return " "

    def _inline_linebreak(self, tok):
        return "<br/>"

    def _inline_inline_html(self, tok):
        raw = tok.get("raw", tok.get("text", ""))
        sup_m = re.match(r"<sup>(.*?)</sup>", raw, re.DOTALL)
        if sup_m:
            return f"<super>{escape_xml(unescape(sup_m.group(1)))}</super>"
        ins_m = re.match(r"<ins>(.*?)</ins>", raw, re.DOTALL)
        if ins_m:
            inner = escape_xml(unescape(ins_m.group(1)))
            return f'<u><font color="{self.ins_color}">{inner}</font></u>'
        del_m = re.match(r"<del>(.*?)</del>", raw, re.DOTALL)
        if del_m:
            inner = escape_xml(unescape(del_m.group(1)))
            return f'<strike><font color="{self.del_color}">{inner}</font></strike>'
        if raw.startswith("<ins>"):
            self._in_ins = True
            return f'<u><font color="{self.ins_color}">'
        if raw.startswith("</ins>"):
            self._in_ins = False
            return '</font></u>'
        if raw.startswith("<del>"):
            self._in_del = True
            return f'<strike><font color="{self.del_color}">'
        if raw.startswith("</del>"):
            self._in_del = False
            return '</font></strike>'
        if raw.startswith("<sup>"):
            return "<super>"
        if raw.startswith("</sup>"):
            return "</super>"
        if raw.startswith("<sub>"):
            return "<sub>"
        if raw.startswith("</sub>"):
            return "</sub>"
        if raw.startswith("<br"):
            return "<br/>"
        return ""

    def _render_image(self, tok):
        src = tok.get("attrs", {}).get("src", "")
        resolved = Path(src)
        if not resolved.is_absolute():
            resolved = self.md_dir / src
        if resolved.exists():
            try:
                img = RLImage(str(resolved), kind="proportional")
                iw, ih = img.imageWidth, img.imageHeight
                if iw > self.content_width:
                    scale = self.content_width / iw
                    img = RLImage(str(resolved),
                                  width=self.content_width,
                                  height=ih * scale)
                return [
                    Spacer(1, self.gap_sm),
                    img,
                    Spacer(1, self.gap_sm),
                ]
            except Exception:
                pass
        return [Paragraph(f"[image: {escape_xml(src)}]", self.ps["body"])]
