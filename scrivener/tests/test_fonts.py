"""Layer 1: Unit tests for lib/fonts.py font registration."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import lib.fonts as fonts_mod


def test_resolve_raises_without_fonts_dir(monkeypatch):
    monkeypatch.setattr(fonts_mod, "_fonts_dir", None)
    with pytest.raises(RuntimeError, match="set_fonts_dir"):
        fonts_mod._resolve("test.ttf")
