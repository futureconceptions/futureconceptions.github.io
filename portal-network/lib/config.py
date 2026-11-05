"""Laden und Prüfen der Netzwerk- und Portal-Konfiguration."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITES_DIR = ROOT / "sites"

SITE_TYPES = {"news", "review", "operator", "redirect"}

REQUIRED = {
    "news": ["domain", "name", "wordmark", "claim", "description", "accent", "ressorts"],
    "review": ["domain", "name", "wordmark", "claim", "description", "accent", "review"],
    "operator": ["domain", "name", "wordmark", "claim", "description", "accent"],
    "redirect": ["domain", "redirect_to"],
}

DEFAULTS = {
    "enabled": False,
    "phase": 1,
    "language": "de-DE",
    "glyph": "lines",
    "accent_dark": None,
    "adsense_client_id": "",
    "adsense_slots": {},
    "analytics": {"script_url": "", "website_id": "", "require_consent": True},
    "newsletter": {"name": "Newsletter", "description": "", "action": ""},
    "forms": {"contact_action": "", "review_action": "", "report_action": "", "claim_action": ""},
    "contact_email": "",
    "redirect_aliases": [],
    "region": "",
}


class ConfigError(Exception):
    pass


def load_json(path: pathlib.Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ConfigError(f"{path}: ungültiges JSON ({e})") from e


def load_network():
    return load_json(ROOT / "config" / "network.json")


def _merge(defaults, cfg):
    out = dict(defaults)
    for k, v in cfg.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            merged = dict(out[k])
            merged.update(v)
            out[k] = merged
        else:
            out[k] = v
    return out


def load_sites():
    """Alle sites/<domain>/site.json laden (auch deaktivierte)."""
    sites = []
    for path in sorted(SITES_DIR.glob("*/site.json")):
        raw = load_json(path)
        t = raw.get("type")
        if t not in SITE_TYPES:
            raise ConfigError(f"{path}: unbekannter type {t!r} (erlaubt: {sorted(SITE_TYPES)})")
        missing = [k for k in REQUIRED[t] if k not in raw]
        if missing:
            raise ConfigError(f"{path}: Pflichtfelder fehlen: {', '.join(missing)}")
        if raw["domain"] != path.parent.name:
            raise ConfigError(f"{path}: domain {raw['domain']!r} passt nicht zum Ordnernamen")
        cfg = _merge(DEFAULTS, raw)
        cfg["_dir"] = path.parent
        if cfg.get("accent_dark") is None:
            cfg["accent_dark"] = cfg.get("accent")
        sites.append(cfg)
    return sites
