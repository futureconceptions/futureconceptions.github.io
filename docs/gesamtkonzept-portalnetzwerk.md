# Gesamtkonzept: Portalnetzwerk für Wirtschaftsnachrichten & Bewertungen

**Arbeitstitel:** BLICKWERK Medien · **Stand:** November 2026 · **Status:** Konzept v1
**Hinweis:** Eigenständiges Projekt, organisatorisch und rechtlich getrennt von ClipFarm Studio. Dieses Dokument gehört langfristig in ein eigenes Repository.

---

## Inhalt

1. Vision & Kernidee
2. Markennamen (Netzwerk, Nachrichtenportal, Bewertungsportale)
3. Netzwerk-Architektur
4. Leitportal: KOPF & KONTOR (Wirtschaftsnachrichten)
5. Bewertungsportale (Blick-Familie)
6. Wie Nachrichten und Bewertungen zusammenspielen
7. Content-Engine: Quellen, Workflow, Tagesplan
8. Technik: Plattform, Datenmodell, Infrastruktur
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

**Grundprinzip, auf dem das ganze Geschäft beruht:** Glaubwürdigkeit. Redaktion und Bewertungen sind nicht käuflich. Bezahlte Inhalte sind immer gekennzeichnet. Der gemeinsame Betreiber wird offen genannt. Das ist keine Pflichtübung, sondern das Produkt: Ohne Unabhängigkeit gibt es keine Reichweite bei Google und keine Leser.

---

## 2. Markennamen

> Alle Namen sind Vorschläge. Vor der Festlegung prüfen: DPMA-/EUIPO-Markenrecherche, Verfügbarkeit von .de-Domain und Social-Handles, Verwechslungsgefahr mit bestehenden Medien.

### 2.1 Dachmarke / Betreiber

| Vorschlag | Idee |
|---|---|
| **BLICKWERK Medien** (Favorit) | Verbindet die „Blick“-Bewertungsportale mit „Werk“ (Handwerk, Mittelstand) |
| Kontorhaus Medien | Hanseatisch, seriös, Kaufmannstradition |
| Mittelweg Media | Mittelstand + Orientierung |

Rechtsform: GmbH oder UG (haftungsbeschränkt), Name z. B. „Blickwerk Medien GmbH“. Erscheint im Impressum aller Portale.

### 2.2 Nachrichtenportal

| Vorschlag | Claim | Bewertung |
|---|---|---|
| **KOPF & KONTOR** (Favorit) | *Nachrichten über Unternehmen und die Menschen dahinter* | Einprägsam, deckt „Köpfe“ und „Unternehmen“ ab, klingt nach Qualitätsmedium |
| Firmenkurier | *Was Deutschlands Unternehmen bewegt* | Klar, aber generisch |
| Chefetage | *Wirtschaft aus der ersten Reihe* | Stark für Personalien, schwächer für Insolvenzen |
| Mittelstandsblick | *Der Mittelstand im Fokus* | Passt zur Blick-Familie, wirkt aber weniger eigenständig |

Domains (zu prüfen): `kopfundkontor.de`, `kopf-kontor.de`, `kuk-news.de`

Regionale Ableger als Unterbereiche, keine eigenen Marken:
`kopfundkontor.de/nrw`, `/bayern`, `/rhein-main`, `/berlin` …

### 2.3 Bewertungsportale („Blick“-Familie)

Einheitliches Namensschema: sofort als Netzwerk erkennbar, ehrlich und skalierbar.

| Portal | Nische | Claim |
|---|---|---|
| **Agenturblick** | Marketing-, Social-Media-, Video- & Content-Agenturen | *Die richtige Agentur. Echte Erfahrungen.* |
| **Softwareblick** | Software-Dienstleister, Web-Agenturen, IT-Partner für KMU | *IT-Partner im Kundenurteil* |
| **Kursblick** | Bootcamps, Weiterbildungsträger, Bildungsgutschein-Anbieter | *Weiterbildung, die hält, was sie verspricht* |
| **Solarblick** | Solar-, Speicher- & Wärmepumpen-Installateure | *Installateure im Erfahrungscheck* |
| **Umzugsblick** | Umzugs- & Entrümpelungsfirmen | *Seriöse Umzugsfirmen finden* |
| *später:* Coachblick | Online-Coaches & Kursanbieter | (erst mit Presserechts-Begleitung) |
| *später:* Betreuungsblick | 24h-Betreuungs- & Pflegevermittlungen | (sensibel, eigene Redaktion) |

Bewusst vermieden: „Test“ oder „Check“ im Namen. Das suggeriert eigene Warentests à la Stiftung Warentest und wäre ohne echte Tests irreführend.

---

## 3. Netzwerk-Architektur

```
                         BLICKWERK Medien GmbH (Betreiber, offen genannt)
                                        │
              ┌─────────────────────────┴─────────────────────────┐
              │                                                   │
      KOPF & KONTOR                                     Blick-Bewertungsportale
   (Wirtschaftsnachrichten)                    Agenturblick · Softwareblick · Kursblick
              │                                     Solarblick · Umzugsblick
              │                                                   │
              └──────────────┬────────────────────────────────────┘
                             │
            ┌────────────────┴─────────────────────┐
            │      GEMEINSAME PLATTFORM (1 Code)    │
            │  • Firmen- & Personendatenbank        │
            │  • CMS / Redaktionssystem             │
            │  • Bewertungs-Engine & Verifizierung  │
            │  • Moderation, Meldeverfahren (DSA)   │
            │  • Daten-Pipelines (Register, PR)     │
            │  • Ads, Newsletter, Accounts, Billing │
            └───────────────────────────────────────┘
```

**Prinzip „ein Kern, viele Oberflächen“:** Ein neues Portal entsteht durch Konfiguration (Domain, Branding, Kategorien, Bewertungskriterien, Redaktionsressorts), nicht durch neue Software.

**Verknüpfung über die Firmen-ID:** Jedes Unternehmen existiert genau einmal in der Datenbank. Es kann:
- in Artikeln von KOPF & KONTOR vorkommen,
- ein Bewertungsprofil auf einem oder mehreren Blick-Portalen haben,
- ein Premium-Profil gebucht haben (gilt netzwerkweit).

---

## 4. Leitportal: KOPF & KONTOR

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
├── Box „Erfahrungen mit diesem Unternehmen“ → Link zum Blick-Portal (falls vorhanden)
└── Mehr zum Thema / Newsletter / Anzeigen

Firmenseite  /unternehmen/<slug>
├── Stammdaten: Name, Rechtsform, Sitz, Register, Gründung, Branche, Website
├── Geschäftsführung / Vorstand (aktuell + Historie)
├── Kennzahlen aus Bundesanzeiger (Umsatz, Mitarbeiter, Bilanzsumme, sofern veröffentlicht)
├── Zeitleiste: alle Registerereignisse und Artikel
├── Bewertungsscore aus Blick-Portal (falls vorhanden)
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
| **KOPF & KONTOR Podcast** | Gespräch mit einem Unternehmer | 14-täglich (Phase 3) |

---

## 5. Bewertungsportale (Blick-Familie)

### 5.1 Gemeinsamer Aufbau (alle Blick-Portale)

```
Startseite: Suche (Firma / Leistung / Ort) + Top-Kategorien + neueste Bewertungen
Kategorie- & Stadtseiten: /social-media-agentur/koeln  (programmatic SEO)
Firmenprofil: /firma/<slug>
  ├── Score, Anzahl, Verteilung 1–5★, Teilkriterien
  ├── Badges: „Profil beansprucht“, „lädt aktiv ein“, „antwortet meist in X Tagen“
  ├── KI-Zusammenfassung der Bewertungen (als KI-generiert gekennzeichnet)
  ├── Bewertungsliste mit Herkunfts-Label (verifiziert / eingeladen / organisch)
  ├── Antworten des Unternehmens
  ├── Box „Aktuelle Nachrichten“ → KOPF & KONTOR
  └── Stammdaten aus gemeinsamer Firmendatenbank
Bewertung schreiben (mit Verifizierung)
Für Unternehmen: Profil beanspruchen, Pakete, Widgets, Einladungs-API
Transparenz: So funktionieren Bewertungen · Score-Methodik · Richtlinien · Transparenzbericht · Melden
```

### 5.2 Nischenspezifische Bewertungskriterien

| Portal | Teilkriterien (je 1–5★) | Zusatzfelder |
|---|---|---|
| **Agenturblick** | Ergebnisse, Kommunikation, Kreativität, Termintreue, Preis-Leistung | Leistung (Social, Video, SEO, Ads …), Projektbudget-Spanne, Laufzeit |
| **Softwareblick** | Qualität, Projektmanagement, Termintreue, Support, Preis-Leistung | Technologie, Projektart, Budget-Spanne |
| **Kursblick** | Inhalte, Dozenten, Organisation, Jobchancen, Betreuung | Kurs, Förderung (Bildungsgutschein ja/nein), Abschluss, Job nach Kurs |
| **Solarblick** | Beratung, Montage, Termintreue, Service nach dem Kauf, Preis-Leistung | Anlagengröße, Komponenten, Monate seit Inbetriebnahme |
| **Umzugsblick** | Pünktlichkeit, Sorgfalt, Freundlichkeit, Preistreue, Preis-Leistung | Umzugsart, Entfernung, Angebot vs. Endpreis |

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
1. 500–2.000 Profile aus öffentlichen Daten anlegen (Register, Websites, Branchenverzeichnisse, AZAV-Datenbank für Kursblick, Marktstammdatenregister für Solarblick).
2. Unternehmen anschreiben: „Ihr Profil ist online. Beanspruchen Sie es kostenlos und laden Sie Kunden ein.“
3. Kostenloses Einladungs-Tool (CSV-Upload, Zapier, Shop-/CRM-Plugins) für die ersten 6 Monate.
4. Redaktionelle Ratgeber und Marktübersichten als SEO-Fundament.
5. Launch-Datenstudie mit PR über KOPF & KONTOR (offen als Schwesterportal gekennzeichnet).

---

## 6. Wie Nachrichten und Bewertungen zusammenspielen

| Verbindung | Nutzen | Regel |
|---|---|---|
| Artikel → Bewertungsprofil | Leser sehen Kundenerfahrungen | Link-Box „Erfahrungen auf Agenturblick“ mit Hinweis „Schwesterportal“ |
| Bewertungsprofil → Artikel | Besucher sehen aktuelle Nachrichten zur Firma | Automatisch über Firmen-ID |
| Gemeinsame Firmendatenbank | Einmal pflegen, überall nutzen | Datenquelle angeben |
| Datenstudien aus Bewertungen | Exklusive Geschichten für KOPF & KONTOR | Methodik offenlegen |
| Netzwerk-Premiumprofil | Höherer Umsatz pro Kunde | Kein Einfluss auf Redaktion oder Score |

**Firewall-Regel:** Die Redaktion von KOPF & KONTOR entscheidet unabhängig vom Vertrieb. Kein Kunde kauft Berichterstattung, Löschungen oder bessere Bewertungen. Die Regel steht in den Redaktionsgrundsätzen und in jedem Kundenvertrag.

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
| Marktstammdatenregister | Solar-Installationen (für Solarblick) | öffentlich |
| AZAV-/Kursnet-Daten | Bildungsträger (für Kursblick) | öffentlich |
| Eigene Recherche, Interviews, Leser-Hinweise | Exklusives, Porträts | Redaktion, Hinweisgeber-Formular |

### 7.2 Workflow („Human in the Loop“)

```
[1] Ingest        Pipelines ziehen alle 15–60 min neue Registerdaten, Insolvenzen, Pressemitteilungen
      ↓
[2] Matching      Zuordnung zu Firma/Person in der Datenbank (Register-Nr., Name, Sitz)
      ↓
[3] Relevanz      Scoring: Größe der Firma, Region, Branche, Neuigkeitswert → Schwellenwert
      ↓
[4] Entwurf       KI erzeugt Meldung + Überschrift + Teaser aus strukturierten Daten
                  (nur aus der Quelle, keine erfundenen Fakten, Quellenangabe Pflicht)
      ↓
[5] Redaktion     Redakteur prüft, ergänzt Kontext, ruft ggf. an, gibt frei
                  (negative Meldungen: Vier-Augen-Prinzip + Checkliste Verdachtsberichterstattung)
      ↓
[6] Publish       Website, Newsletter-Queue, Social, Google-News-Sitemap, MSN-Feed
      ↓
[7] Pflege        Updates (z. B. Insolvenzverfahren eröffnet → aufgehoben), Korrekturspalte
```

KI-Kennzeichnung: Im Fuß jedes Artikels steht ein Hinweis wie *„Erstellt mit Unterstützung automatisierter Datenauswertung, redaktionell geprüft von [Name].“*

### 7.3 Tagesplan KOPF & KONTOR (Phase 2, 2–3 Redakteure)

| Uhrzeit | Aufgabe | Output |
|---|---|---|
| 05:30 | Nachtschicht-Queue prüfen (Register-Bekanntmachungen vom Vortag) | 10–15 Entwürfe |
| 06:30 | **Morgen-Briefing** raus (Newsletter + Artikel) | 1 |
| 07:00–09:00 | Personalien & Firmennachrichten freigeben | 8–12 Meldungen |
| 09:00 | Redaktionskonferenz (15 min): Aufmacher, Recherchen | – |
| 09:00–12:00 | Pressemitteilungen auswerten, 1 Hintergrundstück | 5–8 Meldungen |
| 12:00 | **Unternehmer des Tages** | 1 Porträt |
| 13:00–16:00 | Insolvenzen (Vier-Augen), Finanzierungsrunden, Regionales | 5–10 Meldungen |
| 16:00 | Ratgeber / Evergreen-Stück | 1 |
| 17:00 | Social-Posts (LinkedIn-Fokus), Aufmacher für Abend | 3–5 Posts |
| 18:00 | Tagesabschluss, Queue für morgen planen | – |
| **Summe** | | **25–40 Beiträge/Tag** |

### 7.4 Wochen-, Monats-, Jahresplan

| Rhythmus | KOPF & KONTOR | Blick-Portale |
|---|---|---|
| Montag | Köpfe der Woche | – |
| Mittwoch | Deal-Monitor | 1 Ratgeber je Portal |
| Freitag | Insolvenz-Report | Wochen-Highlights (Social) |
| Monatlich | Gründungsatlas, Branchen-Daten-Story | Ranking „Top 10 in [Kategorie]“ (aus Score, transparent) |
| Quartal | Interview-Serie / Themenschwerpunkt | Consumer-Alerts, Moderationszahlen |
| Jährlich | Award „Wachstumschampions“ + Event | Blick-Award „Kundenliebling 2027“, Transparenzbericht |

### 7.5 Social Media
- **LinkedIn** (Hauptkanal): Personalien mit Verlinkung der Personen, Deals, Rankings. Personen teilen ihre eigenen Meldungen weiter, das bringt kostenlose Reichweite.
- **WhatsApp-Kanal / Telegram:** Morgen-Briefing.
- **Instagram/TikTok:** Kurzvideo „Firma der Woche“, Gründerstorys (Phase 3).
- **X/Bluesky/Threads:** Eilmeldungen automatisiert.

---

## 8. Technik

### 8.1 Stack (Vorschlag)

| Schicht | Wahl | Begründung |
|---|---|---|
| Frontend | **Next.js** (App Router) oder Astro, Multi-Tenant über Domain | SSR/ISR für SEO, ein Codebase für alle Portale |
| CMS | **Payload CMS** (Headless, TypeScript, self-hosted) | Redaktions-Workflow, Rollen, Versionierung, gleiche Sprache wie Frontend |
| Datenbank | **PostgreSQL** (z. B. Supabase oder Neon) + pg_trgm/Volltext | Relationales Firmen-/Personenmodell, Volltextsuche |
| Suche | Meilisearch oder Typesense | Schnelle Firmen- und Artikelsuche |
| Pipelines | Python-Worker (Cron/Queue), z. B. auf Fly.io / Railway / Cloudflare Workers + Queues | Register-, Insolvenz-, PR-Ingest |
| KI | LLM-API für Entwürfe, Zusammenfassungen, Matching-Hilfe | Mit Quellenbindung & Freigabepflicht |
| Medien | S3-kompatibler Speicher + Bild-CDN | Logos, Fotos |
| Hosting/CDN | Vercel oder Cloudflare | Edge-Caching, Multi-Domain |
| Mail | Postmark/Brevo (Transaktional), Newsletter-Tool (z. B. Brevo, Mailchimp, Beehiiv) | Einladungen, Briefing |
| Ads | Google Ad Manager (+ später Vermarkter) | Werbeflächen, Native-Ads |
| Analytics | Plausible/Matomo (DSGVO-freundlich) | Ohne Cookie-Banner-Zwang für Basis-Metriken |
| Consent | CMP mit TCF 2.2 (für Programmatic nötig) | Pflicht bei personalisierten Ads |

### 8.2 Datenmodell (Kern)

```
portal            id, slug, domain, type (news|reviews), name, branding{}, settings{}

company           id, name, legal_form, register_court, register_no, address, geo,
                  founded_at, industry_codes[], website, status (active|insolvent|liquidated|deleted),
                  claimed_by, premium_plan, created_at, updated_at
company_alias     company_id, name                       (frühere Namen, Schreibweisen)
company_financials company_id, year, revenue, employees, total_assets, source

person            id, display_name, slug, public_role_only=true, created_at
person_role       person_id, company_id, role (GF|Vorstand|Prokura|Gründer|AR),
                  from_date, to_date, source

register_event    id, company_id, type, published_at, raw_text, source_url, processed
insolvency_event  id, company_id, court, case_no, stage (vorläufig|eröffnet|Eigenverwaltung|aufgehoben),
                  published_at, source_url

article           id, portal_id, ressort, title, teaser, body, status (draft|review|published|corrected),
                  author_id, reviewer_id, ai_assisted:boolean, sponsored:boolean, sponsor_company_id,
                  published_at, updated_at, sources[], region_codes[]
article_entity    article_id, company_id | person_id
correction        article_id, text, created_at

review_profile    id, portal_id, company_id, category_ids[], score, review_count, response_rate
review            id, review_profile_id, author_id, rating, sub_ratings{}, title, text,
                  experience_date, source (organic|invited|imported), verification_level (0|1|2),
                  status (pending|live|removed), removal_reason, created_at
review_reply      id, review_id, company_user_id, text, created_at
report            id, target_type (review|article), target_id, reporter, reason, decision, decided_at

customer          id, company_id, plan, billing{}, contract_signed_at
invitation        id, review_profile_id, recipient_hash, sent_at, status
```

### 8.3 Systemübersicht

```
 Register / Insolvenz / PR / Bundesanzeiger
            │  (Pipelines, Cron)
            ▼
   ┌──────────────────┐      ┌───────────────┐
   │ Ingest & Matching │────▶│  PostgreSQL   │◀──── Payload CMS (Redaktion, Moderation)
   └──────────────────┘      └──────┬────────┘
            │ KI-Entwürfe           │
            ▼                       ▼
     Review-Queue (CMS)     Next.js Multi-Tenant ──▶ CDN ──▶ kopfundkontor.de
                                    │                          agenturblick.de …
                                    ├─▶ Google-News-Sitemap, RSS, MSN-Feed
                                    ├─▶ Newsletter
                                    └─▶ Widgets/Siegel (JS + SVG) auf Kunden-Websites
```

### 8.4 SEO-Grundlagen
- schema.org: `NewsArticle`, `Organization`/`LocalBusiness`, `Person`, `AggregateRating`, `Review`, `BreadcrumbList`.
- Google-News-Sitemap (Artikel der letzten 48 h), XML-Sitemaps je Portal.
- Saubere URLs: `/unternehmen/mustermann-gmbh-koeln`, `/koepfe/max-mustermann`, `/insolvenzen/2026/11/…`
- Autorenseiten mit Expertise (E-E-A-T), Redaktionsgrundsätze, Korrekturspalte.
- Interne Verlinkung über Firmen-/Personen-Entitäten.
- Kein „Thin Content“: automatisch erzeugte Firmenseiten erst indexieren, wenn genug Substanz da ist (z. B. ≥ 1 Artikel oder ≥ 3 Registerereignisse oder ≥ 1 Bewertung).

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
| **Widgets/Siegel** | Backlinks & Markenbekanntheit | Blick-Siegel auf Kunden-Websites |

---

## 10. Geschäftsmodell & Preise

### 10.1 Erlösquellen

| Quelle | Portal | Ab Phase |
|---|---|---|
| Display & Programmatic Ads | alle | 1 |
| Native-Ad-Widgets (Taboola/Outbrain als *Publisher*) | KOPF & KONTOR | 2 |
| Newsletter-Sponsoring | KOPF & KONTOR | 2 |
| Blick-Pakete (Einladungen, Widgets, Analytics) | Blick | 2 |
| Netzwerk-Premiumprofil | alle | 2 |
| Gekennzeichnete Partnerinhalte („Anzeige“) | KOPF & KONTOR | 2 |
| Stellenmarkt | KOPF & KONTOR | 3 |
| Leads (Anfrageformular „3 Angebote erhalten“) | Solarblick, Umzugsblick, Agenturblick | 3 |
| Awards & Events | alle | 3 |
| Daten-Abo (Alerts zu Insolvenzen und Personalwechseln, API) | KOPF & KONTOR | 3 |

### 10.2 Preis-Entwurf Blick-Portale (monatlich, netto)

| Paket | Preis | Leistungen |
|---|---|---|
| **Basis** | 0 € | Profil beanspruchen, Daten pflegen, auf Bewertungen antworten |
| **Starter** | 49 € | Einladungen (100/Monat), Widget, Siegel, Basis-Statistik |
| **Pro** | 149 € | Einladungen unbegrenzt, API/Integrationen, Wettbewerbsvergleich, Logo & Bilder |
| **Netzwerk** | 299 € | Pro + Premium-Firmenprofil auf KOPF & KONTOR + Stellenanzeigen + Newsroom |

Gekennzeichnete Partnerinhalte KOPF & KONTOR: 490–1.490 € je Beitrag (Unternehmensporträt, Fachbeitrag), immer mit „Anzeige“ markiert.

### 10.3 Beispielrechnung (Ende Jahr 2, konservativ)

| Posten | Annahme | Monat |
|---|---|---|
| Ads (alle Portale) | 1,2 Mio. Seitenaufrufe × 8 € RPM | ~9.600 € |
| Blick-Pakete | 150 zahlende Firmen × Ø 110 € | ~16.500 € |
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
- Alle Portale nennen **Blickwerk Medien GmbH** als Betreiber.
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

| Phase | Rollen | Umfang |
|---|---|---|
| **1 (Monat 0–6)** | Gründer/Herausgeber (Verantwortlicher MStV) · 1 Entwickler (Freelance/Agentur) · 1–2 freie Redakteure · Anwalt (Projekt) | Kernteam ~2–3 FTE |
| **2 (Monat 7–18)** | + Chef vom Dienst · + 2 Redakteure · + Community-/Moderations-Manager (Blick) · + Vertrieb (Teilzeit) | ~6 FTE |
| **3 (ab Monat 19)** | + Regionalredakteure · + Vertriebsteam · + Data Engineer · + Events | 10+ FTE |

**Trennung Redaktion/Vertrieb** von Beginn an: Vertrieb hat keinen Schreibzugriff auf Artikel und keine Moderationsrechte.

---

## 13. Kosten (grobe Schätzung, Phase 1)

| Posten | Einmalig | Monatlich |
|---|---|---|
| Plattform-Entwicklung (MVP: K&K + 1 Blick-Portal) | 25.000–60.000 € (Freelance/Agentur) bzw. Eigenleistung | – |
| Hosting, DB, CDN, Suche | – | 150–500 € |
| Datenquellen (Register-/Firmendaten-API) | – | 200–1.500 € (je nach Anbieter/Volumen) |
| KI-API | – | 100–500 € |
| Newsletter/Mail | – | 50–300 € |
| Freie Redakteure (2 × Teilzeit) | – | 4.000–7.000 € |
| Recht (Setup + Retainer) | 5.000–10.000 € | 300–800 € |
| Versicherung | – | 100–250 € |
| Marken & Domains | 1.000–3.000 € | – |
| **Summe Phase 1** | **~31.000–73.000 €** | **~5.000–11.000 €** |

*Spannen sind Erfahrungswerte, keine Angebote. Vor Start mit konkreten Angeboten ersetzen.*

---

## 14. Roadmap

### Phase 0: Fundament (Monat 0–1)
- [ ] Namen final prüfen (DPMA, Domains, Handles), Domains sichern
- [ ] Gesellschaft gründen bzw. Betreiber festlegen, Verantwortlicher MStV benennen
- [ ] Eigenes Repository anlegen, Plattform-Grundgerüst (Multi-Tenant, CMS, DB)
- [ ] Datenquellen auswählen und Testzugang einrichten
- [ ] Anwalt: Redaktionsstatut, Bewertungsrichtlinien, AGB, Datenschutz

### Phase 1: MVP (Monat 2–6)
- [ ] **KOPF & KONTOR** live für **1 Region** (z. B. NRW): Unternehmen, Köpfe, Insolvenzen, Gründungen
- [ ] Pipelines: Handelsregister + Insolvenzen + Pressemitteilungen → Entwurfs-Queue
- [ ] Firmen- & Personenseiten (mit Indexierungsschwelle)
- [ ] Morgen-Briefing (Newsletter)
- [ ] **Agenturblick** live: 1.000 Profile, Einladungs-Tool, Verifizierung, Transparenzseiten
- [ ] Google Publisher Center, Search Console, LinkedIn-Präsenz
- **Ziel:** 15–25 Beiträge/Tag, 50.000 Seitenaufrufe/Monat, 1.000 Newsletter-Abonnenten, 50 beanspruchte Profile

### Phase 2: Wachstum (Monat 7–18)
- [ ] KOPF & KONTOR bundesweit, Regionalfilter für alle Bundesländer
- [ ] **Softwareblick** + **Kursblick** live
- [ ] Bezahlpakete, Premiumprofile, Partnerinhalte, Ads
- [ ] Bewerbung MSN Partner Hub
- [ ] Erster Transparenzbericht, erstes Ranking
- **Ziel:** 300.000–1 Mio. Seitenaufrufe/Monat, 100+ zahlende Kunden, Break-even der laufenden Kosten

### Phase 3: Skalierung (ab Monat 19)
- [ ] **Solarblick** + **Umzugsblick** (mit Lead-Modell)
- [ ] Awards „Wachstumschampions“ & „Kundenliebling“ + Event
- [ ] Daten-Abo/API, Stellenmarkt, Podcast
- [ ] Content-Partnerschaften mit Startseiten-Portalen
- [ ] Prüfen: Coachblick / Betreuungsblick (mit Presserechtsbegleitung)

---

## 15. KPIs

| Bereich | KPI |
|---|---|
| Reichweite | Seitenaufrufe, Unique Users, Anteil Discover/News/Suche/Direkt |
| Redaktion | Beiträge/Tag, Zeit bis Veröffentlichung (Registerereignis → Artikel), Korrekturquote |
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

---

## 17. Nächste Schritte

1. **Namen festlegen:** Favoriten BLICKWERK Medien · KOPF & KONTOR · Agenturblick bestätigen oder Alternativen wählen. Danach Marken- und Domainprüfung.
2. **Startregion für KOPF & KONTOR** wählen (Vorschlag: NRW, größter Wirtschaftsraum mit vielen Registerereignissen).
3. **Eigenes Repository** anlegen und mit Claude verbinden. Dann folgt das technische Grundgerüst:
   Multi-Tenant-Frontend, Payload CMS, Datenmodell aus Abschnitt 8.2, erste Pipeline (Handelsregister → Entwurf), Firmen- und Artikelseiten, Agenturblick-Profilseite.
4. **Rechtliches Paket** beim Anwalt beauftragen (Abschnitt 11).
5. **Datenanbieter** vergleichen und Testzugang einrichten.

---

*Begleitdokument: `docs/reputationsportale-analyse.md` (Analyse, wie Reputationsportale aufgebaut sind).*
