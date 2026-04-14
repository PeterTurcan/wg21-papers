"""Span normalization - snap style boundaries to word edges.

When a bold or italic boundary falls inside a word (no whitespace
between adjacent spans with different styles), extend the styled
region to the word boundary. Monospace boundaries are exempt
because code boundaries are intentional.
"""

import logging

from .types import Block, Line, Span

_log = logging.getLogger(__name__)


def _is_style_span(span: Span) -> tuple[bool, bool]:
    """Return (bold, italic) flags, ignoring monospace."""
    return (span.bold, span.italic)


def _spans_touch(prev: Span, cur: Span) -> bool:
    """Check if two spans are adjacent with no whitespace between them."""
    if not prev.text or not cur.text:
        return False
    return not prev.text[-1].isspace() and not cur.text[0].isspace()


def _find_word_boundary_left(text: str) -> int:
    """Find the start of the last word in text (index of first char of word)."""
    i = len(text) - 1
    while i >= 0 and not text[i].isspace():
        i -= 1
    return i + 1


def _find_word_boundary_right(text: str) -> int:
    """Find the end of the first word in text (index after last char of word)."""
    i = 0
    while i < len(text) and not text[i].isspace():
        i += 1
    return i


def _normalize_line_spans(spans: list[Span]) -> list[Span]:
    """Normalize style boundaries within a single line's spans.

    If a style change (bold/italic) falls mid-word between two
    non-monospace spans, move text across the boundary so the style
    change aligns with a word edge.
    """
    if len(spans) < 2:
        return spans

    result = list(spans)

    i = 1
    while i < len(result):
        prev = result[i - 1]
        cur = result[i]

        if prev.monospace or cur.monospace:
            i += 1
            continue

        prev_style = _is_style_span(prev)
        cur_style = _is_style_span(cur)

        if prev_style == cur_style:
            i += 1
            continue

        if not _spans_touch(prev, cur):
            i += 1
            continue

        wb = _find_word_boundary_left(prev.text)
        if wb < len(prev.text) and wb > 0:
            fragment = prev.text[wb:]
            result[i - 1] = Span(
                text=prev.text[:wb],
                font_name=prev.font_name,
                font_size=prev.font_size,
                bold=prev.bold,
                italic=prev.italic,
                monospace=prev.monospace,
                bbox=prev.bbox,
                origin=prev.origin,
                color=prev.color,
                link_url=prev.link_url,
            )
            result[i] = Span(
                text=fragment + cur.text,
                font_name=cur.font_name,
                font_size=cur.font_size,
                bold=cur.bold,
                italic=cur.italic,
                monospace=cur.monospace,
                bbox=cur.bbox,
                origin=cur.origin,
                color=cur.color,
                link_url=cur.link_url,
            )
            if not result[i - 1].text:
                result.pop(i - 1)
                continue

        i += 1

    i = 0
    while i < len(result) - 1:
        cur = result[i]
        nxt = result[i + 1]

        if cur.monospace or nxt.monospace:
            i += 1
            continue

        cur_style = _is_style_span(cur)
        nxt_style = _is_style_span(nxt)

        if cur_style == nxt_style:
            i += 1
            continue

        if not _spans_touch(cur, nxt):
            i += 1
            continue

        wb = _find_word_boundary_right(nxt.text)
        if wb > 0 and wb < len(nxt.text):
            fragment = nxt.text[:wb]
            result[i] = Span(
                text=cur.text + fragment,
                font_name=cur.font_name,
                font_size=cur.font_size,
                bold=cur.bold,
                italic=cur.italic,
                monospace=cur.monospace,
                bbox=cur.bbox,
                origin=cur.origin,
                color=cur.color,
                link_url=cur.link_url,
            )
            result[i + 1] = Span(
                text=nxt.text[wb:],
                font_name=nxt.font_name,
                font_size=nxt.font_size,
                bold=nxt.bold,
                italic=nxt.italic,
                monospace=nxt.monospace,
                bbox=nxt.bbox,
                origin=nxt.origin,
                color=nxt.color,
                link_url=nxt.link_url,
            )
            if not result[i + 1].text:
                result.pop(i + 1)
                continue

        i += 1

    return result


def normalize_spans(blocks: list[Block]) -> list[Block]:
    """Snap bold/italic style boundaries to word edges across all blocks.

    Monospace boundaries are exempt (code boundaries are intentional).
    """
    result = []
    for block in blocks:
        new_lines = []
        for line in block.lines:
            new_spans = _normalize_line_spans(line.spans)
            new_lines.append(Line(
                spans=new_spans,
                bbox=line.bbox,
                page_num=line.page_num,
            ))
        result.append(Block(
            lines=new_lines,
            bbox=block.bbox,
            page_num=block.page_num,
        ))
    return result
