"""Shared test fixtures for scrivener test suite."""

import copy
import struct
import sys
import zlib
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


# 1x1 transparent PNG (67 bytes) - shared across test modules
MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
    b"\r\n\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def make_png(width, height):
    """Build a minimal RGBA PNG of the given dimensions."""
    raw_row = b"\x00" + b"\x00\x00\x00\xff" * width
    raw_data = raw_row * height
    compressed = zlib.compress(raw_data)

    def chunk(ctype, data):
        c = ctype + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)

    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr_data)
            + chunk(b"IDAT", compressed)
            + chunk(b"IEND", b""))


@pytest.fixture
def tmp_md(tmp_path):
    """Factory: write markdown text to a temp file and return its path."""
    def _write(text, name="test.md"):
        p = tmp_path / name
        p.write_text(text, encoding="utf-8")
        return p
    return _write
