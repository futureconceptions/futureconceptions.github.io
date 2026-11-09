"""Minimaler Front-Matter-Parser (YAML-Teilmenge, ohne Abhängigkeiten).

Unterstützt:
    key: wert                 # Zeichenkette (Anführungszeichen optional)
    key: true / false         # Wahrheitswert
    key: 42                   # Ganzzahl
    key: [a, b, "c d"]        # Inline-Liste
    key:                      # Block-Liste
      - eintrag
      - "eintrag mit: Doppelpunkt"
    # Kommentar
"""
import re


def _scalar(v: str):
    v = v.strip()
    if not v:
        return ""
    if v[0] == v[-1] and v[0] in "\"'" and len(v) >= 2:
        return v[1:-1]
    low = v.lower()
    if low in ("true", "yes", "ja"):
        return True
    if low in ("false", "no", "nein"):
        return False
    if low in ("null", "~"):
        return None
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        parts = re.findall(r'"[^"]*"|\'[^\']*\'|[^,]+', inner)
        return [_scalar(p) for p in parts if p.strip()]
    return v


def parse(text: str):
    """Gibt (metadaten: dict, body: str) zurück."""
    text = text.lstrip("﻿")
    if not text.startswith("---"):
        return {}, text
    m = re.match(r"---[ \t]*\n(.*?)\n---[ \t]*(?:\n|$)", text, re.S)
    if not m:
        raise ValueError("Front Matter nicht abgeschlossen (fehlendes '---').")
    meta, key = {}, None
    for raw in m.group(1).splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        stripped = raw.strip()
        if stripped.startswith("- ") or stripped == "-":
            if key is None or not isinstance(meta.get(key), list):
                raise ValueError(f"Listeneintrag ohne Schlüssel: {raw!r}")
            meta[key].append(_scalar(stripped[2:]))
            continue
        k, sep, v = raw.partition(":")
        if not sep:
            raise ValueError(f"Ungültige Front-Matter-Zeile: {raw!r}")
        key = k.strip()
        meta[key] = [] if not v.strip() else _scalar(v)
    return meta, text[m.end():]
