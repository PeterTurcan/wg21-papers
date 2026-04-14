"""Shared test fixtures for scrivener test suite."""

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.config import load_style, resolve_style_path
from lib.font_manifest import (
    ensure_fonts_downloaded,
    load_font_manifest,
    resolve_font_files,
)
from lib.fonts import (
    build_body_cmap,
    register_families,
    register_fonts,
    set_fonts_dir,
)


@pytest.fixture
def min_style():
    """Resolved default style dict - deep-copied so tests can mutate freely."""
    style_path = resolve_style_path(None)
    return copy.deepcopy(load_style(style_path))


_fonts_ready = False


@pytest.fixture(scope="session")
def font_registered():
    """Download, register, and cache fonts once per test session."""
    global _fonts_ready
    if _fonts_ready:
        return
    style_path = resolve_style_path(None)
    style = load_style(style_path)
    manifest = load_font_manifest()
    resolve_font_files(style, manifest)
    fonts_dir = ensure_fonts_downloaded(style, manifest)
    set_fonts_dir(fonts_dir)
    register_fonts(style)
    register_families()
    _fonts_ready = True


@pytest.fixture
def tmp_md(tmp_path):
    """Factory: write markdown text to a temp file and return its path."""
    def _write(text, name="test.md"):
        p = tmp_path / name
        p.write_text(text, encoding="utf-8")
        return p
    return _write
