"""Unit tests for the native ReportLab Mermaid renderer."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.mermaid import (
    draw_mermaid,
    _parse_and_layout,
    _polyline_midpoint,
    _strip_label_quotes,
)


SIMPLE_STYLE = {
    "body_size": 10,
    "heading_rule_color": "#333333",
    "accent_color": "#9370DB",
    "mermaid_max_height_ratio": 0.8,
}


def test_parse_and_layout_simple(font_registered):
    code = "flowchart TD\n    A[Start] --> B[End]"
    diagram, layout = _parse_and_layout(code, "Body", 8.5)
    assert len(layout.nodes) == 2
    assert len(layout.edges) == 1
    assert layout.width > 0
    assert layout.height > 0


def test_draw_mermaid_returns_flowables(font_registered):
    code = "flowchart TD\n    A[Start] --> B[End]"
    result = draw_mermaid(code, 500, 700, SIMPLE_STYLE, body_font="Body")
    assert result is not None
    assert len(result) == 3  # Spacer, Drawing, Spacer


def test_draw_mermaid_with_diamond(font_registered):
    code = "flowchart TD\n    A[Start] --> B{Decision}\n    B --> C[End]"
    result = draw_mermaid(code, 500, 700, SIMPLE_STYLE, body_font="Body")
    assert result is not None


def test_draw_mermaid_with_edge_labels(font_registered):
    code = "flowchart TD\n    A[Start] -->|yes| B[End]\n    A -.->|no| C[Alt]"
    result = draw_mermaid(code, 500, 700, SIMPLE_STYLE, body_font="Body")
    assert result is not None


def test_draw_mermaid_with_subgraph(font_registered):
    code = (
        "flowchart TD\n"
        "    subgraph grp [My Group]\n"
        "        A[One] --> B[Two]\n"
        "    end\n"
        "    B --> C[Three]"
    )
    result = draw_mermaid(code, 500, 700, SIMPLE_STYLE, body_font="Body")
    assert result is not None


def test_draw_mermaid_multiline_label(font_registered):
    code = 'flowchart TD\n    A["Line One\\nLine Two"] --> B[End]'
    result = draw_mermaid(code, 500, 700, SIMPLE_STYLE, body_font="Body")
    assert result is not None


def test_draw_mermaid_lr_direction(font_registered):
    code = "flowchart LR\n    A[Start] --> B[End]"
    result = draw_mermaid(code, 500, 700, SIMPLE_STYLE, body_font="Body")
    assert result is not None


def test_draw_mermaid_returns_none_on_bad_input(font_registered):
    result = draw_mermaid("not valid mermaid", 500, 700, SIMPLE_STYLE)
    assert result is None


def test_draw_mermaid_circle_shape(font_registered):
    code = "flowchart TD\n    A((Circle)) --> B[End]"
    result = draw_mermaid(code, 500, 700, SIMPLE_STYLE, body_font="Body")
    assert result is not None


def test_drawing_fits_content_width(font_registered):
    code = "flowchart TD\n    A[Start] --> B[End]"
    width = 400
    result = draw_mermaid(code, width, 700, SIMPLE_STYLE, body_font="Body")
    assert result is not None
    drawing = result[1]
    assert drawing.width <= width + 1  # allow rounding tolerance


# ---------------------------------------------------------------------------
# Edge label and arrowhead positioning regression tests.
#
# These pin down four bugs in the native mermaid renderer that made labelled
# edges unreadable in the rendered PDF:
#
#   1. ``points[len(points)//2]`` returned the *target* vertex for any
#      2-point polyline, slamming the edge label into the arrowhead.
#   2. Labels had no opaque background, so the polyline showed through the
#      glyphs.
#   3. ``merm`` keeps the surrounding double quotes from Mermaid's
#      ``-- "label" -->`` safe-quoting syntax, so labels rendered as
#      ``"prepare(n)"`` instead of ``prepare(n)``.
#   4. Arrowheads were drawn before nodes, so a node fill that touched the
#      polyline endpoint could erase the arrow tip.
# ---------------------------------------------------------------------------


class _Pt:
    """Minimal stand-in for ``merm.layout.Point`` for unit tests."""
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x = x
        self.y = y


def test_polyline_midpoint_two_points():
    """Bug 1 regression: 2-point midpoint is the segment midpoint, not p[1]."""
    mx, my = _polyline_midpoint([_Pt(0, 0), _Pt(10, 20)])
    assert mx == pytest.approx(5.0)
    assert my == pytest.approx(10.0)


def test_polyline_midpoint_three_equal_segments():
    mx, my = _polyline_midpoint([_Pt(0, 0), _Pt(10, 0), _Pt(20, 0)])
    assert mx == pytest.approx(10.0)
    assert my == pytest.approx(0.0)


def test_polyline_midpoint_three_uneven_segments():
    """Midpoint walks segment lengths, not vertex indices."""
    pts = [_Pt(0, 0), _Pt(2, 0), _Pt(12, 0)]  # lengths 2 and 10, total 12
    mx, my = _polyline_midpoint(pts)
    # half of total length = 6 → 4 units into the second segment
    assert mx == pytest.approx(6.0)
    assert my == pytest.approx(0.0)


def test_polyline_midpoint_zero_length_first_segment():
    """A duplicated point must not produce a divide-by-zero."""
    pts = [_Pt(5, 5), _Pt(5, 5), _Pt(5, 15)]
    mx, my = _polyline_midpoint(pts)
    assert mx == pytest.approx(5.0)
    assert my == pytest.approx(10.0)


def test_polyline_midpoint_single_point():
    assert _polyline_midpoint([_Pt(7, 9)]) == (7, 9)


def test_polyline_midpoint_empty():
    assert _polyline_midpoint([]) == (0.0, 0.0)


@pytest.mark.parametrize("raw,expected", [
    ('"prepare(n)"', "prepare(n)"),
    ("'commit'", "commit"),
    ('plain', "plain"),
    ('""', ""),
    ('"', '"'),                 # too short to be a quoted pair
    ('', ''),
    ('"mismatched\'', '"mismatched\''),
    (None, None),               # non-string input passes through
])
def test_strip_label_quotes(raw, expected):
    """Bug 3 regression: surrounding quote pair gets stripped exactly once."""
    assert _strip_label_quotes(raw) == expected


def _diagram_contents(code):
    """Render *code* and return the list of ReportLab shape primitives."""
    flowables = draw_mermaid(code, 460, 700, SIMPLE_STYLE, body_font="Body")
    assert flowables is not None
    return flowables[1].contents


def _kind(shape):
    return type(shape).__name__


def test_edge_label_strips_surrounding_quotes(font_registered):
    """Bug 3 regression: ``-- "label" -->`` renders as ``label``."""
    code = (
        'flowchart TB\n'
        '    A[A] -- "prepare(n)" --> B[B]\n'
        '    B -- "commit(m)" --> C[C]'
    )
    contents = _diagram_contents(code)
    body_size = SIMPLE_STYLE["body_size"]
    label_texts = [
        s.text for s in contents
        if _kind(s) == "String" and s.fontSize < body_size
    ]
    assert "prepare(n)" in label_texts
    assert "commit(m)" in label_texts
    for t in label_texts:
        assert not (t.startswith('"') and t.endswith('"')), (
            f"surrounding quotes leaked into label: {t!r}"
        )


def test_edge_label_at_polyline_midpoint_not_endpoint(font_registered):
    """Bug 1 regression: the label lands at the geometric midpoint, far from
    the target endpoint where the arrowhead lives."""
    code = 'flowchart TB\n    A[A] -- "lbl" --> B[B]'
    diagram, layout = _parse_and_layout(code, "Body", SIMPLE_STYLE["body_size"])
    el = layout.edges[0]
    p0, p1 = el.points[0], el.points[-1]

    scale = min(460 / layout.width, 1.0)
    max_h = 700 * SIMPLE_STYLE["mermaid_max_height_ratio"]
    if layout.height * scale > max_h:
        scale = max_h / layout.height

    expected_x = 0.5 * (p0.x + p1.x) * scale
    midpoint_y_rl = (layout.height - 0.5 * (p0.y + p1.y)) * scale
    target_y_rl = (layout.height - p1.y) * scale

    contents = _diagram_contents(code)
    labels = [s for s in contents if _kind(s) == "String" and s.text == "lbl"]
    assert len(labels) == 1
    label = labels[0]

    assert label.x == pytest.approx(expected_x, abs=0.5)
    # The baseline is offset slightly above the midpoint y; allow one body unit.
    assert abs(label.y - midpoint_y_rl) < SIMPLE_STYLE["body_size"]
    # And it must be much closer to the midpoint than to the endpoint.
    assert abs(label.y - midpoint_y_rl) < abs(label.y - target_y_rl)


def test_edge_label_has_opaque_background_mask(font_registered):
    """Bug 2 regression: an opaque white Rect precedes every edge label."""
    code = 'flowchart TB\n    A[A] -- "lbl" --> B[B]'
    contents = _diagram_contents(code)
    label_idx = next(
        i for i, s in enumerate(contents)
        if _kind(s) == "String" and s.text == "lbl"
    )
    bg = contents[label_idx - 1]
    assert _kind(bg) == "Rect", (
        "edge label is not preceded by a background Rect — the polyline "
        "will show through the label glyphs"
    )
    fc = bg.fillColor
    assert fc is not None and fc.red == 1.0 and fc.green == 1.0 and fc.blue == 1.0
    # No visible stroke on the mask — it must blend into the page.
    assert bg.strokeColor is None or bg.strokeWidth == 0


def test_arrowheads_drawn_after_nodes(font_registered):
    """Bug 4 regression: arrowhead polygons appear after every node Rect, so
    a node fill at the polyline endpoint cannot erase the arrow."""
    code = 'flowchart TB\n    A[Start] --> B[End]'
    contents = _diagram_contents(code)
    body_size = SIMPLE_STYLE["body_size"]
    # Node labels render at full body_size; edge labels render smaller.
    last_node_label_idx = max(
        (i for i, s in enumerate(contents)
         if _kind(s) == "String" and s.fontSize >= body_size),
        default=-1,
    )
    assert last_node_label_idx >= 0
    polygon_indices = [i for i, s in enumerate(contents) if _kind(s) == "Polygon"]
    assert polygon_indices, "expected at least one arrowhead polygon"
    assert min(polygon_indices) > last_node_label_idx


@pytest.mark.parametrize("code,desc", [
    (
        'flowchart TD\n'
        '    A["parent resumes - slot = parent.frame_alloc"]\n'
        '    A --> B["parent calls child()"]\n'
        '    B --> C["child operator new - reads slot"]',
        "long labels (d4172-style)",
    ),
    (
        'flowchart TD\n    A["Line One\\nLine Two"] --> B[End]',
        "multi-line label",
    ),
    (
        'flowchart TD\n'
        '    A[Short] --> B{Decision Point}\n'
        '    B --> C((Circle))',
        "mixed shapes",
    ),
])
def test_text_fits_in_boxes(font_registered, code, desc):
    """Verify that every node label fits inside its laid-out box."""
    from reportlab.pdfbase.pdfmetrics import stringWidth

    font_size = SIMPLE_STYLE["body_size"]
    diagram, layout = _parse_and_layout(code, "Body", font_size)

    content_width = 460
    page_h = 700
    scale = content_width / layout.width
    max_h = page_h * SIMPLE_STYLE.get("mermaid_max_height_ratio", 0.8)
    if layout.height * scale > max_h:
        scale = max_h / layout.height

    fs = font_size * scale
    node_map = {n.id: n for n in diagram.nodes}

    for nid, nl in layout.nodes.items():
        ir = node_map.get(nid)
        if not ir or not ir.label:
            continue
        label = ir.label
        lines = label.split("\\n") if "\\n" in label else label.split("\n")

        box_w = nl.width * scale
        box_h = nl.height * scale
        text_w = max(stringWidth(ln.strip(), "Body", fs) for ln in lines)
        text_h = fs * 1.3 * len(lines)

        assert text_w < box_w, (
            f"[{desc}] node {nid}: text width {text_w:.1f} > box width {box_w:.1f}"
        )
        assert text_h < box_h, (
            f"[{desc}] node {nid}: text height {text_h:.1f} > box height {box_h:.1f}"
        )
