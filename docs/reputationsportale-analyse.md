# Reverse Engineering: Wie Reputationsportale aufgebaut sind

Stand: November 2026 · Untersuchte Muster: Trustpilot, ProvenExpert, Google Business Profile, Kununu, Jameda, Glassdoor, eKomi, Trusted Shops, Yelp, Check24/Idealo-Bewertungen, G2/Capterra (B2B-Software).

---

## 1. Was ein Portal überhaupt zum „Reputationsportal“ macht

Nutzer und Suchmaschinen stufen eine Seite nicht wegen ihres Designs als Reputationsportal ein, sondern wegen **dreier Eigenschaften, die zusammen auftreten müssen**:

| Eigenschaft | Woran man es erkennt | Warum es wirkt |
|---|---|---|
| **Neutralität** | Betreiber ist nicht der bewertete Anbieter; negative Bewertungen sind sichtbar | Ohne Kritik wirkt jedes Portal wie Werbung |
| **Masse & Aktualität** | Tausende Profile, ständig neue Bewertungen mit Datum | „Hier passiert etwas“ = echte Nutzer |
| **Nachvollziehbares Verfahren** | Offengelegte Prüf-, Lösch- und Sortierregeln | Seit 2022 gesetzlich gefordert (siehe Abschnitt 6) |

Alles andere (Sterne, Siegel, Widgets) ist nur die Oberfläche dieser drei Punkte.

---

## 2. Informationsarchitektur (Seitenstruktur)

Fast alle großen Portale folgen derselben Hierarchie:

```
Startseite
├── Suche (Firmenname / Kategorie / Ort)          ← Haupteinstieg
├── Kategorien  (/kategorie/handwerker/berlin)    ← SEO-Landingpages
│   └── Rankinglisten „Die besten X in Y“
├── Unternehmensprofil (/firma/<slug>)            ← Kernseite, 80–90 % des Traffics
│   ├── Header: Name, Logo, Gesamtnote, Anzahl Bewertungen, Verifiziert-Badge
│   ├── Notenverteilung (5★ … 1★ als Balken)
│   ├── Teilkriterien (Service, Preis, Lieferung …)
│   ├── Bewertungsliste (Filter, Sortierung, Paginierung)
│   │   └── Einzelbewertung + öffentliche Antwort des Unternehmens
│   ├── Firmendaten (Adresse, Kontakt, Website, Öffnungszeiten)
│   └── „Ähnliche Unternehmen“ (interne Verlinkung)
├── Bewertung schreiben (Flow mit Verifizierung)
├── Für Unternehmen (B2B-Bereich, hier verdient das Portal Geld)
│   ├── Profil beanspruchen
│   ├── Preise / Pakete
│   └── Widgets, Siegel, Einladungstools
├── Vertrauen & Transparenz
│   ├── „So funktionieren Bewertungen“ / Richtlinien
│   ├── Transparenzbericht (gelöschte/gemeldete Bewertungen)
│   └── Meldefunktion
├── Blog / Ratgeber / Branchenstudien
└── Impressum, Datenschutz, AGB, Nutzungsbedingungen
```

### Das Unternehmensprofil im Detail
Das Profil ist die wichtigste Seite. Typische Bausteine von oben nach unten:

1. **Score-Block**: Durchschnitt (meist 1 Nachkommastelle), Sterne, Gesamtzahl, Label („Hervorragend“, „Gut“…).
2. **Verteilungsbalken** – zeigt, dass auch schlechte Bewertungen existieren.
3. **Status-Badges**: „Profil beansprucht“, „Lädt aktiv zu Bewertungen ein“, „Antwortet auf negative Bewertungen in X Tagen“. (Trustpilot weist explizit aus, *ob* ein Unternehmen zahlt/einlädt.)
4. **KI-Zusammenfassung** der Bewertungen (seit 2024/25 Standard bei Google, Trustpilot, Amazon).
5. **Bewertungsliste** mit: Vorname/Initiale, Land, Anzahl Bewertungen des Autors, Datum der Erfahrung + Datum der Veröffentlichung, Label „Verifiziert“ / „Eingeladen“ / „Unaufgefordert“, Text, Hilfreich-Button, Melden-Link.
6. **Unternehmensantworten** direkt unter der Bewertung.

---

## 3. Datenmodell (vereinfacht)

```
Company      id, slug, name, category_ids[], address, geo, website, claimed:boolean,
             plan (free/paid), trust_score, review_count, response_rate
Review       id, company_id, author_id, rating(1-5), sub_ratings{}, title, text,
             experience_date, created_at, source (invited|organic|imported),
             verification (none|email|order_id|document), status (live|pending|removed),
             removal_reason, helpful_count, language
Author       id, display_name, country, review_count, verified_email, created_at
Reply        id, review_id, company_id, text, created_at
Report       id, review_id, reporter, reason, decision, decided_at
Category     id, parent_id, name, slug
```

Wichtige Logik:
- **Score ist nicht der reine Durchschnitt**: Trustpilot gewichtet neuere Bewertungen stärker und zieht eine Bayes-Glättung (neue Firmen starten bei ~3,5); Google mittelt ungewichtet; Kununu/Jameda nutzen Teilnoten.
- **Verifizierungsstufen** werden pro Bewertung gespeichert und im UI angezeigt.
- **Moderationsstatus** ist pflichtig (Meldeverfahren nach DSA).

---

## 4. Woher der „tägliche Content“ kommt

Wichtigste Erkenntnis: **Reputationsportale „posten“ fast nichts selbst.** Der tägliche Strom an Inhalten ist User-Generated Content, ausgelöst durch Mechanismen:

| Quelle | Anteil (typisch) | Mechanismus |
|---|---|---|
| Automatische Bewertungseinladungen | 60–80 % | Unternehmen binden das Portal an Shop/CRM an; nach Kauf geht automatisch eine Mail „Wie war Ihre Erfahrung?“ raus |
| Organische Bewertungen | 15–30 % | Nutzer finden das Profil über Google und schreiben selbst (oft negativ) |
| Unternehmensantworten | laufend | Antworten auf Bewertungen erzeugen frischen Text auf der Seite |
| Neue Profile | täglich | Automatisch aus Handelsregister/Branchendaten angelegt oder durch erste Bewertung |
| Redaktionelle Inhalte | 1–5 / Woche | Blog, Branchenreports, Rankings („Beste Arbeitgeber 2026“) |

### Was die Portale selbst täglich/wöchentlich veröffentlichen
- **Daten-Stories**: „Die bestbewerteten Online-Shops im Oktober“, Branchenindizes, Studien → PR und Backlinks.
- **Awards/Siegel**: Kununu „Top Company“, ProvenExpert „Top-Dienstleister“, Trusted Shops „Kundenliebling“ – Unternehmen teilen diese Siegel selbst und erzeugen so Gratis-Reichweite für das Portal.
- **Ratgeber für Verbraucher**: „Fake-Shops erkennen“, „Wie bewerte ich richtig?“ – stärkt das Image als Verbraucherschützer.
- **Ratgeber für Unternehmen**: „Wie antworte ich auf negative Bewertungen?“ – Lead-Gen für die Bezahlpakete.
- **Transparenzberichte** (meist jährlich, Trustpilot quartalsweise Updates): Zahl entfernter Fake-Bewertungen, gesperrter Firmen, Warnhinweise („Consumer Alerts“).
- **Social Media**: wenig Eigenwerbung, eher Verbrauchertipps, Zahlen aus Studien, ausgewählte positive/kuriose Bewertungen (mit Einwilligung).

---

## 5. Vertrauenssignale (Trust-Design)

Diese Elemente erzeugen die Wahrnehmung „unabhängiges Portal“:

1. **Sichtbare Negativbewertungen** – der wichtigste einzelne Faktor. Profile mit ausschließlich 5★ wirken unglaubwürdig (Studien: Kaufwahrscheinlichkeit maximal bei ~4,2–4,7★).
2. **Offengelegte Herkunft jeder Bewertung** (eingeladen/organisch/verifiziert).
3. **Unternehmen können nicht löschen**, nur melden und antworten – und das wird kommuniziert.
4. **Warnhinweise** bei Manipulationsverdacht direkt auf dem Profil.
5. **Zeitstempel überall**, inklusive Datum der eigentlichen Erfahrung.
6. **Methodenseite**: wie der Score berechnet wird, wie Fake-Erkennung funktioniert.
7. **Rechtliche Vollständigkeit**: Impressum mit echter Firma, AGB, Datenschutz, Meldeweg, Ansprechpartner nach DSA.
8. **Externe Bestätigung**: Presseberichte, Google-Seller-Ratings-Partnerstatus, Börsennotierung (Trustpilot), TÜV-/ISO-Zertifikate.
9. **Wiedererkennbare Widgets/Siegel** auf tausenden fremden Websites → Markenbekanntheit.

---

## 6. SEO & Distribution

- **Programmatic SEO**: Für jede Firma eine Profilseite, für jede Kategorie×Stadt eine Landingpage → Millionen indexierbarer Seiten mit ständig frischem Text.
- **Strukturierte Daten**: `Organization`/`LocalBusiness` + `AggregateRating` + `Review` (schema.org). Hinweis: Google zeigt seit 2019 keine Sterne für „self-serving reviews“ auf der eigenen Firmenseite an – Sterne in den Suchergebnissen gibt es nur für Bewertungen *über Dritte*. Genau dieser Drittanbieter-Status ist der SEO-Vorteil der Portale.
- **Google Seller Ratings**: Lizenzierte Partner (Trustpilot, eKomi, Trusted Shops …) liefern Sterne in Google Ads – starkes Verkaufsargument.
- **Brand-Suchen**: „<Firma> Erfahrungen“ – Portale ranken hier fast immer auf Seite 1.
- **Backlinks** aus Widgets, Siegeln und Datenstudien.

---

## 7. Geschäftsmodell (warum die Struktur so aussieht)

| Modell | Beispiele | Was bezahlt wird |
|---|---|---|
| Freemium SaaS für Unternehmen | Trustpilot, ProvenExpert | Einladungs-Automation, Widgets, Analytics, Branding |
| Zertifizierung + Bewertungen | Trusted Shops, eKomi | Gütesiegel, Käuferschutz, Seller Ratings |
| Arbeitgeber-Branding | Kununu, Glassdoor | Employer-Profile, Stellenanzeigen |
| Lead-Gen / Premium-Listing | Jameda, Yelp, Check24 | Hervorgehobene Platzierung, Terminbuchung |

Rechtlich wichtig: Premium-Platzierungen müssen als solche gekennzeichnet sein (BGH-Urteil Jameda 2018: Portal verliert Neutralitätsstatus, wenn zahlende Kunden bevorzugt werden).

---

## 8. Rechtlicher Rahmen (DE/EU) – nicht optional

- **UWG § 5b Abs. 3** (seit 28.05.2022, Omnibus-Richtlinie): Wer Bewertungen zugänglich macht, muss angeben, *ob und wie* sichergestellt wird, dass sie von echten Kunden stammen.
- **UWG Anhang Nr. 23b/23c**: Gefälschte Bewertungen zu erstellen, in Auftrag zu geben oder falsch darzustellen ist **per se unlauter** (Abmahnung, Bußgelder bis 4 % des Jahresumsatzes nach Art. 9 Omnibus-RL).
- **Digital Services Act**: Meldeverfahren, Begründung von Löschungen, Transparenzberichte, Kontaktstelle.
- **Persönlichkeitsrecht / Prüfpflichten** (BGH „Hotelbewertung“, „Ärztebewertung II“): Portale müssen auf Beanstandung hin prüfen und ggf. Nachweise vom Bewertenden anfordern.
- **DSGVO**: Bewertungseinladungen nur mit Rechtsgrundlage; Autorenprofile sind personenbezogene Daten.
- **Kennzeichnungspflicht** bezahlter Platzierungen und Incentives (Gutschein gegen Bewertung muss offengelegt werden).

**Konsequenz:** Eine Seite, die nur *aussieht* wie ein Reputationsportal (selbst erstellte Bewertungen, nur positive Inhalte, Betreiber = bewertetes Unternehmen oder versteckter Auftraggeber), ist in DE/EU wettbewerbswidrig und wird von Google zusätzlich als Spam abgewertet. Die Wahrnehmung „Reputationsportal“ lässt sich nachhaltig nur durch tatsächliche Neutralität erreichen.

---

## 9. Takeaways für ein eigenes Projekt

Falls Ziel ist, ein eigenes (Nischen-)Portal oder eine Reputations-Funktion aufzubauen:

1. **Nische statt Breite** – z. B. Bewertungen für Content-Creator-Tools/Agenturen. Große Portale sind in Nischen dünn besetzt.
2. **Kaltstartproblem lösen ohne Fakes**: Profile aus öffentlichen Daten anlegen, Unternehmen zum Beanspruchen einladen, Einladungs-API kostenlos anbieten, eigene redaktionelle Tests als solche gekennzeichnet veröffentlichen.
3. **Verifizierung von Tag 1** (Order-ID, E-Mail, Beleg-Upload) und Label pro Bewertung.
4. **Pflichtseiten zuerst bauen**: Richtlinien, Score-Methodik, Meldeweg, Impressum, Datenschutz, § 5b-Hinweis.
5. **Content-Rhythmus**: täglich = UGC + Antworten (automatisiert), wöchentlich = 1 Ratgeber, monatlich = Ranking/Datenreport, jährlich = Award + Transparenzbericht.
6. **Technik**: schema.org-Markup, programmatic Kategorie-Seiten, embeddable Widget (JS-Snippet + SVG-Siegel) als Wachstumsmotor.

Alternativ – falls das Ziel ist, die **eigene** Reputation (z. B. ClipFarm Studio) zu stärken: Profil auf Trustpilot/ProvenExpert/Google beanspruchen, automatische Einladungen nach Projektabschluss, auf jede Bewertung antworten, Widget auf der Website einbinden. Das ist schneller und glaubwürdiger als ein eigenes Portal.
