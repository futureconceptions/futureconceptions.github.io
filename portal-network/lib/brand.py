"""SVG-Wortmarken und Favicons – vollständig im Code erzeugt.

Text-basierte Wortmarken in Systemschrift mit einem einfachen geometrischen
Zeichen. Bewusst schlicht und ohne Anlehnung an fremde Marken.
"""
from .util import esc

FONT = "system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"

# Geometrische Zeichen auf einer 32×32-Fläche (weiß auf Akzentfarbe)
GLYPHS = {
    # Nachrichten: drei Zeilen einer Spalte
    "lines": '<rect x="8" y="9" width="16" height="3" rx="1.5"/><rect x="8" y="15" width="16" height="3" rx="1.5"/><rect x="8" y="21" width="10" height="3" rx="1.5"/>',
    # IT: Eingabeaufforderung >_
    "prompt": '<path d="M8 10l7 6-7 6" fill="none" stroke="#fff" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/><rect x="17" y="20.5" width="8" height="3" rx="1.5"/>',
    # Bewertungen: Stern
    "star": '<path d="M16 6.5l2.9 5.9 6.5.9-4.7 4.6 1.1 6.5L16 21.3l-5.8 3.1 1.1-6.5-4.7-4.6 6.5-.9z"/>',
    # Netzwerk/Betreiber: verbundene Knoten
    "nodes": '<g fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round"><path d="M10 22L16 10l6 12"/><path d="M10 22h12"/></g><circle cx="16" cy="10" r="3"/><circle cx="10" cy="22" r="3"/><circle cx="22" cy="22" r="3"/>',
    # Köpfe/Personen: stilisierte Silhouette
    "person": '<circle cx="16" cy="12" r="4.5"/><path d="M8 25c.8-4.6 4-7 8-7s7.2 2.4 8 7z"/>',
    # Agentur: Kreis + Quadrat
    "shapes": '<circle cx="12.5" cy="13" r="5"/><rect x="15" y="15" width="10" height="10" rx="2"/>',
    # Systemhaus: Server-Einschübe
    "server": '<rect x="8" y="8" width="16" height="6" rx="1.5"/><rect x="8" y="18" width="16" height="6" rx="1.5"/><circle cx="21" cy="11" r="1.2" fill="#000" fill-opacity=".35"/><circle cx="21" cy="21" r="1.2" fill="#000" fill-opacity=".35"/>',
}

# grobe Zeichenbreiten (Anteil der Schriftgröße) für Versalien
_W_BOLD, _W_REG = 0.70, 0.64


def _mark(glyph: str, accent: str, x: float = 0, y: float = 0, size: float = 32) -> str:
    s = size / 32
    return (f'<g transform="translate({x} {y}) scale({s:.4f})">'
            f'<rect width="32" height="32" rx="7" fill="{accent}"/>'
            f'<g fill="#fff">{GLYPHS.get(glyph, GLYPHS["lines"])}</g></g>')


def wordmark(parts, accent: str, glyph: str, title: str, text_color: str = "currentColor",
             height: int = 40, idattr: str = "") -> str:
    """parts: [[Text, 'bold'|'regular'], …] → SVG-Zeichenkette.

    Der zweite Teil wird in der Akzentfarbe gesetzt. textLength fixiert die
    Breite, damit die Marke unabhängig von der Systemschrift gleich groß bleibt.
    """
    fs = 22
    widths = [len(t) * fs * (_W_BOLD if w == "bold" else _W_REG) for t, w in parts]
    gap = 4
    text_w = sum(widths) + gap * (len(parts) - 1)
    total_w = 32 + 10 + text_w
    spans, x = [], 42.0
    for (t, w), tw in zip(parts, widths):
        weight = 800 if w == "bold" else 500
        color = text_color if w == "bold" else accent
        spans.append(f'<text x="{x:.1f}" y="24" font-family="{FONT}" font-size="{fs}" '
                     f'font-weight="{weight}" letter-spacing=".5" fill="{color}" '
                     f'textLength="{tw:.1f}" lengthAdjust="spacingAndGlyphs">{esc(t)}</text>')
        x += tw + gap
    w_px = round(total_w * height / 32)
    ida = f' id="{idattr}"' if idattr else ""
    return (f'<svg{ida} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w:.0f} 32" '
            f'width="{w_px}" height="{height}" role="img" aria-label="{esc(title)}">'
            f'<title>{esc(title)}</title>{_mark(glyph, accent)}{"".join(spans)}</svg>')


def favicon(accent: str, glyph: str) -> str:
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
            f'{_mark(glyph, accent)}</svg>')
