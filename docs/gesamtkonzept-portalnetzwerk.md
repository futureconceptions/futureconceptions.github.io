# Gesamtkonzept: Portalnetzwerk für Wirtschaftsnachrichten & Bewertungen

**Netzwerk:** MERKANT Medien · **Stand:** November 2026 · **Status:** Konzept v2 (Betrieb auf Raspberry Pi, KI-Entwürfe, Freigabe per Telegram)
**Hinweis:** Eigenständiges Projekt, organisatorisch und rechtlich getrennt von ClipFarm Studio. Dieses Dokument gehört langfristig in ein eigenes Repository.

---

## Inhalt

1. Vision & Kernidee
2. Markennamen (Netzwerk, Nachrichtenportal, Bewertungsportale)
3. Netzwerk-Architektur
4. Leitportal: KONTORKURIER (Wirtschaftsnachrichten)
5. Bewertungsportale (Urteil-Familie)
6. Wie Nachrichten und Bewertungen zusammenspielen
7. Content-Engine: Quellen, KI-Workflow, Tagesplan
8. Technik: Betrieb auf dem Raspberry Pi, Telegram-Freigabe, Regel-Engine
9. Reichweite & Distribution
10. Geschäftsmodell & Preise
11. Recht & Compliance
12. Organisation & Team
13. Kosten (Schätzung)
14. Roadmap
15. KPIs
16. Risiken & Gegenmaßnahmen
17. Nächste Schritte

---

## 1. Vision & Kernidee

**Ein Netzwerk unabhängiger Portale, das dem deutschen Mittelstand ein Gesicht gibt:**
- ein **Nachrichtenportal**, das täglich über Unternehmen und Unternehmer berichtet, also über die Firmen, die Handelsblatt & Co. übersehen,
- mehrere **Bewertungsportale** für Branchen, in denen Kunden vor teuren, riskanten Entscheidungen stehen,
- alles auf **einer gemeinsamen Plattform** mit gemeinsamer Firmen- und Personendatenbank.

**Leitsatz:** *„Wer über ein Unternehmen Bescheid wissen will, landet bei uns: mit Nachrichten, Zahlen, Köpfen und echten Kundenerfahrungen.“*

**Betriebsmodell:**
- Alle Portale laufen auf **einem Raspberry Pi**, der über einen Cloudflare Tunnel und den Cloudflare-Cache erreichbar ist.
- **Regeln** erzeugen jeden Tag automatisch Beitragsentwürfe, die **KI** schreibt.
- **Du gibst jeden Beitrag per Telegram frei.** Erst dann geht er online.
- Zeitaufwand im Tagesbetrieb: ca. 1 Stunde, in drei Freigabeblöcken.

**Grundprinzip, auf dem das ganze Geschäft beruht:** Glaubwürdigkeit. Redaktion und Bewertungen sind nicht käuflich. Bezahlte Inhalte sind immer gekennzeichnet. Der gemeinsame Betreiber wird offen genannt. Das ist keine Pflichtübung, sondern das Produkt: Ohne Unabhängigkeit gibt es keine Reichweite bei Google und keine Leser.

---

## 2. Markennamen (Domainprüfung vom 02.11.2026)

> **Prüfmethode:** `.com` über die Cloudflare-Registrar-API (verbindliche Live-Abfrage bei der Registry). `.de` über die WHOIS-Abfrage von Cloudflare Intel (zeigt, ob die Domain bei DENIC registriert ist). Insgesamt wurden über 100 Domains geprüft.
> **Wichtig:** Domains können jederzeit weggeschnappt werden. Die gewählten Domains deshalb **zeitnah registrieren**. `.de` ist bei Cloudflare Registrar nicht erhältlich und wird bei einem deutschen Registrar gekauft (z. B. INWX, Hetzner, netcup, United Domains; ca. 5–15 €/Jahr). `.com` kostet bei Cloudflare 11,17 USD/Jahr.
> **Vor dem Kauf zusätzlich:** DPMA-/EUIPO-Markenrecherche (Klassen 35, 38, 41, 42) und Social-Handles prüfen.

### 2.1 Festgelegte Namen

| Rolle | Name | Hauptdomain | Weitere Domains (alle frei) |
|---|---|---|---|
| **Dachmarke / Betreiber** | **MERKANT Medien** | `merkant-medien.de` | `merkantmedien.de`, `merkant-medien.com`, `merkantmedien.com` |
| **Nachrichtenportal** | **KONTORKURIER** | `kontorkurier.de` | `kontor-kurier.de`, `kontorkurier.com`, `kontor-kurier.com` |
| Bewertungsportal | **Agentururteil** | `agentururteil.de` | `agentur-urteil.de`, `agentururteil.com`, `agentur-urteil.com` |
| Bewertungsportal | **Softwareurteil** | `softwareurteil.de` | `software-urteil.de`, `softwareurteil.com`, `software-urteil.com` |
| Bewertungsportal | **Kursurteil** | `kursurteil.de` | `kurs-urteil.de`, `kursurteil.com` |
| Bewertungsportal | **Solarurteil** | `solarurteil.de` | `solar-urteil.de`, `solarurteil.com` |
| Bewertungsportal | **Umzugsurteil** | `umzugsurteil.de` | `umzugs-urteil.de`, `umzugsurteil.com` |
| später | **Coachurteil** | `coachurteil.de` | `coach-urteil.de`, `coachurteil.com` |
| später | **Betreuungsurteil** | `betreuungsurteil.de` | `betreuungs-urteil.de`, `betreuungsurteil.com` |

**Claims:**
- **MERKANT Medien:** *Medien für den Mittelstand.* „Merkant“ (vom lateinischen *mercator*, Kaufmann) ist neutral, passt zu Nachrichten und Bewertungen, und eine Websuche hat keine gleichnamige Medienmarke gefunden. Rechtsform z. B. „Merkant Medien GmbH“ oder UG. Erscheint im Impressum aller Portale. Hinweis: `merkant.de`/`.com` sind vergeben, deshalb der Zusatz „Medien“.
- **KONTORKURIER:** *Nachrichten über Unternehmen und die Menschen dahinter.* Das Kontor steht für Kaufmannstradition, der Kurier für ein Nachrichtenmedium. Eine Websuche fand keine Marke mit diesem Namen. Mit Abstand zu „Kontor Records“ (Musiklabel) durch den Zusatz „Kurier“.
- **„-urteil“-Familie:** Die einzige geprüfte Namensfamilie, bei der **alle sieben Portale auf .de und .com frei** sind. Der Name ist ehrlich („das Urteil der Kunden“) und als Netzwerk erkennbar. Claims: *Agentururteil – Die richtige Agentur. Echte Erfahrungen.* · *Softwareurteil – IT-Partner im Kundenurteil* · *Kursurteil – Weiterbildung, die hält, was sie verspricht* · *Solarurteil – Installateure im Erfahrungscheck* · *Umzugsurteil – Seriöse Umzugsfirmen finden*.
- **Abwägung „-urteil“:** Das Wort kann an Gerichtsurteile erinnern (z. B. bei Suchen wie „Umzug Urteil“). Für die Marke unkritisch, für SEO aber nicht auf Suchbegriffe mit „Urteil“ optimieren, sondern auf „Erfahrungen“ und „Bewertungen“.

Regionale Ausgaben des Nachrichtenportals als Unterbereiche: `kontorkurier.de/nrw`, `/bayern`, `/rhein-main`, `/berlin` …

Bewusst vermieden: „Test“ oder „Check“ im Namen. Das suggeriert eigene Warentests à la Stiftung Warentest und wäre ohne echte Tests irreführend.

### 2.2 Verworfene Favoriten (Domain vergeben)

| Name | Ergebnis | Bemerkung |
|---|---|---|
| KOPF & KONTOR | `kopfundkontor.de` + `kopf-kontor.de` vergeben (gleicher Inhaber, aktiv, zuletzt geändert 28.10.2026), `.com` vergeben, `kopfkontor.de` vergeben | Nur `kopf-und-kontor.de` frei. Wegen aktiver Nutzung des Namens Konfliktgefahr, deshalb verworfen |
| BLICKWERK Medien | `blickwerk.de`/`.com` vergeben, `blickwerk-media.de` vergeben | `blickwerk-medien.de` wäre frei, aber die Blick-Familie entfällt |
| Blick-Familie | `agenturblick.de`, `softwareblick.de`, `kursblick.de` (Sedo-geparkt, evtl. käuflich), `solarblick.de`, `umzugsblick.de`, `coachblick.de`, `pflegeblick.de` vergeben | Familie nicht einheitlich verfügbar |
| Firmenkurier | `.de` vergeben | `.com` frei |
| Chefetage | `.de`/`.com` vergeben | `chefetage-news.de` frei |
| Firmenblick, Unternehmerblick | `.de` vergeben (firmenblick.de Sedo-geparkt) | – |
| „-radar“, „-kompass“, „-lupe“, „-echo“ | jeweils mehrere Portale vergeben | Familie nicht vollständig |

### 2.3 Freie Reserve-Namen (.de und .com frei)

| Für | Freie Alternativen |
|---|---|
| Dachmarke | Urteilwerk (Medien), Mittelweg Media, Blickfeld Medien, Blickhaus Medien, Portalwerk Medien, Kurierwerk Medien, Radarwerk Medien, Lupenwerk Medien |
| Nachrichtenportal | Mittelstandsblick, Mittelstandszeit, Mittelstandspost, Mittelstandsticker, Unternehmenskurier, Kontorzeit, Kontorticker, Kontorblick, Firmenköpfe (`firmenkoepfe`), Köpfe & Firmen (`koepfeundfirmen`), Registerkurier, Registerticker, Chefetage News |
| Bewertungsportale | Lupe-Familie teilweise frei (`agenturlupe`, `kurslupe`, `coachlupe`), Echo-Familie teilweise frei (`softwareecho`, `kursecho`, `umzugsecho`, `betreuungsecho`) |

---

## 3. Netzwerk-Architektur

```
                         MERKANT Medien GmbH (Betreiber, offen genannt)
                                        │
              ┌─────────────────────────┴─────────────────────────┐
              │                                                   │
      KONTORKURIER                                     Urteil-Bewertungsportale
   (Wirtschaftsnachrichten)                    Agentururteil · Softwareurteil · Kursurteil
              │                                     Solarurteil · Umzugsurteil
              │                                                   │
              └──────────────┬────────────────────────────────────┘
                             │
            ┌────────────────┴─────────────────────┐
            │  GEMEINSAME PLATTFORM auf Raspberry Pi│
            │  • Firmen- & Personendatenbank        │
            │  • CMS / Redaktionssystem             │
            │  • Bewertungs-Engine & Verifizierung  │
            │  • Moderation, Meldeverfahren (DSA)   │
            │  • Daten-Pipelines (Register, PR)     │
            │  • Regel-Engine + KI + Telegram-Bot   │
            │  • Ads, Newsletter, Accounts, Billing │
            └───────────────────────────────────────┘
```

**Prinzip „ein Kern, viele Oberflächen“:** Ein neues Portal entsteht durch Konfiguration (Domain, Branding, Kategorien, Bewertungskriterien, Redaktionsressorts), nicht durch neue Software.

**Verknüpfung über die Firmen-ID:** Jedes Unternehmen existiert genau einmal in der Datenbank. Es kann:
- in Artikeln von KONTORKURIER vorkommen,
- ein Bewertungsprofil auf einem oder mehreren Urteil-Portalen haben,
- ein Premium-Profil gebucht haben (gilt netzwerkweit).

---

## 4. Leitportal: KONTORKURIER

### 4.1 Positionierung
- **Zielgruppe:** Unternehmer, Geschäftsführer, Führungskräfte, Gründer, Investoren, Vertriebler, Journalisten, Bewerber, interessierte Bürger einer Region.
- **Lücke:** Die überregionale Wirtschaftspresse berichtet über DAX und Konzerne. Lokalzeitungen berichten unregelmäßig und hinter Paywalls. Über Mittelstand, Gründer und Firmenwechsel berichtet niemand systematisch.
- **Tonalität:** sachlich, schnell, nahbar. Keine Häme bei Pleiten, kein Hofberichterstatter-Ton bei Erfolgen.

### 4.2 Ressorts

| Ressort | Inhalt | Frequenz |
|---|---|---|
| **Aktuell** | Eilmeldungen, Tagesthemen, Aufmacher | laufend |
| **Unternehmen** | Zahlen, Übernahmen, Standorte, Expansion, Stellenabbau | 8–15 / Tag |
| **Köpfe** | Wechsel in der Geschäftsführung, Personalien, Nachfolge, Porträts, Interviews | 5–10 / Tag |
| **Gründer & Startups** | Finanzierungsrunden, Neugründungen, Exits | 3–6 / Tag |
| **Mittelstand** | Familienunternehmen, Hidden Champions, Nachfolge | 1–3 / Tag |
| **Insolvenzen** | Insolvenzen, Sanierungen, Rettungen (amtlich belegt) | 3–10 / Tag |
| **Regional** | Filter aller Ressorts nach Bundesland/Stadt | automatisch |
| **Ratgeber** | Recht, Steuern, Finanzierung, Führung, KI im Betrieb | 1 / Tag |
| **Rankings & Daten** | Wachstumschampions, Top-Arbeitgeber, Gründungsatlas | monatlich |

### 4.3 Seitentypen

```
Startseite
├── Aufmacher (1 großes Thema)
├── Kachelraster nach Ressorts
├── Live-Ticker „Handelsregister heute“ (neue Gründungen, Wechsel in der Geschäftsführung)
├── Module: Insolvenz-Ticker, Finanzierungsrunden der Woche, Köpfe der Woche
├── Newsletter-Anmeldung („Das Morgen-Briefing“)
└── Werbeflächen (gekennzeichnet)

Artikelseite
├── Ressort, Überschrift, Teaser, Bild, Autor, Datum + „aktualisiert“
├── Text mit verlinkten Firmen & Personen (Firmen-Chips)
├── Infobox „Über das Unternehmen“ (aus Datenbank)
├── Quellenangaben (z. B. „Handelsregister HRB 12345, AG Köln, 30.10.2026“)
├── Box „Erfahrungen mit diesem Unternehmen“ → Link zum Urteil-Portal (falls vorhanden)
└── Mehr zum Thema / Newsletter / Anzeigen

Firmenseite  /unternehmen/<slug>
├── Stammdaten: Name, Rechtsform, Sitz, Register, Gründung, Branche, Website
├── Geschäftsführung / Vorstand (aktuell + Historie)
├── Kennzahlen aus Bundesanzeiger (Umsatz, Mitarbeiter, Bilanzsumme, sofern veröffentlicht)
├── Zeitleiste: alle Registerereignisse und Artikel
├── Bewertungsscore aus Urteil-Portal (falls vorhanden)
└── Premium: Logo, Selbstdarstellung, Newsroom, Stellen (als „Firmeninformation“ gekennzeichnet)

Personenseite  /koepfe/<slug>
├── Nur berufliche Rolle: Funktionen, Firmen, Zeiträume
├── Artikel, in denen die Person vorkommt
└── KEINE privaten Daten (Adresse, Familie, Alter nur wenn öffentlich relevant)

Ressort- & Regionalseiten, Themenseiten (z. B. „Wärmepumpen-Branche“), Autorenseiten,
Über uns / Redaktionsgrundsätze / Korrekturen / Impressum / Datenschutz / Mediadaten
```

### 4.4 Formate

| Format | Beschreibung | Rhythmus |
|---|---|---|
| **Das Morgen-Briefing** | Newsletter + Artikel: 5 wichtigste Firmennachrichten, 3 Köpfe, 1 Zahl des Tages | werktags 6:30 |
| **Unternehmer des Tages** | Porträt / Kurzinterview (redaktionell, nicht bezahlt) | werktags |
| **Insolvenz-Report** | Wochenauswertung nach Region & Branche | freitags |
| **Gründungsatlas** | Neugründungen nach Region/Branche (Daten-Story) | monatlich |
| **Köpfe der Woche** | Alle relevanten Wechsel in der Geschäftsführung | montags |
| **Deal-Monitor** | Finanzierungsrunden & Übernahmen | wöchentlich |
| **Wachstumschampions [Region]** | Ranking aus Bilanzdaten | jährlich + Award |
| **KONTORKURIER Podcast** | Gespräch mit einem Unternehmer | 14-täglich (Phase 3) |

---

## 5. Bewertungsportale (Urteil-Familie)

### 5.1 Gemeinsamer Aufbau (alle Urteil-Portale)

```
Startseite: Suche (Firma / Leistung / Ort) + Top-Kategorien + neueste Bewertungen
Kategorie- & Stadtseiten: /social-media-agentur/koeln  (programmatic SEO)
Firmenprofil: /firma/<slug>
  ├── Score, Anzahl, Verteilung 1–5★, Teilkriterien
  ├── Badges: „Profil beansprucht“, „lädt aktiv ein“, „antwortet meist in X Tagen“
  ├── KI-Zusammenfassung der Bewertungen (als KI-generiert gekennzeichnet)
  ├── Bewertungsliste mit Herkunfts-Label (verifiziert / eingeladen / organisch)
  ├── Antworten des Unternehmens
  ├── Box „Aktuelle Nachrichten“ → KONTORKURIER
  └── Stammdaten aus gemeinsamer Firmendatenbank
Bewertung schreiben (mit Verifizierung)
Für Unternehmen: Profil beanspruchen, Pakete, Widgets, Einladungs-API
Transparenz: So funktionieren Bewertungen · Score-Methodik · Richtlinien · Transparenzbericht · Melden
```

### 5.2 Nischenspezifische Bewertungskriterien

| Portal | Teilkriterien (je 1–5★) | Zusatzfelder |
|---|---|---|
| **Agentururteil** | Ergebnisse, Kommunikation, Kreativität, Termintreue, Preis-Leistung | Leistung (Social, Video, SEO, Ads …), Projektbudget-Spanne, Laufzeit |
| **Softwareurteil** | Qualität, Projektmanagement, Termintreue, Support, Preis-Leistung | Technologie, Projektart, Budget-Spanne |
| **Kursurteil** | Inhalte, Dozenten, Organisation, Jobchancen, Betreuung | Kurs, Förderung (Bildungsgutschein ja/nein), Abschluss, Job nach Kurs |
| **Solarurteil** | Beratung, Montage, Termintreue, Service nach dem Kauf, Preis-Leistung | Anlagengröße, Komponenten, Monate seit Inbetriebnahme |
| **Umzugsurteil** | Pünktlichkeit, Sorgfalt, Freundlichkeit, Preistreue, Preis-Leistung | Umzugsart, Entfernung, Angebot vs. Endpreis |

### 5.3 Verifizierungsstufen

| Stufe | Nachweis | Label |
|---|---|---|
| 0 | E-Mail bestätigt | „Organisch“ |
| 1 | Einladung durch Unternehmen (Auftrags-/Kundennummer) | „Eingeladen“ |
| 2 | Beleg-Upload (Rechnung, Vertrag, Teilnahmebescheinigung), wird nach Prüfung gelöscht | „Verifiziert“ |

### 5.4 Score-Methodik (öffentlich dokumentiert)
- Gewichteter Mittelwert, neuere Bewertungen zählen stärker (Halbwertszeit 12 Monate).
- Bayes-Glättung: Profile mit wenigen Bewertungen starten bei 3,5 und nähern sich dem echten Wert an.
- Verifizierte Bewertungen erhalten Gewicht 1,2, organische 1,0.
- **Zahlung hat keinen Einfluss** auf Score, Sortierung oder Sichtbarkeit von Bewertungen.

### 5.5 Kaltstart je Portal (ohne Fake-Bewertungen)
1. 500–2.000 Profile aus öffentlichen Daten anlegen (Register, Websites, Branchenverzeichnisse, AZAV-Datenbank für Kursurteil, Marktstammdatenregister für Solarurteil).
2. Unternehmen anschreiben: „Ihr Profil ist online. Beanspruchen Sie es kostenlos und laden Sie Kunden ein.“
3. Kostenloses Einladungs-Tool (CSV-Upload, Zapier, Shop-/CRM-Plugins) für die ersten 6 Monate.
4. Redaktionelle Ratgeber und Marktübersichten als SEO-Fundament.
5. Launch-Datenstudie mit PR über KONTORKURIER (offen als Schwesterportal gekennzeichnet).

---

## 6. Wie Nachrichten und Bewertungen zusammenspielen

| Verbindung | Nutzen | Regel |
|---|---|---|
| Artikel → Bewertungsprofil | Leser sehen Kundenerfahrungen | Link-Box „Erfahrungen auf Agentururteil“ mit Hinweis „Schwesterportal“ |
| Bewertungsprofil → Artikel | Besucher sehen aktuelle Nachrichten zur Firma | Automatisch über Firmen-ID |
| Gemeinsame Firmendatenbank | Einmal pflegen, überall nutzen | Datenquelle angeben |
| Datenstudien aus Bewertungen | Exklusive Geschichten für KONTORKURIER | Methodik offenlegen |
| Netzwerk-Premiumprofil | Höherer Umsatz pro Kunde | Kein Einfluss auf Redaktion oder Score |

**Firewall-Regel:** Die Redaktion von KONTORKURIER entscheidet unabhängig vom Vertrieb. Kein Kunde kauft Berichterstattung, Löschungen oder bessere Bewertungen. Die Regel steht in den Redaktionsgrundsätzen und in jedem Kundenvertrag.

---

## 7. Content-Engine

### 7.1 Quellen

| Quelle | Daraus entsteht | Zugang |
|---|---|---|
| Handelsregister-Bekanntmachungen | Gründungen, Wechsel in der Geschäftsführung, Prokura, Verschmelzungen, Sitzverlegung, Liquidation | handelsregister.de / Datenanbieter (z. B. North Data, Implisense, Creditreform-APIs) |
| Insolvenzbekanntmachungen | Insolvenz-Meldungen | insolvenzbekanntmachungen.de (Nutzungsbedingungen beachten) |
| Unternehmensregister / Bundesanzeiger | Jahresabschlüsse, Kennzahlen | unternehmensregister.de |
| Pressemitteilungen | Firmennachrichten | presseportal.de (ots), Firmen-Newsrooms, RSS, Presseverteiler |
| Finanzierungsrunden | Startup-News | Pressemitteilungen, LinkedIn, Dealroom/Crunchbase (Lizenz) |
| Behörden & Kammern | Ansiedlungen, Förderungen, Statistiken | IHK, Wirtschaftsförderungen, Destatis, Landesämter |
| Marktstammdatenregister | Solar-Installationen (für Solarurteil) | öffentlich |
| AZAV-/Kursnet-Daten | Bildungsträger (für Kursurteil) | öffentlich |
| Eigene Recherche, Interviews, Leser-Hinweise | Exklusives, Porträts | Redaktion, Hinweisgeber-Formular |

### 7.2 Workflow: Regeln → KI-Entwurf → Telegram-Freigabe

Kernprinzip: **Die KI schreibt, du gibst frei.** Nichts geht ohne deinen Klick in Telegram online. Als Verantwortlicher nach § 18 Abs. 2 MStV bist du die menschliche Prüfinstanz. Die Freigabe ist deshalb eine echte Prüfung, kein Durchwinken.

```
[1] Regel feuert     Der Scheduler startet eine Regel (Cron, z. B. „06:00 Personalien NRW“)
      ↓
[2] Ingest           Die Regel holt Daten aus ihrer Quelle (Register, Insolvenzen, PR-Feeds, Bewertungs-DB)
      ↓
[3] Filter           Regelbedingungen: Region, Branche, Mindestgröße, Duplikate, Tageslimit
      ↓
[4] Entwurf (KI)     LLM schreibt nach Vorlage der Regel: Titel, Teaser, Text, Tags, Bild-Vorschlag
                     → nur Fakten aus den gelieferten Quelldaten, Quellenliste Pflicht
      ↓
[5] Faktencheck (KI) Zweiter, unabhängiger Durchlauf vergleicht den Entwurf satzweise mit der Quelle
                     → nicht belegte Aussagen werden markiert oder gestrichen
      ↓
[6] Risikoklasse     🟢 grün (Gründung, Ratgeber, Ranking) · 🟡 gelb (Personalwechsel, Zahlen)
                     · 🔴 rot (Insolvenz, Vorwürfe, Rechtsstreit, Personen in negativem Kontext)
      ↓
[7] Telegram         Bot schickt die Freigabekarte an dich (siehe 8.4)
      ↓
[8] Entscheidung     ✅ Freigeben · ✏️ Ändern · 🔁 Neu schreiben · ⏰ Später · ❌ Verwerfen
      ↓
[9] Publish          Statische Seiten neu bauen → Cloudflare-Cache leeren → Google-News-Sitemap,
                     RSS, Newsletter-Queue, Telegram-/LinkedIn-Kanal
      ↓
[10] Protokoll       Audit-Log: Entwurf, Änderungen, Freigabe durch wen, wann (Nachweis Sorgfaltspflicht)
```

**Harte KI-Regeln (im System-Prompt jeder Vorlage):**
- Keine erfundenen Fakten, Zahlen, Zitate oder Personen. Nur Inhalte aus den Quelldaten.
- Keine Wertungen über Personen, keine Spekulation über Ursachen (z. B. bei Insolvenzen).
- Verfahrensstadien exakt benennen („vorläufiges Insolvenzverfahren beantragt“, nicht „pleite“).
- Jede Meldung endet mit Quellenangabe und KI-Hinweis.
- **Die KI schreibt niemals Bewertungen**, keine Antworten im Namen von Unternehmen und keine Leserkommentare. Auf den Urteil-Portalen schreibt sie nur Ratgeber, Marktübersichten, Ranking-Texte und als KI gekennzeichnete Zusammenfassungen echter Bewertungen.

### 7.3 Tagesplan: was die Regeln automatisch erzeugen

Ausgelegt auf **eine Person**, die freigibt: ca. **35–50 Freigaben pro Tag**, bei 30–90 Sekunden pro Karte also **45–60 Minuten**, verteilt auf drei Blöcke.

| Zeit | Regel | Portal | Anzahl | Risiko |
|---|---|---|---|---|
| 05:30 | Registerereignisse Vortag → Personalien & Gründungen | KONTORKURIER | 10–15 | 🟢/🟡 |
| 05:45 | Morgen-Briefing (aus gestern freigegebenen Artikeln) | KONTORKURIER | 1 | 🟢 |
| **06:15–06:45** | **Freigabeblock 1** (Telegram) | | | |
| 07:00 | Briefing → Newsletter + Telegram-Kanal | KONTORKURIER | auto | – |
| 09:00 | Pressemitteilungen → Firmennachrichten | KONTORKURIER | 5–8 | 🟢/🟡 |
| 10:00 | Finanzierungsrunden/Deals | KONTORKURIER | 2–4 | 🟢 |
| 11:00 | Insolvenzbekanntmachungen | KONTORKURIER | 2–6 | 🔴 |
| 11:30 | Unternehmer des Tages (Porträt-Entwurf aus Daten + PR, mit Rückfrage-Hinweis) | KONTORKURIER | 1 | 🟡 |
| **12:00–12:20** | **Freigabeblock 2** | | | |
| 14:00 | Ratgeber (aus Themenliste, rotierend) | je 1 Urteil-Portal | 1–2 | 🟢 |
| 15:00 | Neue Bewertungen: KI-Zusammenfassung von Profilen mit ≥ 5 neuen Bewertungen | Urteil-Portale | 2–5 | 🟢 |
| 15:30 | Moderations-Queue: gemeldete Bewertungen (Entscheidung durch dich) | Urteil-Portale | variabel | 🔴 |
| 16:00 | Social-Posts (LinkedIn/Telegram-Kanal) aus freigegebenen Artikeln | alle | 3–5 | 🟢 |
| **17:00–17:20** | **Freigabeblock 3** | | | |

Wöchentliche und monatliche Regeln (Köpfe der Woche, Insolvenz-Report, Deal-Monitor, Rankings, Gründungsatlas) laufen wie in 7.4, ebenfalls mit Freigabekarte.

**Tageslimits** pro Regel verhindern, dass du zugeschüttet wirst. Was nicht freigegeben wird, verfällt nach 24 h (Nachrichten) oder bleibt in der Queue (Ratgeber).

### 7.4 Wochen-, Monats-, Jahresplan

| Rhythmus | KONTORKURIER | Urteil-Portale |
|---|---|---|
| Montag | Köpfe der Woche | – |
| Mittwoch | Deal-Monitor | 1 Ratgeber je Portal |
| Freitag | Insolvenz-Report | Wochen-Highlights (Social) |
| Monatlich | Gründungsatlas, Branchen-Daten-Story | Ranking „Top 10 in [Kategorie]“ (aus Score, transparent) |
| Quartal | Interview-Serie / Themenschwerpunkt | Consumer-Alerts, Moderationszahlen |
| Jährlich | Award „Wachstumschampions“ + Event | Urteil-Award „Kundenliebling 2027“, Transparenzbericht |

### 7.5 Social Media
- **LinkedIn** (Hauptkanal): Personalien mit Verlinkung der Personen, Deals, Rankings. Personen teilen ihre eigenen Meldungen weiter, das bringt kostenlose Reichweite.
- **WhatsApp-Kanal / Telegram:** Morgen-Briefing.
- **Instagram/TikTok:** Kurzvideo „Firma der Woche“, Gründerstorys (Phase 3).
- **X/Bluesky/Threads:** Eilmeldungen automatisiert.

---

## 8. Technik: Betrieb auf dem Raspberry Pi

### 8.1 Grundidee
**Alles läuft auf einem Raspberry Pi bei dir zu Hause.** Damit das stabil, schnell und sicher ist, gelten drei Prinzipien:
1. **Statische Seiten:** Jede Freigabe erzeugt fertige HTML-Dateien. Der Pi muss Besuchern nur Dateien ausliefern, keine Datenbankabfragen pro Aufruf.
2. **Cloudflare davor:** Ein Cloudflare Tunnel verbindet den Pi mit dem Internet. Es braucht keine Portfreigabe am Router, die Heim-IP bleibt verborgen, und Cloudflare liefert die Seiten aus dem Cache. 95 %+ der Aufrufe erreichen den Pi gar nicht. Fällt der Pi aus, bleiben die Seiten aus dem Cache erreichbar.
3. **KI über API:** Texte schreibt ein Cloud-LLM per API. Auf dem Pi laufende Modelle sind für Nachrichtentexte zu schwach und zu langsam. Lokal laufen höchstens kleine Hilfsaufgaben (z. B. Duplikat-Erkennung).

### 8.2 Hardware

| Teil | Empfehlung | ca. Preis |
|---|---|---|
| Rechner | **Raspberry Pi 5, 8 GB** (16 GB bei vielen Portalen) | 90–130 € |
| Speicher | **NVMe-SSD 512 GB–1 TB** über M.2-HAT (keine SD-Karte für Daten, die verschleißt) | 60–100 € |
| Kühlung & Gehäuse | Active Cooler + Gehäuse mit HAT-Platz | 20–30 € |
| Netzteil | Offizielles 27-W-USB-C-Netzteil | 15 € |
| Stromausfall | Kleine USV (oder Pi-UPS-HAT) | 40–80 € |
| Backup | Externe SSD **und** Offsite-Speicher (z. B. Hetzner Storage Box, Backblaze B2) | 0–5 €/Monat |
| Netz | LAN-Kabel statt WLAN | – |

### 8.3 Software-Stack (Docker Compose auf Raspberry Pi OS 64-bit)

```
┌──────────────────────────────── Raspberry Pi 5 ────────────────────────────────┐
│                                                                                │
│  cloudflared ── Tunnel ──▶ Cloudflare (DNS, CDN-Cache, TLS, WAF, Turnstile)   │
│       │                                                                        │
│  Caddy (Webserver) ── liefert /sites/<domain>/ statisch aus                    │
│       │              ── /api/* → Backend (Bewertungsformular, Suche, Newsletter)│
│       │                                                                        │
│  backend (Python, FastAPI)                                                     │
│   ├── rules/        Regel-Engine (YAML) + Scheduler (APScheduler)              │
│   ├── ingest/       Handelsregister, Insolvenzen, PR-Feeds, Bundesanzeiger     │
│   ├── writer/       LLM-Client: Entwurf → Faktencheck → Risikoklasse           │
│   ├── telegram/     Freigabe-Bot (python-telegram-bot) + Kanal-Posting         │
│   ├── builder/      Static-Site-Build (Jinja2-Templates je Portal) + Sitemaps  │
│   ├── reviews/      Bewertungs-API, Verifizierung, Moderation                  │
│   └── admin/        kleines Web-Admin (nur über Cloudflare Access erreichbar)  │
│                                                                                │
│  PostgreSQL (oder SQLite für den Start)    Meilisearch (Suche, optional)       │
│  restic (nächtliches Backup)               Uptime-Check → Alarm per Telegram   │
└────────────────────────────────────────────────────────────────────────────────┘
```

Alle Portale (KONTORKURIER + alle Urteil-Portale) laufen **in derselben Installation**. Der Builder schreibt pro Domain einen eigenen Ordner. Caddy und Cloudflare ordnen die Domains zu.

**Warum selbstgebauter Static-Site-Builder statt Next.js/Payload?** Auf dem Pi ist ein schlanker Python-Builder (Jinja2) robuster und ressourcenschonender. Es gibt keinen dauerhaft laufenden Node-Server, und Rebuilds betreffen nur geänderte Seiten (inkrementell).

### 8.4 Telegram-Freigabe im Detail

**Bot-Sicherheit:**
- Der Bot reagiert nur auf **freigeschaltete Telegram-User-IDs** (Whitelist), alle anderen werden ignoriert und geloggt.
- Bot-Token liegt nur in der `.env` auf dem Pi. Der Bot nutzt Long-Polling, also keinen offenen Port.
- Optional: zweite freigebende Person (z. B. Vertretung im Urlaub) mit eigener Rolle.

**Freigabekarte (Beispiel):**
```
🟡 KONTORKURIER · Köpfe · NRW                     Regel: personalien_nrw
────────────────────────────────────────────────
Neuer Geschäftsführer bei Mustermann Logistik GmbH

Die Mustermann Logistik GmbH aus Köln hat einen neuen Geschäftsführer:
Laut Handelsregister-Eintrag vom 30.10.2026 ist Max Beispiel …
(Vorschau gekürzt, 📄 Volltext-Vorschau: preview.kontorkurier.de/…)

📎 Quellen: HRB 12345, AG Köln, Bekanntmachung 30.10.2026
🔍 Faktencheck: 6/6 Aussagen belegt
🏢 Firma: verknüpft (ID 48213) · 👤 Person: verknüpft
────────────────────────────────────────────────
[✅ Freigeben] [✏️ Ändern] [🔁 Neu] [⏰ Später] [❌ Verwerfen]
```

**Aktionen:**
| Button | Wirkung |
|---|---|
| ✅ Freigeben | Sofort veröffentlichen (oder zum geplanten Zeitpunkt) |
| ✏️ Ändern | Du antwortest mit Text („Titel kürzer, Branche ergänzen“). Die KI überarbeitet, und eine neue Karte kommt |
| 🔁 Neu | Kompletter Neuentwurf |
| ⏰ Später | Zurück in die Queue (+2 h oder nächster Block) |
| ❌ Verwerfen | Mit Grund (Dropdown), damit die Regeln lernen, was du nicht willst |

**Zusätzliche Sicherung bei 🔴 roten Beiträgen:**
- Die Karte zeigt die **Originalquelle als Link** und eine Checkliste: ☐ Quelle geöffnet ☐ Verfahrensstadium korrekt ☐ keine Wertung ☐ Person nur in beruflicher Rolle.
- Freigabe erst nach **zweitem Klick** („Ja, geprüft – veröffentlichen“).
- Rote Beiträge werden **nie gebündelt** freigegeben.

**Bündel-Freigabe** (nur 🟢 grün): „Alle 8 grünen Gründungsmeldungen freigeben?“ mit Liste der Titel. Spart Zeit bei unkritischen Routinemeldungen.

**Weitere Bot-Befehle:**
`/queue` offene Entwürfe · `/heute` Tagesstatistik · `/regeln` Regeln an/aus · `/pause` alles anhalten · `/status` Pi-Zustand (CPU, Speicher, Backup, Tunnel) · `/korrektur <url>` Korrektur an veröffentlichtem Artikel anstoßen · `/meldungen` gemeldete Bewertungen

**Alarme an dich:** Pi offline, Tunnel down, Backup fehlgeschlagen, Quelle liefert nichts mehr, ungewöhnlich viele Bewertungen für eine Firma (Manipulationsverdacht), rechtliche Beschwerde über das Kontaktformular eingegangen.

### 8.5 Regel-Engine (YAML)

Jede Regel ist eine Datei in `rules/`. Neue Formate entstehen ohne Programmierung.

```yaml
# rules/kuk_personalien_nrw.yaml
id: personalien_nrw
portal: kontorkurier
ressort: koepfe
schedule: "30 5 * * 1-6"          # Mo–Sa 05:30
source: handelsregister
filter:
  event_types: [geschaeftsfuehrer_neu, geschaeftsfuehrer_abberufen, vorstand_neu]
  region: [NRW]
  min_company_size: { employees: 20 }   # falls bekannt, sonst Stammkapital ≥ 100.000
  exclude_duplicates_days: 30
limit_per_day: 12
risk: yellow
template: templates/personalie.md.j2
prompt: prompts/personalie.txt
publish:
  sitemap_news: true
  telegram_channel: true
  linkedin: false
expire_after_hours: 24
```

```yaml
# rules/blick_ratgeber_rotation.yaml
id: blick_ratgeber
portal: [agentururteil, softwareurteil, kursurteil]   # rotierend
schedule: "0 14 * * 1-5"
source: topic_list                                   # topics/<portal>.yaml, von dir gepflegt
limit_per_day: 1
risk: green
template: templates/ratgeber.md.j2
prompt: prompts/ratgeber.txt
min_words: 900
require_sources: true
expire_after_hours: never
```

```yaml
# rules/kuk_insolvenzen.yaml
id: insolvenzen
portal: kontorkurier
ressort: insolvenzen
schedule: "0 11 * * 1-5"
source: insolvenzbekanntmachungen
filter:
  region: [NRW]
  only_companies: true          # keine Privatinsolvenzen, niemals
  min_company_size: { employees: 10 }
limit_per_day: 6
risk: red                       # erzwingt Checkliste + Doppelklick
template: templates/insolvenz.md.j2
prompt: prompts/insolvenz.txt
followup:
  watch_status_changes: true    # automatischer Update-Entwurf bei Eröffnung/Aufhebung
  noindex_after_months: 24
```

### 8.6 Datenmodell
Wie bisher (Firma, Person, Rolle, Ereignisse, Artikel, Bewertungen, Meldungen), ergänzt um:

```
rule              id, portal, yaml, enabled, last_run, stats{}
draft             id, rule_id, portal_id, payload{title,teaser,body,tags,image}, sources[],
                  factcheck{supported,unsupported[]}, risk (green|yellow|red),
                  status (queued|sent|changes_requested|approved|rejected|expired),
                  telegram_message_id, created_at, decided_at, decided_by, reject_reason
approval_log      id, draft_id, action, user_id, note, created_at        (unveränderlich)
publication       id, draft_id, article_id, url, published_at, channels[]
```

Kerntabellen (Kurzform): `portal`, `company`, `company_alias`, `company_financials`, `person`, `person_role`, `register_event`, `insolvency_event`, `article`, `article_entity`, `correction`, `review_profile`, `review`, `review_reply`, `report`, `customer`, `invitation`.

### 8.7 Was der Pi leisten muss und warum es reicht

| Last | Einschätzung |
|---|---|
| Seitenaufrufe | Werden fast vollständig vom Cloudflare-Cache bedient. Der Pi liefert nur Cache-Misses. |
| Builds | Inkrementell: 1 Freigabe → Artikel + Ressort- und Startseite + Firmen-/Personenseite neu, also Sekunden |
| KI | Läuft extern per API. Der Pi wartet nur auf Antworten. |
| Ingest | Ein paar tausend Datensätze pro Tag, für einen Pi 5 trivial |
| Datenbank | Bis zu Millionen Zeilen sind mit PostgreSQL auf NVMe problemlos |
| Bewertungsformular / Suche | Dynamisch, aber geringes Volumen. Turnstile filtert Bots vor dem Pi. |

**Wann der Pi nicht mehr reicht:** bei dauerhaft > 1–2 Mio. Seitenaufrufen/Monat **mit** viel dynamischem Anteil, bei mehreren Mitarbeitern im Admin oder wenn Ausfälle Umsatz kosten. Dann zieht dieselbe Docker-Compose-Installation unverändert auf einen kleinen Cloud-Server um (z. B. Hetzner, ca. 5–15 €/Monat).

### 8.8 Betrieb & Sicherheit
- **Updates:** unattended-upgrades für das OS, Container-Updates wöchentlich nach Freigabe per Telegram.
- **Backups:** nächtlich DB-Dump + Medien mit restic auf externe SSD **und** offsite. Wöchentlicher automatischer Wiederherstellungstest, Ergebnis per Telegram.
- **Zugänge:** SSH nur mit Schlüssel, nur im Heimnetz oder über Cloudflare Access/Tailscale. Admin-Oberfläche nur hinter Cloudflare Access.
- **Secrets:** `.env` mit API-Keys (LLM, Telegram, Datenanbieter), nicht im Git-Repository.
- **Überwachung:** Healthchecks (z. B. healthchecks.io oder Uptime Kuma) mit Alarm an Telegram.
- **Stromausfall/Internetausfall:** USV überbrückt kurze Ausfälle. Cloudflare „Always Online“/Cache hält Seiten erreichbar. Die Regeln holen verpasste Läufe nach.
- **Internetvertrag prüfen:** Manche private Anschlüsse untersagen gewerblichen Serverbetrieb. Bei Bedarf einen Geschäftskundentarif nutzen. Durch den Tunnel ist keine feste IP nötig.
- **Impressum:** Braucht eine ladungsfähige Anschrift. Wenn du nicht deine Wohnadresse veröffentlichen willst, eine Geschäftsadresse nutzen (kein Postfach). Der Serverstandort ist dafür egal.

### 8.9 SEO-Grundlagen
- schema.org: `NewsArticle`, `Organization`/`LocalBusiness`, `Person`, `AggregateRating`, `Review`, `BreadcrumbList`.
- Google-News-Sitemap (Artikel der letzten 48 h), XML-Sitemaps je Portal, beim Build erzeugt.
- Saubere URLs: `/unternehmen/mustermann-gmbh-koeln`, `/koepfe/max-mustermann`, `/insolvenzen/2026/11/…`
- Autorenseite des Herausgebers, Redaktionsgrundsätze inklusive offener Beschreibung des KI-Workflows, Korrekturspalte.
- Kein „Thin Content“: automatisch angelegte Firmenseiten erst indexieren, wenn genug Substanz da ist (≥ 1 Artikel oder ≥ 3 Registerereignisse oder ≥ 1 Bewertung).
- **Google und KI-Texte:** Erlaubt, solange sie hilfreich und geprüft sind. Massenhaft erzeugte Seiten ohne Mehrwert werden als „scaled content abuse“ abgestraft. Die Tageslimits und die Freigabepflicht sind deshalb auch SEO-Schutz.

---

## 9. Reichweite & Distribution

| Kanal | Bedeutung | Maßnahme |
|---|---|---|
| **Google Suche** | Firmen- & Personensuchen („[Firma] Insolvenz“, „[Firma] Geschäftsführer“) | Firmen-/Personenseiten, schnelle Meldungen |
| **Google Discover / News** | Größter Hebel für Nachrichten | Publisher Center, starke Bilder ≥1200 px, klare Überschriften |
| **MSN Start (Microsoft Start)** | Direkter Weg auf eine Browser-Startseite | Bewerbung im **MSN Partner Hub** als Content-Partner (ab stabiler Qualität/Frequenz) |
| **t-online / web.de / GMX** | Startseiten mit hoher Reichweite | Content-Partnerschaft anfragen (Phase 3, mit Reichweitennachweis) |
| **LinkedIn** | B2B-Kern | Personen markieren, Teilen durch Betroffene |
| **Newsletter** | Eigener, unabhängiger Kanal | Morgen-Briefing, regionale Ausgaben |
| **Kooperationen** | IHKs, Wirtschaftsförderungen, Gründerzentren, Verbände | Datenpartnerschaften, Award-Partner |
| **Widgets/Siegel** | Backlinks & Markenbekanntheit | Urteil-Siegel auf Kunden-Websites |

---

## 10. Geschäftsmodell & Preise

### 10.1 Erlösquellen

| Quelle | Portal | Ab Phase |
|---|---|---|
| Display & Programmatic Ads | alle | 1 |
| Native-Ad-Widgets (Taboola/Outbrain als *Publisher*) | KONTORKURIER | 2 |
| Newsletter-Sponsoring | KONTORKURIER | 2 |
| Urteil-Pakete (Einladungen, Widgets, Analytics) | Urteil-Portale | 2 |
| Netzwerk-Premiumprofil | alle | 2 |
| Gekennzeichnete Partnerinhalte („Anzeige“) | KONTORKURIER | 2 |
| Stellenmarkt | KONTORKURIER | 3 |
| Leads (Anfrageformular „3 Angebote erhalten“) | Solarurteil, Umzugsurteil, Agentururteil | 3 |
| Awards & Events | alle | 3 |
| Daten-Abo (Alerts zu Insolvenzen und Personalwechseln, API) | KONTORKURIER | 3 |

### 10.2 Preis-Entwurf Urteil-Portale (monatlich, netto)

| Paket | Preis | Leistungen |
|---|---|---|
| **Basis** | 0 € | Profil beanspruchen, Daten pflegen, auf Bewertungen antworten |
| **Starter** | 49 € | Einladungen (100/Monat), Widget, Siegel, Basis-Statistik |
| **Pro** | 149 € | Einladungen unbegrenzt, API/Integrationen, Wettbewerbsvergleich, Logo & Bilder |
| **Netzwerk** | 299 € | Pro + Premium-Firmenprofil auf KONTORKURIER + Stellenanzeigen + Newsroom |

Gekennzeichnete Partnerinhalte KONTORKURIER: 490–1.490 € je Beitrag (Unternehmensporträt, Fachbeitrag), immer mit „Anzeige“ markiert.

### 10.3 Beispielrechnung (Ende Jahr 2, konservativ)

| Posten | Annahme | Monat |
|---|---|---|
| Ads (alle Portale) | 1,2 Mio. Seitenaufrufe × 8 € RPM | ~9.600 € |
| Urteil-Pakete | 150 zahlende Firmen × Ø 110 € | ~16.500 € |
| Partnerinhalte | 8 Beiträge × 800 € | ~6.400 € |
| Newsletter-Sponsoring | 4 Wochen × 600 € | ~2.400 € |
| **Summe** | | **~35.000 €/Monat** |

*Annahmen, keine Prognose. Realistisch zu validieren nach Phase 1.*

---

## 11. Recht & Compliance

### 11.1 Pflichten Nachrichtenportal
- **Impressum** (§ 5 DDG) + **Verantwortlicher nach § 18 Abs. 2 MStV** (natürliche Person mit Anschrift).
- **Journalistische Sorgfaltspflicht** (§ 19 MStV): Wahrheit, Inhalt, Herkunft prüfen.
- **Trennungsgebot:** Werbung klar als „Anzeige“ kennzeichnen. Partnerinhalte optisch abgesetzt, nicht in redaktionellen Rankings.
- **Verdachtsberichterstattung:** Mindestbestand an Beweistatsachen, Anhörung des Betroffenen vor Veröffentlichung, ausgewogene Darstellung, keine Vorverurteilung.
- **Insolvenzen:** Nur nach amtlicher Bekanntmachung, Verfahrensstadium korrekt benennen. Updates bei Aufhebung oder Einstellung. Ältere Meldungen nach angemessener Zeit auf „noindex“ setzen bzw. aktualisieren (Recht auf Vergessenwerden).
- **Urheberrecht / Leistungsschutzrecht:** Keine fremden Artikel übernehmen oder umschreiben. Pressemitteilungen nur als Grundlage für eigene Texte nutzen, Bilder nur mit Lizenz.
- **Gegendarstellung & Korrekturen:** Prozess und öffentliche Korrekturspalte.
- **Freiwillig, aber vertrauensbildend:** Bekenntnis zum Pressekodex des Deutschen Presserats.

### 11.2 Pflichten Bewertungsportale
- **§ 5b Abs. 3 UWG:** Hinweis, ob und wie die Echtheit von Bewertungen geprüft wird (Seite „So funktionieren Bewertungen“).
- **UWG Anhang Nr. 23b/23c:** Keine gefälschten, gekauften oder selektiv unterdrückten Bewertungen. Gilt auch für den Betreiber selbst.
- **DSA:** Meldeverfahren, begründete Moderationsentscheidungen, Kontaktstelle, Transparenzbericht.
- **BGH-Prüfpflichten** (Hotelbewertung, Ärztebewertung): Auf Beanstandung hin Nachweise beim Bewertenden anfordern, Stellungnahmen weiterleiten.
- **Keine Vorteile für zahlende Kunden** bei Score oder Sortierung (BGH Jameda 2018). Bezahlte Platzierungen sind sichtbar als „Anzeige“ gekennzeichnet.
- **Incentives offenlegen:** Wenn Unternehmen für Bewertungen Gutscheine o. Ä. bieten, wird das gekennzeichnet bzw. untersagt.

### 11.3 Datenschutz (DSGVO)
- Medienprivileg (Art. 85 DSGVO i. V. m. Landespresse-/Mediengesetzen) für redaktionelle Inhalte.
- Personenseiten nur mit beruflicher Rolle. Löschkonzept für Personen ohne aktuelle Funktion.
- Bewertungseinladungen: AV-Vertrag mit einladenden Unternehmen. Empfängerdaten nach Versand hashen bzw. löschen.
- Beleg-Uploads nach Prüfung löschen, nur Prüfergebnis speichern.
- Consent-Management für Ads/Tracking.

### 11.4 Netzwerk-Transparenz
- Alle Portale nennen **Merkant Medien GmbH** als Betreiber.
- Seite „Unser Netzwerk“ auf jedem Portal.
- Querverweise zwischen den Portalen als „Schwesterportal“ kennzeichnen.

### 11.5 Absolute No-Gos (in Redaktionsstatut & Kundenverträgen)
- ❌ Löschung oder Abschwächung von Artikeln/Bewertungen gegen Bezahlung
- ❌ Ungekennzeichnete bezahlte Artikel („bekannt aus …“-Verkauf)
- ❌ Eigene oder gekaufte Bewertungen, auch nicht zum „Anschieben“
- ❌ Nachahmung anderer Medienmarken in Werbung oder Design
- ❌ Ungeprüfte KI-Texte
- ❌ Bewertung von Unternehmen, an denen Betreiber oder Mitarbeiter beteiligt sind, ohne Offenlegung

### 11.6 Absicherung
- Medienhaftpflicht- bzw. Vermögensschadenhaftpflichtversicherung
- Anwalt für Presse- & Wettbewerbsrecht (Retainer)
- Rechtliche Prüfung vor Start: AGB, Nutzungsbedingungen, Bewertungsrichtlinien, Redaktionsstatut, Kundenverträge

---

## 12. Organisation & Team

Durch den Workflow aus KI-Entwurf und Telegram-Freigabe kann der Start **als Ein-Personen-Betrieb** laufen.

| Phase | Rollen | Aufwand |
|---|---|---|
| **1 (Monat 0–6)** | **Du:** Herausgeber, Verantwortlicher nach MStV, Freigabe per Telegram (ca. 1 h/Tag), Regeln & Themenlisten pflegen · Entwicklung des Systems (Eigenleistung mit KI-Unterstützung oder Freelancer) · Anwalt (Projekt) | ~1–1,5 h/Tag + Aufbau |
| **2 (Monat 7–18)** | + freier Redakteur für Porträts, Interviews und Recherchen (das kann die KI nicht) · + Vertretung für Freigaben (Urlaub/Krankheit) · + Vertrieb in Teilzeit | ~2–3 Personen |
| **3 (ab Monat 19)** | + Regionalredakteure · + Moderation Urteil-Portale · Umzug auf Cloud-Server prüfen | 4+ Personen |

**Grenzen der Automatisierung (bewusst menschlich):** Interviews, Anhörung Betroffener bei kritischen Berichten, Gegendarstellungen, Moderationsentscheidungen, Kundengespräche, Korrekturen.

**Trennung Redaktion und Vertrieb:** Auch als Einzelperson gilt die Firewall-Regel. Bezahlte Inhalte laufen über eine eigene Regel mit Pflichtkennzeichnung „Anzeige“ und tauchen nie in redaktionellen Rankings auf.

---

## 13. Kosten (grobe Schätzung, Phase 1)

| Posten | Einmalig | Monatlich |
|---|---|---|
| Raspberry Pi 5 + NVMe + Kühlung + Netzteil + USV | 230–350 € | – |
| Strom Pi (~5–8 W Dauerbetrieb) | – | ~2–3 € |
| Cloudflare (Tunnel, CDN, DNS, Turnstile, Access) | – | 0 € (Free-Plan reicht anfangs) |
| Domains (ca. 8–12 Stück .de/.com) | – | ~10–15 € (≈ 1–1,5 €/Domain) |
| Offsite-Backup | – | 0–5 € |
| LLM-API (Entwurf + Faktencheck, ~50 Texte/Tag) | – | ca. 30–200 € je nach Modell und Textlänge |
| Datenquellen (Register-/Firmendaten-API) | – | 0–1.500 € (Start mit öffentlichen Bekanntmachungen möglich, Komfort-APIs kosten) |
| Newsletter-Versand | – | 0–50 € |
| Entwicklung | Eigenleistung bzw. 5.000–20.000 € Freelancer | – |
| Recht (Setup + Retainer) | 5.000–10.000 € | 300–800 € |
| Versicherung (Medienhaftpflicht) | – | 100–250 € |
| Markenanmeldung | 300–3.000 € | – |
| **Summe Phase 1** | **~5.500–33.000 €** | **~450–2.800 €** |

*Spannen sind Erfahrungswerte, keine Angebote. Größter Hebel: Eigenleistung bei der Entwicklung und Start mit kostenlosen öffentlichen Datenquellen.*

---

## 14. Roadmap

### Phase 0: Fundament (Monat 0–1)
- [ ] Namen final prüfen (DPMA, Domains, Handles), Domains sichern
- [ ] Gesellschaft gründen bzw. Betreiber festlegen, Verantwortlicher MStV benennen
- [ ] **Domainprüfung** aller Namen (DENIC/Verisign) und Namen final festlegen
- [ ] Raspberry Pi 5 + NVMe + USV beschaffen, Raspberry Pi OS 64-bit, Docker, Cloudflare Tunnel
- [ ] Eigenes Repository anlegen: Docker Compose, Backend, Regel-Engine, Telegram-Bot, Static-Site-Builder
- [ ] Telegram-Bot anlegen (BotFather), Whitelist mit deiner User-ID
- [ ] Datenquellen auswählen und Testzugang einrichten
- [ ] Anwalt: Redaktionsstatut, Bewertungsrichtlinien, AGB, Datenschutz

### Phase 1: MVP (Monat 2–6)
- [ ] **KONTORKURIER** live für **1 Region** (z. B. NRW): Unternehmen, Köpfe, Insolvenzen, Gründungen
- [ ] Regeln: Personalien, Gründungen, Pressemitteilungen, Insolvenzen (NRW) → KI-Entwurf → Telegram-Freigabe
- [ ] Faktencheck-Durchlauf und Risikoklassen aktiv, Audit-Log
- [ ] Backups (lokal + offsite) mit Wiederherstellungstest, Alarme per Telegram
- [ ] Firmen- & Personenseiten (mit Indexierungsschwelle)
- [ ] Morgen-Briefing (Newsletter)
- [ ] **Agentururteil** live: 1.000 Profile, Einladungs-Tool, Verifizierung, Transparenzseiten
- [ ] Google Publisher Center, Search Console, LinkedIn-Präsenz
- **Ziel:** 15–25 Beiträge/Tag, 50.000 Seitenaufrufe/Monat, 1.000 Newsletter-Abonnenten, 50 beanspruchte Profile

### Phase 2: Wachstum (Monat 7–18)
- [ ] KONTORKURIER bundesweit, Regionalfilter für alle Bundesländer
- [ ] **Softwareurteil** + **Kursurteil** live
- [ ] Bezahlpakete, Premiumprofile, Partnerinhalte, Ads
- [ ] Bewerbung MSN Partner Hub
- [ ] Erster Transparenzbericht, erstes Ranking
- [ ] Prüfen: Umzug vom Pi auf Cloud-Server, sobald Last oder Ausfallrisiko es erfordern
- **Ziel:** 300.000–1 Mio. Seitenaufrufe/Monat, 100+ zahlende Kunden, Break-even der laufenden Kosten

### Phase 3: Skalierung (ab Monat 19)
- [ ] **Solarurteil** + **Umzugsurteil** (mit Lead-Modell)
- [ ] Awards „Wachstumschampions“ & „Kundenliebling“ + Event
- [ ] Daten-Abo/API, Stellenmarkt, Podcast
- [ ] Content-Partnerschaften mit Startseiten-Portalen
- [ ] Prüfen: Coachurteil / Betreuungsurteil (mit Presserechtsbegleitung)

---

## 15. KPIs

| Bereich | KPI |
|---|---|
| Reichweite | Seitenaufrufe, Unique Users, Anteil Discover/News/Suche/Direkt |
| Redaktion | Beiträge/Tag, Zeit bis Veröffentlichung (Registerereignis → Artikel), Korrekturquote |
| KI-Workflow | Freigabequote je Regel, Anteil „Ändern“/„Verwerfen“, nicht belegte Aussagen im Faktencheck, Freigabezeit/Tag |
| Betrieb | Verfügbarkeit, Cache-Trefferquote Cloudflare, Backup-Erfolg |
| Bindung | Newsletter-Abonnenten, Öffnungsrate (Ziel > 40 %), wiederkehrende Leser |
| Bewertungen | Neue Bewertungen/Tag, Anteil verifiziert, beanspruchte Profile, Antwortquote der Firmen |
| Vertrauen | Gemeldete/entfernte Bewertungen, Abmahnungen/Beschwerden, Gegendarstellungen |
| Umsatz | RPM, zahlende Kunden, MRR, Churn, Umsatz pro Firma im Netzwerk |

---

## 16. Risiken & Gegenmaßnahmen

| Risiko | Wahrscheinlichkeit | Auswirkung | Gegenmaßnahme |
|---|---|---|---|
| Abmahnungen/Klagen wegen negativer Berichte oder Bewertungen | hoch | hoch | Vier-Augen-Prinzip, Checklisten, Anwalt, Versicherung, sauberes Meldeverfahren |
| Google wertet automatisierte Inhalte ab | mittel | hoch | Menschliche Prüfung, eigener Mehrwert, Indexierungsschwellen, keine Massen-Seiten ohne Substanz |
| Glaubwürdigkeitsverlust durch Vermischung von Vertrieb und Redaktion | mittel | sehr hoch | Firewall-Regel, Statut, transparente Kennzeichnung |
| Kaltstart: zu wenige Bewertungen | hoch | mittel | Einladungs-Tool kostenlos, Fokus auf 1 Nische, Redaktion als Zugpferd |
| Kosten der Datenquellen steigen | mittel | mittel | Mehrere Anbieter, eigene Verarbeitung öffentlicher Bekanntmachungen |
| Werbeerlöse schwanken | hoch | mittel | Erlösmix: SaaS-Pakete als stabile Basis |
| Abhängigkeit von Google/MSN | mittel | hoch | Newsletter und LinkedIn als eigene Kanäle |
| Datenschutzbeschwerden (Personenseiten) | mittel | mittel | Nur berufliche Rolle, Löschkonzept, schnelle Bearbeitung |
| KI-Fehler (falsche Fakten, Halluzination) | mittel | hoch | Nur Quelldaten als Input, Faktencheck-Durchlauf, Risikoklassen, Doppelklick bei 🔴, Korrekturprozess |
| „Durchwinken“ aus Routine | hoch | hoch | Tageslimits, rote Beiträge nie gebündelt, Checkliste, Freigabezeiten sichtbar im Audit-Log |
| Pi-Ausfall (Hardware, Strom, Internet) | mittel | mittel | Cloudflare-Cache, USV, NVMe statt SD, tägliche Offsite-Backups, Umzugsplan auf Cloud-Server |
| Verlust/Kompromittierung des Telegram-Kontos | gering | hoch | 2FA in Telegram, Whitelist, `/pause`-Befehl, Freigaben nur von registrierten IDs |

---

## 17. Nächste Schritte

1. **Domainprüfung freischalten** (Hosts `rdap.denic.de`, `rdap.verisign.com`, `rdap.org` in den Netzwerkeinstellungen der Umgebung erlauben), dann **Namen festlegen:** Favoriten MERKANT Medien · KONTORKURIER · Agentururteil bestätigen oder Alternativen wählen. Danach Marken- und Domainprüfung.
2. **Startregion für KONTORKURIER** wählen (Vorschlag: NRW, größter Wirtschaftsraum mit vielen Registerereignissen).
3. **Eigenes Repository** anlegen und mit Claude verbinden. Dann folgt das technische Grundgerüst für den Pi:
   Docker Compose (Caddy, cloudflared, Backend, PostgreSQL), Regel-Engine mit den drei Beispielregeln aus 8.5, Telegram-Freigabe-Bot, Static-Site-Builder für KONTORKURIER und Agentururteil.
4. **Rechtliches Paket** beim Anwalt beauftragen (Abschnitt 11).
5. **Datenanbieter** vergleichen und Testzugang einrichten.

---

*Begleitdokument: `docs/reputationsportale-analyse.md` (Analyse, wie Reputationsportale aufgebaut sind).*
