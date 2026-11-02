# MERKANT Medien – Portalnetzwerk (statische Websites)

Startfertige, statische Websites für das Portalnetzwerk aus `docs/gesamtkonzept-portalnetzwerk.md`:

| Portal | Typ | Status |
|---|---|---|
| **firmennachrichten.de** | Nachrichtenportal (Ressorts nach Konzept 4.2, Startregion NRW, `/koepfe/`) | aktiv (Phase 1) |
| **itszene.de** | Nachrichtenportal IT im Mittelstand (Konzept 4.5) | aktiv (Phase 1) |
| **it-erfahrungen.de** | Bewertungsportal IT-Dienstleister (Konzept 5) | aktiv (Phase 1) |
| **merkant-medien.de** | Betreiber-/Netzwerkseite | aktiv (Phase 0) |
| **firmenkoepfe.de** | nur 301-Weiterleitung → `https://firmennachrichten.de/koepfe/` (Caddy) | aktiv (Phase 1) |
| systemhauserfahrungen.de, agenturerfahrungen.de | Bewertungsportale | `enabled: false` (Phase 2) |
| unternehmenserfahrungen.de | Bewertungsportal | `enabled: false` (Phase 3) |

Der Builder ist ein schlanker **Python-Generator ohne Abhängigkeiten** (nur Standardbibliothek, Python ≥ 3.11). Er läuft unverändert auf dem Raspberry Pi 5. Es gibt keine externen Schriften, kein externes JavaScript und keine Tracker. Google-Skripte werden erst geladen, wenn eine AdSense-ID eingetragen ist.

---

## Struktur

```
portal-network/
├── build.py                 # baut alle aktivierten Portale → dist/<domain>/
├── preview.py               # lokale Vorschau eines Portals (http://localhost:8000)
├── check_site.py            # Linkprüfung, HTML-Wohlgeformtheit, XML/JSON-LD-Prüfung
├── config/network.json      # Betreiber, Impressumsangaben ([PLATZHALTER]), KI-Hinweis, Pakete
├── sites/<domain>/
│   ├── site.json            # EIN Portal = EINE Konfigurationsdatei (Name, Farben, Ressorts, AdSense …)
│   ├── content/articles/    # Beiträge als Markdown mit Front Matter (status: draft|approved)
│   ├── content/companies/   # Firmenprofile (JSON, inkl. Bewertungen beim Bewertungsportal)
│   ├── content/people/      # Personenseiten (JSON, nur berufliche Rolle)
│   └── static/img/          # Bilder (siehe IMAGE_PROMPTS.md) – optional
├── legal/*.md               # Rechts- und Vertrauensseiten (Vorlagen mit ${Variablen} und Bedingungen)
├── templates/base.html      # Seitenrahmen
├── static/                  # gemeinsames CSS (hell/dunkel) und kleines JS (Suche, Consent-Gate)
├── lib/                     # Builder-Code (Markdown, Front Matter, SVG-Logos, SEO, Deploy-Configs)
├── deploy/                  # docker-compose.yml, Caddyfile, cloudflared-Vorlage, .env.example
├── tests/fixtures/          # FIKTIVE Testdaten, nur für build.py --test
├── IMAGE_PROMPTS.md         # alle benötigten Bilder mit fertigen letz.ai-Prompts
└── dist/                    # Build-Ausgabe (nicht im Git)
```

## Bauen, prüfen, ansehen

```bash
python3 portal-network/build.py                 # Live-Build aller aktivierten Portale → dist/
python3 portal-network/build.py --site itszene.de
python3 portal-network/check_site.py            # Links, HTML, Sitemaps, RSS, JSON-LD prüfen
python3 portal-network/preview.py firmennachrichten.de   # → http://127.0.0.1:8000/

python3 portal-network/build.py --drafts        # Vorschau INKL. Entwürfe → dist-preview/ (noindex, rotes Banner)
python3 portal-network/preview.py itszene.de --drafts

python3 portal-network/build.py --test          # Testbuild mit fiktiven Testdaten → dist-test/ (noindex)
python3 portal-network/check_site.py dist-test

python3 portal-network/build.py --deploy-configs   # deploy/Caddyfile + cloudflared-Vorlage neu erzeugen
```

Der Build gibt am Ende alle noch offenen `[PLATZHALTER]` aus.

Je Portal entstehen: Startseite, Ressort- bzw. Kategorieseiten, Artikelseiten, Firmen- und Personenseiten, Suche (`/suche/`, clientseitig über `/search-index.json`), `404.html`, alle Rechtsseiten, `robots.txt`, `sitemap.xml`, `news-sitemap.xml` (Nachrichtenportale, Beiträge der letzten 48 h), `feed.xml` (RSS), `ads.txt`, `favicon.svg` und `static/logo.svg` (SVG-Wortmarke, im Code erzeugt).

## Freigabe-Status (Grundlage für die Telegram-Freigabe)

Jede Inhaltsdatei hat einen `status`:

- `status: draft` → **wird nie live veröffentlicht.** Entwürfe sind die Eingabe für den späteren Telegram-Freigabe-Workflow (Konzept 7.2/8.4).
- `status: approved` → wird gerendert. Ein Datum in der Zukunft (`date:`) verschiebt die Veröffentlichung, bis es erreicht ist.
- Alles andere (`queued`, `rejected` …) wird ignoriert.

Das gilt auch für einzelne Bewertungen und KI-Zusammenfassungen in Firmenprofilen.

**Freigeben heute (manuell):** In der Datei `status: draft` → `status: approved` ändern, Datum setzen, prüfen, `build.py` ausführen. Der spätere Telegram-Bot macht genau das automatisch nach deinem Klick. Vorher kannst du mit `build.py --drafts` eine Vorschau erzeugen, z. B. für `preview.firmennachrichten.de` hinter Cloudflare Access.

Beispiel-Front-Matter eines Beitrags:

```yaml
---
title: Neuer Geschäftsführer bei …
status: draft                 # draft | approved
ressort: koepfe               # muss in site.json definiert sein
kind: news                    # news (URL /ressort/JJJJ/MM/slug/) | ratgeber (URL /ressort/slug/)
region: NRW
teaser: …
author: Redaktion FIRMENNACHRICHTEN
date: 2026-11-03T06:30:00+01:00
updated: 2026-11-03T09:00:00+01:00
image: /static/img/artikel/beispiel.webp   # optional; sonst Ressortbild bzw. Farbverlauf
image_alt: …
companies: [firmen-slug]      # verlinkt /unternehmen/<slug>/
people: [personen-slug]       # verlinkt /koepfe/<slug>/
sources:
  - "Handelsregister HRB 12345, AG Köln, Bekanntmachung 30.10.2026 | https://www.handelsregister.de/"
corrections:
  - "05.11.2026: Funktion korrigiert."
needs_fact_check: true        # zeitkritische Fakten (Gesetze, Fristen) vor Freigabe prüfen
sources_to_verify:
  - …
---
Text in Markdown (## Zwischenüberschriften, Listen, Tabellen, **fett**, [Links](https://…)).
```

### Mitgelieferte Entwürfe

**Es sind bewusst keine Nachrichten, keine Firmenprofile und keine Bewertungen enthalten** (keine erfundenen Inhalte über echte Unternehmen oder Personen, keine Fake-Bewertungen). Die Portale zeigen saubere Leerzustände („Noch keine Bewertungen – Profil beanspruchen“).

Enthalten sind **22 Ratgeber-Entwürfe** (`status: draft`), je ca. 600–800 Wörter, sachlich, ohne erfundene Statistiken oder Zitate:

- firmennachrichten.de (8): Unternehmensnachfolge, Rechtsformen, Handelsregister, Insolvenzverfahren-Stadien, GmbH-Gründung, Geschäftsführerwechsel, Jahresabschluss/Offenlegung, Prokura/Handlungsvollmacht
- itszene.de (8): NIS2 für KMU, E-Rechnungspflicht, Backup 3-2-1, Managed Services, Cloud vs. On-Premise, MFA, IT-Notfallplan, Phishing
- it-erfahrungen.de (6): IT-Dienstleister finden, Was ist ein Systemhaus, Checkliste Vertrag/SLA, Kosten Managed Services, Warnsignale, 20 Fragen fürs Erstgespräch

Beiträge mit Gesetzen, Fristen oder Schwellenwerten tragen `needs_fact_check: true` und eine Liste `sources_to_verify`. **Diese Punkte vor der Freigabe prüfen.**

## Ein Portal hinzufügen (z. B. Phase 2)

1. In `sites/<domain>/site.json` `"enabled": true` setzen. Für ein neues Portal den Ordner `sites/<domain>/` mit `site.json` anlegen; Vorlage ist ein bestehendes Portal gleichen Typs (`news`, `review`, `operator`, `redirect`).
2. Optional `content/` und `static/img/` anlegen.
3. `python3 portal-network/build.py --deploy-configs` (Caddyfile und cloudflared-Vorlage werden aktualisiert) und `python3 portal-network/check_site.py`.

Weitere Software ist nicht nötig. Querverweise („Schwesterportale“), Netzwerkseite, „Über uns“ und Impressum übernehmen das neue Portal automatisch.

`firmenkoepfe.de` als eigenes Portal (Phase 2): `type` von `redirect` auf `news` umstellen und Ressorts eintragen.

## AdSense, Consent und Analytics

In `sites/<domain>/site.json`:

```json
"adsense_client_id": "",                      // z. B. "ca-pub-1234567890123456" – erst nach Freigabe
"adsense_slots": {"article_top": "", …},      // Anzeigenblock-IDs aus AdSense
"analytics": {"script_url": "", "website_id": "", "require_consent": true},
"google_site_verification": ""                // Search Console (Meta-Tag-Methode)
```

- **ID leer (Standard):** Es wird kein Google-Skript geladen. Anzeigenflächen sind unsichtbare Platzhalter mit fester Höhe, damit das Layout später nicht springt. `ads.txt` enthält die Platzhalterzeile.
- **ID gesetzt:** Das AdSense-Skript steht im `<head>`, `ads.txt` enthält die echte Publisher-ID, und im Fuß erscheint „Datenschutzeinstellungen“. Sind zusätzlich Slot-IDs eingetragen, werden Anzeigen mit der Kennzeichnung „Anzeige“ ausgespielt. Die Einwilligung holt **Googles eigene CMP** (AdSense → Datenschutz und Mitteilungen → Europäische Bestimmungen, TCF 2.2). Sie muss dort aktiviert werden.
- **Analytics** (z. B. Umami, selbst gehostet) lädt erst, wenn die TCF-CMP die Einwilligung für Zweck 1 und 8 meldet. Ohne CMP findet keine Messung statt.
- Anzeigen erscheinen nur auf Seiten mit Inhalt (Artikel, gefüllte Listen, Profile mit Bewertungen), nie auf Rechtsseiten oder leeren Profilen.

## Vor dem Livegang ausfüllen

**Livegang erst nach Eintragung der UG ins Handelsregister** (docs/roi-google-ads.md, Abschnitt 7). Danach in `config/network.json` „ i.G.“ aus `legal_name` entfernen.

Platzhalter in `config/network.json` (erscheinen gelb markiert auf allen Portalen):

| Feld | Inhalt |
|---|---|
| `street`, `postal_city` | ladungsfähige Geschäftsanschrift (kein Postfach) |
| `managing_director` | Geschäftsführer/in |
| `register_court`, `register_number` | Registergericht, HRB-Nummer |
| `vat_id` | USt-IdNr. |
| `email`, `phone` | Kontakt (E-Mail ist Pflicht; Telefon empfohlen) |
| `mstv_responsible` | verantwortliche Person nach § 18 Abs. 2 MStV mit Anschrift |
| `dpa_authority` | zuständige Datenschutz-Aufsichtsbehörde |
| `dsa_contact` | optional eigene DSA-Kontaktadresse (sonst `email`) |

Platzhalter in `legal/datenschutz.md`: Speicherdauer der Server-Logs, Aufbewahrung der Analytics-Daten, Aufbewahrung der Moderationsprotokolle, Newsletter-Versanddienstleister mit AV-Vertrag, ggf. Datenschutzbeauftragte/r.

Außerdem:

- **Alle Rechtstexte sind Entwürfe** („ENTWURF – vor Livegang anwaltlich prüfen“). Nach der anwaltlichen Prüfung in `legal/*.md` die Zeile `draft_note:` entfernen.
- Die Pakete/Preise auf „Für Unternehmen“ sind als Entwurf gekennzeichnet (`config/network.json` → `packages`).
- **Formulare** (Kontakt, Newsletter, Bewertung, Melden, Profil beanspruchen) brauchen ein Backend. Solange `forms.*_action` bzw. `newsletter.action` leer sind, zeigen die Seiten einen Hinweis mit der Kontakt-E-Mail statt eines toten Formulars.
- Bilder nach `IMAGE_PROMPTS.md` erzeugen. Das ist optional, die Seiten funktionieren auch ohne.

## Betrieb auf dem Raspberry Pi

```bash
git clone … && cd …/portal-network
python3 build.py
cd deploy && cp .env.example .env    # CLOUDFLARE_TUNNEL_TOKEN eintragen
docker compose up -d
```

- **Caddy** liefert `dist/<domain>` je nach Host aus (HTTP intern; TLS macht Cloudflare). Dazu kommen www → Apex (301), firmenkoepfe.de → firmennachrichten.de/koepfe/ (301), Sicherheits- und Cache-Header, `404.html` und ein Healthcheck auf `127.0.0.1:8080/healthz`.
- **cloudflared**, Variante A: Token aus dem Dashboard, Hostnamen dort auf `http://caddy:80` routen. Variante B: lokal verwaltet mit `deploy/cloudflared/config.yml.example`.
- Nach jeder Freigabe genügt `python3 build.py`. Caddy liest die Dateien direkt; danach den Cloudflare-Cache leeren (oder kurze Cache-Zeiten nutzen, siehe Caddyfile).

## Launch-Checkliste je Domain

Für **jede** Domain (merkant-medien.de, firmennachrichten.de, itszene.de, it-erfahrungen.de, firmenkoepfe.de):

1. ☐ **Domain kaufen** (.de bei deutschem Registrar). Bis zur Eintragung als „futureconceptions UG (haftungsbeschränkt) i.G.“ bzw. mit dokumentierter späterer Übertragung.
2. ☐ **Zu Cloudflare hinzufügen** (Free-Plan), Nameserver beim Registrar umstellen, SSL/TLS-Modus „Full“, „Always Use HTTPS“ an.
3. ☐ **Tunnel-Route** anlegen: `<domain>` und `www.<domain>` → `http://caddy:80` (Dashboard) bzw. `cloudflared tunnel route dns merkant-pi <hostname>`.
4. ☐ **Impressum-Platzhalter ausfüllen** (`config/network.json`), `i.G.` nach Eintragung entfernen, Rechtstexte anwaltlich prüfen lassen, `draft_note` entfernen, neu bauen. `build.py` darf keine offenen Platzhalter mehr melden.
5. ☐ **Inhalte**: Ratgeber-Entwürfe prüfen (`needs_fact_check`) und freigeben. Für die AdSense-Prüfung substanzielle Inhalte aufbauen (Richtwert 30–50 freigegebene Beiträge je Nachrichtenportal).
6. ☐ **Google Search Console**: Domain-Property per DNS-TXT bei Cloudflare bestätigen (oder `google_site_verification` in `site.json`).
7. ☐ **Sitemap einreichen**: `https://<domain>/sitemap.xml`, bei Nachrichtenportalen zusätzlich `https://<domain>/news-sitemap.xml`.
8. ☐ **AdSense**: Konto als Unternehmenskonto der UG. Website hinzufügen, CMP (TCF 2.2) aktivieren, nach Freigabe `adsense_client_id` (+ Slot-IDs) in `site.json` eintragen und neu bauen. `https://<domain>/ads.txt` prüfen.
9. ☐ **Google Publisher Center** (nur firmennachrichten.de, itszene.de): Publikation anlegen, Domain bestätigen, RSS-Feed `https://<domain>/feed.xml` angeben.
10. ☐ Abschlusstest: `check_site.py` ohne Fehler, Seiten auf dem Handy prüfen, `curl -I https://www.<domain>/` liefert 301.

Für **firmenkoepfe.de** entfallen die Schritte 4–9: Es genügen die Schritte 1–3 und der Test `curl -I https://firmenkoepfe.de/` → 301 auf `https://firmennachrichten.de/koepfe/`.

## Grenzen dieses Stands

- Kein Backend: Formulare, Newsletter-Versand, Bewertungsabgabe, Verifizierung und Telegram-Bot sind vorbereitet, aber noch nicht gebaut (Konzept 8.3).
- Stadt-/Kategorie-Kombinationsseiten (`/kategorie/<leistung>/<stadt>/`) folgen, sobald echte Profile existieren.
- Die Suche ist clientseitig. Für Tausende Profile später Meilisearch o. Ä. (Konzept 8.3).
