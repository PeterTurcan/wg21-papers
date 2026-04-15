"""Layer 1: Unit tests for lib/colors.py color math."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.colors import (
    _FALLBACK_ACCENT,
    derive_mid,
    hex_to_hsl,
    hsl_to_hex,
    parse_color,
    resolve_accent,
    resolve_colors,
)


# -- hex_to_hsl / hsl_to_hex round-trip --

@pytest.mark.parametrize("color", [
    "#ff0000", "#00ff00", "#0000ff",
    "#8b1a1a", "#a91c21", "#333333",
    "#ffffff", "#000000", "#1b5196",
])
def test_hex_to_hsl_roundtrip(color):
    h, s, l = hex_to_hsl(color)
    result = hsl_to_hex(h, s, l)
    # Allow 1/255 rounding tolerance per channel
    for i in range(1, 7, 2):
        orig = int(color[i:i+2], 16)
        got = int(result[i:i+2], 16)
        assert abs(orig - got) <= 1, f"{color} -> {result} (channel {i})"


def test_hex_to_hsl_known_red():
    h, s, l = hex_to_hsl("#ff0000")
    assert h == pytest.approx(0.0)
    assert s == pytest.approx(1.0)
    assert l == pytest.approx(0.5)


def test_hex_to_hsl_known_white():
    h, s, l = hex_to_hsl("#ffffff")
    assert l == pytest.approx(1.0)
    assert s == pytest.approx(0.0)


def test_hex_to_hsl_known_black():
    h, s, l = hex_to_hsl("#000000")
    assert l == pytest.approx(0.0)


# -- derive_mid --

def test_derive_mid_lighter_and_less_saturated():
    sat = "#8b1a1a"
    mid = derive_mid(sat)
    _, s_sat, l_sat = hex_to_hsl(sat)
    _, s_mid, l_mid = hex_to_hsl(mid)
    assert l_mid >= l_sat, "mid should be at least as light"
    assert s_mid <= s_sat, "mid should be at most as saturated"


def test_derive_mid_pure_color():
    mid = derive_mid("#ff0000")
    _, s, l = hex_to_hsl(mid)
    assert l > 0.5
    assert s < 1.0


# -- resolve_accent --

def test_resolve_accent_passthrough():
    assert resolve_accent("#aabbcc", "/some/logo.svg") == "#aabbcc"


def test_resolve_accent_from_logo_no_logo():
    assert resolve_accent("from_logo", None) == _FALLBACK_ACCENT


def test_resolve_accent_plain_value():
    assert resolve_accent("auto", None) == "auto"


# -- parse_color --

def test_parse_color_hex():
    c = parse_color("#ff0000")
    assert hasattr(c, "red") and hasattr(c, "green") and hasattr(c, "blue")
    assert c.red == pytest.approx(1.0)
    assert c.green == pytest.approx(0.0)


def test_parse_color_named():
    c = parse_color("red")
    assert c is not None
    assert hasattr(c, "red")


def test_parse_color_passthrough():
    from reportlab.lib.colors import HexColor
    obj = HexColor("#123456")
    assert parse_color(obj) is obj


# -- resolve_colors --

def test_resolve_colors_mutates_in_place():
    style = {"accent_saturated": "#8b1a1a", "accent_mid": "auto", "link_color": "auto"}
    original_id = id(style)
    resolve_colors(style, None)
    assert id(style) == original_id
    assert style["accent_saturated"] == "#8b1a1a"
    assert style["accent_mid"] != "auto"
    assert style["link_color"] != "auto"


def test_resolve_colors_sets_keys():
    style = {"accent_saturated": "#8b1a1a"}
    resolve_colors(style, None)
    assert "accent_saturated" in style
    assert "accent_mid" in style
    assert "link_color" in style


def test_resolve_colors_missing_accent_raises():
    with pytest.raises(KeyError):
        resolve_colors({}, None)
