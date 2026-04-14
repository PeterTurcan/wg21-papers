"""Color math and accent resolution."""

import colorsys

from PIL import Image
from reportlab.lib.colors import HexColor, toColor


_FALLBACK_ACCENT = "#8b1a1a"


def parse_color(value):
    """Parse a color from hex (#rrggbb) or ReportLab named color."""
    if not isinstance(value, str):
        return value
    if value.startswith("#"):
        return HexColor(value)
    return toColor(value)


def hex_to_hsl(hex_str):
    hex_str = hex_str.lstrip("#")
    r, g, b = (int(hex_str[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h, s, l


def hsl_to_hex(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))


def dominant_chromatic_color(image_path):
    with Image.open(image_path) as raw:
        img = raw.convert("RGB")
    img = img.quantize(colors=8, method=Image.Quantize.MEDIANCUT).convert("RGB")
    colors = img.getcolors(maxcolors=img.width * img.height)
    colors.sort(key=lambda c: c[0], reverse=True)
    for count, (r, g, b) in colors:
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if s > 0.15 and 0.1 < l < 0.9:
            return "#{:02x}{:02x}{:02x}".format(r, g, b)
    return _FALLBACK_ACCENT


def resolve_accent(value, logo_path):
    if value == "from_logo" and logo_path:
        return dominant_chromatic_color(logo_path)
    if value == "from_logo":
        return _FALLBACK_ACCENT
    return value


def derive_mid(saturated_hex):
    h, s, l = hex_to_hsl(saturated_hex)
    s = max(0, s * 0.6)
    l = min(1, l + 0.2)
    return hsl_to_hex(h, s, l)


def resolve_colors(style, logo_path):
    sat = resolve_accent(style.get("accent_saturated", _FALLBACK_ACCENT), logo_path)
    style["accent_saturated"] = sat
    mid = style.get("accent_mid", "auto")
    if mid == "auto":
        style["accent_mid"] = derive_mid(sat)
    else:
        style["accent_mid"] = resolve_accent(mid, logo_path)
    lc = style.get("link_color", "auto")
    if lc == "auto":
        style["link_color"] = style["accent_mid"]
    else:
        style["link_color"] = resolve_accent(lc, logo_path)
