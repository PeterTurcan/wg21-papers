"""Per-user configuration, persisted to ~/.paperworks/config.json."""

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".paperworks"
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULTS = {
    "watch_dirs": [],
    "output_dir": "",
    "render_output_dir": "",
    "style": "wg21",
    "render_style": "wg21",
    "port": 7780,
    "isocpp_username": "",
    "isocpp_password": "",
}

SCRIVENER_CONFIG = Path.home() / ".scrivener" / "config.json"


def _normalize_dir(entry):
    if isinstance(entry, str):
        return {"path": entry, "recursive": False, "enabled": True}
    return {
        "path": entry.get("path", ""),
        "recursive": bool(entry.get("recursive", False)),
        "enabled": bool(entry.get("enabled", True)),
    }


def _read_scrivener_config():
    """Read scrivener's config for fallback values."""
    if not SCRIVENER_CONFIG.exists():
        return {}
    try:
        with open(SCRIVENER_CONFIG, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_config():
    if not CONFIG_PATH.exists():
        cfg = dict(DEFAULTS)
    else:
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            cfg = dict(DEFAULTS)
        else:
            cfg = dict(DEFAULTS)
            cfg.update({k: v for k, v in data.items() if k in DEFAULTS})

    cfg["watch_dirs"] = [_normalize_dir(d) for d in cfg.get("watch_dirs", [])]

    scrivener = _read_scrivener_config()
    if not cfg.get("output_dir"):
        cfg["output_dir"] = scrivener.get("output_dir", "")
    if not cfg.get("watch_dirs"):
        scr_dirs = scrivener.get("watch_dirs", [])
        cfg["watch_dirs"] = [_normalize_dir(d) for d in scr_dirs]
    if not cfg.get("style") or cfg["style"] == DEFAULTS["style"]:
        cfg["style"] = scrivener.get("style", "wg21")

    return cfg


def save_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
