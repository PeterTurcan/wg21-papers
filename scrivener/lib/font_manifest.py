"""Font manifest loading, logical ID resolution, and on-demand downloading."""

import logging
import urllib.error
import urllib.request

import yaml

from .config import FONTS_DIR, MANIFEST_PATH

log = logging.getLogger(__name__)


def load_font_manifest():
    """Load fonts.yaml keyed by logical id."""
    if not MANIFEST_PATH.exists():
        return {}
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        entries = yaml.safe_load(f) or []
    return {e["id"]: {"file": e["file"], "url": e.get("url")}
            for e in entries if "id" in e and "file" in e}


def _iter_font_entries(cfg):
    """Yield dict-typed font entries from the fonts config."""
    for entry in cfg.get("fonts", {}).values():
        if isinstance(entry, dict):
            yield entry


def resolve_font_files(cfg, manifest):
    """Resolve font: logical ids to file: filenames in the fonts config. Mutates cfg in place."""
    for entry in _iter_font_entries(cfg):
        font_id = entry.get("font")
        if font_id and "file" not in entry:
            info = manifest.get(font_id)
            if not info:
                raise KeyError(f"unknown font id '{font_id}' (not in fonts.yaml)")
            entry["file"] = info["file"]


def ensure_fonts_downloaded(cfg, manifest):
    """Download missing fonts into the shared .fonts/ cache."""
    file_to_id = {v["file"]: k for k, v in manifest.items()}
    needed = {}
    for entry in _iter_font_entries(cfg):
        fname = entry.get("file")
        if fname and fname not in needed:
            font_id = file_to_id.get(fname)
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
        log.info("fetch: %s", fname)
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                dest.write_bytes(resp.read())
            size_mb = dest.stat().st_size / (1024 * 1024)
            log.info("ok (%s) %.1fM", fname, size_mb)
        except (urllib.error.URLError, OSError):
            dest.unlink(missing_ok=True)
            raise
    return FONTS_DIR
