"""HTML build orchestration. Parallel to builder.py for the PDF path.
No font loading, no ReportLab imports."""

from html import escape, unescape
from pathlib import Path

import mistune

from .colors import resolve_colors
from .config import (
    CSS_DIR,
    IMAGES_DIR,
    extract_front_matter,
    merge_config,
)
from .css import generate_css
from .html_renderer import HTMLRenderer


def _style_slug(cfg):
    return cfg.get("name", "default").lower().replace(" ", "-")


def build_html(md_path, output_path, cli_cfg, style,
               mode="full", inline_css=False):
    """Render a markdown file to HTML.

    Args:
        md_path: path to the markdown source file
        output_path: path for the output HTML (parent dirs created)
        cli_cfg: dict of CLI overrides (toc, no_toc)
        style: style dict from load_style (may be mutated)
        mode: "full" for complete HTML5 document,
              "fragment" for article-only output
        inline_css: if True, embed CSS in <style> tag instead of
                    writing a separate .css file

    Returns:
        Path to the output HTML.
    """
    md_path = Path(md_path)
    md_text = md_path.read_text(encoding="utf-8")
    md_dir = md_path.parent

    fm, body_text = extract_front_matter(md_text)
    cfg = merge_config(cli_cfg, fm, style)
    resolve_colors(cfg, None)

    md = mistune.create_markdown(
        renderer="ast", plugins=["strikethrough", "table"])
    tokens = md(body_text)

    has_fm_title = bool(fm.get("title"))
    display_title = str(fm["title"]) if has_fm_title else ""

    renderer = HTMLRenderer(cfg, md_dir, has_fm_title=has_fm_title)
    body_html = renderer.render(tokens)

    parts = []

    logo_path = cfg.get("logo")
    if logo_path:
        lp = Path(logo_path)
        if not lp.is_absolute():
            candidates = [IMAGES_DIR / logo_path, md_dir / logo_path]
            lp = next((c for c in candidates if c.exists()), None)
        if lp and lp.exists():
            logo_path = str(lp)
        else:
            logo_path = None

    fm_html = renderer.render_front_matter(fm)
    if has_fm_title:
        hide_title_rule = bool(fm_html)
        parts.append(renderer.render_title_block(
            escape(unescape(display_title)),
            hide_rule=hide_title_rule,
            logo_path=logo_path))
    if fm_html:
        parts.append(fm_html)

    toc = cfg.get("toc")
    if toc is True or (toc == "auto" and fm_html):
        parts.append(renderer.render_toc())

    parts.append(body_html)

    style_name = _style_slug(cfg)
    article_content = "".join(parts)
    article = f'<article class="scrivener {escape(style_name)}">\n{article_content}</article>\n'

    css_text = generate_css(cfg, mode=mode)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if mode == "full":
        html = _wrap_full_page(display_title, css_text, article,
                               style_name, inline_css)
        output_path.write_text(html, encoding="utf-8")
    else:
        if inline_css:
            html = f"<style>\n{css_text}</style>\n{article}"
        else:
            html = article
        output_path.write_text(html, encoding="utf-8")

    if not inline_css:
        css_path = output_path.parent / f"{style_name}.css"
        css_path.write_text(css_text, encoding="utf-8")

    return output_path


def build_css(style, output_path=None, mode="fragment"):
    """Generate CSS for a style and write it to a file.

    Args:
        style: resolved style dict
        output_path: where to write the CSS (default: css/{name}.css)
        mode: "full" or "fragment"

    Returns:
        Path to the written CSS file.
    """
    resolve_colors(style, None)
    css_text = generate_css(style, mode=mode)

    style_name = _style_slug(style)
    if output_path is None:
        CSS_DIR.mkdir(parents=True, exist_ok=True)
        output_path = CSS_DIR / f"{style_name}.css"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(css_text, encoding="utf-8")
    return output_path


def _wrap_full_page(title, css_text, article, style_name, inline_css):
    head_parts = [
        '<!DOCTYPE html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="utf-8">',
        f'<title>{escape(title)}</title>',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
    ]

    if inline_css:
        head_parts.append(f'<style>\n{css_text}</style>')
    else:
        head_parts.append(f'<link rel="stylesheet" href="{escape(style_name)}.css">')

    head_parts.append('</head>')
    head_parts.append('<body>')

    return "\n".join(head_parts) + "\n" + article + "</body>\n</html>\n"
