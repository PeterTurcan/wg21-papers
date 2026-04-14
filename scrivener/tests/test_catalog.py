"""Layer 4: Style and catalog tests."""

import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.catalog import list_images, list_styles
from lib.config import STYLES_DIR, load_style, resolve_style_path


# -- list_styles --

def test_list_styles_contains_default():
    styles = list_styles()
    ids = {s["id"] for s in styles}
    assert "default" in ids


def test_list_styles_contains_wg21():
    styles = list_styles()
    wg21 = next(s for s in styles if s["id"] == "wg21")
    assert wg21["inherits"] == "default"


def test_list_styles_entry_shape():
    styles = list_styles()
    for s in styles:
        assert "id" in s
        assert "name" in s
        assert "images" in s


def test_list_styles_options():
    styles = list_styles()
    default = next(s for s in styles if s["id"] == "default")
    assert "options" in default
    opt_ids = {o["id"] for o in default["options"]}
    assert "toc" in opt_ids
    assert "logo" in opt_ids
    assert "accent_saturated" in opt_ids


def test_list_styles_options_have_required_keys():
    styles = list_styles()
    default = next(s for s in styles if s["id"] == "default")
    for opt in default["options"]:
        assert "id" in opt
        assert "label" in opt
        assert "type" in opt


# -- list_images --

def test_list_images():
    images = list_images()
    assert "C++ Alliance - Logo.svg" in images


def test_list_images_returns_sorted():
    images = list_images()
    assert images == sorted(images)


# -- load_style --

_REQUIRED_KEYS = [
    "body_size", "line_height", "code_fg", "code_bg",
    "blockquote_fg", "blockquote_bg", "heading_rule_color",
    "page_number_color", "front_matter_label_color",
    "accent_saturated", "table_rule_color", "table_header_bg",
]


def test_load_style_default_keys():
    style = load_style(resolve_style_path(None))
    for key in _REQUIRED_KEYS:
        assert key in style, f"missing key: {key}"


def test_load_style_default_has_sections():
    style = load_style(resolve_style_path(None))
    assert "headings" in style
    assert "code_block" in style
    assert "blockquote" in style
    assert "wording" in style
    assert "table" in style
    assert "fonts" in style


def test_load_style_wg21_inherits():
    style = load_style(resolve_style_path("wg21"))
    assert "body_size" in style
    assert "front_matter" in style
    assert "fields" in style["front_matter"]
    assert len(style["front_matter"]["fields"]) > 0


def test_load_style_palette_resolved():
    style = load_style(resolve_style_path(None))
    def check(obj, path=""):
        if isinstance(obj, str) and obj.startswith("@"):
            pytest.fail(f"unresolved @-reference at {path}: {obj}")
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if k == "palette":
                    continue
                check(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                check(v, f"{path}[{i}]")
    check(style)


def test_load_style_wg21_palette_resolved():
    style = load_style(resolve_style_path("wg21"))
    def check(obj, path=""):
        if isinstance(obj, str) and obj.startswith("@"):
            pytest.fail(f"unresolved @-reference at {path}: {obj}")
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if k == "palette":
                    continue
                check(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                check(v, f"{path}[{i}]")
    check(style)


# -- circular inheritance --

def test_circular_inheritance():
    with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", dir=STYLES_DIR,
            delete=False, encoding="utf-8") as f:
        f.write(f"inherits: {Path(f.name).stem}\nname: Self\n")
        temp_style = Path(f.name)
    try:
        with pytest.raises(ValueError, match="circular"):
            load_style(temp_style)
    finally:
        os.unlink(temp_style)
