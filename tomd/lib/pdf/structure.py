"""Dual-path comparison, heading intelligence, and document structuring."""

import logging
import re
from collections import Counter

from .types import (
    Block, Line, Span, Section, SectionKind, Confidence,
    SIMILARITY_THRESHOLD,
    _SECTION_NUM_RE, _DOC_FIELD_RE, _REPLY_TO_RE, _AUDIENCE_RE, _DATE_RE,
    _BULLET_RE, _NUMBERED_LIST_RE, _KNOWN_SECTIONS,
)

HEADING_SIZE_RATIO = 1.05
TITLE_SIZE_RATIO = 1.2

_log = logging.getLogger(__name__)


def _block_words(blocks: list[Block]) -> list[str]:
    """Flatten blocks to a list of words for comparison."""
    words = []
    for block in blocks:
        for line in block.lines:
            words.extend(line.text.split())
    return words


def _word_similarity(words_a: list[str], words_b: list[str]) -> float:
    """Compute word-level similarity between two word lists."""
    if not words_a and not words_b:
        return 1.0
    if not words_a or not words_b:
        return 0.0
    set_a = Counter(words_a)
    set_b = Counter(words_b)
    intersection = sum((set_a & set_b).values())
    total = max(sum(set_a.values()), sum(set_b.values()))
    return intersection / total if total > 0 else 0.0


def compare_extractions(mupdf_blocks: list[Block],
                        spatial_blocks: list[Block],
                        ) -> list[Section]:
    """Compare two extraction paths using coarse word-level similarity.

    Walks both paths by page, comparing text region by region.
    High similarity = confident. Low similarity = uncertain.
    """
    mupdf_by_page: dict[int, list[Block]] = {}
    spatial_by_page: dict[int, list[Block]] = {}
    for b in mupdf_blocks:
        mupdf_by_page.setdefault(b.page_num, []).append(b)
    for b in spatial_blocks:
        spatial_by_page.setdefault(b.page_num, []).append(b)

    all_pages = sorted(set(mupdf_by_page) | set(spatial_by_page))
    sections: list[Section] = []

    for pg in all_pages:
        m_blocks = mupdf_by_page.get(pg, [])
        s_blocks = spatial_by_page.get(pg, [])

        m_words = _block_words(m_blocks)
        s_words = _block_words(s_blocks)
        sim = _word_similarity(m_words, s_words)

        if sim >= SIMILARITY_THRESHOLD:
            for block in m_blocks:
                sections.append(Section(
                    kind=SectionKind.PARAGRAPH,
                    text=block.text,
                    confidence=Confidence.HIGH,
                    lines=block.lines,
                    page_num=block.page_num,
                    font_size=block.font_size,
                ))
        else:
            _log.debug("Page %d: similarity %.2f < threshold, marking uncertain",
                        pg, sim)
            m_text = "\n\n".join(b.text for b in m_blocks)
            s_text = "\n\n".join(b.text for b in s_blocks)
            sections.append(Section(
                kind=SectionKind.UNCERTAIN,
                text=m_text,
                confidence=Confidence.UNCERTAIN,
                mupdf_text=m_text,
                spatial_text=s_text,
                page_num=pg,
                lines=[ln for b in m_blocks for ln in b.lines],
            ))

    return sections


def _detect_body_size(sections: list[Section]) -> float:
    """Find the most common font size across all sections (= body text)."""
    sizes: Counter[float] = Counter()
    for sec in sections:
        for line in sec.lines:
            for span in line.spans:
                if span.text.strip():
                    sizes[span.font_size] += len(span.text)
    if not sizes:
        return 11.0
    return sizes.most_common(1)[0][0]


def _rank_font_sizes(sections: list[Section],
                     body_size: float) -> dict[float, int]:
    """Rank font sizes larger than body. Returns {size: heading_level}."""
    sizes = set()
    for sec in sections:
        for line in sec.lines:
            fs = line.font_size
            if fs > body_size * HEADING_SIZE_RATIO:
                sizes.add(fs)
    ranked = sorted(sizes, reverse=True)
    return {sz: i + 1 for i, sz in enumerate(ranked)}


def _heading_level_from_number(section_num: str) -> int:
    """Compute heading level from dotted decimal: depth + 1."""
    parts = section_num.split(".")
    return len(parts) + 1


def _heading_confidence(has_number: bool, number_level: int,
                        font_level: int | None, is_bold: bool,
                        is_known: bool) -> tuple[int, Confidence]:
    """Determine heading level and confidence from multiple signals."""
    if has_number:
        level = number_level
        if font_level is not None and font_level == level:
            if is_bold:
                return level, Confidence.HIGH
            return level, Confidence.HIGH
        if font_level is not None:
            return level, Confidence.MEDIUM
        return level, Confidence.MEDIUM

    if font_level is not None:
        if is_known and is_bold:
            return 2, Confidence.MEDIUM
        if is_known:
            return 2, Confidence.MEDIUM
        if is_bold:
            return font_level + 1, Confidence.LOW
        return font_level + 1, Confidence.LOW

    if is_known:
        return 2, Confidence.LOW

    return 0, Confidence.UNCERTAIN


def _extract_metadata(sections: list[Section]) -> tuple[dict, list[Section]]:
    """Pull WG21 metadata fields from early sections into a dict.

    Returns (metadata_dict, remaining_sections).
    """
    meta: dict[str, str] = {}
    remaining = []
    metadata_zone = True

    for sec in sections:
        if sec.kind == SectionKind.UNCERTAIN:
            remaining.append(sec)
            continue

        text = sec.text.strip()
        if not text:
            remaining.append(sec)
            continue

        if metadata_zone:
            consumed = False
            for line_text in text.split("\n"):
                lt = line_text.strip()
                if not lt:
                    continue

                m = _DOC_FIELD_RE.match(lt)
                if m:
                    meta["doc-number"] = m.group(1).upper()
                    consumed = True
                    continue

                m = _DATE_RE.search(lt)
                if m and "date" not in meta and not _SECTION_NUM_RE.match(lt):
                    if lt.lower().startswith("date"):
                        meta["date"] = m.group(1)
                        consumed = True
                        continue

                m = _REPLY_TO_RE.match(lt)
                if m:
                    raw = m.group(1).strip()
                    raw = re.sub(r"<[^>]+>", "", raw)
                    raw = re.sub(r"\S+@\S+\.\S+", "", raw)
                    raw = re.sub(r"\s{2,}", " ", raw).strip()
                    raw = re.sub(r"^[,\s]+|[,\s]+$", "", raw)
                    if raw:
                        meta["reply-to"] = raw
                    consumed = True
                    continue

                m = _AUDIENCE_RE.match(lt)
                if m:
                    meta["audience"] = m.group(1).strip()
                    consumed = True
                    continue

            if consumed:
                leftover = []
                for line_text in text.split("\n"):
                    lt = line_text.strip()
                    if not lt:
                        continue
                    if (_DOC_FIELD_RE.match(lt) or _REPLY_TO_RE.match(lt)
                            or _AUDIENCE_RE.match(lt)):
                        continue
                    if lt.lower().startswith("date") and _DATE_RE.search(lt):
                        continue
                    leftover.append(lt)
                if leftover:
                    sec.text = "\n".join(leftover)
                    remaining.append(sec)
                continue

            if _SECTION_NUM_RE.match(text.split("\n")[0]):
                metadata_zone = False

        remaining.append(sec)

    return meta, remaining


def structure_sections(sections: list[Section],
                       has_title: bool = False) -> tuple[dict, list[Section]]:
    """Apply heading intelligence, paragraph grouping, and list detection.

    If has_title is True, the title was already extracted from front matter
    and no title detection is performed.

    Returns (metadata_dict, structured_sections).
    """
    metadata, sections = _extract_metadata(sections)
    body_size = _detect_body_size(sections)
    font_ranks = _rank_font_sizes(sections, body_size)

    _log.debug("Body size: %.1f, font ranks: %s", body_size, font_ranks)

    title_found = has_title
    structured: list[Section] = []

    for sec in sections:
        if sec.kind in (SectionKind.UNCERTAIN, SectionKind.TABLE):
            structured.append(sec)
            continue

        first_line = sec.text.split("\n")[0].strip()

        if not title_found:
            if (sec.font_size > body_size * TITLE_SIZE_RATIO
                    and not _SECTION_NUM_RE.match(first_line)):
                metadata["title"] = first_line
                sec.kind = SectionKind.TITLE
                sec.heading_level = 1
                sec.confidence = Confidence.HIGH
                title_found = True
                structured.append(sec)
                continue

        m = _SECTION_NUM_RE.match(first_line)
        has_number = m is not None
        section_num = m.group(1) if m else ""

        line_fs = sec.font_size
        font_level = font_ranks.get(line_fs)
        is_bold = bool(sec.lines) and sec.lines[0].is_bold
        is_known = first_line.lower().rstrip(":") in _KNOWN_SECTIONS

        if has_number or font_level is not None or is_known:
            number_level = _heading_level_from_number(section_num) if has_number else 0
            level, conf = _heading_confidence(
                has_number, number_level, font_level, is_bold, is_known)

            if level > 0:
                sec.kind = SectionKind.HEADING
                sec.heading_level = level
                sec.confidence = conf
                structured.append(sec)
                continue

        lines = sec.text.split("\n")
        is_list = all(
            _BULLET_RE.match(ln) or _NUMBERED_LIST_RE.match(ln)
            for ln in lines if ln.strip()
        )
        if is_list and any(ln.strip() for ln in lines):
            sec.kind = SectionKind.LIST
            structured.append(sec)
            continue

        sec.kind = SectionKind.PARAGRAPH
        structured.append(sec)

    structured = _detect_lists_by_position(structured)
    structured = _merge_paragraphs(structured)
    structured = _detect_code_blocks(structured)
    structured = [s for s in structured if _detect_lang_label(s) is None]
    _validate_nesting(structured)
    return metadata, structured


_BULLET_CHARS = frozenset("-*\u2022\u2023\u25cf\u25e6\u2043\u2219\u25aa\u25ab")
_BULLET_SPLIT_RE = re.compile(
    r"(?=[\u2022\u2023\u25cf\u25e6\u2043\u2219\u25aa\u25ab][\s\u200b])"
)

INDENT_TOLERANCE = 5.0


def _get_body_margin(sections: list[Section]) -> float:
    """Find the leftmost frequent x-position (= body left margin).

    Uses the leftmost x that accounts for at least 10% of lines,
    rather than the most common x, to handle PDFs where indented
    content is more frequent than body text.
    """
    x_counts: Counter[float] = Counter()
    for sec in sections:
        for line in sec.lines:
            if line.text.strip() and line.spans:
                x = round(line.bbox[0] / INDENT_TOLERANCE) * INDENT_TOLERANCE
                x_counts[x] += 1
    if not x_counts:
        return 0.0
    total = sum(x_counts.values())
    threshold = total * 0.1
    for x in sorted(x_counts.keys()):
        if x_counts[x] >= threshold:
            return x
    return x_counts.most_common(1)[0][0]


def _line_starts_with_bullet(line) -> bool:
    """Check if a line starts with a bullet character."""
    text = line.text.strip()
    if not text:
        return False
    return text[0] in _BULLET_CHARS


def _detect_lists_by_position(sections: list[Section]) -> list[Section]:
    """Detect list structure using line x-positions and bullet characters.

    Uses indentation (x-coordinate) to identify list items. Lines
    indented from the body margin that start with a bullet character
    are list items. Lines at the body margin between bullet groups
    are parent list items. Also handles inline bullet splitting
    when position data is unavailable.
    """
    body_margin = _get_body_margin(sections)

    result = []
    for sec in sections:
        if sec.kind != SectionKind.PARAGRAPH:
            result.append(sec)
            continue

        if sec.lines:
            items = _split_section_by_position(sec, body_margin)
            result.extend(items)
        else:
            items = _split_inline_bullets_text(sec)
            result.extend(items)

    return result


def _join_bullet_marker_lines(lines: list) -> list:
    """Join bullet marker lines with their following text lines.

    Some PDFs render the dash/bullet on one line (x=90) and the text
    on the next line (x=108). Combine them into a single line.
    """
    if len(lines) < 2:
        return lines
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        text = line.text.strip()
        if (text and text[0] in _BULLET_CHARS and len(text) <= 3
                and i + 1 < len(lines)):
            next_line = lines[i + 1]
            from .cleanup import strip_zero_width
            bullet = strip_zero_width(text).rstrip()
            combined_text = bullet + " " + next_line.text.lstrip()
            bullet_span = Span(
                text=bullet + " ",
                font_name=line.spans[0].font_name if line.spans else "",
                font_size=line.spans[0].font_size if line.spans else 0,
                bold=line.spans[0].bold if line.spans else False,
                italic=line.spans[0].italic if line.spans else False,
                monospace=line.spans[0].monospace if line.spans else False,
                bbox=line.spans[0].bbox if line.spans else (0, 0, 0, 0),
                origin=line.spans[0].origin if line.spans else (0, 0),
            )
            combined_spans = [bullet_span] + list(next_line.spans)
            result.append(Line(
                spans=combined_spans,
                bbox=(line.bbox[0], line.bbox[1], next_line.bbox[2], next_line.bbox[3]),
                page_num=line.page_num,
            ))
            i += 2
        else:
            result.append(line)
            i += 1
    return result


def _split_section_by_position(sec: Section, body_margin: float) -> list[Section]:
    """Split a section into list items using line x-positions."""
    lines = _join_bullet_marker_lines(sec.lines)

    indented_bullets = []
    for line in lines:
        if not line.text.strip() or not line.spans:
            continue
        x = line.bbox[0]
        if x > body_margin + INDENT_TOLERANCE and _line_starts_with_bullet(line):
            indented_bullets.append(line)

    if len(indented_bullets) < 1:
        return [sec]

    items: list[Section] = []
    current_lines: list = []
    current_indent = 0
    current_is_bullet = False

    for line in lines:
        if not line.text.strip():
            if current_lines:
                current_lines.append(line)
            continue

        x = line.bbox[0]
        is_bullet = _line_starts_with_bullet(line)
        indent = 0
        if x > body_margin + INDENT_TOLERANCE:
            indent = 1
        if x > body_margin + INDENT_TOLERANCE * 3:
            indent = 2

        if is_bullet and indent > 0:
            if current_lines:
                text = "\n".join(ln.text for ln in current_lines if ln.text.strip())
                items.append(Section(
                    kind=SectionKind.LIST if current_is_bullet else SectionKind.PARAGRAPH,
                    text=text,
                    confidence=sec.confidence,
                    lines=list(current_lines),
                    page_num=sec.page_num,
                    font_size=sec.font_size,
                    indent_level=current_indent,
                ))
            current_lines = [line]
            current_indent = indent
            current_is_bullet = True
        elif indent == 0 and current_is_bullet:
            if current_lines:
                text = "\n".join(ln.text for ln in current_lines if ln.text.strip())
                items.append(Section(
                    kind=SectionKind.LIST,
                    text=text,
                    confidence=sec.confidence,
                    lines=list(current_lines),
                    page_num=sec.page_num,
                    font_size=sec.font_size,
                    indent_level=current_indent,
                ))
            current_lines = [line]
            current_indent = 0
            current_is_bullet = False
        else:
            current_lines.append(line)

    if current_lines:
        text = "\n".join(ln.text for ln in current_lines if ln.text.strip())
        if text.strip():
            items.append(Section(
                kind=SectionKind.LIST if current_is_bullet else SectionKind.PARAGRAPH,
                text=text,
                confidence=sec.confidence,
                lines=list(current_lines),
                page_num=sec.page_num,
                font_size=sec.font_size,
                indent_level=current_indent,
            ))

    if not items:
        return [sec]

    bullet_count = sum(1 for it in items if it.kind == SectionKind.LIST)
    if bullet_count < 1:
        return [sec]

    return items


def _split_inline_bullets_text(sec: Section) -> list[Section]:
    """Fallback: split paragraphs at Unicode bullet characters in text."""
    text = sec.text
    parts = _BULLET_SPLIT_RE.split(text)
    if len(parts) <= 1:
        return [sec]

    result = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        starts_with_bullet = part[0] in _BULLET_CHARS
        result.append(Section(
            kind=SectionKind.LIST if starts_with_bullet else SectionKind.PARAGRAPH,
            text=part,
            confidence=sec.confidence,
            lines=[],
            page_num=sec.page_num,
            font_size=sec.font_size,
        ))
    return result if result else [sec]


_TERMINAL = frozenset(".?!:")


def _merge_paragraphs(sections: list[Section]) -> list[Section]:
    """Merge consecutive sections that are continuations.

    When a section ends without terminal punctuation and the next
    paragraph starts with a lowercase letter, they are the same
    logical paragraph split by PDF line wrapping. Works for
    PARAGRAPH+PARAGRAPH and LIST+PARAGRAPH (bullet continuation).
    """
    if len(sections) < 2:
        return sections

    mergeable = frozenset({SectionKind.PARAGRAPH, SectionKind.LIST})

    result = [sections[0]]
    for sec in sections[1:]:
        prev = result[-1]
        if (prev.kind in mergeable
                and sec.kind == SectionKind.PARAGRAPH
                and prev.text.rstrip()
                and sec.text.lstrip()):
            prev_end = prev.text.rstrip()[-1]
            cur_start = sec.text.lstrip()[0]
            if prev_end not in _TERMINAL and cur_start.islower():
                prev.text = prev.text.rstrip() + " " + sec.text.lstrip()
                prev.lines.extend(sec.lines)
                if prev.lines:
                    prev.font_size = prev.lines[0].font_size
                continue
        result.append(sec)
    return result


def _line_is_monospace(line) -> bool:
    """Check if all non-whitespace spans in a line are monospace."""
    text_spans = [s for s in line.spans if s.text.strip()]
    return bool(text_spans) and all(s.monospace for s in text_spans)


def _section_is_all_monospace(sec: Section) -> bool:
    """Check if every non-whitespace line in a section is monospace."""
    content_lines = [ln for ln in sec.lines if ln.text.strip()]
    return bool(content_lines) and all(_line_is_monospace(ln) for ln in content_lines)


def _section_is_empty(sec: Section) -> bool:
    """Check if a section has no visible text content."""
    return not sec.text.strip()


_LANG_LABELS = {
    "c/c++": "cpp",
    "c++": "cpp",
    "cpp": "cpp",
    "c": "c",
    "python": "python",
    "javascript": "javascript",
    "typescript": "typescript",
    "java": "java",
    "rust": "rust",
    "go": "go",
    "bash": "bash",
    "shell": "bash",
    "sql": "sql",
    "json": "json",
    "yaml": "yaml",
    "xml": "xml",
    "html": "html",
    "css": "css",
}


def _detect_lang_label(sec: Section) -> str | None:
    """Check if a section is a code block language label."""
    from .cleanup import strip_zero_width
    text = strip_zero_width(sec.text).strip().lower()
    return _LANG_LABELS.get(text)


def _detect_code_blocks(sections: list[Section]) -> list[Section]:
    """Detect runs of consecutive monospace sections and merge into CODE.

    Bridges empty sections (blank lines in code) between monospace runs.
    Detects language labels (e.g. "C/C++") immediately before code blocks
    and uses them for the fence language.
    """
    result: list[Section] = []
    mono_run: list[Section] = []
    fence_lang = "cpp"
    pending_label_idx = -1

    def flush_mono():
        nonlocal fence_lang, pending_label_idx
        if not mono_run:
            return
        all_lines = []
        for s in mono_run:
            if _section_is_empty(s):
                all_lines.append(Line(spans=[], bbox=(0, 0, 0, 0)))
            else:
                all_lines.extend(s.lines)
        code_text = "\n".join(ln.text for ln in all_lines)
        result.append(Section(
            kind=SectionKind.CODE,
            text=code_text,
            confidence=Confidence.HIGH,
            lines=all_lines,
            page_num=mono_run[0].page_num,
            fence_lang=fence_lang,
        ))
        # Remove the language label that preceded this block
        if pending_label_idx >= 0 and pending_label_idx < len(result) - 1:
            del result[pending_label_idx]
        mono_run.clear()
        fence_lang = "cpp"
        pending_label_idx = -1

    for i, sec in enumerate(sections):
        if sec.kind in (SectionKind.PARAGRAPH, SectionKind.LIST):
            if _section_is_all_monospace(sec):
                mono_run.append(sec)
                continue

            if _section_is_empty(sec) and mono_run:
                mono_run.append(sec)
                continue

        if mono_run:
            flush_mono()

        lang = _detect_lang_label(sec)
        if lang is not None:
            result.append(sec)
            fence_lang = lang
            pending_label_idx = len(result) - 1
        else:
            result.append(sec)
            if pending_label_idx >= 0:
                fence_lang = "cpp"
                pending_label_idx = -1

    flush_mono()
    return result


def _validate_nesting(sections: list[Section]) -> None:
    """Ensure heading levels don't skip more than one level deeper."""
    prev_level = 0
    for sec in sections:
        if sec.kind != SectionKind.HEADING:
            continue
        if prev_level > 0 and sec.heading_level > prev_level + 1:
            corrected = prev_level + 1
            _log.debug("Nesting fix: h%d -> h%d for %r",
                        sec.heading_level, corrected,
                        sec.text[:40])
            sec.heading_level = corrected
            if sec.confidence == Confidence.HIGH:
                sec.confidence = Confidence.MEDIUM
        prev_level = sec.heading_level
