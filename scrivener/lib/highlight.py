"""Syntax highlighting via Pygments.

highlight()      - ReportLab XML markup (PDF path)
highlight_html() - HTML with class-based spans (HTML path)
"""

from html import escape as _html_escape

from . import escape_xml
from .css import _PYGMENTS_CLASS_MAP

try:
    from pygments import highlight as _hl
    from pygments.formatter import Formatter
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.token import (
        Comment, Keyword, Literal, Name,
        Number, Operator, Punctuation, String,
    )
    from pygments.util import ClassNotFound
    HAS_PYGMENTS = True
except ImportError:
    HAS_PYGMENTS = False

_TOKEN_MAP = {
    Keyword:            "keyword",
    Keyword.Type:       "type",
    Name.Builtin:       "type",
    Name.Class:         "type",
    Name.Function:      "function",
    Name.Decorator:     "function",
    Name.Namespace:     "type",
    String:             "string",
    Literal.String:     "string",
    Number:             "number",
    Literal.Number:     "number",
    Comment:            "comment",
    Comment.Preproc:    "preprocessor",
    Operator:           "operator",
    Punctuation:        "operator",
}


def _resolve(tok, colors):
    """Walk the token type hierarchy to find a matching color."""
    t = tok
    while t:
        key = _TOKEN_MAP.get(t)
        if key and key in colors:
            return colors[key]
        t = t.parent
    return None


def _get_lexer(code, lang):
    """Return a Pygments lexer or None if unrecognized."""
    try:
        if lang:
            return get_lexer_by_name(lang, stripall=True)
        return guess_lexer(code)
    except (ClassNotFound, ValueError):
        return None


class _RLFormatter(Formatter):
    """Pygments formatter that emits ReportLab paragraph XML."""
    def __init__(self, colors, **kw):
        super().__init__(**kw)
        self.colors = colors

    def format(self, tokensource, outfile):
        for ttype, value in tokensource:
            text = escape_xml(value)
            color = _resolve(ttype, self.colors)
            if color:
                outfile.write(f'<font color="{color}">{text}</font>')
            else:
                outfile.write(text)


def highlight(code, lang, colors):
    """Highlight code, returning ReportLab XML markup.

    Falls back to plain escaped text if Pygments is unavailable
    or the language is not recognized.
    """
    if not HAS_PYGMENTS or not colors:
        return escape_xml(code)

    lexer = _get_lexer(code, lang)
    if not lexer:
        return escape_xml(code)

    fmt = _RLFormatter(colors)
    return _hl(code, lexer, fmt)


class _HtmlClassFormatter(Formatter):
    """Pygments formatter that emits HTML spans with CSS classes."""
    def format(self, tokensource, outfile):
        for ttype, value in tokensource:
            text = _html_escape(value, quote=False)
            key = _resolve(ttype, _PYGMENTS_CLASS_MAP)
            if key:
                outfile.write(f'<span class="{key}">{text}</span>')
            else:
                outfile.write(text)


def highlight_html(code, lang):
    """Highlight code, returning HTML with class-based spans.

    Falls back to plain HTML-escaped text if Pygments is unavailable
    or the language is not recognized.
    """
    if not HAS_PYGMENTS:
        return _html_escape(code, quote=False)

    lexer = _get_lexer(code, lang)
    if not lexer:
        return _html_escape(code, quote=False)

    fmt = _HtmlClassFormatter()
    return _hl(code, lexer, fmt)
