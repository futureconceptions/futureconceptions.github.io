#!/usr/bin/env python3
"""MERKANT Medien – baut alle aktivierten Portale als statische Websites.

    python3 portal-network/build.py                  # Live-Build → dist/<domain>/
    python3 portal-network/build.py --site itszene.de
    python3 portal-network/build.py --drafts         # Vorschau inkl. Entwürfe → dist-preview/ (noindex)
    python3 portal-network/build.py --test           # Testbuild mit fiktiven Testdaten → dist-test/ (noindex)
    python3 portal-network/build.py --deploy-configs # deploy/Caddyfile + cloudflared-Vorlage neu erzeugen

Nur Python-Standardbibliothek (läuft auf dem Raspberry Pi 5 mit Python ≥ 3.11).
"""
import argparse
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib.builder import SiteBuilder  # noqa: E402
from lib.config import ConfigError, load_network, load_sites  # noqa: E402
from lib.content import ContentError  # noqa: E402
from lib.deploy import write_deploy_configs  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", action="append", help="nur diese Domain(s) bauen")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--drafts", action="store_true", help="Vorschau inkl. Entwürfe nach dist-preview/")
    mode.add_argument("--test", action="store_true", help="Testbuild mit tests/fixtures nach dist-test/")
    ap.add_argument("--all", action="store_true", help="auch deaktivierte Portale bauen (nur Vorschau/Test)")
    ap.add_argument("--deploy-configs", action="store_true", help="Caddyfile + cloudflared-Vorlage erzeugen")
    ap.add_argument("--out", help="Ausgabeordner überschreiben")
    args = ap.parse_args(argv)

    try:
        network = load_network()
        sites = load_sites()
    except ConfigError as e:
        print(f"FEHLER (Konfiguration): {e}", file=sys.stderr)
        return 2

    if args.deploy_configs:
        write_deploy_configs(sites)
        print("deploy/Caddyfile und deploy/cloudflared/config.yml.example erzeugt.")

    m = "preview" if args.drafts else "test" if args.test else "live"
    out = pathlib.Path(args.out) if args.out else HERE / {"live": "dist", "preview": "dist-preview", "test": "dist-test"}[m]
    if args.all and m == "live":
        print("FEHLER: --all ist nur mit --drafts oder --test erlaubt.", file=sys.stderr)
        return 2
    targets = [s for s in sites if s["type"] != "redirect" and (s.get("enabled") or args.all)]
    if args.site:
        targets = [s for s in targets if s["domain"] in args.site]
        if not targets:
            print(f"FEHLER: keine aktivierte Site passt zu {args.site}", file=sys.stderr)
            return 2
    # Querverweise sollen nur auf tatsächlich gebaute Portale zeigen
    view = [dict(s, enabled=True) if (args.all and s["type"] != "redirect") else s for s in sites]

    t0 = time.time()
    placeholders = set()
    total = 0
    for cfg in targets:
        cfg = next(v for v in view if v["domain"] == cfg["domain"])
        try:
            b = SiteBuilder(cfg, network, view, out, m).build()
        except (ContentError, ConfigError) as e:
            print(f"FEHLER ({cfg['domain']}): {e}", file=sys.stderr)
            return 1
        n = len(list(b.out.rglob("*.html")))
        total += n
        drafts = b.draft_articles + b.draft_companies + b.draft_people
        pub = sum(1 for a in b.articles if a["status"] == "approved")
        print(f"✓ {cfg['domain']:<28} {n:>4} Seiten · {pub} freigegebene Beiträge · "
              f"{drafts} Entwürfe warten auf Freigabe")
        for w in b.warnings:
            print(f"  ! {w}")
        placeholders.update(b.placeholders_in_output())
    print(f"\n{total} HTML-Seiten in {time.time() - t0:.1f}s → {out}")
    if placeholders and m == "live":
        print(f"\n⚠ {len(placeholders)} offene [PLATZHALTER] in den Seiten (vor Livegang ausfüllen, "
              f"siehe config/network.json):")
        for p in sorted(placeholders):
            print(f"   {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
