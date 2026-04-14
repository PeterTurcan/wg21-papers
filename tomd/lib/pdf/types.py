"""Shared data types, constants, and precompiled regex patterns for PDF conversion."""

import re
from dataclasses import dataclass, field
from enum import Enum


class Confidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


@dataclass
class Span:
    """A run of text with uniform font properties."""
    text: str
    font_name: str = ""
    font_size: float = 0.0
    bold: bool = False
    italic: bool = False
    monospace: bool = False
    bbox: tuple[float, float, float, float] = (0, 0, 0, 0)
    origin: tuple[float, float] = (0, 0)
    color: int = 0
    link_url: str | None = None


@dataclass
class Line:
    """A sequence of spans forming a single line of text."""
    spans: list[Span] = field(default_factory=list)
    bbox: tuple[float, float, float, float] = (0, 0, 0, 0)
    page_num: int = 0

    @property
    def text(self) -> str:
        return "".join(s.text for s in self.spans)

    @property
    def font_size(self) -> float:
        if not self.spans:
            return 0.0
        sizes = [s.font_size for s in self.spans if s.text.strip()]
        return max(sizes) if sizes else 0.0

    @property
    def is_bold(self) -> bool:
        text_spans = [s for s in self.spans if s.text.strip()]
        return bool(text_spans) and all(s.bold for s in text_spans)


@dataclass
class Block:
    """A group of lines forming a paragraph-level unit."""
    lines: list[Line] = field(default_factory=list)
    bbox: tuple[float, float, float, float] = (0, 0, 0, 0)
    page_num: int = 0

    @property
    def text(self) -> str:
        return "\n".join(ln.text for ln in self.lines)

    @property
    def font_size(self) -> float:
        sizes = [ln.font_size for ln in self.lines if ln.text.strip()]
        if not sizes:
            return 0.0
        from collections import Counter
        return Counter(sizes).most_common(1)[0][0]


class SectionKind(Enum):
    TITLE = "title"
    METADATA = "metadata"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    CODE = "code"
    TABLE = "table"
    UNCERTAIN = "uncertain"


@dataclass
class Section:
    """A classified region of the document."""
    kind: SectionKind
    text: str
    confidence: Confidence = Confidence.HIGH
    heading_level: int = 0
    lines: list[Line] = field(default_factory=list)
    mupdf_text: str = ""
    spatial_text: str = ""
    page_num: int = 0
    font_size: float = 0.0
    metadata: dict = field(default_factory=dict)
    columns: list[list[list]] = field(default_factory=list)
    fence_lang: str = "cpp"
    indent_level: int = 0


@dataclass
class PageEdgeItem:
    """A text item near the top or bottom of a page, used for header/footer detection."""
    text: str
    y: float
    page_num: int
    bbox: tuple[float, float, float, float] = (0, 0, 0, 0)


# Spatial rule thresholds (relative to font size)
WORD_GAP_RATIO = 0.3
LINE_SPACING_RATIO = 1.8
PARA_SPACING_RATIO = 2.5

# Y-position tolerance for header/footer matching across pages
Y_TOLERANCE = 2.0

# Minimum pages a text must appear on (as fraction) to be a header/footer
REPEATING_THRESHOLD = 0.5

EDGE_ITEMS_PER_PAGE = 3

# Similarity threshold for dual-path comparison (word-level)
SIMILARITY_THRESHOLD = 0.85

# --- Precompiled regex patterns ---
# Canonical source: paperworks/lib/pdf_reader.py

_SECTION_NUM_RE = re.compile(
    r"^(\d+(?:\.\d+)*)\s+(.+)",
)

_DOC_NUM_RE = re.compile(
    r"\b([DPN]\d{3,5}R\d+)\b"
    r"|\b([DPN]\d{3,5})\b"
    r"|\b(N\d{3,5})\b",
    re.IGNORECASE,
)

_DOC_FIELD_RE = re.compile(
    r"Document\s+(?:Number|#)[:\s]+([DPN]\d{3,5}(?:R\d+)?|N\d{3,5})",
    re.IGNORECASE,
)

_REPLY_TO_RE = re.compile(
    r"(?:Reply[- ]to|Author)[:\s]+(.+)",
    re.IGNORECASE,
)

_AUDIENCE_RE = re.compile(
    r"Audience[:\s]+(.+)",
    re.IGNORECASE,
)

_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")

_PAGE_NUM_RE = re.compile(
    r"^\d+$"
    r"|^[Pp]age\s+\d+"
    r"|^\d+\s+of\s+\d+",
)

_BULLET_RE = re.compile(r"^[\s]*[-*\u2022\u2023\u25cf\u25e6\u2043\u2219\u25aa\u25ab]\s+")

_NUMBERED_LIST_RE = re.compile(r"^[\s]*(?:\d+[.)]\s+|[a-z][.)]\s+|\([a-z]\)\s+)", re.IGNORECASE)

_COMPOUND_PREFIXES = frozenset({
    "self", "non", "well", "cross", "pre", "post", "re", "co", "anti",
    "multi", "semi", "sub", "inter", "intra", "over", "under", "out",
})

_KNOWN_SECTIONS = frozenset({
    "abstract",
    "revision history",
    "references",
    "acknowledgements",
    "acknowledgments",
    "motivation",
    "wording",
    "proposed wording",
    "design decisions",
    "design",
    "implementation",
    "implementation experience",
    "future work",
    "introduction",
    "overview",
    "background",
    "scope",
    "impact on the standard",
    "proposed changes",
    "poll results",
    "changelog",
    "appendix",
    "bibliography",
    "summary",
    "conclusion",
})

_ALLOWED_LINK_SCHEMES = frozenset({"http", "https", "mailto"})

READABLE_MIN_LENGTH = 100
READABLE_MIN_RATIO = 0.3
READABLE_MAX_SLASH_RATIO = 0.1
READABLE_SAMPLE_SIZE = 2000


def is_readable(text: str) -> bool:
    """Return True if text looks like real content rather than encoded garbage.

    Catches encrypted PDFs, scanned-image-only PDFs, and CID-encoded
    artifacts that produce mostly non-alphanumeric output.
    """
    if not text or len(text.strip()) < READABLE_MIN_LENGTH:
        return False
    sample = text[:READABLE_SAMPLE_SIZE]
    non_space = [c for c in sample if not c.isspace()]
    if not non_space:
        return False
    readable = sum(1 for c in non_space if c.isalnum() or c in ".,;:!?-()[]{}\"'")
    if sample.count("/") > len(sample) * READABLE_MAX_SLASH_RATIO:
        return False
    return (readable / len(non_space)) > READABLE_MIN_RATIO
