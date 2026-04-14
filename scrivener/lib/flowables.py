"""Stable drawing primitives. Changes here affect every visual
element in every style. Modify with care."""

from reportlab.platypus import Flowable

from .colors import parse_color
from .config import PAGE_CONFIGS


class AccentBox(Flowable):
    """Box with background fill, accent-colored left bar, and inner content.

    Used for front-matter blocks (radius=0) and blockquotes (radius>0).
    Do not duplicate this pattern elsewhere.
    """
    def __init__(self, content, bg, accent, bar_w,
                 left_pad, right_pad, v_pad, width=None,
                 cap_shift=0, top_rule=None, top_rule_thickness=None):
        super().__init__()
        self._content = content
        self.bg = bg
        self.accent = accent
        self.bar_w = bar_w
        self.left_pad = left_pad
        self.right_pad = right_pad
        self.v_pad = v_pad
        self.box_width = width
        self.cap_shift = cap_shift
        self.top_rule = top_rule
        self.top_rule_thickness = top_rule_thickness if top_rule_thickness is not None else 1.5

    def wrap(self, availWidth, availHeight):
        w = self.box_width if self.box_width is not None else availWidth
        self._inner_w = w - self.left_pad - self.right_pad
        cw, ch = self._content.wrap(self._inner_w, availHeight - 2 * self.v_pad)
        self._ch = ch
        self.width = w
        self.height = ch + 2 * self.v_pad
        return self.width, self.height

    def split(self, availWidth, availHeight):
        if self.height <= availHeight:
            return [self]
        inner_avail = availHeight - 2 * self.v_pad
        if inner_avail <= 0:
            return []
        parts = self._content.split(self._inner_w, inner_avail)
        if not parts or len(parts) < 2:
            return []
        top = AccentBox(parts[0], self.bg, self.accent, self.bar_w,
                        self.left_pad, self.right_pad, self.v_pad,
                        width=self.box_width,
                        cap_shift=self.cap_shift,
                        top_rule=self.top_rule,
                        top_rule_thickness=self.top_rule_thickness)
        bot = AccentBox(parts[1], self.bg, self.accent, self.bar_w,
                        self.left_pad, self.right_pad, self.v_pad,
                        width=self.box_width,
                        cap_shift=self.cap_shift)
        return [top, bot]

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(self.bg)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        if self.top_rule:
            c.saveState()
            c.setFillColor(self.top_rule)
            c.rect(0, self.height - self.top_rule_thickness, self.width,
                self.top_rule_thickness, fill=1, stroke=0)
            c.restoreState()
        c.setFillColor(self.accent)
        c.rect(0, 0, self.bar_w, self.height, fill=1, stroke=0)
        c.restoreState()
        y = (self.height - self._ch) / 2 - self.cap_shift
        self._content.drawOn(c, self.left_pad, y)


class TitleEnd(Flowable):
    """Zero-height sentinel marking the end of title-block flows."""
    def wrap(self, availWidth, availHeight):
        return 0, 0

    def draw(self):
        pass


class PageChrome:
    """Page-level drawing: page number."""
    def __init__(self, style):
        self.pn_color = parse_color(style["page_number_color"])
        self.pn_font_size = style.get("page_number_font_size", 8)
        pc = PAGE_CONFIGS[style.get("page_size", "letter")]
        self.page_w, self.page_h = pc["size"]
        self.margin = pc["margin"]

    def __call__(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("Body", self.pn_font_size)
        canvas.setFillColor(self.pn_color)
        canvas.drawCentredString(
            self.page_w / 2, self.margin - 20,
            str(canvas.getPageNumber()))
        canvas.restoreState()
