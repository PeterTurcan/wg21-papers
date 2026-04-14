"""Triple-signal monospace font detection.

Three independent signals, any two agreeing = high confidence:
  1. Font name decomposition (strip modifiers, split camelCase, check keywords)
  2. Glyph bounding box widths are uniform (low coefficient of variation)
  3. Glyph x-origin spacing is uniform (measures advance width directly)

Signal 3 is the strongest - it measures the defining property of monospace.
"""

import math
import re

_FONT_MODIFIERS = frozenset({
    "thin", "hairline", "extralight", "ultralight", "light",
    "regular", "normal", "book", "medium",
    "semibold", "demibold", "bold", "extrabold", "ultrabold",
    "black", "heavy",
    "italic", "oblique", "roman", "upright",
    "condensed", "narrow", "extended", "expanded", "wide", "compressed",
    "display", "text", "caption", "subhead", "headline", "mt",
})

_MONO_KEYWORDS = frozenset({"mono", "courier", "code", "consolas"})

_CAMEL_SPLIT_RE = re.compile(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")

GLYPH_CV_THRESHOLD = 0.15

_MIN_CHARS_FOR_METRICS = 3


def _strip_modifiers(font_name: str) -> str:
    """Remove separators and known style/weight/width modifiers."""
    name = font_name.replace("-", " ").replace("_", " ")
    tokens = name.split()
    kept = [t for t in tokens if t.lower() not in _FONT_MODIFIERS]
    return "".join(kept)


def _split_camel(name: str) -> list[str]:
    """Split a PascalCase/camelCase string into lowercase tokens."""
    parts = _CAMEL_SPLIT_RE.sub(" ", name).split()
    return [p.lower() for p in parts if p]


def font_name_is_monospace(font_name: str) -> bool:
    """Signal 1: font name contains a monospace keyword after decomposition.

    Strips style/weight modifiers, splits camelCase, checks for
    mono/courier/code/consolas in the remaining family tokens.
    """
    family = _strip_modifiers(font_name)
    tokens = _split_camel(family)
    return bool(_MONO_KEYWORDS & set(tokens))


def _coefficient_of_variation(values: list[float]) -> float:
    """Compute coefficient of variation (stddev / mean). Lower = more uniform."""
    if len(values) < 2:
        return -1.0
    mean = sum(values) / len(values)
    if mean == 0:
        return -1.0
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance) / mean


def glyph_widths_uniform(char_widths: list[float]) -> float:
    """Signal 2: coefficient of variation of character bbox widths.

    Lower value = more uniform = more likely monospace.
    Returns CV, or -1.0 if not enough data.
    """
    widths = [w for w in char_widths if w > 0]
    if len(widths) < _MIN_CHARS_FOR_METRICS:
        return -1.0
    return _coefficient_of_variation(widths)


def glyph_spacing_uniform(char_x_origins: list[float]) -> float:
    """Signal 3: coefficient of variation of inter-glyph x-origin spacing.

    Measures the advance width directly - the defining property of
    monospace fonts. Strongest signal.
    Returns CV, or -1.0 if not enough data.
    """
    if len(char_x_origins) < _MIN_CHARS_FOR_METRICS:
        return -1.0
    spacings = []
    for i in range(1, len(char_x_origins)):
        dx = char_x_origins[i] - char_x_origins[i - 1]
        if dx > 0:
            spacings.append(dx)
    if len(spacings) < 2:
        return -1.0
    return _coefficient_of_variation(spacings)


def classify_monospace(
    font_name: str,
    char_widths: list[float] | None = None,
    char_x_origins: list[float] | None = None,
) -> bool:
    """Combine all available signals to determine if text is monospace.

    Called during extraction when raw character data is available
    (all three signals), or later with just font_name (signal 1 only).
    """
    s1 = font_name_is_monospace(font_name)

    s2_cv = glyph_widths_uniform(char_widths) if char_widths else -1.0
    s3_cv = glyph_spacing_uniform(char_x_origins) if char_x_origins else -1.0

    s2 = 0.0 <= s2_cv <= GLYPH_CV_THRESHOLD
    s3 = 0.0 <= s3_cv <= GLYPH_CV_THRESHOLD

    signals = sum([s1, s2, s3])

    if signals >= 2:
        return True

    if s3:
        return True

    if s1:
        return True

    return False
