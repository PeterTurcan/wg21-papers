# ReportLab keepWithNext Bug

## The Problem

ReportLab's `keepWithNext` (on `ParagraphStyle` or set directly on a flowable) is unreliable. A heading with `keepWithNext=True` can still be orphaned at the bottom of a page with its content on the next page.

## Root Cause

`BaseDocTemplate.handle_keepWithNext()` wraps consecutive keepWithNext flowables plus the next flowable into a `KeepTogether`. Before doing so, it writes `f.__dict__['keepWithNext'] = 0` on all but the last flowable in the group to prevent infinite recursion.

If the `KeepTogether` doesn't fit on the current page, `KeepTogether.split()` inserts a `FrameBreak` and returns the original flowables back into the layout pipeline. But those flowables now have `keepWithNext=0` baked into their `__dict__`, which permanently shadows the style-based value. On retry, `getKeepWithNext()` finds the instance attribute `0` first and returns it. The heading is placed alone.

### getKeepWithNext lookup order

```python
def getKeepWithNext(self):
    if hasattr(self, 'keepWithNext'): return self.keepWithNext      # (1) instance dict — corrupted to 0
    elif hasattr(self, 'style') and hasattr(self.style, 'keepWithNext'): return self.style.keepWithNext  # (2) never reached
    else: return 0
```

After the `KeepTogether` split, step (1) always returns `0`, step (2) is never checked.

### Additional hazards

- `ListFlowable.split()` dissolves the list into raw `LIIndenter` flowables, losing the wrapper. Combined with the `__dict__` corruption this makes `keepWithNext` + `ListFlowable` especially fragile.
- `_listWrapOn()` skips zero-width flowables when computing height but `Frame._add()` does not, causing height miscalculation in `KeepTogether`. Acknowledged by the ReportLab maintainer (2021), never fixed.

## The Fix

Use `CondPageBreak(height)` before the heading instead of relying on `keepWithNext`. `CondPageBreak` inserts a page break only if less than `height` points of space remain. This avoids the `KeepTogether` wrapping entirely.

```python
from reportlab.platypus import CondPageBreak

# height = heading + two lines of body text
hs = self.ps[style_key]
body_lines = style["body_size"] * style["line_height"] * 2
cpb_h = hs.fontSize + hs.leading + hs.spaceBefore + body_lines
flows.append(CondPageBreak(cpb_h))
flows.append(Paragraph(text, hs))
```

This is the workaround recommended by the ReportLab maintainer.

## Rules

- Do not rely on `keepWithNext` as the sole mechanism to prevent orphaned headings. Always pair it with a `CondPageBreak`.
- Do not remove the existing `keepWithNext=True` from heading `ParagraphStyle` definitions — it still helps in cases where the `KeepTogether` wrapping succeeds without splitting.
- If you encounter orphaned flowables in PDF output, check this file before debugging from scratch.
