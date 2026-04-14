"""Layer 1: Unit tests for escape_xml in lib/__init__.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib import escape_xml


def test_escape_amp():
    assert escape_xml("a & b") == "a &amp; b"


def test_escape_lt():
    assert escape_xml("<tag>") == "&lt;tag&gt;"


def test_escape_gt():
    assert escape_xml("x > y") == "x &gt; y"


def test_escape_combined():
    assert escape_xml("<a & b>") == "&lt;a &amp; b&gt;"


def test_escape_passthrough():
    assert escape_xml("hello world") == "hello world"


def test_escape_empty():
    assert escape_xml("") == ""


def test_escape_double_amp():
    assert escape_xml("&&") == "&amp;&amp;"
