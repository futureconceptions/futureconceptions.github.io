# Designkonzept MERKANT-Portale (v1, Entwurf)

**Stand:** 05.11.2026 · **Gilt für:** firmennachrichten.de, itszene.de, it-erfahrungen.de, merkant-medien.de (+ firmenkoepfe.de)
**Dateien:**
- Logo-Entwürfe: `design/logos/*.svg`
- Übersicht: `design/concept-board.html` bzw. `design/concept-board.png`

> **Methodik und Grenzen:** Die Wettbewerbsanalyse beruht auf Fachkenntnis der Seiten (Stand Ende 2026), nicht auf einer Live-Prüfung. Die Cloud-Sitzung, in der dieses Konzept entstand, hat keinen Zugriff auf externe Webseiten. Vor der Umsetzung sollte eine kurze Live-Prüfung mit Screenshots folgen, z. B. über die Pi-Sitzung.
> **Wichtig:** „Fusionieren“ heißt hier, **bewährte Muster** zu übernehmen (Informationsarchitektur, Komponenten, Lesbarkeit). Es heißt **nicht**, Logos, Farben, Schriften oder das Gesamtbild einzelner Marken nachzuahmen. Das wäre markenrechtlich (MarkenG, UWG-Nachahmungsschutz) und für die eigene Glaubwürdigkeit riskant. Alle Logos und Paletten unten sind eigenständig.

---

## 1. Analyse des aktuellen Stands

| Bereich | Heute | Problem |
|---|---|---|
| **Logos** | Alle Portale: gleiches Quadrat mit Symbol + Versalien-Wortmarke in Systemschrift, per `textLength` gestaucht | Austauschbar, wirkt wie ein Baukasten. Keine eigene Schrift, keine Haltung. Auf manchen Geräten verzerrt |
| **Schrift** | Systemschriften (`system-ui`), Serifenschrift nur als Fallback | Kein Wiedererkennungswert. Nachrichtenportale leben von Schlagzeilen-Typografie |
| **Farbe** | Pro Portal nur **eine** Akzentfarbe, sonst identisch | Die Portale unterscheiden sich kaum. Kein System für Zustände (Warnstufen, Verifizierung, Anzeige) |
| **Layout** | Gleiches Kachelraster für News- und Bewertungsportal | Nachrichten brauchen Dichte und Zeitbezug, Bewertungsportale brauchen Suche, Filter und Vergleich. Beides bedient das Raster schlecht |
| **Bilder** | Farbverläufe als Platzhalter | Die Seiten wirken leer und unfertig |
| **Vertrauenssignale** | Vorhanden (Transparenzblöcke), aber visuell gleichrangig | Wichtige Signale wie „verifiziert“ oder „Anzeige“ brauchen eine eigene, feste Bildsprache |
| **Stärken (behalten)** | Schnell, statisch, barrierearm, Dark Mode, saubere Rechtsseiten | Grundlage ist gut, das Redesign baut darauf auf |

---

## 2. Gemeinsames Fundament (alle Portale)

- **Rastersystem:**
  - 12 Spalten, maximale Breite 1240 px
  - 8-px-Abstandsraster
  - Ecken 4–6 px statt 10 px, das wirkt redaktioneller
  - Karten über Linien und Weißraum statt Schatten
- **Schriften:** Nur Open-Font-Lizenz-Schriften, **selbst gehostet**. Google Fonts nicht vom Google-Server laden: Laut LG München (2022) ist das ohne Einwilligung ein DSGVO-Verstoß. Pro Portal höchstens zwei Familien plus eine Mono-Schrift.
- **Feste Zeichen** (auf allen Portalen identisch):
  - „Anzeige“: grauer Rahmen, Label oben links
  - „KI-unterstützt, redaktionell geprüft“: kleines Label am Artikelende
  - „Verifiziert“: blaues Häkchen, nur auf Bewertungsportalen
  - Quellenbox mit Link
- **Dachzeile (Kicker)** über jeder Schlagzeile: Ressort · Ort. Das ist Standard bei allen großen Wirtschaftstiteln und verbessert die Orientierung.
- **Netzwerk-Leiste** im Footer: „Ein Portal von MERKANT Medien“ mit den Schwester-Logos.
- **Dark Mode:** eigene, geprüfte Paletten, nicht einfach invertiert.
- **Barrierefreiheit:** Kontrast mindestens 4,5 : 1, sichtbarer Fokus, keine Information nur über Farbe (Warnstufen immer mit Text).

---

## 3. FIRMENNACHRICHTEN (firmennachrichten.de)

### 3.1 Benchmarks: die 5 relevantesten Wirtschaftsmedien im DACH-Markt

| Medium | Was es gut macht (Muster) |
|---|---|
| **Handelsblatt** | Dichte, hierarchische Startseite. Serifenschlagzeilen als Qualitätsmerkmal. Marktdaten-Leiste. Klare Kennzeichnung von Bezahlinhalten. Morgen-Briefing als Kernprodukt |
| **WirtschaftsWoche** | Starke Dachzeilen, große Aufmacher, gute Ressort-Navigation. Rankings und Listen als wiederkehrendes Format |
| **manager magazin** | Personen-Fokus („Köpfe“, Personalien) mit Porträtbildern. Wechsel in Vorständen und Geschäftsführungen als eigenes Format |
| **Business Insider Deutschland (mit Gründerszene)** | Gründer- und Deal-News schnell und mobil zuerst. Kurze Teaser, viele Zwischenüberschriften, Newsletter-Boxen im Lesefluss |
| **Capital** | Ruhige, magazinige Typografie. Ratgeber und Erklärstücke klar getrennt von Nachrichten |

### 3.2 Fusioniertes Konzept

- **Positionierung:** „Das Handelsregister als Nachrichtenquelle“, also seriös, schnell und regional.
- **Bildsprache:**
  - Tinte und Bordeaux auf kühlem Papierweiß
  - Wenig Farbe, viel Typografie
  - Fotos: Firmengebäude, Innenräume, Branchenbilder (KI-Illustrationen nach `IMAGE_PROMPTS.md`, ohne reale Personen)
- **Palette:**

| Token | Hell | Dunkel | Verwendung |
|---|---|---|---|
| `--ink` | #121A2B | #E8EBF1 | Text, Kopfzeile |
| `--accent` | #8E1B3A (Bordeaux) | #E0577A | Dachzeilen, Links, aktive Navigation |
| `--paper` | #F5F6F8 | #0F131B | Flächen |
| `--line` | #E8ECF2 | #263040 | Trennlinien |
| `--plus` | #0F7B6C | #3CC4A8 | positive Kennzahlen (Gründungen) |

- **Schriften:**
  - Schlagzeilen: **Source Serif 4**, Bold
  - Text, Navigation und Interface: **Public Sans**
  - Uhrzeiten und Registernummern: **JetBrains Mono**
- **Logo:** `logos/firmennachrichten.svg`
  - **Zeichen:** ein Spaltensatz. Oben die Dachzeile in Bordeaux, darunter Schlagzeile und Textzeilen. Das Zeichen erzählt „Nachrichtenspalte“ und funktioniert auch als Favicon.
  - **Wortmarke:** „**Firmen**nachrichten“ in Serifenschrift, gemischt Groß/Klein statt Versalien. Das wirkt redaktionell statt technisch. Der Bordeaux-Unterstrich unter „Firmen“ ist das wiederkehrende Detail.
  - **Ableitung:** Firmenköpfe (`logos/firmenkoepfe.svg`): Die Spalte wird zur Person, Wortmarke im gleichen System.
- **Startseite (von oben nach unten):**
  1. **Tagesleiste** (dunkel): Datum · Gründungen heute · Wechsel in der Geschäftsführung · Insolvenzen (Zahlen aus der eigenen Datenbank)
  2. **Kopf:** Logo links, Button „Morgen-Briefing abonnieren“ rechts, Ressort-Navigation mit Regionen-Menü
  3. **Aufmacher:** groß, 2/3 Breite. Daneben „Köpfe“ (Porträt-Liste) und der **Live-Ticker Handelsregister** (Uhrzeit · Ereignis · Ort)
  4. **Ressort-Bänder:** Unternehmen, Gründer & Startups, Mittelstand, jeweils 1 großer und 3 kleine Beiträge
  5. **Regional-Modul:** NRW-Karte bzw. Städte-Chips
  6. **Rankings & Daten:** Diagramm-Teaser (Gründungsatlas)
  7. **Newsletter-Band**, dann der Footer mit Netzwerk-Leiste
- **Artikelseite:**
  - Dachzeile, Serifenschlagzeile, Teaser, Autorenzeile, Datum und „aktualisiert“
  - Infobox „Über das Unternehmen“ (Stammdaten, Link zum Profil)
  - Quellenbox
  - „Mehr aus Köln“, „Mehr Personalien“
- **Firmen- und Personenseiten:**
  - Kopf mit Name, Rechtsform, Sitz und Register
  - Zeitleiste der Registerereignisse (vertikale Linie mit Punkten)
  - Box „Erfahrungen auf IT-Erfahrungen“, falls vorhanden

---

## 4. ITSZENE (itszene.de)

### 4.1 Benchmarks: die 5 relevantesten IT-Fachmedien im DACH-Markt

| Medium | Was es gut macht (Muster) |
|---|---|
| **heise online** | Nachrichtenstrom mit Uhrzeit, hohe Dichte, Themen-Kanäle (Security, Developer, Pro). Klare Kennzeichnung exklusiver Inhalte, sehr gute Suche |
| **Golem.de** | Kompakte Listen mit Vorschaubild, schnelle Ladezeit, klare Ressorts, gutes Lesen auf dem Handy |
| **t3n** | Moderne, großzügige Magazin-Optik, starke Bilder, Erklär- und Ratgeber-Formate, Newsletter-Funnel |
| **Computerwoche / CIO** | B2B-Fokus (Entscheider), Themen-Hubs, Whitepaper und Studien, Karriere- und Führungsthemen |
| **Security-Insider / Vogel-IT-Insider** | Fachkanäle je Thema, Glossar-Seiten („Was ist …?“), Webinar- und Whitepaper-Bereiche, klare Werbetrennung |

### 4.2 Fusioniertes Konzept

- **Positionierung:** „IT-Nachrichten für Entscheider im Mittelstand“: was passiert und was das für meinen Betrieb heißt.
- **Bildsprache:**
  - Graphit-Kopf mit Cyan als Akzent, Inhaltsfläche hell
  - Technisch, präzise, nicht verspielt
  - Warnstufen als festes Farbsystem
  - Illustrationen: isometrisch und abstrakt (Netze, Server, Schlösser), keine Klischee-Hacker im Kapuzenpulli
- **Palette:**

| Token | Hell | Dunkel | Verwendung |
|---|---|---|---|
| `--graphite` | #0C1015 | #0C1015 | Kopfzeile, Text |
| `--accent` | #0891B2 | #22D3EE | Links, aktive Navigation, „it“ im Logo |
| `--surface` | #F1F5F9 | #151B23 | Infoboxen |
| `--sev-critical` | #DC2626 | #F87171 | Warnstufe kritisch |
| `--sev-high` | #EA580C | #FB923C | hoch |
| `--sev-medium` | #CA8A04 | #FACC15 | mittel |
| `--sev-low` | #0E7490 | #67E8F9 | niedrig/Info |

- **Schriften:**
  - Text und Schlagzeilen: **IBM Plex Sans**
  - Uhrzeit, CVE-Nummern, CVSS und Fristen: **JetBrains Mono**
- **Logo:** `logos/itszene.svg`
  - **Zeichen:** eckige Klammern mit Block-Cursor, also „etwas wird gerade geschrieben, live“. Das Zeichen ist eindeutig IT, ohne Klischee-Platine.
  - **Wortmarke:** „**it**szene“ in Kleinbuchstaben, „it“ in Cyan. Das Kleinschreiben ist modern und unterscheidet sich von den Versalien-Marken der Konkurrenz.
  - **Animation (optional, nur Startseite):** Der Cursor blinkt zweimal beim Laden. Wer reduzierte Bewegung eingestellt hat, sieht keine Animation.
- **Startseite (von oben nach unten):**
  1. **Kopf** in Graphit: Logo, Suche (Tastenkürzel ⌘K), Ressort-Navigation (Sicherheit zuerst)
  2. **Warnband:** aktuelle Sicherheitswarnung mit Stufe, CVSS und dem Hinweis „Was KMU jetzt tun sollten“
  3. **Nachrichtenstrom** (links, 2/3): Uhrzeit in Mono, Schlagzeile, Ressort-Chip
  4. **Rechte Spalte:** „Erklärt“ (Ratgeber), **Fristen-Radar** (E-Rechnung, NIS2 usw. mit Datum), Newsletter
  5. **Themen-Hubs:** NIS2, Backup, Cloud, KI im Betrieb, jeweils mit Glossar-Seite
  6. **IT-Unternehmen:** Personalien und Übernahmen, verknüpft mit IT-Erfahrungen
- **Artikelseite:**
  - Infobox „Betroffen / Was tun?“ mit 3 konkreten Schritten
  - Bei Sicherheitsmeldungen ein Kasten mit Stufe, betroffenen Versionen und Link zur amtlichen Quelle
  - Glossar-Links

---

## 5. IT-ERFAHRUNGEN (it-erfahrungen.de)

### 5.1 Benchmarks: die 5 relevantesten Bewertungs- und Vergleichsplattformen

| Plattform | Was sie gut macht (Muster) |
|---|---|
| **Trustpilot** | Suche als Einstieg, ein klarer Gesamtwert pro Firma, Verteilungsbalken, Herkunfts-Labels, öffentliche Firmenantworten |
| **Clutch** (B2B-Dienstleister weltweit) | Genau unsere Nische: Filter nach Leistung, Budget, Stundensatz, Teamgröße und Ort. Ausführliche, strukturierte Projektberichte (Projekt, Budget, Dauer, Ergebnis) |
| **OMR Reviews** | Deutschsprachig, B2B, Kategorie-Seiten mit „Top bewertet“, Vergleiche, Ratgeber-Inhalte zur Kategorie |
| **Capterra / GetApp** | Vergleich mehrerer Anbieter nebeneinander, Filter-Seitenleiste, Pro/Contra-Zusammenfassung |
| **ProvenExpert** | Siegel und Widgets für Firmen-Websites, Gesamtwert und Empfehlungsquote, starke B2B-Vertrauensoptik in Deutschland |

### 5.2 Fusioniertes Konzept

- **Positionierung:** „Den richtigen IT-Partner finden, mit geprüften Projekterfahrungen“. Ruhig, vertrauenswürdig, entscheidungsorientiert.
- **Bewusste Abgrenzung:** **keine Sterne in Quadraten** und keine Signalgrün-Optik (prägende Merkmale bekannter Portale). Stattdessen gibt es eine **Punkte-Skala** in Bernstein und eine **Zahl im Tannengrün-Kasten**.
- **Palette:**

| Token | Hell | Dunkel | Verwendung |
|---|---|---|---|
| `--forest` | #14532D | #4ADE80 | Marke, Gesamtwert-Kasten, Haupt-Buttons |
| `--amber` | #D97706 | #FBBF24 | Bewertungspunkte, Häkchen im Logo |
| `--surface` | #F3F7F4 | #111A15 | Suchbereich, Filter |
| `--text` | #1F2937 | #E5E7EB | Text |
| `--verified` | #2563EB | #60A5FA | „Profil verifiziert“ / „verifizierte Erfahrung“ |

- **Schrift:** **Figtree** (freundlich, sehr gut lesbar). Werte mit tabellarischen Ziffern.
- **Logo:** `logos/it-erfahrungen.svg`
  - **Zeichen:** eine Sprechblase (Erfahrung teilen) mit Häkchen (geprüft)
  - **Wortmarke:** „**IT-**Erfahrungen“, darunter die Bewertungspunkte als wiederkehrendes Markenelement
- **Startseite (von oben nach unten):**
  1. **Suchbereich:** „Welchen IT-Dienstleister suchen Sie?“, Eingabefeld (Leistung, Firma oder Ort), Kategorie-Chips
  2. **Kategorie-Kacheln:** Managed Services, Cloud, IT-Security, Softwareentwicklung, IT-Beratung, Systemhaus
  3. **So prüfen wir:** 3 Schritte mit Symbolen (Herkunft, Verifizierung, keine Löschung gegen Geld)
  4. **Neueste geprüfte Erfahrungen**, sonst ein ehrlicher Leerzustand
  5. **Ratgeber** für die Auswahl (Checklisten, Kosten)
  6. **Für IT-Dienstleister:** Profil beanspruchen
- **Kategorie- und Ergebnisseite** (Muster von Clutch und Capterra):
  - Filter-Seitenleiste: Region, Firmengröße des Kunden (Arbeitsplätze), Budget pro Monat, Leistungen, nur verifizierte
  - Anbieterkarte: Wert-Kasten, Punkte-Skala, Anzahl der Erfahrungen, Antwortzeit, Verifiziert-Label, Checkbox „vergleichen“
  - **Vergleichsleiste** am unteren Rand (bis 3 Anbieter) mit Vergleichstabelle
- **Firmenprofil:**
  - Kopf mit Wert-Kasten, Verteilungsbalken und Teilkriterien als horizontale Balken
  - **Projektberichte** statt kurzer Bewertungstexte, mit festen Feldern: Leistung, Kundengröße, Budget-Spanne, Laufzeit, Ergebnis
  - Firmenantwort eingerückt
  - Herkunfts-Label je Bericht
- **Siegel und Widget:** rundes Siegel mit Wert, Punkte-Skala, „IT-Erfahrungen“ und Jahr. Es verlinkt auf das Profil.

---

## 6. MERKANT Medien (merkant-medien.de)

### 6.1 Benchmarks: Unternehmensseiten von Medienhäusern

| Haus | Muster |
|---|---|
| **Axel Springer** (Konzernseite) | Klare Portfolio-Übersicht, Haltung und Werte prominent, Presse und Karriere |
| **Hubert Burda Media** | Marken-Raster mit Logo und Kurzbeschreibung, Unternehmensgeschichte |
| **Vogel Communications Group** | B2B-Fachmedien, Mediadaten und Werbeangebote leicht auffindbar, Zielgruppen-Beschreibung |
| **Ippen Media** | Regionale Portale als Netzwerk dargestellt, Reichweiten-Zahlen |
| **Foundry (vormals IDG)** | Zielgruppen-Fokus (IT-Entscheider), Leistungen für Werbekunden, Fallbeispiele |

### 6.2 Fusioniertes Konzept

- **Positionierung:** „Unabhängige Fachmedien für den Mittelstand“: seriös, transparent, klein, aber professionell.
- **Palette:**
  - Marine #1B2A4E
  - Messing #C9A24A, nur für Akzentlinien
  - Fläche #F6F7F9
  - Schiefer #374151
- **Schriften:** **Fraunces** (Display, nur Überschriften) und **IBM Plex Sans** (Text)
- **Logo:** `logos/merkant-medien.svg`
  - **Monogramm:** ein „M“ aus einer durchgehenden Linie, für die drei Säulen Nachrichten, IT und Erfahrungen, mit Messing-Grundlinie
  - **Wortmarke:** „MERKANT“ in gesperrten Versalien, darunter „MEDIEN“
- **Seitenaufbau:**
  1. Haltungs-Band in Marine („Redaktion und Bewertungen sind nicht käuflich …“)
  2. Portfolio-Raster: je Portal Logo, Zielgruppe und Farbstreifen in der Portalfarbe
  3. Haltung & Transparenz: Redaktionsgrundsätze, KI-Arbeitsweise, Transparenzbericht
  4. Mediadaten und Werben (Pakete, Kennzeichnung)
  5. Kontakt und Impressum

---

## 7. Umsetzung (Vorschlag)

1. **Freigabe** dieses Konzepts: Logos, Paletten und Schriften bestätigen oder Änderungswünsche nennen.
2. **Schriften** (OFL) herunterladen, als WOFF2 unter `static/fonts/` ablegen, `@font-face` mit `font-display: swap`. Logos final als Pfade setzen, damit sie unabhängig von der Schrift sind.
3. **Code:**
   - `lib/brand.py`: neue Logos (SVG-Dateien statt generierter Marken)
   - `static/base.css`: Design-Token pro Portal (`sites/*/theme.css`), neue Komponenten (Tagesleiste, Live-Ticker, Warnband, Fristen-Radar, Filterleiste, Vergleichsleiste, Projektbericht)
   - `templates/base.html`: Kopfvarianten je Portaltyp
4. **Bilder** nach `IMAGE_PROMPTS.md` mit letz.ai erzeugen. Die Stilvorgaben je Portal (Abschnitte 3–6) gelten als Ergänzung.
5. **Tests:** Linkprüfung, Kontrastprüfung, Screenshots für Handy und Desktop, hell und dunkel.
6. **Deployment:** Build auf dem Pi. Wichtig: Der Pi hat lokale Commits, die noch nicht auf GitHub sind (OSM-Profile, Bot). Vor der Umsetzung müssen GitHub und Pi zusammengeführt werden, sonst entstehen Konflikte.
