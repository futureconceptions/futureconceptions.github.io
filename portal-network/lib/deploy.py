"""Erzeugt deploy/Caddyfile und deploy/cloudflared/config.yml.example aus den site.json-Dateien."""
from .config import ROOT

HEADER = """# ------------------------------------------------------------------
# AUTOMATISCH ERZEUGT von `python3 portal-network/build.py --deploy-configs`
# Quelle: portal-network/sites/*/site.json – Änderungen bitte dort vornehmen.
# ------------------------------------------------------------------
"""


def _hosts(*domains):
    return ", ".join(f"http://{d}" for d in domains)


def caddyfile(sites):
    out = [HEADER, """{
\t# TLS terminiert Cloudflare; der Tunnel spricht intern HTTP mit Caddy.
\tauto_https off
\tadmin off
}

(static_site) {
\tencode zstd gzip
\theader {
\t\tX-Content-Type-Options "nosniff"
\t\tReferrer-Policy "strict-origin-when-cross-origin"
\t\tX-Frame-Options "SAMEORIGIN"
\t\tPermissions-Policy "camera=(), microphone=(), geolocation=(), interest-cohort=()"
\t\tStrict-Transport-Security "max-age=31536000"
\t\t-Server
\t}
\t@assets path /static/* /favicon.svg
\theader @assets Cache-Control "public, max-age=2592000"
\t@html path *.html */
\theader @html Cache-Control "public, max-age=300, s-maxage=600"
\t@feeds path /sitemap.xml /news-sitemap.xml /feed.xml /robots.txt /ads.txt /search-index.json
\theader @feeds Cache-Control "public, max-age=300"
\tfile_server
\thandle_errors {
\t\t@404 expression {err.status_code} == 404
\t\thandle @404 {
\t\t\trewrite * /404.html
\t\t\tfile_server
\t\t}
\t}
}

# Healthcheck für Uptime-Monitoring (z. B. Uptime Kuma): http://<pi>:8080/healthz
:8080 {
\trespond /healthz "ok" 200
}
"""]
    for s in sites:
        d = s["domain"]
        if s["type"] == "redirect":
            if not s.get("enabled"):
                continue
            target = s["redirect_to"].rstrip("/")
            hosts = [d, f"www.{d}"] + list(s.get("redirect_aliases", []))
            out.append(f"# {s.get('name', d)} – Weiterleitung (301)\n{_hosts(*hosts)} {{\n"
                       f"\tredir {target}{{uri}} 301\n}}\n")
            continue
        if not s.get("enabled"):
            out.append(f"# {d}: deaktiviert (enabled: false in sites/{d}/site.json)\n")
            continue
        out.append(f"# {s['name']}\nhttp://{d} {{\n\troot * /srv/sites/{d}\n\timport static_site\n}}\n")
        aliases = [f"www.{d}"] + list(s.get("redirect_aliases", []))
        out.append(f"{_hosts(*aliases)} {{\n\tredir https://{d}{{uri}} 301\n}}\n")
    return "\n".join(out)


def cloudflared(sites):
    lines = [
        "# cloudflared – lokal verwaltete Tunnel-Konfiguration (Vorlage)",
        "# 1) cloudflared tunnel login",
        "# 2) cloudflared tunnel create merkant-pi   → erzeugt <TUNNEL-ID>.json",
        "# 3) Datei nach deploy/cloudflared/<TUNNEL-ID>.json kopieren, diese Vorlage als config.yml speichern",
        "# 4) DNS je Hostname: cloudflared tunnel route dns merkant-pi <hostname>",
        "# AUTOMATISCH ERZEUGT von build.py --deploy-configs (Quelle: sites/*/site.json)",
        "",
        "tunnel: PLATZHALTER_TUNNEL_ID",
        "credentials-file: /etc/cloudflared/PLATZHALTER_TUNNEL_ID.json",
        "",
        "ingress:",
    ]
    for s in sites:
        if not s.get("enabled"):
            continue
        d = s["domain"]
        for h in [d, f"www.{d}"] + list(s.get("redirect_aliases", [])):
            lines.append(f"  - hostname: {h}")
            lines.append("    service: http://caddy:80")
    lines += ["  # alles andere ablehnen", "  - service: http_status:404", ""]
    return "\n".join(lines)


def write_deploy_configs(sites):
    (ROOT / "deploy" / "Caddyfile").write_text(caddyfile(sites), encoding="utf-8")
    cf = ROOT / "deploy" / "cloudflared"
    cf.mkdir(parents=True, exist_ok=True)
    (cf / "config.yml.example").write_text(cloudflared(sites), encoding="utf-8")
