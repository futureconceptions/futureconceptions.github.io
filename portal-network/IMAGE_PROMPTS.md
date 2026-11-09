# Bildprompts für letz.ai

Alle Rasterbilder, die die Templates erwarten. **Kein Bild ist Pflicht:** Fehlt eine Datei, zeigen die Seiten automatisch einen Farbverlauf in der Portalfarbe (CSS-Fallback), und `og:image` wird weggelassen. Bilder können also nach dem Launch nach und nach ergänzt werden – einfach Datei ablegen und `python3 portal-network/build.py` erneut ausführen.

## Grundregeln für alle Bilder

- **Keine Schrift, keine Buchstaben, keine Zahlen, keine Logos oder Markenzeichen** im Bild. Logos sind die SVG-Wortmarken, die der Builder erzeugt.
- **Keine echten Personen**, keine erkennbaren Gesichter, keine echten Firmenlogos, keine Produkte erkennbarer Marken.
- Personen nur stilisiert, gesichtslos oder von hinten, divers (Alter, Geschlecht, Herkunft), Business-casual.
- Pro Portal einheitlicher Stil (siehe Stilblock). Den Stilblock immer **vor** das Motiv setzen – die fertigen Prompts unten enthalten ihn bereits.
- Ruhige, seriöse Anmutung: Nachrichten- und B2B-Marke, nichts Reißerisches (besonders bei „Insolvenzen“).
- Motiv **mittig** halten: Viele Flächen werden je nach Bildschirm auf 3:1, 16:9 oder 21:9 beschnitten.

## Stil je Portal

- **FIRMENNACHRICHTEN** (firmennachrichten.de): Editorial flat vector illustration, calm serious business-news look, clean geometric shapes, warm off-white background, limited palette of deep crimson red (#B3261E), charcoal grey and soft sand beige, subtle paper grain, generous negative space, no text.
- **ITSZENE** (itszene.de): Clean isometric flat illustration, modern IT for small and medium businesses, soft shadows, palette of petrol blue (#0B6A8A), deep navy, light grey and a touch of cyan, minimal and precise, no text.
- **IT-ERFAHRUNGEN** (it-erfahrungen.de): Friendly modern flat illustration, trustworthy and calm, rounded shapes, light neutral background, palette of forest green (#1A7F37), mint, warm grey and white, simple and uncluttered, no text.
- **MERKANT Medien** (merkant-medien.de): Abstract editorial illustration, elegant and restrained, connected geometric nodes and lines, palette of deep navy (#1F3A8A), slate blue and off-white, lots of negative space, no text.

## Einheitlicher Negativ-Prompt

```
text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated
```

## Export & Ablage

1. In letz.ai im passenden Seitenverhältnis erzeugen (Spalte „Format“), dann auf die Zielgröße skalieren/beschneiden.
2. **Zielordner:** `portal-network/sites/<domain>/static/` + Pfad aus der Tabelle (z. B. `portal-network/sites/itszene.de/static/img/ressorts/sicherheit.webp`).
3. **Formate:** `og-default` immer als **JPG** (Social-Media-Plattformen unterstützen WebP nicht zuverlässig). Alle anderen bevorzugt als **WebP** (Qualität 75–82); die Templates nehmen `.webp`, sonst `.jpg`, sonst `.png` mit demselben Namen. Optional zusätzlich JPG als Reserve ablegen.
4. **Dateigröße:** Ziel **≤ 200 KB** pro Bild (Hero ≤ 250 KB vertretbar). JPG: Qualität ca. 75–80, progressiv, sRGB, Metadaten entfernen. Beispiele:
   - `cwebp -q 78 -m 6 -metadata none eingabe.png -o hero.webp`
   - `magick eingabe.png -resize 1200x630^ -gravity center -extent 1200x630 -strip -interlace JPEG -quality 78 og-default.jpg`
   - alternativ squoosh.app (Browser, ohne Upload).
5. Dateinamen exakt wie angegeben (Kleinbuchstaben, ohne Umlaute). Danach `python3 portal-network/build.py` – fertig.
6. Bildnachweis: Das Impressum enthält bereits den Hinweis auf KI-generierte Illustrationen.

## Übersicht

| # | Portal | Datei (unter `sites/<domain>/static/`) | Größe | Format | Verwendung |
|---|---|---|---|---|---|
| 1 | firmennachrichten.de | `img/og-default.jpg` | 1200×630 (1,91:1) | jpg | Standard-Vorschaubild für Social Media / Google Discover (og:image), wenn ein Beitrag kein eigenes Bild hat |
| 2 | firmennachrichten.de | `img/hero.webp` | 2100×900 (21:9) | webp + jpg | Startseite – Aufmacher-/Hero-Fläche (wird angezeigt, solange kein Artikel als Aufmacher existiert) |
| 3 | itszene.de | `img/og-default.jpg` | 1200×630 (1,91:1) | jpg | Standard-Vorschaubild für Social Media / Google Discover (og:image), wenn ein Beitrag kein eigenes Bild hat |
| 4 | itszene.de | `img/hero.webp` | 2100×900 (21:9) | webp + jpg | Startseite – Aufmacher-/Hero-Fläche (wird angezeigt, solange kein Artikel als Aufmacher existiert) |
| 5 | it-erfahrungen.de | `img/og-default.jpg` | 1200×630 (1,91:1) | jpg | Standard-Vorschaubild für Social Media / Google Discover (og:image), wenn ein Beitrag kein eigenes Bild hat |
| 6 | it-erfahrungen.de | `img/hero.webp` | 2100×900 (21:9) | webp + jpg | Startseite – Aufmacher-/Hero-Fläche (wird angezeigt, solange kein Artikel als Aufmacher existiert) |
| 7 | merkant-medien.de | `img/og-default.jpg` | 1200×630 (1,91:1) | jpg | Standard-Vorschaubild für Social Media / Google Discover (og:image), wenn ein Beitrag kein eigenes Bild hat |
| 8 | merkant-medien.de | `img/hero.webp` | 2100×900 (21:9) | webp + jpg | Startseite – Aufmacher-/Hero-Fläche (wird angezeigt, solange kein Artikel als Aufmacher existiert) |
| 9 | firmennachrichten.de | `img/ressorts/aktuell.webp` | 1600×900 (16:9) | webp + jpg | Ressort „Aktuell“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild |
| 10 | firmennachrichten.de | `img/ressorts/unternehmen.webp` | 1600×900 (16:9) | webp + jpg | Ressort „Unternehmen“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild |
| 11 | firmennachrichten.de | `img/ressorts/koepfe.webp` | 1600×900 (16:9) | webp + jpg | Ressort „Köpfe“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild |
| 12 | firmennachrichten.de | `img/ressorts/gruender.webp` | 1600×900 (16:9) | webp + jpg | Ressort „Gründer & Startups“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild |
| 13 | firmennachrichten.de | `img/ressorts/mittelstand.webp` | 1600×900 (16:9) | webp + jpg | Ressort „Mittelstand“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild |
| 14 | firmennachrichten.de | `img/ressorts/insolvenzen.webp` | 1600×900 (16:9) | webp + jpg | Ressort „Insolvenzen“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild |
| 15 | firmennachrichten.de | `img/ressorts/regional.webp` | 1600×900 (16:9) | webp + jpg | Ressort „Regional“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild |
| 16 | firmennachrichten.de | `img/ressorts/ratgeber.webp` | 1600×900 (16:9) | webp + jpg | Ressort „Ratgeber“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild |
| 17 | firmennachrichten.de | `img/ressorts/rankings.webp` | 1600×900 (16:9) | webp + jpg | Ressort „Rankings & Daten“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild |
| 18 | itszene.de | `img/ressorts/it-unternehmen.webp` | 1600×900 (16:9) | webp + jpg | Ressort „IT-Unternehmen“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild |
| 19 | itszene.de | `img/ressorts/sicherheit.webp` | 1600×900 (16:9) | webp + jpg | Ressort „Sicherheit“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild |
| 20 | itszene.de | `img/ressorts/software-cloud.webp` | 1600×900 (16:9) | webp + jpg | Ressort „Software & Cloud“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild |
| 21 | itszene.de | `img/ressorts/digitalisierung.webp` | 1600×900 (16:9) | webp + jpg | Ressort „Digitalisierung“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild |
| 22 | itszene.de | `img/ressorts/ratgeber.webp` | 1600×900 (16:9) | webp + jpg | Ressort „Ratgeber“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild |
| 23 | it-erfahrungen.de | `img/kategorien/managed-services.webp` | 1600×900 (16:9) | webp + jpg | Kategorie „Managed Services“ (Startseite, Kategorien-Kachel) |
| 24 | it-erfahrungen.de | `img/kategorien/cloud.webp` | 1600×900 (16:9) | webp + jpg | Kategorie „Cloud“ (Startseite, Kategorien-Kachel) |
| 25 | it-erfahrungen.de | `img/kategorien/it-security.webp` | 1600×900 (16:9) | webp + jpg | Kategorie „IT-Security“ (Startseite, Kategorien-Kachel) |
| 26 | it-erfahrungen.de | `img/kategorien/softwareentwicklung.webp` | 1600×900 (16:9) | webp + jpg | Kategorie „Softwareentwicklung“ (Startseite, Kategorien-Kachel) |
| 27 | it-erfahrungen.de | `img/kategorien/it-beratung.webp` | 1600×900 (16:9) | webp + jpg | Kategorie „IT-Beratung“ (Startseite, Kategorien-Kachel) |
| 28 | it-erfahrungen.de | `img/empty/keine-bewertungen.webp` | 1200×900 (4:3) | webp + jpg | Leerzustand „Noch keine Bewertungen – Profil beanspruchen“ (Startseite, Kategorie- und Firmenseiten) |
| 29 | firmennachrichten.de | `img/newsletter.webp` | 1200×900 (4:3) | webp + jpg | Newsletter-Box (Startseite, Ressort- und Artikelseiten) |
| 30 | itszene.de | `img/newsletter.webp` | 1200×900 (4:3) | webp + jpg | Newsletter-Box (Startseite, Ressort- und Artikelseiten) |
| 31 | it-erfahrungen.de | `img/newsletter.webp` | 1200×900 (4:3) | webp + jpg | Newsletter-Box (Startseite, Ressort- und Artikelseiten) |
| 32 | firmennachrichten.de | `img/autor-redaktion.webp` | 512×512 (1:1) | webp + jpg | Autoren-Platzhalter auf /autoren/redaktion/ (kein Foto einer echten Person) |
| 33 | itszene.de | `img/autor-redaktion.webp` | 512×512 (1:1) | webp + jpg | Autoren-Platzhalter auf /autoren/redaktion/ (kein Foto einer echten Person) |

Insgesamt **33 Bilder**. Phase-2-Portale (systemhauserfahrungen.de, agenturerfahrungen.de, unternehmenserfahrungen.de) brauchen dieselben Bildtypen wie it-erfahrungen.de, sobald sie aktiviert werden.

## Prompts

### FIRMENNACHRICHTEN (firmennachrichten.de)

**1. `portal-network/sites/firmennachrichten.de/static/img/og-default.jpg`** – 1200×630, 1,91:1, jpg  
Verwendung: Standard-Vorschaubild für Social Media / Google Discover (og:image), wenn ein Beitrag kein eigenes Bild hat

```
Editorial flat vector illustration, calm serious business-news look, clean geometric shapes, warm off-white background, limited palette of deep crimson red (#B3261E), charcoal grey and soft sand beige, subtle paper grain, generous negative space, no text. Subject: a stylised German city skyline with office buildings, a factory and a small workshop side by side, morning light, symbolising the German Mittelstand. Composition: main subject centred with calm margins, aspect ratio 1,91:1. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

**2. `portal-network/sites/firmennachrichten.de/static/img/hero.webp`** – 2100×900, 21:9 (zentrales Motiv, Ränder werden auf Mobilgeräten beschnitten), webp + jpg  
Verwendung: Startseite – Aufmacher-/Hero-Fläche (wird angezeigt, solange kein Artikel als Aufmacher existiert)

```
Editorial flat vector illustration, calm serious business-news look, clean geometric shapes, warm off-white background, limited palette of deep crimson red (#B3261E), charcoal grey and soft sand beige, subtle paper grain, generous negative space, no text. Subject: wide panorama of a German business district at dawn transitioning into an industrial park and a rural Mittelstand factory, river in the foreground. Composition: main subject centred with calm margins, aspect ratio 21:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

### ITSZENE (itszene.de)

**3. `portal-network/sites/itszene.de/static/img/og-default.jpg`** – 1200×630, 1,91:1, jpg  
Verwendung: Standard-Vorschaubild für Social Media / Google Discover (og:image), wenn ein Beitrag kein eigenes Bild hat

```
Clean isometric flat illustration, modern IT for small and medium businesses, soft shadows, palette of petrol blue (#0B6A8A), deep navy, light grey and a touch of cyan, minimal and precise, no text. Subject: an isometric small office with a server rack, laptops, a cloud symbol and a shield symbol connected by thin lines. Composition: main subject centred with calm margins, aspect ratio 1,91:1. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

**4. `portal-network/sites/itszene.de/static/img/hero.webp`** – 2100×900, 21:9 (zentrales Motiv, Ränder werden auf Mobilgeräten beschnitten), webp + jpg  
Verwendung: Startseite – Aufmacher-/Hero-Fläche (wird angezeigt, solange kein Artikel als Aufmacher existiert)

```
Clean isometric flat illustration, modern IT for small and medium businesses, soft shadows, palette of petrol blue (#0B6A8A), deep navy, light grey and a touch of cyan, minimal and precise, no text. Subject: wide isometric panorama of a modern small-business office floor with workstations, a compact server room and cloud connections. Composition: main subject centred with calm margins, aspect ratio 21:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

### IT-ERFAHRUNGEN (it-erfahrungen.de)

**5. `portal-network/sites/it-erfahrungen.de/static/img/og-default.jpg`** – 1200×630, 1,91:1, jpg  
Verwendung: Standard-Vorschaubild für Social Media / Google Discover (og:image), wenn ein Beitrag kein eigenes Bild hat

```
Friendly modern flat illustration, trustworthy and calm, rounded shapes, light neutral background, palette of forest green (#1A7F37), mint, warm grey and white, simple and uncluttered, no text. Subject: two businesspeople shaking hands in front of an abstract network of IT devices, a few abstract five-point star shapes floating above. If people appear: small, stylised, faceless or seen from behind, diverse in age, gender and ethnicity, business casual. Composition: main subject centred with calm margins, aspect ratio 1,91:1. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

**6. `portal-network/sites/it-erfahrungen.de/static/img/hero.webp`** – 2100×900, 21:9 (zentrales Motiv, Ränder werden auf Mobilgeräten beschnitten), webp + jpg  
Verwendung: Startseite – Aufmacher-/Hero-Fläche (wird angezeigt, solange kein Artikel als Aufmacher existiert)

```
Friendly modern flat illustration, trustworthy and calm, rounded shapes, light neutral background, palette of forest green (#1A7F37), mint, warm grey and white, simple and uncluttered, no text. Subject: wide scene of a friendly consultation table with a laptop, a checklist without readable text and a stylised IT network in the background. Composition: main subject centred with calm margins, aspect ratio 21:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

### MERKANT Medien (merkant-medien.de)

**7. `portal-network/sites/merkant-medien.de/static/img/og-default.jpg`** – 1200×630, 1,91:1, jpg  
Verwendung: Standard-Vorschaubild für Social Media / Google Discover (og:image), wenn ein Beitrag kein eigenes Bild hat

```
Abstract editorial illustration, elegant and restrained, connected geometric nodes and lines, palette of deep navy (#1F3A8A), slate blue and off-white, lots of negative space, no text. Subject: an abstract network of connected nodes forming a constellation, some nodes shaped like simplified newspapers and star icons. Composition: main subject centred with calm margins, aspect ratio 1,91:1. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

**8. `portal-network/sites/merkant-medien.de/static/img/hero.webp`** – 2100×900, 21:9 (zentrales Motiv, Ränder werden auf Mobilgeräten beschnitten), webp + jpg  
Verwendung: Startseite – Aufmacher-/Hero-Fläche (wird angezeigt, solange kein Artikel als Aufmacher existiert)

```
Abstract editorial illustration, elegant and restrained, connected geometric nodes and lines, palette of deep navy (#1F3A8A), slate blue and off-white, lots of negative space, no text. Subject: wide abstract composition of interconnected nodes and lines flowing from left to right like a map. Composition: main subject centred with calm margins, aspect ratio 21:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

### FIRMENNACHRICHTEN (firmennachrichten.de)

**9. `portal-network/sites/firmennachrichten.de/static/img/ressorts/aktuell.webp`** – 1600×900, 16:9 (wird auch als 3:1-Streifen und 21:9 beschnitten – Motiv mittig halten), webp + jpg  
Verwendung: Ressort „Aktuell“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild

```
Editorial flat vector illustration, calm serious business-news look, clean geometric shapes, warm off-white background, limited palette of deep crimson red (#B3261E), charcoal grey and soft sand beige, subtle paper grain, generous negative space, no text. Subject: a stack of fresh newspapers and a tablet on a desk, morning coffee, abstract. Composition: main subject centred with calm margins, aspect ratio 16:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

**10. `portal-network/sites/firmennachrichten.de/static/img/ressorts/unternehmen.webp`** – 1600×900, 16:9 (wird auch als 3:1-Streifen und 21:9 beschnitten – Motiv mittig halten), webp + jpg  
Verwendung: Ressort „Unternehmen“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild

```
Editorial flat vector illustration, calm serious business-news look, clean geometric shapes, warm off-white background, limited palette of deep crimson red (#B3261E), charcoal grey and soft sand beige, subtle paper grain, generous negative space, no text. Subject: modern office buildings and a factory hall with rising abstract bar shapes. Composition: main subject centred with calm margins, aspect ratio 16:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

**11. `portal-network/sites/firmennachrichten.de/static/img/ressorts/koepfe.webp`** – 1600×900, 16:9 (wird auch als 3:1-Streifen und 21:9 beschnitten – Motiv mittig halten), webp + jpg  
Verwendung: Ressort „Köpfe“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild

```
Editorial flat vector illustration, calm serious business-news look, clean geometric shapes, warm off-white background, limited palette of deep crimson red (#B3261E), charcoal grey and soft sand beige, subtle paper grain, generous negative space, no text. Subject: a row of stylised faceless business figures in silhouette standing on steps, one stepping forward. If people appear: small, stylised, faceless or seen from behind, diverse in age, gender and ethnicity, business casual. Composition: main subject centred with calm margins, aspect ratio 16:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

**12. `portal-network/sites/firmennachrichten.de/static/img/ressorts/gruender.webp`** – 1600×900, 16:9 (wird auch als 3:1-Streifen und 21:9 beschnitten – Motiv mittig halten), webp + jpg  
Verwendung: Ressort „Gründer & Startups“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild

```
Editorial flat vector illustration, calm serious business-news look, clean geometric shapes, warm off-white background, limited palette of deep crimson red (#B3261E), charcoal grey and soft sand beige, subtle paper grain, generous negative space, no text. Subject: a small rocket launching from a laptop in a shared workspace, abstract sparks. Composition: main subject centred with calm margins, aspect ratio 16:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

**13. `portal-network/sites/firmennachrichten.de/static/img/ressorts/mittelstand.webp`** – 1600×900, 16:9 (wird auch als 3:1-Streifen und 21:9 beschnitten – Motiv mittig halten), webp + jpg  
Verwendung: Ressort „Mittelstand“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild

```
Editorial flat vector illustration, calm serious business-news look, clean geometric shapes, warm off-white background, limited palette of deep crimson red (#B3261E), charcoal grey and soft sand beige, subtle paper grain, generous negative space, no text. Subject: a traditional family-run factory building with a modern extension, trees, workshop tools. Composition: main subject centred with calm margins, aspect ratio 16:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

**14. `portal-network/sites/firmennachrichten.de/static/img/ressorts/insolvenzen.webp`** – 1600×900, 16:9 (wird auch als 3:1-Streifen und 21:9 beschnitten – Motiv mittig halten), webp + jpg  
Verwendung: Ressort „Insolvenzen“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild

```
Editorial flat vector illustration, calm serious business-news look, clean geometric shapes, warm off-white background, limited palette of deep crimson red (#B3261E), charcoal grey and soft sand beige, subtle paper grain, generous negative space, no text. Subject: a neutral courthouse facade with columns and a folder of documents, sober and respectful mood, nothing dramatic. Composition: main subject centred with calm margins, aspect ratio 16:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

**15. `portal-network/sites/firmennachrichten.de/static/img/ressorts/regional.webp`** – 1600×900, 16:9 (wird auch als 3:1-Streifen und 21:9 beschnitten – Motiv mittig halten), webp + jpg  
Verwendung: Ressort „Regional“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild

```
Editorial flat vector illustration, calm serious business-news look, clean geometric shapes, warm off-white background, limited palette of deep crimson red (#B3261E), charcoal grey and soft sand beige, subtle paper grain, generous negative space, no text. Subject: a stylised map of the German state of North Rhine-Westphalia with river lines and small city markers, no labels. Composition: main subject centred with calm margins, aspect ratio 16:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

**16. `portal-network/sites/firmennachrichten.de/static/img/ressorts/ratgeber.webp`** – 1600×900, 16:9 (wird auch als 3:1-Streifen und 21:9 beschnitten – Motiv mittig halten), webp + jpg  
Verwendung: Ressort „Ratgeber“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild

```
Editorial flat vector illustration, calm serious business-news look, clean geometric shapes, warm off-white background, limited palette of deep crimson red (#B3261E), charcoal grey and soft sand beige, subtle paper grain, generous negative space, no text. Subject: an open book with abstract icons for law, tax, finance and leadership floating above it. Composition: main subject centred with calm margins, aspect ratio 16:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

**17. `portal-network/sites/firmennachrichten.de/static/img/ressorts/rankings.webp`** – 1600×900, 16:9 (wird auch als 3:1-Streifen und 21:9 beschnitten – Motiv mittig halten), webp + jpg  
Verwendung: Ressort „Rankings & Daten“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild

```
Editorial flat vector illustration, calm serious business-news look, clean geometric shapes, warm off-white background, limited palette of deep crimson red (#B3261E), charcoal grey and soft sand beige, subtle paper grain, generous negative space, no text. Subject: abstract ascending podium and bar charts made of paper shapes, without any numbers. Composition: main subject centred with calm margins, aspect ratio 16:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

### ITSZENE (itszene.de)

**18. `portal-network/sites/itszene.de/static/img/ressorts/it-unternehmen.webp`** – 1600×900, 16:9 (wird auch als 3:1-Streifen und 21:9 beschnitten – Motiv mittig halten), webp + jpg  
Verwendung: Ressort „IT-Unternehmen“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild

```
Clean isometric flat illustration, modern IT for small and medium businesses, soft shadows, palette of petrol blue (#0B6A8A), deep navy, light grey and a touch of cyan, minimal and precise, no text. Subject: isometric office block of an IT company with server racks visible through windows. Composition: main subject centred with calm margins, aspect ratio 16:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

**19. `portal-network/sites/itszene.de/static/img/ressorts/sicherheit.webp`** – 1600×900, 16:9 (wird auch als 3:1-Streifen und 21:9 beschnitten – Motiv mittig halten), webp + jpg  
Verwendung: Ressort „Sicherheit“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild

```
Clean isometric flat illustration, modern IT for small and medium businesses, soft shadows, palette of petrol blue (#0B6A8A), deep navy, light grey and a touch of cyan, minimal and precise, no text. Subject: a shield and a padlock protecting a small office network, isometric. Composition: main subject centred with calm margins, aspect ratio 16:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

**20. `portal-network/sites/itszene.de/static/img/ressorts/software-cloud.webp`** – 1600×900, 16:9 (wird auch als 3:1-Streifen und 21:9 beschnitten – Motiv mittig halten), webp + jpg  
Verwendung: Ressort „Software & Cloud“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild

```
Clean isometric flat illustration, modern IT for small and medium businesses, soft shadows, palette of petrol blue (#0B6A8A), deep navy, light grey and a touch of cyan, minimal and precise, no text. Subject: isometric cloud above stacked application windows without readable content. Composition: main subject centred with calm margins, aspect ratio 16:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

**21. `portal-network/sites/itszene.de/static/img/ressorts/digitalisierung.webp`** – 1600×900, 16:9 (wird auch als 3:1-Streifen und 21:9 beschnitten – Motiv mittig halten), webp + jpg  
Verwendung: Ressort „Digitalisierung“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild

```
Clean isometric flat illustration, modern IT for small and medium businesses, soft shadows, palette of petrol blue (#0B6A8A), deep navy, light grey and a touch of cyan, minimal and precise, no text. Subject: a paper document transforming into digital data blocks flowing into a laptop, isometric. Composition: main subject centred with calm margins, aspect ratio 16:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

**22. `portal-network/sites/itszene.de/static/img/ressorts/ratgeber.webp`** – 1600×900, 16:9 (wird auch als 3:1-Streifen und 21:9 beschnitten – Motiv mittig halten), webp + jpg  
Verwendung: Ressort „Ratgeber“: Kachel auf der Startseite und Standard-Artikelbild für Beiträge ohne eigenes Bild

```
Clean isometric flat illustration, modern IT for small and medium businesses, soft shadows, palette of petrol blue (#0B6A8A), deep navy, light grey and a touch of cyan, minimal and precise, no text. Subject: isometric desk with a laptop, an open handbook and abstract IT icons for backup, cloud and security. Composition: main subject centred with calm margins, aspect ratio 16:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

### IT-ERFAHRUNGEN (it-erfahrungen.de)

**23. `portal-network/sites/it-erfahrungen.de/static/img/kategorien/managed-services.webp`** – 1600×900, 16:9 (wird auch als 3:1-Streifen und 21:9 beschnitten – Motiv mittig halten), webp + jpg  
Verwendung: Kategorie „Managed Services“ (Startseite, Kategorien-Kachel)

```
Friendly modern flat illustration, trustworthy and calm, rounded shapes, light neutral background, palette of forest green (#1A7F37), mint, warm grey and white, simple and uncluttered, no text. Subject: an IT technician figure seen from behind monitoring a dashboard of abstract status lights for a small office. If people appear: small, stylised, faceless or seen from behind, diverse in age, gender and ethnicity, business casual. Composition: main subject centred with calm margins, aspect ratio 16:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

**24. `portal-network/sites/it-erfahrungen.de/static/img/kategorien/cloud.webp`** – 1600×900, 16:9 (wird auch als 3:1-Streifen und 21:9 beschnitten – Motiv mittig halten), webp + jpg  
Verwendung: Kategorie „Cloud“ (Startseite, Kategorien-Kachel)

```
Friendly modern flat illustration, trustworthy and calm, rounded shapes, light neutral background, palette of forest green (#1A7F37), mint, warm grey and white, simple and uncluttered, no text. Subject: a stylised cloud connected to office laptops and a small server, data flowing. Composition: main subject centred with calm margins, aspect ratio 16:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

**25. `portal-network/sites/it-erfahrungen.de/static/img/kategorien/it-security.webp`** – 1600×900, 16:9 (wird auch als 3:1-Streifen und 21:9 beschnitten – Motiv mittig halten), webp + jpg  
Verwendung: Kategorie „IT-Security“ (Startseite, Kategorien-Kachel)

```
Friendly modern flat illustration, trustworthy and calm, rounded shapes, light neutral background, palette of forest green (#1A7F37), mint, warm grey and white, simple and uncluttered, no text. Subject: a large shield protecting a group of devices, padlock, calm mood. Composition: main subject centred with calm margins, aspect ratio 16:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

**26. `portal-network/sites/it-erfahrungen.de/static/img/kategorien/softwareentwicklung.webp`** – 1600×900, 16:9 (wird auch als 3:1-Streifen und 21:9 beschnitten – Motiv mittig halten), webp + jpg  
Verwendung: Kategorie „Softwareentwicklung“ (Startseite, Kategorien-Kachel)

```
Friendly modern flat illustration, trustworthy and calm, rounded shapes, light neutral background, palette of forest green (#1A7F37), mint, warm grey and white, simple and uncluttered, no text. Subject: abstract code blocks as coloured bars on a monitor, gears and puzzle pieces, no readable code. Composition: main subject centred with calm margins, aspect ratio 16:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

**27. `portal-network/sites/it-erfahrungen.de/static/img/kategorien/it-beratung.webp`** – 1600×900, 16:9 (wird auch als 3:1-Streifen und 21:9 beschnitten – Motiv mittig halten), webp + jpg  
Verwendung: Kategorie „IT-Beratung“ (Startseite, Kategorien-Kachel)

```
Friendly modern flat illustration, trustworthy and calm, rounded shapes, light neutral background, palette of forest green (#1A7F37), mint, warm grey and white, simple and uncluttered, no text. Subject: two figures at a whiteboard with abstract diagrams and arrows, no readable text. If people appear: small, stylised, faceless or seen from behind, diverse in age, gender and ethnicity, business casual. Composition: main subject centred with calm margins, aspect ratio 16:9. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

**28. `portal-network/sites/it-erfahrungen.de/static/img/empty/keine-bewertungen.webp`** – 1200×900, 4:3, webp + jpg  
Verwendung: Leerzustand „Noch keine Bewertungen – Profil beanspruchen“ (Startseite, Kategorie- und Firmenseiten)

```
Friendly modern flat illustration, trustworthy and calm, rounded shapes, light neutral background, palette of forest green (#1A7F37), mint, warm grey and white, simple and uncluttered, no text. Subject: an empty friendly speech bubble with an outline of five-point stars waiting to be filled, a small plant beside it, optimistic mood. Composition: main subject centred with calm margins, aspect ratio 4:3. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

### FIRMENNACHRICHTEN (firmennachrichten.de)

**29. `portal-network/sites/firmennachrichten.de/static/img/newsletter.webp`** – 1200×900, 4:3, webp + jpg  
Verwendung: Newsletter-Box (Startseite, Ressort- und Artikelseiten)

```
Editorial flat vector illustration, calm serious business-news look, clean geometric shapes, warm off-white background, limited palette of deep crimson red (#B3261E), charcoal grey and soft sand beige, subtle paper grain, generous negative space, no text. Subject: an envelope opening at sunrise with a folded newspaper inside, coffee cup beside it. Composition: main subject centred with calm margins, aspect ratio 4:3. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

### ITSZENE (itszene.de)

**30. `portal-network/sites/itszene.de/static/img/newsletter.webp`** – 1200×900, 4:3, webp + jpg  
Verwendung: Newsletter-Box (Startseite, Ressort- und Artikelseiten)

```
Clean isometric flat illustration, modern IT for small and medium businesses, soft shadows, palette of petrol blue (#0B6A8A), deep navy, light grey and a touch of cyan, minimal and precise, no text. Subject: an isometric envelope with small icons for shield, cloud and calendar flying out of it. Composition: main subject centred with calm margins, aspect ratio 4:3. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

### IT-ERFAHRUNGEN (it-erfahrungen.de)

**31. `portal-network/sites/it-erfahrungen.de/static/img/newsletter.webp`** – 1200×900, 4:3, webp + jpg  
Verwendung: Newsletter-Box (Startseite, Ressort- und Artikelseiten)

```
Friendly modern flat illustration, trustworthy and calm, rounded shapes, light neutral background, palette of forest green (#1A7F37), mint, warm grey and white, simple and uncluttered, no text. Subject: an envelope with a checklist card and a small star shape peeking out. Composition: main subject centred with calm margins, aspect ratio 4:3. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

### FIRMENNACHRICHTEN (firmennachrichten.de)

**32. `portal-network/sites/firmennachrichten.de/static/img/autor-redaktion.webp`** – 512×512, 1:1 (wird rund beschnitten), webp + jpg  
Verwendung: Autoren-Platzhalter auf /autoren/redaktion/ (kein Foto einer echten Person)

```
Editorial flat vector illustration, calm serious business-news look, clean geometric shapes, warm off-white background, limited palette of deep crimson red (#B3261E), charcoal grey and soft sand beige, subtle paper grain, generous negative space, no text. Subject: an abstract round emblem of a fountain pen nib crossing a small circuit line, centred, flat, symbolising an editorial team (no person). Composition: main subject centred with calm margins, aspect ratio 1:1. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`

### ITSZENE (itszene.de)

**33. `portal-network/sites/itszene.de/static/img/autor-redaktion.webp`** – 512×512, 1:1 (wird rund beschnitten), webp + jpg  
Verwendung: Autoren-Platzhalter auf /autoren/redaktion/ (kein Foto einer echten Person)

```
Clean isometric flat illustration, modern IT for small and medium businesses, soft shadows, palette of petrol blue (#0B6A8A), deep navy, light grey and a touch of cyan, minimal and precise, no text. Subject: an abstract round emblem of a fountain pen nib crossing a small circuit line, centred, flat, symbolising an editorial team (no person). Composition: main subject centred with calm margins, aspect ratio 1:1. High quality, crisp, professional, no text, no logos.
```
Negativ: `text, letters, words, typography, numbers, captions, logo, watermark, signature, brand marks, trademark, real company logos, real people, celebrity, recognizable faces, portrait of a specific person, readable screen content, flags, blurry, low quality, jpeg artifacts, distorted hands, extra fingers, cluttered, oversaturated`
