"""Monkey-patch ReportLab's inline backColor rendering to use
rounded rectangles with padding derived from font metrics.

This replaces ReportLab's default _do_post_text with a version
that draws inline code backgrounds as rounded rects. Controls
the fill, stroke, radius, and padding of inline `code` spans.
"""

from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import paragraph as _mod

_orig = _mod._do_post_text

RADIUS = 2


def _patched(tx):
    xs = tx.XtraState
    if xs.backColors:
        f = xs.f
        fs = f.fontSize
        fn = getattr(f, 'fontName', None) or getattr(f, 'name', 'Helvetica')
        y0 = xs.cur_y
        leading = xs.style.leading

        from reportlab.pdfbase.pdfmetrics import getFont
        face = getFont(fn).face
        em = face.ascent + abs(face.descent)
        asc = face.ascent / em * fs
        desc = abs(face.descent) / em * fs

        gap = leading - asc - desc
        pad_x = stringWidth(' ', fn, fs) / 3
        bot = y0 - desc - gap / 3
        top = y0 + asc + gap / 3
        h = top - bot

        # Merge consecutive spans with the same color into one rectangle.
        merged = []
        for x1, x2, color in xs.backColors:
            if merged and str(merged[-1][2]) == str(color) and x1 <= merged[-1][1] + pad_x * 3:
                merged[-1] = (merged[-1][0], x2, color)
            else:
                merged.append([x1, x2, color])

        c = tx._canvas
        for x1, x2, color in merged:
            c.saveState()
            c.setFillColor(color)
            c.roundRect(x1 - pad_x, bot, (x2 - x1) + 2 * pad_x,
                        h, RADIUS, stroke=0, fill=1)
            c.restoreState()
        xs.backColors = []
        xs.backColor = None
    _orig(tx)


import reportlab
_rl_version = tuple(int(x) for x in reportlab.Version.split("."))
if _rl_version < (3, 5):
    import warnings
    warnings.warn("inline_patch: untested with ReportLab < 3.5")
_mod._do_post_text = _patched
