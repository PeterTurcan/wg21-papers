"""String similarity algorithms for fuzzy matching.

Two independent algorithms with per-algorithm thresholds:
  1. SequenceMatcher - character-level (difflib, stdlib)
  2. Jaccard - word-level set overlap

A 200-character circuit breaker protects against expensive
comparisons on paragraph-length strings.
"""

from difflib import SequenceMatcher as _SM

MAX_COMPARE_LENGTH = 200

SEQUENCE_THRESHOLD = 0.75
JACCARD_THRESHOLD = 0.65


def sequence_similarity(a: str, b: str) -> float:
    """Character-level similarity using difflib.SequenceMatcher.

    Returns 0.0-1.0. Returns 0.0 for strings over MAX_COMPARE_LENGTH.
    """
    if len(a) > MAX_COMPARE_LENGTH or len(b) > MAX_COMPARE_LENGTH:
        return 0.0
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return _SM(None, a, b).ratio()


def jaccard_similarity(a: str, b: str) -> float:
    """Word-level similarity using set intersection/union.

    Returns 0.0-1.0. Returns 0.0 for strings over MAX_COMPARE_LENGTH.
    Systematically scores lower than SequenceMatcher on short strings
    with one extra word.
    """
    if len(a) > MAX_COMPARE_LENGTH or len(b) > MAX_COMPARE_LENGTH:
        return 0.0
    sa = set(a.lower().split())
    sb = set(b.lower().split())
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    intersection = sa & sb
    union = sa | sb
    return len(intersection) / len(union)


def similar(a: str, b: str) -> bool:
    """True if EITHER algorithm scores above its calibrated threshold.

    The per-string check is lenient because the caller (TOC detection)
    provides a second guard via the 3+ consecutive run requirement.
    """
    if len(a) > MAX_COMPARE_LENGTH or len(b) > MAX_COMPARE_LENGTH:
        return False
    if sequence_similarity(a, b) >= SEQUENCE_THRESHOLD:
        return True
    if jaccard_similarity(a, b) >= JACCARD_THRESHOLD:
        return True
    return False
