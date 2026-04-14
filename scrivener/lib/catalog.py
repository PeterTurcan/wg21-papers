"""Style catalog and image listing for the JSON API."""

import yaml

from .config import IMAGES_DIR, STYLES_DIR, load_style

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".svg", ".gif"}


def list_images():
    """List image files in the shared images/ directory."""
    if not IMAGES_DIR.is_dir():
        return []
    return sorted(f.name for f in IMAGES_DIR.iterdir()
                  if f.is_file() and f.suffix.lower() in IMAGE_EXTS)


def list_styles():
    """Scan styles/ for .yaml files and return JSON-serializable catalog."""
    images = list_images()
    result = []
    if not STYLES_DIR.is_dir():
        return result
    for f in sorted(STYLES_DIR.iterdir()):
        if not f.is_file() or f.suffix != ".yaml":
            continue
        with open(f, encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}

        base_name = raw.get("inherits")
        if base_name:
            merged = load_style(f)
        else:
            merged = raw

        style_id = f.stem
        entry = {
            "id": style_id,
            "name": merged.get("name", style_id),
            "description": merged.get("description", ""),
        }
        if base_name:
            entry["inherits"] = base_name

        options = []
        for opt in merged.get("options", []):
            o = {
                "id": opt.get("id"),
                "label": opt.get("label", opt.get("id", "")),
                "type": opt.get("type", "string"),
                "default": opt.get("default"),
            }
            if opt.get("choices"):
                o["choices"] = opt["choices"]
            options.append(o)
        if options:
            entry["options"] = options
        entry["images"] = images
        result.append(entry)
    return result
