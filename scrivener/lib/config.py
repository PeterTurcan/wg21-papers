"""Style loading, configuration merge, and proportional spacing."""

import copy
import re
from pathlib import Path

import yaml
from reportlab.lib.pagesizes import (
    A3, A4, A5, A6,
    B4, B5,
    HALF_LETTER, JUNIOR_LEGAL, LEDGER, LEGAL, LETTER, TABLOID,
    GOV_LEGAL, GOV_LETTER,
    legal, letter,
)
from reportlab.lib.units import mm

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STYLES_DIR = PROJECT_ROOT / "styles"
IMAGES_DIR = PROJECT_ROOT / "images"
FONTS_DIR = PROJECT_ROOT / ".fonts"
MANIFEST_PATH = PROJECT_ROOT / "fonts.yaml"

_in = 72
_mm20 = 20 * mm
_mm15 = 15 * mm
_mm10 = 10 * mm

PAGE_CONFIGS = {
    "letter":       {"size": letter,        "margin": _in},
    "legal":        {"size": legal,         "margin": _in},
    "half-letter":  {"size": HALF_LETTER,   "margin": 54},
    "junior-legal": {"size": JUNIOR_LEGAL,  "margin": 54},
    "tabloid":      {"size": TABLOID,       "margin": _in},
    "ledger":       {"size": LEDGER,        "margin": _in},
    "gov-letter":   {"size": GOV_LETTER,    "margin": _in},
    "gov-legal":    {"size": GOV_LEGAL,     "margin": _in},
    "a3":           {"size": A3,            "margin": _mm20},
    "a4":           {"size": A4,            "margin": _mm20},
    "a5":           {"size": A5,            "margin": _mm15},
    "a6":           {"size": A6,            "margin": _mm10},
    "b4":           {"size": B4,            "margin": _mm20},
    "b5":           {"size": B5,            "margin": _mm15},
}


def sp(cfg, r):
    """Spacing proportional to body_size."""
    return cfg.get("body_size", 11) * r


def deep_merge(base, override):
    """Recursively merge override into base. Dicts merge; scalars/lists replace."""
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def resolve_style_path(style_arg):
    """Resolve a --style argument to a .yaml file path."""
    if style_arg is None:
        return STYLES_DIR / "default.yaml"
    p = Path(style_arg)
    if p.is_file():
        return p
    candidate = STYLES_DIR / f"{style_arg}.yaml"
    if candidate.is_file():
        return candidate
    candidate = STYLES_DIR / style_arg
    if candidate.is_file():
        return candidate
    raise FileNotFoundError(f"style not found: {style_arg}")


def load_style(style_path, _loading=None):
    """Load a style YAML file with inheritance support."""
    style_path = Path(style_path)

    if _loading is None:
        _loading = set()
    key = str(style_path.resolve())
    if key in _loading:
        raise ValueError(f"circular style inheritance involving {style_path.stem}")
    _loading.add(key)

    with open(style_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    base_name = raw.pop("inherits", None)
    if base_name:
        base_path = STYLES_DIR / f"{base_name}.yaml"
        if not base_path.exists():
            raise FileNotFoundError(f"base style '{base_name}' not found")
        base = load_style(base_path, _loading)
        style = deep_merge(base, raw)
    else:
        style = raw

    resolve_palette(style)
    return style


def apply_options(style, options_dict):
    """Apply user option overrides to the style config."""
    schema = style.get("options", [])
    valid_ids = {opt["id"] for opt in schema}
    for key, value in options_dict.items():
        if key not in valid_ids:
            valid = ", ".join(sorted(valid_ids)) if valid_ids else "(none)"
            raise ValueError(f"unknown option '{key}'. valid options: {valid}")
        style[key] = value


def resolve_palette(style):
    """Resolve @name color references using style.palette. Mutates style in place."""
    palette = style.get("palette", {})
    if not palette:
        return
    def resolve(obj):
        if isinstance(obj, str) and obj.startswith("@"):
            key = obj[1:]
            if key in palette:
                return palette[key]
        return obj
    def walk(obj):
        if isinstance(obj, dict):
            return {k: walk(resolve(v)) for k, v in obj.items()}
        if isinstance(obj, list):
            return [walk(resolve(v)) for v in obj]
        return obj
    resolved = walk(style)
    style.clear()
    style.update(resolved)


def extract_front_matter(md_text):
    """Split YAML front matter from body text."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", md_text, re.DOTALL)
    if not m:
        return {}, md_text
    fm = yaml.safe_load(m.group(1)) or {}
    body = md_text[m.end():]
    return fm, body


_FM_STYLE_KEYS = {"logo", "toc", "accent_saturated", "accent_mid"}


def merge_config(cli_cfg, front_matter, style):
    """Merge CLI overrides, front matter, and style into a single config dict."""
    cfg = copy.deepcopy(style)
    for k, v in front_matter.items():
        if k in _FM_STYLE_KEYS and v is not None:
            cfg[k] = v
    if cli_cfg.get("logo"):
        cfg["logo"] = cli_cfg["logo"]
    if cli_cfg.get("toc") is True:
        cfg["toc"] = True
    if cli_cfg.get("no_toc") is True:
        cfg["toc"] = False
    return cfg


