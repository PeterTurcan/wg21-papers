"""Font cache, variable-font instantiation, and ReportLab registration.

Variable fonts are instantiated at specific axis values via fontTools.
Instantiated fonts are cached to .fonts/cache/ as static TTFs so
subsequent runs skip the expensive glyph computation. Cache is
invalidated when the source font file is newer than the cached file.
"""

from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_cache = {}
_cmap_cache = {}
_lazy = {}
_families = set()
_fonts_dir = None


def set_fonts_dir(path):
    global _fonts_dir
    _fonts_dir = path


def _resolve(file_name):
    return _fonts_dir / file_name


def _axes_key(axes):
    return "-".join(f"{k}{v}" for k, v in sorted(axes.items()))


def _cache_path(name, axes):
    return _fonts_dir / "cache" / f"{name}-{_axes_key(axes)}.ttf"


def ensure_font(name, var_path, axes):
    cache_key = (str(var_path), tuple(sorted(axes.items())) if axes else ())
    if _cache.get(name) == cache_key:
        return
    if not axes:
        pdfmetrics.registerFont(TTFont(name, str(var_path)))
        _cache[name] = cache_key
        return

    cached = _cache_path(name, axes)
    if cached.exists() and cached.stat().st_mtime >= Path(var_path).stat().st_mtime:
        pdfmetrics.registerFont(TTFont(name, str(cached)))
        _cache[name] = cache_key
        return

    from fontTools.ttLib import TTFont as FTFont
    from fontTools.varLib.instancer import instantiateVariableFont

    vf = FTFont(str(var_path))
    instantiateVariableFont(vf, axes, inplace=True)
    ps_name = name.replace(" ", "-")
    for rec in vf["name"].names:
        if rec.nameID == 6:
            rec.string = ps_name

    cached.parent.mkdir(parents=True, exist_ok=True)
    vf.save(str(cached))
    pdfmetrics.registerFont(TTFont(name, str(cached)))
    _cache[name] = cache_key


def get_cmap(var_path, axes):
    key = (str(var_path), tuple(sorted(axes.items())))
    if key in _cmap_cache:
        return _cmap_cache[key]
    from fontTools.ttLib import TTFont as FTFont
    from fontTools.varLib.instancer import instantiateVariableFont

    vf = FTFont(str(var_path))
    instantiateVariableFont(vf, axes, inplace=True)
    cmap = set()
    for table in vf["cmap"].tables:
        if table.cmap:
            cmap.update(table.cmap.keys())
    _cmap_cache[key] = cmap
    return cmap


def ensure_lazy(name):
    if name not in _lazy:
        return
    var_path, axes = _lazy[name]
    ensure_font(name, var_path, axes)


def register_fonts(style):
    fonts_cfg = style.get("fonts", {})
    font_map = {
        "body": "Body",
        "body_bold": "Body-Bold",
        "body_italic": "Body-Italic",
        "body_bold_italic": "Body-BoldItalic",
        "code": "Code",
        "code_bold": "Code-Bold",
        "code_italic": "Code-Italic",
        "code_bold_italic": "Code-BoldItalic",
        "cjk": "CJK",
    }
    eager = {"body", "body_bold"}
    for key, rl_name in font_map.items():
        entry = fonts_cfg.get(key)
        if not entry:
            continue
        path = _resolve(entry["file"])
        axes = dict(entry.get("axes", {}))
        if key in eager:
            ensure_font(rl_name, path, axes)
        else:
            _lazy[rl_name] = (path, axes)


def register_families():
    if "Body" not in _families:
        ensure_lazy("Body-Italic")
        ensure_lazy("Body-BoldItalic")
        pdfmetrics.registerFontFamily(
            "Body", normal="Body", bold="Body-Bold",
            italic="Body-Italic", boldItalic="Body-BoldItalic")
        _families.add("Body")


def ensure_code_family():
    if "Code" in _families:
        return
    ensure_lazy("Code")
    ensure_lazy("Code-Bold")
    ensure_lazy("Code-Italic")
    ensure_lazy("Code-BoldItalic")
    pdfmetrics.registerFontFamily(
        "Code", normal="Code", bold="Code-Bold",
        italic="Code-Italic", boldItalic="Code-BoldItalic")
    _families.add("Code")


def build_body_cmap(style):
    entry = style.get("fonts", {}).get("body", {})
    if not entry:
        return set()
    path = _resolve(entry["file"])
    axes = dict(entry.get("axes", {}))
    return get_cmap(path, axes)
