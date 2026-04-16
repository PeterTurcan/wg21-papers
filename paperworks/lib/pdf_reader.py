"""Extract metadata from WG21 PDF papers."""

import logging
import re
from pathlib import Path

_log = logging.getLogger(__name__)


_DOC_NUM_RE = re.compile(
    r"\b([DPN]\d{3,5}R\d+)\b"
    r"|\b([DPN]\d{3,5})\b"
    r"|\b(N\d{3,5})\b",
    re.IGNORECASE,
)

_DOC_FIELD_RE = re.compile(
    r"Document(?:\s+Number)?[:\s]+([DPN]\d{3,5}(?:R\d+)?|N\d{3,5})",
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

_STOP_RE = re.compile(r"^(Revision\s+History|R\d+:|Table\s+of\s+Contents|\d+\.\s)", re.IGNORECASE)


def _extract_doc_number(text):
    """Find the document number from the 'Document Number:' structured field.

    Only the structured header is trusted. Free-text scanning is intentionally
    absent: paper titles that mention other paper numbers (e.g. "Coroutine
    Executors and P2464R0") would otherwise be misidentified.
    """
    m = _DOC_FIELD_RE.search(text)
    if m:
        return m.group(1).upper()
    return None


def _doc_number_from_filename(path):
    stem = Path(path).stem.lower()
    m = re.match(r"([dpn]\d{3,5}(?:r\d+)?)", stem)
    if m:
        return m.group(1).upper()
    return None


def _extract_title(lines):
    for line in lines[:20]:
        stripped = line.strip()
        if len(stripped) > 10 and not _DOC_NUM_RE.match(stripped):
            if not _REPLY_TO_RE.match(stripped) and not _DATE_RE.match(stripped):
                if not stripped.startswith("Document") and not stripped.startswith("Date"):
                    return stripped
    return None


def _extract_authors(text):
    m = _REPLY_TO_RE.search(text)
    if m:
        raw = m.group(1).strip()
        raw = re.sub(r"<[^>]+>", "", raw)
        raw = re.sub(r"\S+@\S+\.\S+", "", raw)
        raw = re.sub(r"\s{2,}", " ", raw).strip()
        raw = re.sub(r"^[,\s]+|[,\s]+$", "", raw)
        return raw or None
    return None


def _extract_abstract_from_doc(doc):
    """Scan pages for the abstract body.

    For multi-page documents, starts at page 1 (page 0 typically has
    the TOC entry). For single-page documents, scans page 0.

    Returns (brutal_summary, abstract) or (None, None).
    The abstract is capped at 1000 characters.
    """
    start = 0 if doc.page_count == 1 else 1
    for pg_num in range(start, min(5, doc.page_count)):
        text = doc[pg_num].get_text()
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if line.strip().lower() != "abstract":
                continue
            body_lines = []
            for j in range(i + 1, min(i + 20, len(lines))):
                l = lines[j].strip()
                if not l or _STOP_RE.match(l):
                    break
                body_lines.append(l)
            if not body_lines:
                continue
            first_line = body_lines[0]
            if len(first_line) < 20 or not re.search(r"[a-zA-Z]{4,}", first_line):
                continue
            full = " ".join(body_lines)
            full = re.sub(r"\s+", " ", full).strip()
            if len(full) < 30:
                continue
            m = re.match(r"([^.]+\.)", full)
            brutal = m.group(1).strip() if m else full[:200]
            return brutal, full[:1000]
    return None, None


def read_pdf(path):
    """Extract metadata from a single PDF file.

    Returns a dict with keys:
        path, filename, doc_number, title, authors, date, audience,
        abstract, brutal_summary
    """
    path = Path(path)
    result = {
        "path": str(path),
        "filename": path.name,
        "doc_number": None,
        "title": None,
        "authors": None,
        "date": None,
        "audience": None,
        "abstract": None,
        "brutal_summary": None,
    }

    try:
        import fitz
        doc = fitz.open(str(path))
        try:
            if doc.page_count == 0:
                result["doc_number"] = _doc_number_from_filename(path)
                return result

            first_page = doc[0].get_text()
            brutal, abstract = _extract_abstract_from_doc(doc)
        finally:
            doc.close()
    except Exception:
        _log.debug("Could not read PDF %s", path, exc_info=True)
        result["doc_number"] = _doc_number_from_filename(path)
        return result

    lines = first_page.split("\n")
    text = first_page[:3000]

    result["doc_number"] = _extract_doc_number(text) or _doc_number_from_filename(path)
    result["title"] = _extract_title(lines)
    result["authors"] = _extract_authors(text)
    result["abstract"] = abstract
    result["brutal_summary"] = brutal

    date_m = _DATE_RE.search(text)
    if date_m:
        result["date"] = date_m.group(1)

    aud_m = _AUDIENCE_RE.search(text)
    if aud_m:
        result["audience"] = aud_m.group(1).strip()

    return result
