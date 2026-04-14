"""WG21-specific metadata extraction from PDF blocks.

Parses the metadata block at the top of WG21 papers (document number,
date, audience, reply-to) from the raw MuPDF block structure, before
table detection or structuring runs.
"""

import logging
import re

from .cleanup import strip_zero_width
from .types import Block

_log = logging.getLogger(__name__)

_LABEL_RE = re.compile(
    r"(Document\s*(?:Number|#)|Date|Audience|Reply[- ]?to|Project)\s*:",
    re.IGNORECASE,
)

_DOC_NUM_VALUE_RE = re.compile(
    r"([DPN]\d{3,5}(?:R\d+)?)",
    re.IGNORECASE,
)

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")

_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _clean(text: str) -> str:
    """Strip zero-width chars and whitespace."""
    return strip_zero_width(text).strip()


def _parse_authors(lines: list[str]) -> list[str]:
    """Parse author name + email from lines into 'Name <email>' entries."""
    authors = []
    pending_name = None

    for raw in lines:
        line = _clean(raw)
        if not line:
            continue

        email_match = _EMAIL_RE.search(line)
        if email_match:
            email = email_match.group(0)
            name_part = line[:email_match.start()].strip()
            name_part = re.sub(r"[()]", "", name_part).strip()

            if name_part:
                authors.append(f"{name_part} <{email}>")
                pending_name = None
            elif pending_name:
                authors.append(f"{pending_name} <{email}>")
                pending_name = None
            else:
                authors.append(f"<{email}>")
        else:
            line_clean = re.sub(r"[()]", "", line).strip()
            if line_clean and not _LABEL_RE.match(line_clean):
                if pending_name:
                    authors.append(pending_name)
                pending_name = line_clean

    if pending_name:
        authors.append(pending_name)

    return authors


def _store_field(metadata: dict, label: str, value_lines: list[str]):
    """Store a parsed metadata field into the dict."""
    label_lower = label.lower()

    if "document" in label_lower:
        value = _clean(" ".join(value_lines))
        m = _DOC_NUM_VALUE_RE.search(value)
        if m:
            metadata["document"] = m.group(1).upper()
    elif label_lower == "date":
        value = _clean(" ".join(value_lines))
        m = _DATE_RE.search(value)
        if m:
            metadata["date"] = m.group(0)
    elif label_lower == "audience":
        metadata["audience"] = _clean(" ".join(value_lines))
    elif "reply" in label_lower:
        authors = _parse_authors(value_lines)
        if authors:
            metadata["reply-to"] = authors


def extract_metadata_from_blocks(blocks: list[Block]) -> tuple[dict, set[int]]:
    """Extract WG21 metadata from the first blocks of page 0.

    Handles two formats:
      - Scrivener: each field is its own block (label on line 0, value on line 1+)
      - Google Docs: multiple fields in one block (each line has label: value)

    Returns (metadata_dict, consumed_block_indices).
    """
    metadata: dict = {}
    consumed: set[int] = set()

    page0_blocks = [(i, b) for i, b in enumerate(blocks) if b.page_num == 0]

    title_idx = None
    for i, block in page0_blocks:
        if not block.lines:
            continue
        has_label = any(_LABEL_RE.match(_clean(ln.text)) for ln in block.lines)
        if has_label:
            break
        content_lines = [_clean(ln.text) for ln in block.lines if _clean(ln.text)]
        if not content_lines:
            continue
        if (title_idx is None
                and not _DOC_NUM_VALUE_RE.match(content_lines[0])
                and block.font_size > 0):
            title_idx = (i, " ".join(content_lines))

    for i, block in page0_blocks:
        if not block.lines:
            continue

        found_any = False

        for li, line in enumerate(block.lines):
            line_text = _clean(line.text)
            if not line_text:
                continue

            m = _LABEL_RE.match(line_text)
            if not m:
                continue

            found_any = True
            label = m.group(1)
            remainder = line_text[m.end():].strip()

            value_lines = []
            if remainder:
                value_lines.append(remainder)

            for vl in block.lines[li + 1:]:
                vl_text = _clean(vl.text)
                if _LABEL_RE.match(vl_text):
                    break
                value_lines.append(vl.text)

            _store_field(metadata, label, value_lines)

        if found_any:
            consumed.add(i)
            if "reply" in " ".join(_clean(ln.text) for ln in block.lines).lower():
                for j, next_block in page0_blocks:
                    if j <= i:
                        continue
                    if j in consumed:
                        continue
                    next_text = _clean(next_block.lines[0].text) if next_block.lines else ""
                    if next_text and not _LABEL_RE.match(next_text):
                        has_email = any(_EMAIL_RE.search(ln.text) for ln in next_block.lines)
                        if has_email:
                            extra_authors = _parse_authors([ln.text for ln in next_block.lines])
                            if extra_authors:
                                existing = metadata.get("reply-to", [])
                                metadata["reply-to"] = existing + extra_authors
                                consumed.add(j)
                    break

    if title_idx is not None and "title" not in metadata:
        idx, title_text = title_idx
        if title_text:
            metadata["title"] = title_text
            consumed.add(idx)

    if consumed:
        _log.debug("Extracted metadata: %s (consumed blocks %s)",
                    list(metadata.keys()), sorted(consumed))

    return metadata, consumed
