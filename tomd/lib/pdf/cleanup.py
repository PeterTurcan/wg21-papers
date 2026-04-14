"""Header/footer detection and text cleanup for PDF extraction."""

import logging
import re
from collections import defaultdict

from .types import (
    Block, Line, Span, PageEdgeItem,
    Y_TOLERANCE, REPEATING_THRESHOLD, EDGE_ITEMS_PER_PAGE,
    _PAGE_NUM_RE, _DOC_NUM_RE, _COMPOUND_PREFIXES,
)

_log = logging.getLogger(__name__)


def _get_edge_items(blocks: list[Block], page_num: int,
                    page_height: float) -> list[PageEdgeItem]:
    """Get the top N and bottom N text items from a page by y-coordinate."""
    items = []
    for block in blocks:
        for line in block.lines:
            text = line.text.strip()
            if not text:
                continue
            y_center = (line.bbox[1] + line.bbox[3]) / 2.0
            items.append(PageEdgeItem(
                text=text,
                y=y_center,
                page_num=page_num,
                bbox=line.bbox,
            ))

    if not items:
        return []

    items.sort(key=lambda it: it.y)
    top = items[:EDGE_ITEMS_PER_PAGE]
    bottom = items[-EDGE_ITEMS_PER_PAGE:]
    seen = set()
    result = []
    for it in top + bottom:
        key = (it.text, round(it.y, 1))
        if key not in seen:
            seen.add(key)
            result.append(it)
    return result


def detect_repeating(all_edge_items: list[list[PageEdgeItem]],
                     total_pages: int) -> set[tuple[float, str]]:
    """Identify header/footer items that repeat across pages.

    For each page, captures the top 3 and bottom 3 items by
    y-coordinate. Items appearing at the same y-position on more
    than half the pages are classified as repeating.

    Returns a set of (y_region, text_or_pattern) tuples to strip.
    """
    if total_pages < 3:
        return set()

    threshold = total_pages * REPEATING_THRESHOLD
    y_buckets: dict[float, list[PageEdgeItem]] = defaultdict(list)

    for page_items in all_edge_items:
        for item in page_items:
            y_key = round(item.y / Y_TOLERANCE) * Y_TOLERANCE
            y_buckets[y_key].append(item)

    repeating = set()
    for y_key, items in y_buckets.items():
        pages_seen = len(set(it.page_num for it in items))
        if pages_seen < threshold:
            continue

        texts = [it.text for it in items]
        if len(set(texts)) == 1:
            repeating.add((y_key, texts[0]))
            _log.debug("Repeating exact: y=%.1f text=%r", y_key, texts[0])
            continue

        if all(_PAGE_NUM_RE.match(t) for t in texts):
            repeating.add((y_key, "__PAGE_NUM__"))
            _log.debug("Repeating page number at y=%.1f", y_key)
            continue

        if all(_DOC_NUM_RE.search(t) for t in texts):
            repeating.add((y_key, "__DOC_NUM__"))
            _log.debug("Repeating doc number at y=%.1f", y_key)
            continue

    return repeating


def strip_repeating(blocks: list[Block], repeating: set[tuple[float, str]],
                    ) -> list[Block]:
    """Remove lines matching repeating header/footer patterns from blocks."""
    if not repeating:
        return blocks

    result = []
    for block in blocks:
        kept_lines = []
        for line in block.lines:
            text = line.text.strip()
            if not text:
                kept_lines.append(line)
                continue
            y_center = (line.bbox[1] + line.bbox[3]) / 2.0
            y_key = round(y_center / Y_TOLERANCE) * Y_TOLERANCE
            stripped = False
            for ry, rpattern in repeating:
                if abs(y_key - ry) > Y_TOLERANCE:
                    continue
                if rpattern == text:
                    stripped = True
                    break
                if rpattern == "__PAGE_NUM__" and _PAGE_NUM_RE.match(text):
                    stripped = True
                    break
                if rpattern == "__DOC_NUM__" and _DOC_NUM_RE.search(text):
                    stripped = True
                    break
            if not stripped:
                kept_lines.append(line)
        if kept_lines:
            result.append(Block(
                lines=kept_lines,
                bbox=block.bbox,
                page_num=block.page_num,
            ))
    return result


def dehyphenate(text: str) -> str:
    """Join words broken by end-of-line hyphenation.

    When a line ends with a hyphen and the next starts with a lowercase
    letter, joins the word. Skips known compound prefixes.
    """
    lines = text.split("\n")
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if (i + 1 < len(lines)
                and line.endswith("-")
                and len(line) > 1
                and lines[i + 1]
                and lines[i + 1][0].islower()):
            prefix = line[:-1].split()[-1].lower() if line[:-1].split() else ""
            if prefix not in _COMPOUND_PREFIXES:
                next_word = lines[i + 1].split()[0] if lines[i + 1].split() else ""
                joined = line[:-1] + next_word
                rest = lines[i + 1][len(next_word):].lstrip()
                result.append(joined)
                if rest:
                    lines[i + 1] = rest
                else:
                    i += 1
                i += 1
                continue
        result.append(line)
        i += 1
    return "\n".join(result)


def join_cross_page(blocks: list[Block]) -> list[Block]:
    """Join paragraphs that span page boundaries.

    When the last block on page N ends without terminal punctuation
    and the first block on page N+1 starts with a lowercase letter,
    merge them into one block.
    """
    if len(blocks) < 2:
        return blocks

    _TERMINAL = frozenset(".?!:")
    result = [blocks[0]]

    for block in blocks[1:]:
        prev = result[-1]
        prev_text = prev.text.rstrip()
        cur_text = block.text.lstrip()

        if (prev.page_num != block.page_num
                and prev_text
                and cur_text
                and prev_text[-1] not in _TERMINAL
                and cur_text[0].islower()):
            prev.lines.extend(block.lines)
            bboxes = [ln.bbox for ln in prev.lines]
            prev.bbox = (
                min(b[0] for b in bboxes),
                min(b[1] for b in bboxes),
                max(b[2] for b in bboxes),
                max(b[3] for b in bboxes),
            )
        else:
            result.append(block)

    return result


_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
_NBSP = "\u00a0"
_ZERO_WIDTH = frozenset("\u200b\u200c\u200d\ufeff\u200e\u200f")


def strip_zero_width(text: str) -> str:
    """Remove zero-width Unicode characters."""
    return "".join(c for c in text if c not in _ZERO_WIDTH)


def normalize_whitespace(text: str) -> str:
    """Collapse runs of spaces, replace non-breaking spaces, strip trailing."""
    text = strip_zero_width(text)
    text = text.replace(_NBSP, " ")
    text = _MULTI_SPACE_RE.sub(" ", text)
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines)


def find_hidden_regions(page, body_fonts: set[str] | None = None,
                        ) -> set[tuple[float, float, float, float]]:
    """Find regions of hidden text on a page.

    Two detection methods:
      1. Rendering mode 3 (declared invisible in the PDF spec) -
         general, reliable, works on any PDF.
      2. Non-document font with non-black color (Google Docs widget
         artifacts) - catches UI framework text like dropdown values
         rendered in Roboto/Material fonts.
    """
    hidden_bboxes = set()

    for span in page.get_texttrace():
        if span.get("type") == 3:
            for ch in span.get("chars", []):
                hidden_bboxes.add(tuple(ch[3]))
            continue

        if body_fonts is not None:
            font = span.get("font", "")
            font_lower = font.lower()
            color = span.get("color")
            is_black = (color == 0 or color == (0, 0, 0)
                        or color == 0x000000)
            if (font_lower not in body_fonts
                    and not is_black
                    and any(p in font_lower
                            for p in ("roboto", "google", "material"))):
                for ch in span.get("chars", []):
                    hidden_bboxes.add(tuple(ch[3]))

    return hidden_bboxes


def strip_hidden_blocks(blocks: list[Block],
                        hidden_bboxes: set[tuple]) -> list[Block]:
    """Remove blocks whose text is entirely within hidden regions."""
    if not hidden_bboxes:
        return blocks

    import fitz
    result = []
    for block in blocks:
        all_hidden = True
        for line in block.lines:
            for span in line.spans:
                if not span.text.strip():
                    continue
                span_rect = fitz.Rect(span.bbox)
                is_hidden = any(
                    fitz.Rect(hb).intersects(span_rect)
                    for hb in hidden_bboxes
                )
                if not is_hidden:
                    all_hidden = False
                    break
            if not all_hidden:
                break
        if not all_hidden:
            result.append(block)
    return result


def cleanup_text(blocks: list[Block]) -> list[Block]:
    """Apply all text cleanup operations to extracted blocks."""
    result = []
    for block in blocks:
        cleaned_lines = []
        for line in block.lines:
            cleaned_spans = []
            for span in line.spans:
                new_text = span.text.replace(_NBSP, " ")
                if not span.monospace:
                    new_text = _MULTI_SPACE_RE.sub(" ", new_text)
                cleaned_spans.append(Span(
                    text=new_text,
                    font_name=span.font_name,
                    font_size=span.font_size,
                    bold=span.bold,
                    italic=span.italic,
                    monospace=span.monospace,
                    bbox=span.bbox,
                    origin=span.origin,
                    color=span.color,
                    link_url=span.link_url,
                ))
            cleaned_lines.append(Line(
                spans=cleaned_spans,
                bbox=line.bbox,
                page_num=line.page_num,
            ))
        result.append(Block(
            lines=cleaned_lines,
            bbox=block.bbox,
            page_num=block.page_num,
        ))

    result = join_cross_page(result)

    dehyphenated = []
    for block in result:
        new_lines = []
        for i, line in enumerate(block.lines):
            if (i + 1 < len(block.lines)
                    and line.spans and block.lines[i + 1].spans):
                last_span = line.spans[-1]
                next_first = block.lines[i + 1].spans[0]
                if (last_span.text.endswith("-")
                        and len(last_span.text) > 1
                        and next_first.text
                        and next_first.text[0].islower()):
                    prefix = last_span.text[:-1].split()[-1].lower() if last_span.text[:-1].split() else ""
                    if prefix not in _COMPOUND_PREFIXES:
                        new_lines.append(line)
                        continue
            new_lines.append(line)
        dehyphenated.append(Block(
            lines=new_lines,
            bbox=block.bbox,
            page_num=block.page_num,
        ))

    return dehyphenated
