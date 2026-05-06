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
    if _fonts_dir is None:
        raise RuntimeError("set_fonts_dir() must be called before font operations")
    return _fonts_dir / file_name


def _cache_path(name, axes, var_path=None):
    src = Path(var_path).stem if var_path else ""
    ak = "-".join(f"{k}{v}" for k, v in sorted(axes.items()))
    return _fonts_dir / "cache" / f"{name}-{src}-{ak}.ttf"


def ensure_font(name, var_path, axes):
    cache_key = (str(var_path), tuple(sorted(axes.items())) if axes else ())
    if _cache.get(name) == cache_key:
        return
    if not axes:
        pdfmetrics.registerFont(TTFont(name, str(var_path)))
        _cache[name] = cache_key
        return

    cached = _cache_path(name, axes, var_path)
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
    key = (str(var_path), tuple(sorted(axes.items())) if axes else ())
    if key in _cmap_cache:
        return _cmap_cache[key]
    from fontTools.ttLib import TTFont as FTFont

    cp = _cache_path(Path(var_path).stem, axes or {}, var_path)
    src = str(cp) if cp.exists() else str(var_path)
    vf = FTFont(src)
    if axes and not cp.exists():
        from fontTools.varLib.instancer import instantiateVariableFont
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


def register_fonts(cfg):
    fonts_cfg = cfg.get("fonts", {})
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
        "emoji": "Emoji",
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


def build_body_cmap(cfg):
    entry = cfg.get("fonts", {}).get("body", {})
    if not entry:
        return set()
    path = _resolve(entry["file"])
    axes = dict(entry.get("axes", {}))
    return get_cmap(path, axes)


def build_fallback_cmaps(cfg):
    """Build ordered fallback chain: [(rl_name, cmap), ...]."""
    fonts_cfg = cfg.get("fonts", {})
    chain = []
    for key, rl_name in [("cjk", "CJK"), ("emoji", "Emoji")]:
        entry = fonts_cfg.get(key)
        if not entry or "file" not in entry:
            continue
        path = _resolve(entry["file"])
        if not path.exists():
            continue
        axes = dict(entry.get("axes", {}))
        cmap = get_cmap(path, axes)
        chain.append((rl_name, cmap))
    return chain


def reset():
    """Clear all module state so fonts are re-registered from scratch.

    Also clears ReportLab's internal registries so that re-registering a font
    under the same name (e.g. "Body") with a different underlying file actually
    takes effect. Without this, registerTypeFace silently skips faces whose
    name already exists in _typefaces.
    """
    _cache.clear()
    _lazy.clear()
    _families.clear()
    pdfmetrics._fonts.clear()
    if hasattr(pdfmetrics, '_typefaces'):
        pdfmetrics._typefaces.clear()
    if hasattr(pdfmetrics, '_dynFaceNames'):
        pdfmetrics._dynFaceNames.clear()


def ensure_fonts_ready(cfg, manifest):
    """One-call font setup: download, register, and build cmaps.

    Returns (fonts_dir, body_cmap, fallback_chain).
    """
    from .font_manifest import ensure_fonts_downloaded, resolve_font_files
    reset()
    resolve_font_files(cfg, manifest)
    fonts_dir = ensure_fonts_downloaded(cfg, manifest)
    set_fonts_dir(fonts_dir)
    register_fonts(cfg)
    register_families()
    body_cmap = build_body_cmap(cfg)
    fallback_chain = build_fallback_cmaps(cfg)
    return fonts_dir, body_cmap, fallback_chain
