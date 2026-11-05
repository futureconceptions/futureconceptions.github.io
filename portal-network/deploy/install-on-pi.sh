#!/usr/bin/env bash
# Richtet die MERKANT-Portale auf dem Pi ein – neben den bestehenden Seiten, ohne sie zu verändern.
# Aufruf (im Repo):  bash portal-network/deploy/install-on-pi.sh
# Optional: TUNNEL_NETWORK=<netz> bash ...   bzw.  CLOUDFLARED_CONTAINER=<name> bash ...
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORTAL_DIR="$(dirname "$DEPLOY_DIR")"

echo "== 1/5 Voraussetzungen prüfen"
command -v docker >/dev/null || { echo "Docker fehlt."; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "docker compose (v2) fehlt."; exit 1; }
command -v python3 >/dev/null || { echo "python3 fehlt."; exit 1; }

if docker ps -a --format '{{.Names}}' | grep -qx merkant-caddy; then
  echo "Hinweis: Container merkant-caddy existiert bereits – er wird aktualisiert."
fi

echo "== 2/5 Bestehenden cloudflared-Container finden"
CF="${CLOUDFLARED_CONTAINER:-}"
if [ -z "$CF" ]; then
  CF="$(docker ps --format '{{.Names}} {{.Image}}' | awk '$2 ~ /cloudflared/ {print $1; exit}')"
fi
if [ -z "$CF" ]; then
  echo "Kein laufender cloudflared-Container gefunden. Name angeben: CLOUDFLARED_CONTAINER=<name> bash $0"
  exit 1
fi
echo "   cloudflared-Container: $CF"

NET="${TUNNEL_NETWORK:-}"
if [ -z "$NET" ]; then
  NETS="$(docker inspect "$CF" --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}')"
  # Netz bevorzugen, in dem auch die bestehenden Seiten-Container hängen (nicht 'bridge'/'host')
  for n in $NETS; do
    case "$n" in bridge|host|none) continue;; esac
    NET="$n"; break
  done
  [ -z "$NET" ] && NET="$(echo "$NETS" | awk '{print $1}')"
fi
if [ "$NET" = "host" ]; then
  echo "cloudflared läuft im Host-Netz. Dann im Cloudflare-Tunnel http://merkant-caddy:80 durch http://127.0.0.1:18080 ersetzen"
  echo "und in docker-compose.yml die ports-Zeile 127.0.0.1:18080:80 aktivieren. Abbruch, damit nichts Falsches gestartet wird."
  exit 1
fi
echo "   Docker-Netz: $NET"
echo "   Container in diesem Netz:"; docker network inspect "$NET" --format '{{range .Containers}}     - {{.Name}}{{"\n"}}{{end}}'

echo "== 3/5 Seiten bauen"
python3 "$PORTAL_DIR/build.py"
python3 "$PORTAL_DIR/check_site.py" | tail -1

echo "== 4/5 Caddy starten (nur neuer Container merkant-caddy, keine Host-Ports)"
cd "$DEPLOY_DIR"
if [ ! -f .env ]; then cp .env.example .env; fi
if grep -q '^TUNNEL_NETWORK=' .env; then
  sed -i "s|^TUNNEL_NETWORK=.*|TUNNEL_NETWORK=$NET|" .env
else
  echo "TUNNEL_NETWORK=$NET" >> .env
fi
docker compose pull -q
docker compose up -d

echo "== 5/5 Test über das Tunnel-Netz"
sleep 3
for h in firmennachrichten.de itszene.de it-erfahrungen.de merkant-medien.de firmenkoepfe.de; do
  code="$(docker run --rm --network "$NET" curlimages/curl:8.10.1 -s -o /dev/null -w '%{http_code}' -H "Host: $h" http://merkant-caddy:80/ || echo ERR)"
  echo "   $h -> HTTP $code"
done
echo
echo "Fertig. Öffentlich prüfen: https://firmennachrichten.de  (Cloudflare-Routing ist bereits eingerichtet)."
echo "Aktualisieren nach neuen Inhalten:  python3 $PORTAL_DIR/build.py   (Caddy liefert sofort die neuen Dateien aus)"
