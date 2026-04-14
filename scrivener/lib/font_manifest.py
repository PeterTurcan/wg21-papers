"""Font manifest loading, logical ID resolution, and on-demand downloading."""

import urllib.request

import yaml

from .config import FONTS_DIR, MANIFEST_PATH


def load_font_manifest():
    """Load fonts.yaml keyed by logical id."""
    if not MANIFEST_PATH.exists():
        return {}
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        entries = yaml.safe_load(f) or []
    return {e["id"]: {"file": e["file"], "url": e.get("url")}
            for e in entries if "id" in e and "file" in e}


def resolve_font_files(style, manifest):
    """Resolve font: logical ids to file: filenames in the style's fonts config."""
    fonts_cfg = style.get("fonts", {})
    for entry in fonts_cfg.values():
        if not isinstance(entry, dict):
            continue
        font_id = entry.get("font")
        if font_id and "file" not in entry:
            info = manifest.get(font_id)
            if not info:
                raise KeyError(f"unknown font id '{font_id}' (not in fonts.yaml)")
            entry["file"] = info["file"]


def ensure_fonts_downloaded(style, manifest):
    """Download missing fonts into the shared .fonts/ cache."""
    fonts_cfg = style.get("fonts", {})
    needed = {}
    for entry in fonts_cfg.values():
        if not isinstance(entry, dict):
            continue
        fname = entry.get("file")
        if fname and fname not in needed:
            font_id = None
            for mid, minfo in manifest.items():
                if minfo["file"] == fname:
                    font_id = mid
                    break
            url = (manifest.get(font_id, {}).get("url")
                   if font_id else None) or entry.get("url")
            needed[fname] = url
    if not needed:
        return FONTS_DIR
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    for fname, url in needed.items():
        dest = FONTS_DIR / fname
        if dest.exists():
            continue
        if not url:
            raise RuntimeError(f"font '{fname}' not found and no URL available")
        print(f"  fetch: {fname} ...", end=" ", flush=True)
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                dest.write_bytes(resp.read())
            size_mb = dest.stat().st_size / (1024 * 1024)
            print(f"ok ({size_mb:.1f}M)")
        except Exception:
            dest.unlink(missing_ok=True)
            raise
    return FONTS_DIR
