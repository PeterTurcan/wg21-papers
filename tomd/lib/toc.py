"""Table of Contents detection and removal.

Format-agnostic: operates on plain strings and returns indices.
No dependency on PDF or HTML converter types.
"""

import logging
import re

from .similarity import similar

_log = logging.getLogger(__name__)

_TRAILING_PAGE_NUM_RE = re.compile(r"\s+\d{1,4}\s*$")
_DOT_LEADER_RE = re.compile(r"\s*[.·]{2,}[\s.·]*")
_SECTION_NUM_PREFIX_RE = re.compile(r"^\d+(?:\.\d+)*\.?\s+")

_TOC_LABELS = frozenset({
    "table of contents",
    "contents",
})

MIN_TOC_RUN = 3


def normalize_toc_entry(text: str) -> str:
    """Normalize text for TOC comparison.

    Strips trailing page numbers, dot leaders, section number prefixes.
    Collapses whitespace, lowercases.
    """
    text = text.split("\n")[0].strip()
    text = _DOT_LEADER_RE.sub(" ", text)
    text = _TRAILING_PAGE_NUM_RE.sub("", text)
    text = _SECTION_NUM_PREFIX_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def _is_toc_label(text: str) -> bool:
    """Check if text is a TOC heading label."""
    normalized = text.strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized in _TOC_LABELS


def find_toc_indices(texts: list[str], headings: set[str]) -> set[int]:
    """Return indices of entries that form a Table of Contents.

    texts: ordered list of section texts from the document
    headings: set of known heading texts to match against

    Both are normalized before comparison. Detects runs of 3+
    consecutive entries that match headings. Also includes any
    "Table of Contents" label immediately preceding a run.
    """
    if not texts or not headings:
        return set()

    norm_headings = {normalize_toc_entry(h) for h in headings}
    norm_headings.discard("")

    def _matches_heading(text: str) -> bool:
        norm = normalize_toc_entry(text)
        if not norm:
            return False
        for h in norm_headings:
            if similar(norm, h):
                return True
        return False

    matches = []
    for i, text in enumerate(texts):
        first_line = text.split("\n")[0].strip()
        matches.append(_matches_heading(first_line))

    # Find the first match - everything before it is pre-TOC (title, metadata)
    first_match = -1
    for i, m in enumerate(matches):
        if m:
            first_match = i
            break

    if first_match < 0:
        return set()

    # From the first match, build a run bridging small gaps.
    # Stop after a gap exceeds MAX_GAP, or when a heading repeats
    # (the second occurrence is the real heading, not a TOC entry).
    MAX_GAP = 3
    run_indices: list[int] = []
    seen_normalized: set[str] = set()
    gap = 0

    for i in range(first_match, len(matches)):
        if matches[i]:
            norm = normalize_toc_entry(texts[i].split("\n")[0].strip())
            if norm in seen_normalized:
                break
            seen_normalized.add(norm)
            if gap > 0:
                for g in range(i - gap, i):
                    run_indices.append(g)
            gap = 0
            run_indices.append(i)
        else:
            gap += 1
            if gap > MAX_GAP:
                break

    match_count = sum(1 for i in run_indices if matches[i])
    toc_indices: set[int] = set()
    if match_count >= MIN_TOC_RUN:
        toc_indices = set(run_indices)
        _log.debug("TOC block: %d entries (%d matched)",
                    len(run_indices), match_count)

    # Include "Table of Contents" / "Contents" label before the block
    if toc_indices:
        first = min(toc_indices)
        prev = first - 1
        if prev >= 0 and _is_toc_label(texts[prev].split("\n")[0].strip()):
            toc_indices.add(prev)
            _log.debug("TOC label at index %d", prev)

    if toc_indices:
        _log.info("Detected TOC: %d entries removed", len(toc_indices))

    return toc_indices
