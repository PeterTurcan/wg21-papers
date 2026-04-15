"""Shared text utilities and constants for PDF and HTML converters."""

import re
import unicodedata

_NAMED_ENTITIES = {
    0xC0: "&Agrave;", 0xC1: "&Aacute;", 0xC2: "&Acirc;", 0xC3: "&Atilde;",
    0xC4: "&Auml;", 0xC5: "&Aring;", 0xC6: "&AElig;", 0xC7: "&Ccedil;",
    0xC8: "&Egrave;", 0xC9: "&Eacute;", 0xCA: "&Ecirc;", 0xCB: "&Euml;",
    0xCC: "&Igrave;", 0xCD: "&Iacute;", 0xCE: "&Icirc;", 0xCF: "&Iuml;",
    0xD0: "&ETH;", 0xD1: "&Ntilde;", 0xD2: "&Ograve;", 0xD3: "&Oacute;",
    0xD4: "&Ocirc;", 0xD5: "&Otilde;", 0xD6: "&Ouml;", 0xD8: "&Oslash;",
    0xD9: "&Ugrave;", 0xDA: "&Uacute;", 0xDB: "&Ucirc;", 0xDC: "&Uuml;",
    0xDD: "&Yacute;", 0xDE: "&THORN;", 0xDF: "&szlig;",
    0xE0: "&agrave;", 0xE1: "&aacute;", 0xE2: "&acirc;", 0xE3: "&atilde;",
    0xE4: "&auml;", 0xE5: "&aring;", 0xE6: "&aelig;", 0xE7: "&ccedil;",
    0xE8: "&egrave;", 0xE9: "&eacute;", 0xEA: "&ecirc;", 0xEB: "&euml;",
    0xEC: "&igrave;", 0xED: "&iacute;", 0xEE: "&icirc;", 0xEF: "&iuml;",
    0xF0: "&eth;", 0xF1: "&ntilde;", 0xF2: "&ograve;", 0xF3: "&oacute;",
    0xF4: "&ocirc;", 0xF5: "&otilde;", 0xF6: "&ouml;", 0xF8: "&oslash;",
    0xF9: "&ugrave;", 0xFA: "&uacute;", 0xFB: "&ucirc;", 0xFC: "&uuml;",
    0xFD: "&yacute;", 0xFE: "&thorn;", 0xFF: "&yuml;",
    0x0141: "&Lstrok;", 0x0142: "&lstrok;",
}


def ascii_escape(text: str) -> str:
    """Encode non-ASCII characters as HTML character references.

    Uses named entities for common diacritics (e.g. &uuml; for u-umlaut),
    falls back to numeric references (e.g. &#8212;) for others.
    """
    out = []
    for ch in text:
        cp = ord(ch)
        if cp <= 127:
            out.append(ch)
        elif cp in _NAMED_ENTITIES:
            out.append(_NAMED_ENTITIES[cp])
        else:
            out.append(f"&#{cp};")
    return "".join(out)


FORMAT_CHARS = frozenset(
    chr(c) for c in range(0x110000)
    if unicodedata.category(chr(c)) == 'Cf'
)


def strip_format_chars(text: str) -> str:
    """Remove Unicode format characters (category Cf)."""
    return "".join(c for c in text if c not in FORMAT_CHARS)


FRONT_MATTER_ORDER = ("title", "document", "date", "audience", "reply-to")


def _yaml_escape(s: str) -> str:
    """Escape a string for safe inclusion in double-quoted YAML."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _yaml_value(key: str, val) -> str:
    """Format a single YAML value, quoting where needed."""
    if isinstance(val, list):
        items = [f'  - "{_yaml_escape(str(v))}"' for v in val]
        return f"{key}:\n" + "\n".join(items)
    val = str(val) if not isinstance(val, str) else val
    if any(c in val for c in ':{}[]#&*?|>!%@`"\'\n\\'):
        return f'{key}: "{_yaml_escape(val)}"'
    return f"{key}: {val}"


def format_front_matter(metadata: dict) -> str:
    """Format metadata dict as YAML front matter.

    Field order: title, document, date, audience, reply-to.
    Title and values containing YAML-special characters are double-quoted
    with backslash-escaping for embedded quotes, backslashes, and newlines.
    Reply-to is a YAML list of double-quoted strings.
    Returns empty string if metadata is empty.
    """
    if not metadata:
        return ""
    lines = ["---"]
    for key in FRONT_MATTER_ORDER:
        if key in metadata:
            lines.append(_yaml_value(key, metadata[key]))
    for key, val in metadata.items():
        if key not in FRONT_MATTER_ORDER:
            lines.append(_yaml_value(key, val))
    lines.append("---")
    return "\n".join(lines)


ALLOWED_LINK_SCHEMES = frozenset({"http", "https", "mailto"})

EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")

DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")

DOC_NUM_RE = re.compile(
    r"\b([DPN]\d{3,5}R\d+)\b"
    r"|\b([DPN]\d{3,5})\b"
    r"|\b(N\d{3,5})\b"
    r"|\b(SD-\d+)\b",
    re.IGNORECASE,
)

SECTION_NUM_PREFIX_RE = re.compile(r"^\d+(?:\.\d+)*\.?\s+")
