"""Scrivener internals. See scrivener.py for the CLI entry point."""

import html

from . import inline_patch  # noqa: F401 - patches ReportLab on import


def escape_xml(text):
    """Escape &, <, > for ReportLab XML paragraph text content.

    Does not escape quotes - not needed for text nodes, only attributes.
    """
    return html.escape(text, quote=False)


def _is_sup_or_sub_open(tok):
    """True if tok is an inline_html token opening <sup> or <sub>."""
    if tok.get("type") == "inline_html":
        raw = tok.get("raw", tok.get("text", ""))
        return raw.startswith("<sup>") or raw.startswith("<sub>")
    return False
