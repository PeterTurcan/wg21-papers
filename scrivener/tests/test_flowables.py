"""Layer 1: Unit tests for lib/flowables.py drawing primitives."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.flowables import PageChrome


def _make_style(body_size=11):
    return {
        "body_size": body_size,
        "page_number_color": "#666666",
        "page_number_font_size": 8,
        "page_size": "letter",
    }


def test_page_chrome_offset_scales():
    """Page number Y offset must scale with body_size, not be hardcoded."""
    chrome_small = PageChrome(_make_style(body_size=9))
    chrome_large = PageChrome(_make_style(body_size=14))

    canvas_small = MagicMock()
    canvas_large = MagicMock()

    chrome_small(canvas_small, MagicMock())
    chrome_large(canvas_large, MagicMock())

    y_small = canvas_small.drawCentredString.call_args[0][1]
    y_large = canvas_large.drawCentredString.call_args[0][1]

    assert y_small != y_large, "page number offset must vary with body_size"
