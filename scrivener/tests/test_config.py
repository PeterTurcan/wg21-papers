"""Layer 1: Unit tests for lib/config.py pure functions."""

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.config import (
    STYLES_DIR,
    apply_options,
    deep_merge,
    extract_front_matter,
    load_style,
    merge_config,
    resolve_palette,
    resolve_style_path,
    sp,
)


# -- deep_merge --

def test_deep_merge_flat():
    assert deep_merge({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}


def test_deep_merge_nested():
    base = {"x": {"a": 1, "b": 2}}
    over = {"x": {"b": 3, "c": 4}}
    result = deep_merge(base, over)
    assert result == {"x": {"a": 1, "b": 3, "c": 4}}


def test_deep_merge_list_replaces():
    base = {"items": [1, 2, 3]}
    over = {"items": [4]}
    assert deep_merge(base, over) == {"items": [4]}


def test_deep_merge_empty_override():
    base = {"a": 1, "b": {"c": 2}}
    assert deep_merge(base, {}) == base


def test_deep_merge_empty_base():
    over = {"a": 1}
    assert deep_merge({}, over) == {"a": 1}


# -- resolve_palette --

def test_resolve_palette_simple():
    style = {"palette": {"brand": "#ff0000"}, "color": "@brand"}
    resolve_palette(style)
    assert style["color"] == "#ff0000"


def test_resolve_palette_nested():
    style = {
        "palette": {"fg": "#111"},
        "section": {"text_color": "@fg"},
        "items": ["@fg", "plain"],
    }
    resolve_palette(style)
    assert style["section"]["text_color"] == "#111"
    assert style["items"] == ["#111", "plain"]


def test_resolve_palette_no_at():
    style = {"palette": {"fg": "#111"}, "color": "#222"}
    resolve_palette(style)
    assert style["color"] == "#222"


def test_resolve_palette_missing_key():
    style = {"palette": {"fg": "#111"}, "color": "@unknown"}
    resolve_palette(style)
    assert style["color"] == "@unknown"


def test_resolve_palette_empty():
    style = {"color": "@brand"}
    resolve_palette(style)
    assert style["color"] == "@brand"


def test_resolve_palette_mutates_in_place():
    style = {"palette": {"brand": "#ff0000"}, "color": "@brand"}
    original_id = id(style)
    resolve_palette(style)
    assert id(style) == original_id
    assert style["color"] == "#ff0000"


# -- extract_front_matter --

def test_extract_front_matter():
    md = "---\ntitle: Hello\n---\nBody text."
    fm, body = extract_front_matter(md)
    assert fm == {"title": "Hello"}
    assert body == "Body text."


def test_extract_front_matter_none():
    md = "No front matter here."
    fm, body = extract_front_matter(md)
    assert fm == {}
    assert body == md


def test_extract_front_matter_empty_block():
    md = "---\n\n---\nBody."
    fm, body = extract_front_matter(md)
    assert fm == {}
    assert body == "Body."


def test_extract_front_matter_multiline():
    md = "---\ntitle: Hello\ndate: 2026-01-01\nreply-to:\n  - A\n  - B\n---\nBody."
    fm, body = extract_front_matter(md)
    assert fm["title"] == "Hello"
    assert fm["reply-to"] == ["A", "B"]
    assert body == "Body."


# -- merge_config --

def test_merge_config_cli_logo_wins():
    style = {"logo": "default.svg", "toc": False}
    fm = {"logo": "fm.svg"}
    cli = {"logo": "cli.svg"}
    cfg = merge_config(cli, fm, style)
    assert cfg["logo"] == "cli.svg"


def test_merge_config_fm_keys():
    style = {"logo": None, "toc": False, "accent_saturated": "#000"}
    fm = {"logo": "fm.svg", "accent_saturated": "#fff"}
    cfg = merge_config({}, fm, style)
    assert cfg["logo"] == "fm.svg"
    assert cfg["accent_saturated"] == "#fff"


def test_merge_config_toc_true():
    style = {"toc": False}
    cfg = merge_config({"toc": True}, {}, style)
    assert cfg["toc"] is True


def test_merge_config_no_toc():
    style = {"toc": True}
    cfg = merge_config({"no_toc": True}, {}, style)
    assert cfg["toc"] is False


def test_merge_config_no_mutation():
    style = {"toc": False, "body_size": 11}
    original_style = {"toc": False, "body_size": 11}
    merge_config({"toc": True}, {}, style)
    assert style == original_style


# -- apply_options --

def test_apply_options_valid():
    style = {"options": [{"id": "toc"}, {"id": "logo"}], "toc": False}
    apply_options(style, {"toc": True})
    assert style["toc"] is True


def test_apply_options_invalid():
    style = {"options": [{"id": "toc"}]}
    with pytest.raises(ValueError, match="unknown option"):
        apply_options(style, {"bogus": 42})


def test_apply_options_empty_schema():
    style = {"options": []}
    with pytest.raises(ValueError):
        apply_options(style, {"anything": 1})


# -- sp --

def test_sp_basic():
    assert sp({"body_size": 11}, 4 / 11) == pytest.approx(4.0)


def test_sp_default():
    assert sp({}, 1.0) == pytest.approx(11.0)


def test_sp_custom_size():
    assert sp({"body_size": 10}, 0.5) == pytest.approx(5.0)


# -- resolve_style_path --

def test_resolve_style_path_default():
    p = resolve_style_path(None)
    assert p == STYLES_DIR / "default.yaml"
    assert p.exists()


def test_resolve_style_path_name():
    p = resolve_style_path("wg21")
    assert p == STYLES_DIR / "wg21.yaml"
    assert p.exists()


def test_resolve_style_path_missing():
    with pytest.raises(FileNotFoundError):
        resolve_style_path("nonexistent_style_xyz")


# -- load_style --

def test_load_style_inheritance():
    style = load_style(STYLES_DIR / "cpp-al.yaml")
    assert "body_size" in style
    assert "front_matter" in style
    assert "fields" in style["front_matter"]



# Circular inheritance test lives in test_catalog.py (layer 4).
