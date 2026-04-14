"""PDF to Markdown converter - pipeline entry point."""

import logging
from pathlib import Path

from .cleanup import (_get_edge_items, detect_repeating, strip_repeating,
                      cleanup_text, find_hidden_regions, strip_hidden_blocks)
from .extract import extract_mupdf, extract_spatial, collect_links, attach_links
from .spans import normalize_spans
from .structure import compare_extractions, structure_sections
from .table import detect_tables, exclude_table_regions
from .wg21 import extract_metadata_from_blocks
from .emit import emit_markdown, emit_prompts
from .types import SectionKind, is_readable
from ..toc import find_toc_indices

_log = logging.getLogger(__name__)


def convert_pdf(path: Path) -> tuple[str, str | None]:
    """Convert a PDF file to Markdown.

    Returns (markdown_text, prompts_text_or_none).
    """
    import fitz

    path = Path(path)
    doc = fitz.open(str(path))
    try:
        page_count = doc.page_count
        if page_count == 0:
            return "", None

        all_mupdf_blocks = []
        all_spatial_blocks = []
        all_edge_items = []
        pages_data = []

        for pg_num in range(page_count):
            page = doc[pg_num]
            page_height = page.rect.height

            mupdf_blocks = extract_mupdf(page, pg_num)
            spatial_blocks = extract_spatial(page, pg_num)

            edge_items = _get_edge_items(mupdf_blocks, pg_num, page_height)
            all_edge_items.append(edge_items)

            links = collect_links(page)
            attach_links(mupdf_blocks, links)
            attach_links(spatial_blocks, links)

            pages_data.append(pg_num)
            all_mupdf_blocks.extend(mupdf_blocks)
            all_spatial_blocks.extend(spatial_blocks)

        from collections import Counter
        font_counts: Counter[str] = Counter()
        for b in all_mupdf_blocks:
            for ln in b.lines:
                for s in ln.spans:
                    if s.text.strip():
                        font_counts[s.font_name.lower()] += len(s.text)
        body_fonts = {f for f, _ in font_counts.most_common(5)}

        all_hidden: set = set()
        for pg_num in range(page_count):
            page = doc[pg_num]
            all_hidden |= find_hidden_regions(page, body_fonts)
    finally:
        doc.close()

    if all_hidden:
        _log.info("Stripping text hidden by %d covered regions", len(all_hidden))
        all_mupdf_blocks = strip_hidden_blocks(all_mupdf_blocks, all_hidden)
        all_spatial_blocks = strip_hidden_blocks(all_spatial_blocks, all_hidden)

    mupdf_text = "\n".join(b.text for b in all_mupdf_blocks)
    if not is_readable(mupdf_text):
        _log.warning("Extracted text is not readable (encrypted/scanned PDF?)")
        return "", None

    repeating = detect_repeating(all_edge_items, page_count)
    if repeating:
        _log.info("Stripping %d repeating header/footer patterns", len(repeating))
        all_mupdf_blocks = strip_repeating(all_mupdf_blocks, repeating)
        all_spatial_blocks = strip_repeating(all_spatial_blocks, repeating)

    all_mupdf_blocks = cleanup_text(all_mupdf_blocks)
    all_spatial_blocks = cleanup_text(all_spatial_blocks)

    all_mupdf_blocks = normalize_spans(all_mupdf_blocks)
    all_spatial_blocks = normalize_spans(all_spatial_blocks)

    wg21_metadata, meta_consumed = extract_metadata_from_blocks(all_mupdf_blocks)
    if meta_consumed:
        consumed_bboxes = [all_mupdf_blocks[i].bbox for i in meta_consumed
                           if i < len(all_mupdf_blocks)]
        all_mupdf_blocks = [b for i, b in enumerate(all_mupdf_blocks)
                            if i not in meta_consumed]
        all_spatial_blocks = [
            b for b in all_spatial_blocks
            if not any(b.page_num == 0
                       and abs(b.bbox[1] - cb[1]) < 5
                       for cb in consumed_bboxes)
        ]

    table_sections, all_mupdf_blocks = detect_tables(all_mupdf_blocks)
    if table_sections:
        _log.info("Detected %d table(s)", len(table_sections))
        all_spatial_blocks = exclude_table_regions(
            all_spatial_blocks, table_sections)

    sections = compare_extractions(all_mupdf_blocks, all_spatial_blocks)

    for ts in table_sections:
        inserted = False
        for i, sec in enumerate(sections):
            if sec.page_num > ts.page_num:
                sections.insert(i, ts)
                inserted = True
                break
            if (sec.page_num == ts.page_num and sec.lines
                    and ts.lines
                    and sec.lines[0].bbox[1] > ts.lines[0].bbox[1]):
                sections.insert(i, ts)
                inserted = True
                break
        if not inserted:
            sections.append(ts)

    has_title = "title" in wg21_metadata
    structure_metadata, sections = structure_sections(sections, has_title=has_title)
    metadata = {**structure_metadata, **wg21_metadata}

    texts = [sec.text.split("\n")[0].strip() for sec in sections]
    heading_texts = {sec.text.split("\n")[0].strip()
                     for sec in sections if sec.kind == SectionKind.HEADING}
    toc_indices = find_toc_indices(texts, heading_texts)
    if toc_indices:
        sections = [s for i, s in enumerate(sections) if i not in toc_indices]

    md = emit_markdown(metadata, sections)
    prompts = emit_prompts(metadata, sections)

    return md, prompts
