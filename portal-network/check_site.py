#!/usr/bin/env python3
"""Prüft gebaute Portale: interne Links, Wohlgeformtheit, XML, JSON-LD, Pflichtdateien.

    python3 portal-network/check_site.py            # prüft dist/
    python3 portal-network/check_site.py dist-test  # prüft einen anderen Build-Ordner

Exit-Code 0 = alles in Ordnung, 1 = Fehler gefunden.
Links auf andere Portale des Netzwerks (https://<domain>/…) werden gegen den
jeweiligen Build-Ordner geprüft, sofern dieser gebaut wurde.
"""
import html.parser
import json
import pathlib
import sys
import urllib.parse
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
REQUIRED = ["index.html", "404.html", "robots.txt", "sitemap.xml", "ads.txt", "favicon.svg",
            "static/base.css", "static/site.js", "static/logo.svg"]


class PageParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.ids, self.errors, self.stack = [], set(), [], []
        self.jsonld, self._in_ld, self._buf = [], False, []
        self.h1 = 0
        self.title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            if a["id"] in self.ids:
                self.errors.append(f"doppelte id: {a['id']}")
            self.ids.add(a["id"])
        for key in ("href", "src", "action"):
            if a.get(key):
                self.links.append((tag, a[key]))
        if tag == "h1":
            self.h1 += 1
        if tag == "title":
            self.title = True
        if tag == "img" and "alt" not in a:
            self.errors.append("img ohne alt")
        if tag == "script" and a.get("type") == "application/ld+json":
            self._in_ld, self._buf = True, []
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID and self.stack and self.stack[-1][0] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag == "script" and self._in_ld:
            self._in_ld = False
            self.jsonld.append("".join(self._buf))
        if not self.stack:
            self.errors.append(f"schließendes </{tag}> ohne öffnendes Tag (Zeile {self.getpos()[0]})")
            return
        if self.stack[-1][0] == tag:
            self.stack.pop()
            return
        # implizit geschlossene Elemente (p, li) tolerieren, sonst Fehler
        names = [t for t, _ in self.stack]
        if tag in names:
            while self.stack and self.stack[-1][0] != tag:
                t, pos = self.stack.pop()
                if t not in ("p", "li", "option", "dt", "dd", "tr", "td", "th"):
                    self.errors.append(f"<{t}> (Zeile {pos[0]}) nicht geschlossen vor </{tag}>")
            self.stack.pop()
        else:
            self.errors.append(f"</{tag}> passt zu keinem offenen Tag (Zeile {self.getpos()[0]})")

    def handle_data(self, data):
        if self._in_ld:
            self._buf.append(data)


def resolve(root_dir, path):
    """Pfad einer Seite → Datei im Build-Ordner (oder None)."""
    p = urllib.parse.unquote(path.split("#")[0].split("?")[0])
    if not p or p == "/":
        p = "/index.html"
    target = root_dir / p.lstrip("/")
    if p.endswith("/"):
        target = target / "index.html"
    if target.is_file():
        return target
    if (target / "index.html").is_file():
        return target / "index.html"
    return None


def check_site(dist, domain_dir, known_domains):
    errors, pages, links_checked = [], 0, 0
    for f in REQUIRED:
        if not (domain_dir / f).is_file():
            errors.append(f"Pflichtdatei fehlt: {f}")
    for f in sorted(domain_dir.rglob("*.html")):
        pages += 1
        rel = "/" + str(f.relative_to(domain_dir))
        p = PageParser()
        p.feed(f.read_text(encoding="utf-8"))
        p.close()
        for e in p.errors:
            errors.append(f"{rel}: {e}")
        for t, pos in p.stack:
            if t not in ("html", "body", "head", "p", "li"):
                errors.append(f"{rel}: <{t}> (Zeile {pos[0]}) nie geschlossen")
        if p.h1 != 1:
            errors.append(f"{rel}: {p.h1} <h1>-Überschriften (erwartet: 1)")
        for raw in p.jsonld:
            try:
                json.loads(raw)
            except json.JSONDecodeError as e:
                errors.append(f"{rel}: ungültiges JSON-LD ({e})")
        for tag, url in p.links:
            if url.startswith(("mailto:", "tel:", "data:", "javascript:")):
                continue
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme in ("http", "https"):
                if parsed.netloc in known_domains:
                    target_dir = dist / parsed.netloc
                    if not target_dir.is_dir():
                        errors.append(f"{rel}: Link auf nicht gebautes Portal {url}")
                        continue
                    links_checked += 1
                    if not resolve(target_dir, parsed.path or "/"):
                        errors.append(f"{rel}: toter Link {url}")
                continue  # externe Links werden nicht geprüft
            links_checked += 1
            if url.startswith("#"):
                if url[1:] and url[1:] not in p.ids:
                    errors.append(f"{rel}: Anker {url} fehlt")
                continue
            path = url if url.startswith("/") else urllib.parse.urljoin(rel, url)
            target = resolve(domain_dir, path)
            if not target:
                errors.append(f"{rel}: toter Link {url}")
            elif "#" in url and target.suffix == ".html":
                frag = url.split("#", 1)[1]
                tp = PageParser()
                tp.feed(target.read_text(encoding="utf-8"))
                if frag and frag not in tp.ids:
                    errors.append(f"{rel}: Anker #{frag} fehlt in {path.split('#')[0]}")
    # XML-Dateien
    for name in ("sitemap.xml", "news-sitemap.xml", "feed.xml"):
        x = domain_dir / name
        if x.is_file():
            try:
                ET.parse(x)
            except ET.ParseError as e:
                errors.append(f"/{name}: kein gültiges XML ({e})")
    si = domain_dir / "search-index.json"
    if si.is_file():
        try:
            for entry in json.loads(si.read_text(encoding="utf-8")):
                if not resolve(domain_dir, entry["url"]):
                    errors.append(f"search-index.json: toter Eintrag {entry['url']}")
        except (json.JSONDecodeError, KeyError) as e:
            errors.append(f"search-index.json ungültig ({e})")
    return pages, links_checked, errors


def main():
    dist = HERE / (sys.argv[1] if len(sys.argv) > 1 else "dist")
    if not dist.is_dir():
        print(f"{dist} existiert nicht – zuerst bauen.", file=sys.stderr)
        return 1
    known = set()
    for cfg in (HERE / "sites").glob("*/site.json"):
        d = json.loads(cfg.read_text(encoding="utf-8"))["domain"]
        known.update({d, f"www.{d}"})
    total_err = 0
    for domain_dir in sorted(p for p in dist.iterdir() if p.is_dir()):
        pages, links, errors = check_site(dist, domain_dir, known)
        status = "OK " if not errors else "FEHLER"
        print(f"{status} {domain_dir.name:<28} {pages:>4} Seiten · {links:>5} interne Links geprüft · {len(errors)} Fehler")
        for e in errors[:50]:
            print(f"      - {e}")
        total_err += len(errors)
    print(f"\nGesamt: {total_err} Fehler")
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main())
