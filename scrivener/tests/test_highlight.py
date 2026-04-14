"""Layer 1: Unit tests for lib/highlight.py syntax highlighting."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.highlight import highlight


_COLORS = {
    "keyword": "#622876",
    "type": "#005f88",
    "function": "#1b5196",
    "string": "#366d36",
    "number": "#8f4700",
    "comment": "#6e6e6e",
    "preprocessor": "#882936",
    "operator": "#444444",
}


def test_highlight_python():
    code = 'x = 42\nprint("hello")'
    result = highlight(code, "python", _COLORS)
    assert '<font color=' in result


def test_highlight_cpp():
    code = "#include <vector>\nint main() { return 0; }"
    result = highlight(code, "cpp", _COLORS)
    assert '<font color=' in result


def test_highlight_unknown_lang():
    code = "some random code"
    result = highlight(code, "not_a_real_language_xyz", _COLORS)
    assert "<font" not in result
    assert "&" not in code or "&amp;" in result


def test_highlight_no_colors():
    code = "x = 42"
    result = highlight(code, "python", None)
    assert "<font" not in result


def test_highlight_empty_colors():
    code = "x = 42"
    result = highlight(code, "python", {})
    assert "<font" not in result


def test_highlight_no_lang():
    code = "def foo(): pass"
    result = highlight(code, None, _COLORS)
    assert isinstance(result, str)


def test_highlight_escapes_xml():
    code = 'x < 10 && y > 5'
    result = highlight(code, "python", _COLORS)
    assert "<" not in result or "<font" in result
    assert "&&" not in result


def test_highlight_empty_code():
    result = highlight("", "python", _COLORS)
    assert isinstance(result, str)
