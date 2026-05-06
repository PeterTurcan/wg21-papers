"""CSS generation from style YAML. Pure function: style dict in, CSS string out."""

from html import escape


_PT_TO_PX = 96 / 72
_TIGHT_GAP = 0.8 * 2 / 3
_PARA_GAP = 0.8


def _bold_wght(cfg):
    return cfg.get("fonts", {}).get("body_bold", {}).get("axes", {}).get("wght", 700)


def _body_wght(cfg):
    return cfg.get("fonts", {}).get("body", {}).get("axes", {}).get("wght", 400)


def su(r):
    """CSS calc expression: r multiples of the base unit. Parallel to sp() for PDF."""
    if r == 1:
        return "var(--u)"
    return f"calc(var(--u) * {r:.4g})"


def _su_abs(cfg, v):
    """Convert an absolute YAML point value to a su() expression."""
    return su(v / cfg["body_size"])


_COLOR_KEYS = [
    ("accent_saturated", "--accent"),
    ("accent_mid", "--accent-mid"),
    ("link_color", "--link-color"),
    ("code_fg", "--code-fg"),
    ("code_inline_fg", "--code-inline-fg"),
    ("code_bg", "--code-bg"),
    ("code_inline_bg", "--code-inline-bg"),
    ("blockquote_fg", "--blockquote-fg"),
    ("blockquote_bg", "--blockquote-bg"),
    ("heading_rule_color", "--heading-rule-color"),
    ("table_header_bg", "--table-header-bg"),
    ("table_header_fg", "--table-header-fg"),
    ("table_rule_color", "--table-rule-color"),
    ("table_stripe_bg", "--table-stripe-bg"),
    ("front_matter_label_color", "--fm-label-color"),
]

_PYGMENTS_CLASS_MAP = {
    "keyword": "hl-k",
    "type": "hl-kt",
    "function": "hl-nf",
    "string": "hl-s",
    "number": "hl-m",
    "comment": "hl-c",
    "preprocessor": "hl-cp",
    "operator": "hl-o",
}


def generate_css(cfg, mode="fragment"):
    """Generate a CSS string from a resolved style dict.

    Args:
        cfg: resolved style dict (palette already expanded, colors resolved)
        mode: "full" emits an html{} rule for accessibility scaling;
              "fragment" emits a fixed px anchor on the article.

    Returns:
        CSS string. No file I/O.
    """
    bs = cfg["body_size"]
    lines = []
    lines.append(f"/* Auto-generated from style: {escape(cfg.get('name', 'unknown'))} */")
    lines.append("")

    _emit_font_imports(lines, cfg)

    if mode == "full":
        pct = bs / 12 * 100
        lines.append(f"html {{ font-size: {pct:.4g}%; }}")
        lines.append("")

    sel = "article.scrivener"
    u_val = "1em" if mode == "full" else f"{bs * _PT_TO_PX:.4g}px"
    lines.append(f"{sel} {{")
    lines.append(f"  --u: {u_val};")

    for yaml_key, css_var in _COLOR_KEYS:
        v = cfg.get(yaml_key)
        if v and v != "auto":
            lines.append(f"  {css_var}: {v};")

    wcfg = cfg.get("wording", {})
    if wcfg.get("ins_color"):
        lines.append(f"  --ins-color: {wcfg['ins_color']};")
    if wcfg.get("del_color"):
        lines.append(f"  --del-color: {wcfg['del_color']};")

    lines.append(f"  display: flex;")
    lines.append(f"  flex-direction: column;")
    lines.append(f"  font-size: var(--u);")
    lines.append(f"  line-height: {cfg['line_height']};")

    text_color = cfg.get("palette", {}).get("text")
    if text_color:
        lines.append(f"  color: {text_color};")

    body_family = _resolve_font_family(cfg, "body")
    if body_family:
        lines.append(f"  font-family: {body_family};")

    pc = cfg.get("page_size", "a4")
    from .config import PAGE_CONFIGS
    if pc in PAGE_CONFIGS:
        page_w = PAGE_CONFIGS[pc]["size"][0]
        margin = PAGE_CONFIGS[pc]["margin"]
        cw = page_w - 2 * margin
        lines.append(f"  max-width: {su(cw / bs)};")

    lines.append(f"}}")
    lines.append("")

    lines.append(f"{sel} > * {{ margin: 0; padding: 0; }}")
    lines.append("")

    h1_scale = cfg.get("headings", {}).get("h1", {}).get("scale", 1.6)

    _emit_body(lines, sel, cfg)
    _emit_headings(lines, sel, cfg)
    _emit_code_block(lines, sel, cfg, h1_scale)
    _emit_blockquote(lines, sel, cfg, h1_scale)
    _emit_list(lines, sel, cfg)
    _emit_table(lines, sel, cfg, h1_scale)
    _emit_front_matter(lines, sel, cfg)
    _emit_wording(lines, sel, cfg)
    _emit_syntax(lines, sel, cfg)
    _emit_misc(lines, sel, cfg, h1_scale)

    return "\n".join(lines) + "\n"


_FONT_ROLE_TO_FAMILY = {
    "body": ("body", "body_bold", "body_italic", "body_bold_italic"),
    "code": ("code", "code_bold", "code_italic", "code_bold_italic"),
}

_GOOGLE_FONT_FAMILY_MAP = {
    "source-serif-4": ("Source Serif 4", "serif"),
    "source-serif-4-italic": ("Source Serif 4", "serif"),
    "source-code-pro": ("Source Code Pro", "monospace"),
    "source-code-pro-italic": ("Source Code Pro", "monospace"),
    "noto-sans": ("Noto Sans", "sans-serif"),
    "noto-serif-italic": ("Noto Serif", "serif"),
    "noto-sans-mono": ("Noto Sans Mono", "monospace"),
    "noto-sans-cjk": ("Noto Sans SC", "sans-serif"),
    "noto-emoji": ("Noto Emoji", "sans-serif"),
}


def _emit_font_imports(lines, cfg):
    """Emit @import rules for web_url entries in the fonts config.

    Consolidates individual Google Fonts CSS2 URLs into a single
    combined request when possible, for faster loading.
    """
    fonts_cfg = cfg.get("fonts", {})
    seen_urls = set()
    gf_families = []
    other_urls = []

    for entry in fonts_cfg.values():
        if not isinstance(entry, dict):
            continue
        url = entry.get("web_url")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        if "fonts.googleapis.com/css2" in url:
            start = url.find("family=")
            if start >= 0:
                end = url.find("&", start)
                frag = url[start:end] if end >= 0 else url[start:]
                if frag not in gf_families:
                    gf_families.append(frag)
        else:
            other_urls.append(url)

    if gf_families:
        combined = "https://fonts.googleapis.com/css2?" + "&".join(gf_families) + "&display=swap"
        lines.append(f'@import url("{combined}");')
    for url in other_urls:
        lines.append(f'@import url("{url}");')
    if gf_families or other_urls:
        lines.append("")


def _resolve_font_family(cfg, role):
    """Resolve the CSS font-family string for a font role (body or code).

    Returns a complete font-family value like '"Noto Sans", sans-serif'
    or None if the font ID is not in the map.
    """
    fonts_cfg = cfg.get("fonts", {})
    roles = _FONT_ROLE_TO_FAMILY.get(role, ())
    for r in roles:
        entry = fonts_cfg.get(r, {})
        if isinstance(entry, dict):
            font_id = entry.get("font", "")
            info = _GOOGLE_FONT_FAMILY_MAP.get(font_id)
            if info:
                name, generic = info
                return f'"{name}", {generic}'
    return None


def _resolve_italic_family(cfg):
    """Resolve the CSS font-family for italic text.

    The PDF uses a separate font (body_italic) which may be a different
    family than the body font (e.g. Noto Serif Italic for a Noto Sans body).
    Returns the font-family string, or None if same as body.
    """
    fonts_cfg = cfg.get("fonts", {})
    body_id = fonts_cfg.get("body", {}).get("font", "")
    italic_id = fonts_cfg.get("body_italic", {}).get("font", "")
    if not italic_id or italic_id == body_id:
        return None
    info = _GOOGLE_FONT_FAMILY_MAP.get(italic_id)
    if info:
        name, generic = info
        return f'"{name}", {generic}'
    return None


def _emit_body(lines, sel, cfg):
    lines.append(f"{sel} strong, {sel} b {{ font-weight: {_bold_wght(cfg)}; }}")

    italic_family = _resolve_italic_family(cfg)
    if italic_family:
        italic_wght = cfg.get("fonts", {}).get("body_italic", {}).get("axes", {}).get("wght", 400)
        lines.append(f"{sel} em, {sel} i {{ font-family: {italic_family}; font-weight: {italic_wght}; }}")

    lines.append(f"{sel} p {{ margin-bottom: {su(_PARA_GAP)}; }}")
    lines.append(f"{sel} a {{ color: var(--link-color); }}")
    code_family = _resolve_font_family(cfg, "code")
    font_decl = f"  font-family: {code_family};\n" if code_family else ""
    lines.append(f"{sel} code {{")
    cb = cfg["code_block"]
    lines.append(f"  font-size: {su(cb['font_scale'])};")
    if font_decl:
        lines.append(font_decl.rstrip())
    lines.append(f"  color: var(--code-inline-fg);")
    lines.append(f"  background: var(--code-inline-bg);")
    lines.append(f"  border-radius: {su(3 / cfg['body_size'])};")
    lines.append(f"  padding: {su(1 / cfg['body_size'])} {su(4 / cfg['body_size'])};")
    lines.append(f"}}")
    lines.append("")


def _emit_headings(lines, sel, cfg):
    hcfg = cfg.get("headings", {})
    bw = _bold_wght(cfg)
    rt = hcfg.get("rule_thickness", 0)
    for level in range(1, 7):
        key = f"h{level}"
        h = hcfg.get(key, {})
        scale = h.get("scale", 1.0)
        lead = h.get("leading_scale", 1.45)
        sb = h.get("space_before", 1.5) * scale
        sa = h.get("space_after", 0.6) * scale
        lines.append(f"{sel} h{level} {{")
        lines.append(f"  font-size: {su(scale)};")
        lines.append(f"  line-height: {lead};")
        lines.append(f"  margin-top: {su(sb)};")
        lines.append(f"  margin-bottom: {su(sa)};")
        lines.append(f"  font-weight: {bw};")
        if h.get("rule") and rt:
            lines.append(f"  border-bottom: {_su_abs(cfg, rt)} solid var(--heading-rule-color);")
            lines.append(f"  padding-bottom: {su(_TIGHT_GAP)};")
        lines.append(f"}}")
    lines.append("")


def _emit_code_block(lines, sel, cfg, h1_scale):
    cb = cfg["code_block"]
    lines.append(f"{sel} pre.code-block {{")
    lines.append(f"  font-size: {su(cb['font_scale'])};")
    lines.append(f"  line-height: {cb['leading_scale']};")
    lines.append(f"  background: var(--code-bg);")
    lines.append(f"  border-left: {_su_abs(cfg, cb['bar_width'])} solid var(--accent);")
    lines.append(f"  padding: {_su_abs(cfg, cb['vertical_padding'])} {_su_abs(cfg, cb['right_padding'])} {_su_abs(cfg, cb['vertical_padding'])} {_su_abs(cfg, cb['left_padding'])};")
    lines.append(f"  overflow-x: auto;")
    lines.append(f"  margin-top: {su(_TIGHT_GAP)};")
    lines.append(f"  margin-bottom: {su(h1_scale)};")
    lines.append(f"}}")
    lines.append(f"{sel} pre.code-block code {{")
    lines.append(f"  color: var(--code-fg);")
    lines.append(f"  background: none;")
    lines.append(f"  font-size: inherit;")
    lines.append(f"}}")
    lines.append("")


def _emit_blockquote(lines, sel, cfg, h1_scale):
    bq = cfg.get("blockquote", {})
    lines.append(f"{sel} blockquote {{")
    lines.append(f"  border-left: {_su_abs(cfg, bq.get('bar_width', 3))} solid var(--accent);")
    lines.append(f"  background: var(--blockquote-bg);")
    lines.append(f"  color: var(--blockquote-fg);")
    lines.append(f"  font-style: italic;")
    lines.append(f"  padding: {_su_abs(cfg, bq.get('vertical_padding', 10))} {_su_abs(cfg, bq.get('right_padding', 15))} {_su_abs(cfg, bq.get('vertical_padding', 10))} {_su_abs(cfg, bq.get('left_padding', 15))};")
    lines.append(f"  margin-top: {su(_TIGHT_GAP)};")
    lines.append(f"  margin-bottom: {su(h1_scale)};")
    lines.append(f"}}")
    lines.append(f"{sel} blockquote p {{ margin-bottom: {su(_PARA_GAP)}; }}")
    lines.append(f"{sel} blockquote p:last-child {{ margin-bottom: 0; }}")

    variants = bq.get("variants", {})
    for vname, vcfg in variants.items():
        lines.append(f"{sel} blockquote.{vname} {{")
        lines.append(f"  border-left-color: {vcfg['bar_color']};")
        lines.append(f"  background: {vcfg['bg']};")
        lines.append(f"}}")
    lines.append("")


def _emit_list(lines, sel, cfg):
    lc = cfg.get("list", {})
    indent = lc.get("left_indent", 20)
    sb = lc.get("space_before", 4)
    sa = lc.get("space_after", 4)
    lines.append(f"{sel} ol, {sel} ul {{")
    lines.append(f"  padding-left: {_su_abs(cfg, indent)};")
    lines.append(f"  margin-top: {_su_abs(cfg, sb)};")
    lines.append(f"  margin-bottom: {_su_abs(cfg, sa)};")
    lines.append(f"}}")
    lines.append(f"{sel} li {{ margin-bottom: 0; }}")
    lines.append("")


def _emit_table(lines, sel, cfg, h1_scale):
    tc = cfg.get("table", {})
    tfs = tc.get("font_scale", 0.92)
    pad = tc.get("cell_padding", {})
    brw = tc.get("body_rule_width", 0.5)
    hrw = tc.get("header_rule_width", 0)
    cell_pad = (f"{_su_abs(cfg, pad.get('top', 5))} {_su_abs(cfg, pad.get('right', 10))} "
                f"{_su_abs(cfg, pad.get('bottom', 5))} {_su_abs(cfg, pad.get('left', 10))}")
    lines.append(f"{sel} table {{")
    lines.append(f"  font-size: {su(tfs)};")
    lines.append(f"  font-weight: {_body_wght(cfg)};")
    lines.append(f"  border-collapse: collapse;")
    lines.append(f"  width: 100%;")
    lines.append(f"  margin-top: {su(_TIGHT_GAP)};")
    lines.append(f"  margin-bottom: {su(h1_scale)};")
    lines.append(f"}}")
    lines.append(f"{sel} td {{")
    lines.append(f"  padding: {cell_pad};")
    lines.append(f"  text-align: left;")
    lines.append(f"  vertical-align: top;")
    if brw:
        lines.append(f"  border-bottom: {_su_abs(cfg, brw)} solid var(--table-rule-color);")
    lines.append(f"}}")
    thw = cfg.get("table_header_weight", _bold_wght(cfg))
    lines.append(f"{sel} th {{")
    lines.append(f"  padding: {cell_pad};")
    lines.append(f"  text-align: left;")
    lines.append(f"  vertical-align: top;")
    lines.append(f"  background: var(--table-header-bg);")
    lines.append(f"  color: var(--table-header-fg);")
    lines.append(f"  font-weight: {thw};")
    if hrw:
        lines.append(f"  border-bottom: {_su_abs(cfg, hrw)} solid var(--table-rule-color);")
    else:
        lines.append(f"  border-bottom: none;")
    lines.append(f"}}")

    stripe = cfg.get("table_stripe_bg")
    if stripe:
        lines.append(f"{sel} tbody tr:nth-child(even) {{ background: var(--table-stripe-bg); }}")
    lines.append("")


def _emit_front_matter(lines, sel, cfg):
    fm = cfg.get("front_matter", {})
    if not fm:
        return
    fs = fm.get("font_scale", 0.9)
    fm_bg = fm.get("bg", cfg.get("blockquote_bg", "#f7f7f7"))
    title_rt = cfg.get("title", {}).get("rule_thickness", 3)
    cell_v = fm.get("cell_v_pad", 3)
    inner_pad = fm.get("inner_pad", 12)
    bar_w = fm.get("bar_width", 3)
    label_col = fm.get("label_col", 130)
    left_pad = bar_w + inner_pad
    lines.append(f"{sel} dl.front-matter {{")
    lines.append(f"  font-size: {su(fs)};")
    lines.append(f"  line-height: {fm.get('leading_scale', 1.2)};")
    lines.append(f"  background: var(--blockquote-bg, {fm_bg});")
    lines.append(f"  border-left: {_su_abs(cfg, bar_w)} solid var(--accent);")
    if title_rt:
        lines.append(f"  border-top: {_su_abs(cfg, title_rt)} solid var(--heading-rule-color);")
    lines.append(f"  padding: {_su_abs(cfg, inner_pad)} {_su_abs(cfg, inner_pad)} {_su_abs(cfg, inner_pad)} {_su_abs(cfg, inner_pad)};")
    lines.append(f"  margin-top: 0;")
    lines.append(f"  margin-bottom: {_su_abs(cfg, fm.get('space_after', 0))};")
    lines.append(f"}}")
    lines.append(f"{sel} dl.front-matter dt {{")
    lines.append(f"  float: left;")
    lines.append(f"  width: {_su_abs(cfg, label_col)};")
    lines.append(f"  clear: left;")
    lines.append(f"  margin: 0;")
    lines.append(f"  padding: {_su_abs(cfg, cell_v)} 0;")
    lines.append(f"  font-weight: {_body_wght(cfg)};")
    lines.append(f"}}")
    lines.append(f"{sel} dl.front-matter dd {{")
    lines.append(f"  margin: 0 0 0 {_su_abs(cfg, label_col)};")
    lines.append(f"  padding: {_su_abs(cfg, cell_v)} 0;")
    lines.append(f"}}")
    lines.append("")


def _emit_wording(lines, sel, cfg):
    wcfg = cfg.get("wording", {})
    if not wcfg:
        return
    bw = wcfg.get("bar_width", 3)
    pad = wcfg.get("padding", 15)

    for cls in ("wording", "wording-add", "wording-remove"):
        v = wcfg.get(cls, {})
        if not v:
            continue
        lines.append(f"{sel} .{cls} {{")
        lines.append(f"  background: {v.get('bg', 'transparent')};")
        lines.append(f"  border-left: {_su_abs(cfg, bw)} solid {v.get('bar_color', '#999')};")
        lines.append(f"  padding: {_su_abs(cfg, pad)};")
        lines.append(f"  margin-top: {su(_TIGHT_GAP)};")
        lines.append(f"  margin-bottom: {su(_PARA_GAP)};")
        lines.append(f"}}")

    lines.append(f"{sel} ins, {sel} .wording-add {{ color: var(--ins-color); text-decoration: underline; }}")
    lines.append(f"{sel} del, {sel} .wording-remove {{ color: var(--del-color); text-decoration: line-through; }}")
    lines.append("")


def _emit_syntax(lines, sel, cfg):
    syntax = cfg.get("syntax", {})
    if not syntax:
        return
    for key, cls in _PYGMENTS_CLASS_MAP.items():
        color = syntax.get(key)
        if color:
            lines.append(f"{sel} .{cls} {{ color: {color}; }}")
    lines.append("")


def _emit_misc(lines, sel, cfg, h1_scale):
    hr_thickness = cfg.get("thematic_break", {}).get("thickness", 1)
    lines.append(f"{sel} hr {{ border: none; border-top: {_su_abs(cfg, hr_thickness)} solid var(--heading-rule-color); margin: {su(_PARA_GAP)} 0; }}")
    title_rt = cfg.get("title", {}).get("rule_thickness", 3)
    lines.append(f"{sel} hr.page-break {{ border-top-width: {_su_abs(cfg, title_rt)}; margin: {su(1.6)} 0; }}")
    lines.append(f"{sel} .title-block {{ margin-bottom: 0; display: flex; align-items: center; justify-content: space-between; }}")
    lines.append(f"{sel} .title-block h1 {{ margin: 0; flex: 1; }}")
    logo_h = cfg.get("title", {}).get("logo_height", 36)
    lines.append(f"{sel} .title-logo {{ height: {_su_abs(cfg, logo_h)}; margin-left: var(--u); }}")

    title_cfg = cfg.get("title", {})
    rt = title_cfg.get("rule_thickness", 3)
    if rt:
        lines.append(f"{sel} .title-block {{ border-bottom: {_su_abs(cfg, rt)} solid var(--heading-rule-color); padding-bottom: {su(0.8)}; }}")
    lines.append(f"{sel} .title-block.no-rule {{ border-bottom: none; padding-bottom: 0; }}")

    toc_fs = cfg.get("toc_font_scale", 0.9)
    fm_cfg = cfg.get("front_matter", {})
    toc_bg = fm_cfg.get("bg", cfg.get("blockquote_bg", "#f7f7f7"))
    toc_pad = fm_cfg.get("inner_pad", 12)
    pn_color = cfg.get("page_number_color", "#888")
    toc_rt = cfg.get("toc_rule_thickness", 2)
    lines.append(f"{sel} nav.toc {{")
    lines.append(f"  margin-top: {su(h1_scale)};")
    lines.append(f"  margin-bottom: {su(h1_scale * 2)};")
    lines.append(f"  font-size: {su(toc_fs)};")
    lines.append(f"  background: var(--blockquote-bg, {toc_bg});")
    lines.append(f"  padding: {_su_abs(cfg, toc_pad)};")
    lines.append(f"  color: {pn_color};")
    lines.append(f"}}")
    lines.append(f"{sel} nav.toc h2 {{")
    lines.append(f"  font-size: var(--u);")
    lines.append(f"  color: {pn_color};")
    lines.append(f"  margin-top: 0;")
    lines.append(f"}}")
    if toc_rt:
        lines.append(f"{sel} nav.toc h2 {{ padding-bottom: {su(_TIGHT_GAP)}; border-bottom: {_su_abs(cfg, toc_rt)} solid var(--heading-rule-color); margin-bottom: {su(_PARA_GAP * 2)}; }}")
    lines.append(f"{sel} nav.toc ul {{ list-style: none; padding-left: 0; }}")
    toc_indent = cfg.get("toc_indent", 18)
    lines.append(f"{sel} nav.toc li {{ padding-left: {_su_abs(cfg, toc_indent)}; }}")
    lines.append(f"{sel} nav.toc a {{ color: {pn_color}; text-decoration: none; }}")
    lines.append(f"{sel} figure {{ margin: {su(_TIGHT_GAP)} 0 {su(_PARA_GAP)} 0; }}")
    lines.append(f"{sel} figure img {{ max-width: 100%; height: auto; }}")
    lines.append("")
