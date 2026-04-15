"""Scrivener internals. See scrivener.py for the CLI entry point."""

from . import inline_patch  # noqa: F401 - patches ReportLab on import


def escape_xml(text):
    """Escape &, <, > for ReportLab XML paragraph text content.

    Does not escape quotes - not needed for text nodes, only attributes.
    """
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
