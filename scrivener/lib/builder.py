"""PDF build orchestration. Wires config, fonts, renderer, and
ReportLab document together."""

from html import unescape
from pathlib import Path

import mistune
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from reportlab.platypus.flowables import HRFlowable

from . import escape_xml
from .colors import resolve_colors
from .config import (
    IMAGES_DIR,
    PAGE_CONFIGS,
    extract_front_matter,
    merge_config,
)
from .font_manifest import load_font_manifest
from .flowables import PageChrome, TitleEnd
from .fonts import ensure_fonts_ready
from .renderer import ASTRenderer


def build_pdf(md_path, output_path, cli_cfg, style):
    """Render a markdown file to PDF.

    Handles font manifest loading, font downloading, font registration,
    color resolution, and ReportLab document construction. Callers do
    not need to manage fonts - this function is self-contained.

    Args:
        md_path: path to the markdown source file
        output_path: path for the output PDF (parent dirs created)
        cli_cfg: dict of CLI overrides (logo, toc, no_toc)
        style: style dict from load_style (may be mutated)

    Returns:
        Path to the output PDF.

    Side effects:
        - Downloads missing fonts to the shared .fonts/ cache
        - Registers fonts globally in ReportLab
        - Creates output parent directories
    """
    md_path = Path(md_path)
    md_text = md_path.read_text(encoding="utf-8")
    md_dir = md_path.parent

    fm, body_text = extract_front_matter(md_text)
    cfg = merge_config(cli_cfg, fm, style)

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
    cfg["logo"] = logo_path

    resolve_colors(cfg, logo_path)
    manifest = load_font_manifest()
    fonts_dir, body_cmap, fallback_chain = ensure_fonts_ready(cfg, manifest)

    page_size_name = cfg.get("page_size", "letter")
    if page_size_name not in PAGE_CONFIGS:
        valid = ", ".join(sorted(PAGE_CONFIGS))
        raise ValueError(f"unknown page_size '{page_size_name}'. valid: {valid}")
    pc = PAGE_CONFIGS[page_size_name]
    page_size = pc["size"]
    margin = pc["margin"]
    page_w, page_h = page_size
    content_width = page_w - 2 * margin
    page_geometry = {"page_w": page_w, "page_h": page_h,
                     "margin": margin, "content_width": content_width}

    md = mistune.create_markdown(
        renderer="ast", plugins=["strikethrough", "table"])
    tokens = md(body_text)

    has_fm_title = bool(fm.get("title"))
    renderer = ASTRenderer(cfg, body_cmap, fallback_chain, content_width,
                           md_dir, has_fm_title=has_fm_title,
                           page_geometry=page_geometry)
    flowables = renderer.render(tokens)

    fm_flows = renderer.build_front_matter_flowables(fm)

    title_flows = []
    rest_flows = flowables

    if has_fm_title:
        title_text = escape_xml(unescape(str(fm["title"])))
        title_flows = renderer.title_block(title_text)
        if fm_flows:
            title_flows = [f for f in title_flows if not isinstance(f, HRFlowable)]
    else:
        in_title = True
        title_flows = []
        rest_flows = []
        for f in flowables:
            if in_title:
                title_flows.append(f)
                if isinstance(f, TitleEnd):
                    in_title = False
            else:
                rest_flows.append(f)
        if not title_flows or in_title:
            rest_flows = flowables
            title_flows = []

    all_flows = title_flows + fm_flows
    toc = cfg.get("toc")
    if toc is True or (toc == "auto" and fm_flows):
        all_flows.extend(renderer.build_toc_flowables())
    all_flows.extend(rest_flows)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    top_m = margin
    bot_m = margin
    left_m = margin
    right_m = margin

    frame = Frame(
        left_m, bot_m,
        page_w - left_m - right_m,
        page_h - top_m - bot_m,
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0,
        id="content")

    header_draw = PageChrome(cfg, page_geometry=page_geometry)

    doc = BaseDocTemplate(
        str(output_path),
        pagesize=page_size,
        topMargin=top_m,
        bottomMargin=bot_m,
        leftMargin=left_m,
        rightMargin=right_m,
        title=fm.get("title", ""),
        author=", ".join(fm.get("reply-to", []))
               if isinstance(fm.get("reply-to"), list)
               else str(fm.get("reply-to", "")),
    )
    doc.addPageTemplates([
        PageTemplate(id="all", frames=[frame], onPage=header_draw),
    ])
    doc.build(all_flows)
    return output_path
