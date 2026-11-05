"""Static-Site-Builder: erzeugt einen Ordner pro Domain (dist/<domain>/)."""
import json
import pathlib
import re
import shutil
import string
import xml.sax.saxutils as sax

from . import brand, content, frontmatter, md
from .config import ROOT
from .util import (PLACEHOLDER_RE, de_date, de_number, esc, has_placeholder, now,
                   rfc822, strip_tags, truncate)

TEMPLATE = string.Template((ROOT / "templates" / "base.html").read_text(encoding="utf-8"))
LEGAL_DIR = ROOT / "legal"
SHARED_STATIC = ROOT / "static"
ASSET_VERSION = "1"

# Reservierte Höhen der Anzeigenflächen (px) – verhindert Layout-Verschiebungen (CLS)
AD_SLOTS = {
    "home_top": 250, "list_top": 250, "article_top": 280,
    "article_mid": 280, "article_bottom": 250, "sidebar": 600, "profile": 250,
}

TYPE_LABEL = {"news": "Nachrichtenportal", "review": "Bewertungsportal", "operator": "Netzwerkseite"}

# Rechts- und Vertrauensseiten je Portaltyp: (Slug, Datei in legal/)
LEGAL_PAGES = {
    "news": ["impressum", "datenschutz", "nutzungsbedingungen", "redaktionsgrundsaetze",
             "korrekturen", "ueber-uns", "kontakt"],
    "review": ["impressum", "datenschutz", "nutzungsbedingungen", "redaktionsgrundsaetze",
               "korrekturen", "ueber-uns", "kontakt", "so-funktionieren-bewertungen",
               "score-methodik", "bewertungsrichtlinien", "melden", "fuer-unternehmen",
               "bewertung-schreiben"],
    "operator": ["impressum", "datenschutz", "nutzungsbedingungen", "redaktionsgrundsaetze",
                 "ueber-uns", "kontakt"],
}

VERIFICATION = [
    ("organisch", "Organisch", "Stufe 0", "E-Mail-Adresse der bewertenden Person bestätigt."),
    ("eingeladen", "Eingeladen", "Stufe 1", "Einladung durch das Unternehmen (Auftrags- oder Kundennummer)."),
    ("verifiziert", "Verifiziert", "Stufe 2", "Beleg (z. B. Rechnung oder Vertrag) geprüft; der Beleg wird nach der Prüfung gelöscht."),
]


def _json_ld(obj):
    return ('<script type="application/ld+json">'
            + json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
            + "</script>")


def stars(score):
    full = int(round(score or 0))
    return (f'<span class="stars" role="img" aria-label="{de_number(score or 0)} von 5 Sternen">'
            f'{"★" * full}{"☆" * (5 - full)}</span>')


class SiteBuilder:
    def __init__(self, cfg, network, all_sites, out_root, mode="live"):
        self.cfg = cfg
        self.net = network
        self.all_sites = all_sites
        self.mode = mode  # live | preview | test
        self.domain = cfg["domain"]
        self.base = f"https://{self.domain}"
        self.out = pathlib.Path(out_root) / self.domain
        self.type = cfg["type"]
        self.pages = []      # dicts: url, lastmod, indexable
        self.search = []
        self.warnings = []
        self.now = now()
        inc = mode == "preview"  # Testbuild prüft gerade die Freigabe-Filterung
        cdir = cfg["_dir"] / "content"
        dirs = lambda sub: [cdir / sub] + ([ROOT / "tests" / "fixtures" / self.domain / sub] if mode == "test" else [])
        self.articles, self.draft_articles = content.load_articles(dirs("articles"), cfg, inc)
        self.companies, self.draft_companies = content.load_json_items(dirs("companies"), inc)
        self.people, self.draft_people = content.load_json_items(dirs("people"), inc)
        if self.type == "review":
            sc = cfg["review"]["score"]
            for c in self.companies:
                c["reviews"] = [r for r in c.get("reviews", [])
                                if r.get("status") == "approved" or (inc and r.get("status") == "draft")]
                c["stats"] = content.compute_score(c["reviews"], sc, self.now)
        self.company_by_slug = {c["slug"]: c for c in self.companies}
        self.person_by_slug = {p["slug"]: p for p in self.people}
        client = (cfg.get("adsense_client_id") or "").strip()
        self.adsense = client

    # ------------------------------------------------------------ Hilfen
    def url(self, path):
        return self.base + path

    def sisters(self):
        return [s for s in self.all_sites
                if s.get("enabled") and s["type"] in ("news", "review", "operator") and s["domain"] != self.domain]

    def find_img(self, name, exts=(".webp", ".jpg", ".jpeg", ".png")):
        """'img/hero' → '/static/img/hero.webp' falls Datei existiert, sonst None."""
        static = self.cfg["_dir"] / "static"
        if name.startswith("/static/"):
            return name if (static / name[len("/static/"):]).is_file() else None
        for ext in exts:
            if (static / (name + ext)).is_file():
                return f"/static/{name}{ext}"
        return None

    def media(self, img_name, cls="", alt=""):
        src = self.find_img(img_name) if img_name else None
        style = f' style="--img:url(\'{esc(src)}\')"' if src else ""
        role = f' role="img" aria-label="{esc(alt)}"' if (alt and src) else ' aria-hidden="true"'
        return f'<div class="media {cls}"{style}{role}></div>'

    def article_media(self, a, cls=""):
        if a.get("image") and self.find_img(a["image"]):
            return self.media(a["image"], cls, a.get("image_alt") or a["title"])
        return self.media(f"img/ressorts/{a['ressort']}", cls)

    def ad(self, name, enabled=True):
        if not enabled:
            return ""
        h = AD_SLOTS[name]
        slot_id = (self.cfg.get("adsense_slots") or {}).get(name, "")
        if self.adsense and slot_id:
            return (f'<aside class="ad ad--live" aria-label="Anzeige" style="--ad-h:{h}px">'
                    f'<span class="ad-label">Anzeige</span>'
                    f'<ins class="adsbygoogle" style="display:block;min-height:{h - 24}px" '
                    f'data-ad-client="{esc(self.adsense)}" data-ad-slot="{esc(slot_id)}" '
                    f'data-ad-format="auto" data-full-width-responsive="true"></ins>'
                    f'<script>(adsbygoogle=window.adsbygoogle||[]).push({{}});</script></aside>')
        return f'<div class="ad ad--reserved" aria-hidden="true" data-slot="{name}" style="--ad-h:{h}px"></div>'

    def contact_email(self):
        return self.cfg.get("contact_email") or self.net["operator"]["email"]

    def email_html(self, addr=None):
        addr = addr or self.contact_email()
        if has_placeholder(addr):
            return f'<mark class="ph">{esc(addr)}</mark>'
        return f'<a href="mailto:{esc(addr)}">{esc(addr)}</a>'

    def email_md(self, addr=None):
        addr = addr or self.contact_email()
        return addr if has_placeholder(addr) else f"[{addr}](mailto:{addr})"

    def breadcrumbs(self, trail):
        """trail: [(Name, Pfad|None), …] – Startseite wird ergänzt."""
        items = [("Startseite", "/")] + trail
        lis = []
        for i, (name, path) in enumerate(items):
            last = i == len(items) - 1
            lis.append(f'<li>{esc(name)}</li>' if last or not path
                       else f'<li><a href="{esc(path)}">{esc(name)}</a></li>')
        ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, **({"item": self.url(p)} if p else {})}
            for i, (n, p) in enumerate(items)]}
        return f'<nav class="breadcrumbs" aria-label="Brotkrumen"><ol>{"".join(lis)}</ol></nav>', ld

    # ------------------------------------------------------------ Seitenrahmen
    def nav_items(self):
        c = self.cfg
        if self.type == "news":
            items = [(r["name"], f"/{r['slug']}/") for r in c["ressorts"] if r.get("nav", True)]
            return items + [("Suche", "/suche/")]
        if self.type == "review":
            return [("Kategorien", "/kategorien/"), ("Ratgeber", "/ratgeber/"),
                    ("So funktionieren Bewertungen", "/so-funktionieren-bewertungen/"),
                    ("Für Unternehmen", "/fuer-unternehmen/"), ("Suche", "/suche/")]
        return [("Portale", "/#portale"), ("Über uns", "/ueber-uns/"),
                ("Grundsätze", "/redaktionsgrundsaetze/"), ("Kontakt", "/kontakt/")]

    def footer(self):
        c, op = self.cfg, self.net["operator"]
        portal_links = [("Über uns", "/ueber-uns/"), ("Redaktionsgrundsätze", "/redaktionsgrundsaetze/")]
        if self.type in ("news", "review"):
            portal_links.append(("Korrekturen", "/korrekturen/"))
        if self.type == "news":
            portal_links.append(("Autoren", "/autoren/redaktion/"))
        if self.type == "review":
            portal_links += [("Score-Methodik", "/score-methodik/"),
                             ("Bewertungsrichtlinien", "/bewertungsrichtlinien/"),
                             ("Inhalt melden", "/melden/")]
        portal_links.append(("Kontakt", "/kontakt/"))
        legal = [("Impressum", "/impressum/"), ("Datenschutz", "/datenschutz/"),
                 ("Nutzungsbedingungen", "/nutzungsbedingungen/")]
        li = lambda xs: "".join(f'<li><a href="{esc(u)}">{esc(n)}</a></li>' for n, u in xs)
        consent = ('<li><button type="button" class="linklike" id="consent-settings">'
                   'Datenschutzeinstellungen</button></li>') if self.adsense else ""
        sis = "".join(f'<li><a href="https://{esc(s["domain"])}/">{esc(s["name"])}</a></li>'
                      for s in self.sisters())
        op_site = next((s for s in self.all_sites if s["type"] == "operator" and s.get("enabled")), None)
        brand_link = (f'<a href="https://{op_site["domain"]}/">{esc(self.net["brand"])}</a>'
                      if op_site and op_site["domain"] != self.domain else esc(self.net["brand"]))
        return (
            f'<section><h2>{esc(c["name"])}</h2><p>{esc(c["description"])}</p>'
            f'<p>Ein Angebot von {brand_link} – eine Marke der {esc(op["legal_name"])}{"" if op["legal_name"].endswith(".") else "."}</p></section>'
            f'<section><h2>{"Portal" if self.type != "operator" else "Netzwerk"}</h2><ul>{li(portal_links)}</ul></section>'
            f'<section><h2>Rechtliches</h2><ul>{li(legal)}{consent}</ul></section>'
            f'<section><h2>Schwesterportale</h2><ul>{sis or "<li>–</li>"}</ul></section>'
            f'<p class="footer-bottom">© {self.now.year} {esc(op["legal_name"])} · '
            f'Werbung ist stets als „Anzeige“ gekennzeichnet. Redaktion und Bewertungen sind nicht käuflich.</p>')

    def render(self, path, title, description, body, *, jsonld=(), og_type="website",
               image=None, noindex=False, body_class="", full_title=None, lastmod=None,
               search=None, active=None):
        c = self.cfg
        noindex = noindex or self.mode != "live"
        accent, accent2 = c["accent"], c.get("accent_2", c["accent"])
        dark, dark2 = c["accent_dark"], c.get("accent_2_dark", c["accent_dark"])
        theme = (f":root{{--accent:{accent};--accent-2:{accent2}}}"
                 f"@media (prefers-color-scheme:dark){{:root{{--accent:{dark};--accent-2:{dark2};--on-accent:#111}}}}")
        og_img = image or self.find_img("img/og-default", (".jpg", ".png"))
        og_html = ""
        if og_img:
            og_html = (f'<meta property="og:image" content="{esc(self.url(og_img))}">'
                       f'<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
                       f'<meta name="twitter:image" content="{esc(self.url(og_img))}">')
        head_extra = []
        if self.adsense:
            head_extra.append(f'<meta name="google-adsense-account" content="{esc(self.adsense)}">'
                              f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={esc(self.adsense)}" crossorigin="anonymous"></script>')
        verify = c.get("google_site_verification")
        if verify:
            head_extra.append(f'<meta name="google-site-verification" content="{esc(verify)}">')
        feed = (f'<link rel="alternate" type="application/rss+xml" title="{esc(c["name"])}" href="/feed.xml">'
                if self.type in ("news", "review") else "")
        an = c.get("analytics") or {}
        body_attrs = ""
        if an.get("script_url") and self.mode == "live":
            body_attrs = (f' data-analytics-src="{esc(an["script_url"])}" data-analytics-id="{esc(an.get("website_id", ""))}"'
                          f' data-analytics-consent="{"true" if an.get("require_consent", True) else "false"}"')
        cur = ' aria-current="page"'
        nav = "".join(
            f'<li><a href="{esc(u)}"{cur if (active or path) == u else ""}>{esc(n)}</a></li>'
            for n, u in self.nav_items())
        if self.type == "news":
            action = '<a class="btn btn-small btn-ghost header-action" href="/suche/">Suche</a>'
        elif self.type == "review":
            action = '<a class="btn btn-small header-action" href="/bewertung-schreiben/">Bewertung schreiben</a>'
        else:
            action = ""
        banner = ""
        if self.mode == "preview":
            banner = '<div class="preview-banner">VORSCHAU – enthält nicht freigegebene Entwürfe · nicht öffentlich</div>'
        elif self.mode == "test":
            banner = '<div class="preview-banner">TESTBUILD mit fiktiven Testdaten – nicht veröffentlichen</div>'
        html = TEMPLATE.substitute(
            title=esc(full_title or f"{title} | {c['name']}"),
            og_title=esc(title), description=esc(truncate(description, 170)),
            canonical=esc(self.url(path)), robots="noindex, follow" if noindex else "index, follow, max-image-preview:large",
            accent=esc(accent), asset_version=ASSET_VERSION, theme_css=theme, feed_link=feed,
            site_name=esc(c["name"]), og_type=og_type, og_image=og_html,
            twitter_card="summary_large_image" if og_img else "summary",
            head_extra="\n".join(head_extra), jsonld="\n".join(_json_ld(j) for j in jsonld),
            body_class=esc(f"type-{self.type} {body_class}".strip()), body_attrs=body_attrs,
            preview_banner=banner, logo=self.logo_inline, claim=esc(c["claim"]),
            header_action=action, nav=nav, content=body, footer=self.footer(), body_end="")
        # Abkürzung „i.G.“ am Satzende: keinen doppelten Punkt erzeugen
        html = re.sub(r"i\.G\.(</strong>|</a>)?\.", r"i.G.\1", html)
        self.write(path, html)
        self.pages.append({"url": path, "lastmod": lastmod or self.now, "indexable": not noindex})
        if search:
            self.search.append({"url": path, "title": title, "text": truncate(search.get("text", description), 300),
                                "section": search.get("section", "")})

    def write(self, path, data):
        if path.endswith("/"):
            target = self.out / path.lstrip("/") / "index.html"
        else:
            target = self.out / path.lstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data, encoding="utf-8")

    # ------------------------------------------------------------ Bausteine
    def org_ld(self):
        op = self.net["operator"]
        t = {"news": "NewsMediaOrganization", "review": "Organization", "operator": "Organization"}[self.type]
        ld = {"@context": "https://schema.org", "@type": t, "name": self.cfg["name"], "url": self.base + "/",
              "logo": self.url("/static/logo.svg"), "description": self.cfg["description"],
              "parentOrganization": {"@type": "Organization", "name": op["legal_name"].replace(" i.G.", ""),
                                     "brand": {"@type": "Brand", "name": self.net["brand"]}}}
        if self.type != "operator":
            ld["publishingPrinciples"] = self.url("/redaktionsgrundsaetze/")
            if self.type in ("news", "review"):
                ld["correctionsPolicy"] = self.url("/korrekturen/")
            ld["ethicsPolicy"] = self.url("/redaktionsgrundsaetze/")
        return ld

    def newsletter_box(self):
        nl = self.cfg["newsletter"]
        media_name = "img/newsletter"
        has_media = bool(self.find_img(media_name))
        if nl.get("action"):
            form = (f'<form class="form-row" method="post" action="{esc(nl["action"])}">'
                    f'<label class="visually-hidden" for="nl-email">E-Mail-Adresse</label>'
                    f'<input id="nl-email" type="email" name="email" required autocomplete="email" placeholder="E-Mail-Adresse">'
                    f'<button class="btn" type="submit">Anmelden</button></form>'
                    f'<p class="form-note">Kostenlos, jederzeit abbestellbar. Wir senden Ihnen zuerst eine Bestätigungs-E-Mail (Double-Opt-in). '
                    f'Details in der <a href="/datenschutz/#newsletter">Datenschutzerklärung</a>.</p>')
        else:
            form = ('<p class="form-note"><strong>Startet in Kürze.</strong> Die Anmeldung wird freigeschaltet, '
                    'sobald der Versand eingerichtet ist (Double-Opt-in).</p>')
        return (f'<section class="newsletter{" with-media" if has_media else ""}" aria-labelledby="nl-h">'
                f'{self.media(media_name) if has_media else ""}<div>'
                f'<h2 id="nl-h">{esc(nl["name"])}</h2><p>{esc(nl.get("description", ""))}</p>{form}</div></section>')

    def article_card(self, a, heading="h3", show_media=True):
        meta = f'<time datetime="{a["date"].isoformat()}">{de_date(a["date"])}</time>'
        if a["kind"] == "ratgeber":
            meta = f'Ratgeber · {a["reading_min"]} Min. Lesezeit'
        flag = ' <span class="draft-flag">ENTWURF</span>' if a["status"] != "approved" else ""
        return (f'<article class="card">{self.article_media(a) if show_media else ""}'
                f'<p class="kicker">{esc(a["ressort_name"])}{" · " + esc(a["region"]) if a["region"] else ""}</p>'
                f'<{heading}><a href="{a["url"]}">{esc(a["title"])}</a>{flag}</{heading}>'
                f'<p>{esc(a["teaser"])}</p><p class="meta">{meta}</p></article>')

    # ------------------------------------------------------------ Build
    def build(self):
        if self.out.exists():
            shutil.rmtree(self.out)
        self.out.mkdir(parents=True)
        shutil.copytree(SHARED_STATIC, self.out / "static")
        site_static = self.cfg["_dir"] / "static"
        if site_static.is_dir():
            shutil.copytree(site_static, self.out / "static", dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns(".gitkeep", "*.md"))
        c = self.cfg
        parts = c["wordmark"]
        self.logo_inline = brand.wordmark(parts, "var(--accent)", c["glyph"], c["name"])
        self.write("/static/logo.svg", '<?xml version="1.0" encoding="UTF-8"?>\n'
                   + brand.wordmark(parts, c["accent"], c["glyph"], c["name"], text_color="#16181d", height=64))
        self.write("/favicon.svg", brand.favicon(c["accent"], c["glyph"]))
        if self.type == "news":
            self.build_news()
        elif self.type == "review":
            self.build_review()
        else:
            self.build_operator()
        self.build_legal()
        if self.type != "operator":
            self.build_search_page()
        self.build_404()
        self.build_seo_files()
        return self

    # ---------------- Nachrichtenportal
    def build_news(self):
        c = self.cfg
        arts = self.articles
        by_ressort = {}
        for a in arts:
            by_ressort.setdefault(a["ressort"], []).append(a)
        region = c.get("region")
        # Startseite
        lead = next((a for a in arts if a["featured"]), arts[0] if arts else None)
        if lead:
            lead_html = (f'<section class="lead-story" aria-label="Aufmacher">{self.article_media(lead, "media-wide")}'
                         f'<div><p class="kicker">Aufmacher · {esc(lead["ressort_name"])}</p>'
                         f'<h2><a href="{lead["url"]}">{esc(lead["title"])}</a></h2>'
                         f'<p>{esc(lead["teaser"])}</p><p class="meta">{de_date(lead["date"])}</p></div></section>')
        else:
            lead_html = (f'<section class="lead-story" aria-label="Aufmacher">{self.media("img/hero", "media-wide")}'
                         f'<div class="welcome"><h1>{esc(c["name"])}</h1><p><strong>{esc(c["claim"])}</strong></p>'
                         f'<p>{esc(c["description"])}</p>'
                         f'<p>Die ersten Beiträge erscheinen in Kürze. Jeder Beitrag wird vor der Veröffentlichung '
                         f'von der Redaktion geprüft und freigegeben – wie das funktioniert, steht in unseren '
                         f'<a href="/redaktionsgrundsaetze/">Redaktionsgrundsätzen</a>.</p></div></section>')
        tiles = []
        for r in c["ressorts"]:
            if r["slug"] == "aktuell":
                continue
            items = by_ressort.get(r["slug"], [])
            if r["slug"] == "regional" and region:
                items = [a for a in arts if a["region"] == region]
            lis = "".join(f'<li><a href="{a["url"]}">{esc(a["title"])}</a></li>' for a in items[:3])
            inner = f"<ul>{lis}</ul>" if lis else '<p class="empty">Noch keine Beiträge in diesem Ressort.</p>'
            tiles.append(f'<section class="tile">{self.media("img/ressorts/" + r["slug"])}<div class="tile-body">'
                         f'<h2><a href="/{r["slug"]}/">{esc(r["name"])}</a></h2><p>{esc(r["description"])}</p>'
                         f'{inner}<a class="more" href="/{r["slug"]}/">Alle Beiträge: {esc(r["name"])} →</a></div></section>')
        h1 = "" if not lead else f'<h1 class="visually-hidden">{esc(c["name"])} – {esc(c["claim"])}</h1>'
        body = (f'{h1}{lead_html}{self.ad("home_top", bool(arts))}'
                f'<h2 class="visually-hidden">Ressorts</h2><div class="tiles">{"".join(tiles)}</div>'
                f'{self.newsletter_box()}')
        website_ld = {"@context": "https://schema.org", "@type": "WebSite", "name": c["name"], "url": self.base + "/",
                      "inLanguage": "de-DE", "potentialAction": {"@type": "SearchAction",
                      "target": self.url("/suche/?q={search_term_string}"), "query-input": "required name=search_term_string"}}
        self.render("/", c["name"], c["description"], body, jsonld=[website_ld, self.org_ld()],
                    full_title=f"{c['name']} – {c['claim']}", body_class="home")

        # Ressortseiten
        for r in c["ressorts"]:
            slug = r["slug"]
            if slug == "aktuell":
                items = arts[:40]
            elif slug == "regional" and region:
                items = [a for a in arts if a["region"] == region]
            else:
                items = by_ressort.get(slug, [])
            extra = ""
            if slug == c.get("people_ressort") and self.people:
                extra += "<h2>Personen</h2><ul>" + "".join(
                    f'<li><a href="/{slug}/{p["slug"]}/">{esc(p["name"])}</a></li>' for p in self.people) + "</ul>"
            if slug == c.get("company_ressort") and self.companies:
                extra += "<h2>Unternehmensprofile</h2><ul>" + "".join(
                    f'<li><a href="/unternehmen/{co["slug"]}/">{esc(co["name"])}</a></li>' for co in self.companies) + "</ul>"
            self.list_page(f"/{slug}/", r["name"], r.get("intro") or r["description"], items, extra=extra,
                           crumbs=[(r["name"], None)])
        # Artikel
        for a in arts:
            self.article_page(a)
        # Firmen- und Personenseiten
        for co in self.companies:
            self.news_company_page(co)
        for p in self.people:
            self.person_page(p)
        # Autorenseite
        self.author_page()

    def list_page(self, path, name, intro, items, extra="", crumbs=None, empty_text=None):
        crumb_html, crumb_ld = self.breadcrumbs(crumbs or [(name, None)])
        cards = "".join(self.article_card(a) for a in items)
        if cards:
            listing = f'{self.ad("list_top")}<div class="cards three">{cards}</div>'
        else:
            listing = (f'<div class="empty-state"><h2>Noch keine Beiträge</h2>'
                       f'<p>{esc(empty_text or "Hier erscheinen in Kürze die ersten Beiträge. Alle Beiträge werden vor der Veröffentlichung redaktionell geprüft.")}</p>'
                       f'<p><a href="/redaktionsgrundsaetze/">So arbeitet unsere Redaktion</a></p></div>')
        body = (f'{crumb_html}<header class="page-head"><h1>{esc(name)}</h1><p class="lead">{esc(intro)}</p></header>'
                f'{listing}{extra}{self.newsletter_box()}')
        self.render(path, name, intro, body, jsonld=[crumb_ld], noindex=not items and not extra,
                    search={"text": intro, "section": "Rubrik"})

    def article_page(self, a):
        c = self.cfg
        crumb_html, crumb_ld = self.breadcrumbs([(a["ressort_name"], f"/{a['ressort']}/"), (a["title"], None)])
        html = a["html"]
        # Anzeige nach dem ersten Absatz und vor der dritten Zwischenüberschrift
        html = html.replace("</p>", "</p>" + self.ad("article_top"), 1)
        h2s = [m.start() for m in re.finditer(r"<h2", html)]
        if len(h2s) >= 3:
            html = html[:h2s[2]] + self.ad("article_mid") + html[h2s[2]:]
        updated = ""
        if a["updated"] and a["updated"] > a["date"]:
            updated = f' · aktualisiert <time datetime="{a["updated"].isoformat()}">{de_date(a["updated"])}</time>'
        src_items = "".join(
            f'<li>{esc(s["text"])}' + (f' – <a href="{esc(s["url"])}" rel="noopener" target="_blank">{esc(s["url"])}</a>' if s["url"] else "") + "</li>"
            for s in a["sources"])
        sources = (f'<section class="box" aria-labelledby="src-h"><h2 id="src-h">Quellen</h2><ul>{src_items}</ul></section>'
                   if src_items else "")
        corr = ""
        if a["corrections"]:
            corr = ('<section class="box" aria-labelledby="corr-h"><h2 id="corr-h">Korrekturen</h2><ul>'
                    + "".join(f"<li>{md.inline(str(x))}</li>" for x in a["corrections"]) + "</ul></section>")
        cos = [self.company_by_slug[s] for s in a["companies"] if s in self.company_by_slug]
        ppl = [self.person_by_slug[s] for s in a["people"] if s in self.person_by_slug]
        chips = ""
        if cos or ppl:
            pr = c.get("people_ressort", "koepfe")
            chips = ('<section class="box"><h2>Im Beitrag erwähnt</h2><ul>'
                     + "".join(f'<li><a href="/unternehmen/{x["slug"]}/">{esc(x["name"])}</a></li>' for x in cos)
                     + "".join(f'<li><a href="/{pr}/{x["slug"]}/">{esc(x["name"])}</a></li>' for x in ppl)
                     + "</ul></section>")
        sister = ""
        for co in cos:
            if co.get("review_profile"):
                sister += (f'<section class="box"><h2>Erfahrungen mit {esc(co["name"])}</h2>'
                           f'<p>Kundenbewertungen finden Sie auf unserem Schwesterportal: '
                           f'<a href="{esc(co["review_profile"])}">{esc(co["review_profile"])}</a> '
                           f'(gleicher Betreiber, unabhängige Redaktion).</p></section>')
        tags = ("<ul class=\"tags\" aria-label=\"Schlagwörter\">" + "".join(f"<li>{esc(t)}</li>" for t in a["tags"]) + "</ul>") if a["tags"] else ""
        ai = (f'<p class="box ai-note">{esc(c.get("ai_note", self.net["ai_note"]))} '
              f'<a href="/redaktionsgrundsaetze/#ki-workflow">Mehr zu unserem Arbeitsablauf</a>.</p>')
        related = [x for x in self.articles if x["ressort"] == a["ressort"] and x is not a][:3]
        rel_html = (f'<section aria-labelledby="rel-h"><h2 id="rel-h">Mehr aus {esc(a["ressort_name"])}</h2>'
                    f'<div class="cards three">{"".join(self.article_card(x, show_media=False) for x in related)}</div></section>'
                    if related else "")
        flag = '<p><span class="draft-flag">ENTWURF – nicht freigegeben</span></p>' if a["status"] != "approved" else ""
        author_url = "/autoren/redaktion/" if self.type == "news" else "/ueber-uns/"
        body = (f'{crumb_html}<div class="layout"><article class="article">{flag}'
                f'<p class="kicker">{esc(a["ressort_name"])}{" · " + esc(a["region"]) if a["region"] else ""}</p>'
                f'<h1>{esc(a["title"])}</h1><p class="teaser">{esc(a["teaser"])}</p>'
                f'<p class="meta">Von <a href="{author_url}">{esc(a["author"])}</a> · '
                f'<time datetime="{a["date"].isoformat()}">{de_date(a["date"])}</time>{updated}'
                f' · {a["reading_min"]} Min. Lesezeit</p>'
                f'<figure>{self.article_media(a, "media-wide")}'
                f'{"<figcaption>" + esc(a["image_alt"]) + "</figcaption>" if a["image_alt"] and a["image"] else ""}</figure>'
                f'<div class="article-body">{html}</div>{sources}{corr}{chips}{sister}{ai}{tags}</article>'
                f'</div>{self.ad("article_bottom")}{rel_html}{self.newsletter_box()}')
        img = a["image"] if a.get("image") and self.find_img(a["image"]) and a["image"].endswith((".jpg", ".png")) else None
        ld_img = self.url(img) if img else (self.url(self.find_img("img/og-default", (".jpg", ".png")))
                                            if self.find_img("img/og-default", (".jpg", ".png")) else None)
        art_ld = {"@context": "https://schema.org",
                  "@type": "NewsArticle" if a["kind"] == "news" else "Article",
                  "headline": a["title"][:110], "description": a["teaser"],
                  "datePublished": a["date"].isoformat(),
                  "dateModified": (a["updated"] or a["date"]).isoformat(),
                  "mainEntityOfPage": self.url(a["url"]), "inLanguage": "de-DE",
                  "articleSection": a["ressort_name"], "wordCount": a["words"],
                  "author": {"@type": "Organization", "name": a["author"], "url": self.url(author_url)},
                  "publisher": {"@type": "Organization", "name": c["name"],
                                "logo": {"@type": "ImageObject", "url": self.url("/static/logo.svg")}}}
        if ld_img:
            art_ld["image"] = [ld_img]
        self.render(a["url"], a["title"], a["teaser"], body, jsonld=[art_ld, crumb_ld], og_type="article",
                    image=img, noindex=a["noindex"], lastmod=a["updated"] or a["date"],
                    search={"text": a["teaser"], "section": a["ressort_name"]}, active=f"/{a['ressort']}/")

    def news_company_page(self, co):
        crumb_html, crumb_ld = self.breadcrumbs([("Unternehmen", "/unternehmen/"), (co["name"], None)])
        facts = [("Rechtsform", co.get("legal_form")), ("Sitz", co.get("city")), ("Register", co.get("register")),
                 ("Gründung", co.get("founded")), ("Branche", co.get("industry"))]
        dl = "".join(f"<dt>{k}</dt><dd>{esc(v)}</dd>" for k, v in facts if v)
        if co.get("website"):
            dl += f'<dt>Website</dt><dd><a href="{esc(co["website"])}" rel="noopener nofollow" target="_blank">{esc(co["website"])}</a></dd>'
        pr = self.cfg.get("people_ressort", "koepfe")
        mgmt = "".join(f'<li><a href="/{pr}/{p["slug"]}/">{esc(p["name"])}</a></li>'
                       for p in self.people if any(r.get("company_slug") == co["slug"] for r in p.get("roles", [])))
        related = [a for a in self.articles if co["slug"] in a["companies"]]
        arts = "".join(self.article_card(a, show_media=False) for a in related)
        sister = (f'<section class="box"><h2>Kundenerfahrungen</h2><p>Bewertungen zu diesem Unternehmen auf unserem '
                  f'Schwesterportal: <a href="{esc(co["review_profile"])}">{esc(co["review_profile"])}</a></p></section>'
                  if co.get("review_profile") else "")
        source = f'<p class="meta">Datenquelle: {esc(co["data_source"])}</p>' if co.get("data_source") else ""
        body = (f'{crumb_html}<header class="page-head"><p class="kicker">Unternehmensprofil</p><h1>{esc(co["name"])}</h1>'
                f'<p class="lead">{esc(co.get("description", ""))}</p></header>'
                f'<section class="box"><h2>Stammdaten</h2><dl class="facts">{dl}</dl>{source}</section>'
                f'{"<section><h2>Geschäftsführung</h2><ul>" + mgmt + "</ul></section>" if mgmt else ""}'
                f'{sister}<section><h2>Beiträge zum Unternehmen</h2>'
                f'{"<div class=cards>" + arts + "</div>" if arts else "<p class=empty>Noch keine Beiträge.</p>"}</section>')
        ld = {"@context": "https://schema.org", "@type": "Organization", "name": co["name"],
              "url": co.get("website") or self.url(f"/unternehmen/{co['slug']}/")}
        if co.get("city"):
            ld["address"] = {"@type": "PostalAddress", "addressLocality": co["city"], "addressCountry": "DE"}
        # Indexierungsschwelle (Konzept 8.9): erst mit ≥ 1 Artikel
        self.render(f"/unternehmen/{co['slug']}/", co["name"], co.get("description") or f"Unternehmensprofil {co['name']}",
                    body, jsonld=[ld, crumb_ld], noindex=not related,
                    search={"text": co.get("description", ""), "section": "Unternehmen"})

    def person_page(self, p):
        pr = self.cfg.get("people_ressort", "koepfe")
        pr_name = next((r["name"] for r in self.cfg["ressorts"] if r["slug"] == pr), "Köpfe")
        crumb_html, crumb_ld = self.breadcrumbs([(pr_name, f"/{pr}/"), (p["name"], None)])
        rows = []
        for r in p.get("roles", []):
            co = self.company_by_slug.get(r.get("company_slug", ""))
            comp = f'<a href="/unternehmen/{co["slug"]}/">{esc(co["name"])}</a>' if co else esc(r.get("company", ""))
            period = f'{esc(r.get("from", ""))} – {esc(r.get("to") or "heute")}'
            rows.append(f"<tr><td>{esc(r.get('title', ''))}</td><td>{comp}</td><td>{period}</td></tr>")
        related = [a for a in self.articles if p["slug"] in a["people"]]
        arts = "".join(self.article_card(a, show_media=False) for a in related)
        current = next((r for r in p.get("roles", []) if not r.get("to")), None)
        body = (f'{crumb_html}<header class="page-head"><p class="kicker">Person · berufliche Rolle</p>'
                f'<h1>{esc(p["name"])}</h1>{"<p class=lead>" + esc(p["summary"]) + "</p>" if p.get("summary") else ""}</header>'
                f'<section><h2>Funktionen</h2><div class="table-wrap"><table><thead><tr><th scope="col">Funktion</th>'
                f'<th scope="col">Unternehmen</th><th scope="col">Zeitraum</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div></section>'
                f'<section><h2>Beiträge</h2>{"<div class=cards>" + arts + "</div>" if arts else "<p class=empty>Noch keine Beiträge.</p>"}</section>'
                f'<p class="box">Diese Seite enthält ausschließlich Angaben zur beruflichen Rolle aus öffentlich zugänglichen Quellen. '
                f'Keine privaten Daten. Korrektur- oder Löschwünsche: <a href="/kontakt/">Kontakt</a>.</p>')
        ld = {"@context": "https://schema.org", "@type": "Person", "name": p["name"],
              "url": self.url(f"/{pr}/{p['slug']}/")}
        if current:
            ld["jobTitle"] = current.get("title", "")
            if current.get("company"):
                ld["worksFor"] = {"@type": "Organization", "name": current["company"]}
        self.render(f"/{pr}/{p['slug']}/", p["name"], p.get("summary") or f"Berufliche Stationen von {p['name']}",
                    body, jsonld=[ld, crumb_ld], noindex=not related,
                    search={"text": p.get("summary", ""), "section": "Person"})

    def author_page(self):
        c = self.cfg
        crumb_html, crumb_ld = self.breadcrumbs([("Autoren", None), (c.get("default_author", "Redaktion"), None)])
        op = self.net["operator"]
        body = (f'{crumb_html}<article class="legal">{self.media("img/autor-redaktion", "avatar")}<h1>{esc(c.get("default_author", "Redaktion"))}</h1>'
                f'<p class="lead">Die Redaktion von {esc(c["name"])} berichtet {esc(c.get("author_focus", "über Unternehmen und Wirtschaft"))}.</p>'
                f'<p>Beiträge entstehen in einem festen Ablauf: Regeln wählen Quellen aus (z. B. amtliche Bekanntmachungen und '
                f'Pressemitteilungen), ein KI-System erstellt daraus einen Entwurf und prüft ihn in einem zweiten Durchlauf gegen die Quellen. '
                f'Veröffentlicht wird ein Beitrag erst, wenn ein verantwortlicher Mensch ihn geprüft und freigegeben hat.</p>'
                f'<p>Verantwortlich nach § 18 Abs. 2 MStV: {md.inline(op["mstv_responsible"])}</p>'
                f'<p>Mehr dazu: <a href="/redaktionsgrundsaetze/">Redaktionsgrundsätze</a> · <a href="/korrekturen/">Korrekturen</a> · '
                f'<a href="/kontakt/">Kontakt zur Redaktion</a></p></article>')
        self.render("/autoren/redaktion/", c.get("default_author", "Redaktion"),
                    f"Wer bei {c['name']} schreibt und wie Beiträge entstehen.", body, jsonld=[crumb_ld])

    # ---------------- Bewertungsportal
    def build_review(self):
        c = self.cfg
        rv = c["review"]
        services = rv["services"]
        # Startseite
        recent = sorted(((co, r) for co in self.companies for r in co["reviews"]),
                        key=lambda x: x[1].get("date", ""), reverse=True)[:6]
        if recent:
            rec_html = "".join(
                f'<article class="card"><p class="kicker">{esc(co["name"])}</p><h3><a href="/firma/{co["slug"]}/">{esc(r.get("title", "Bewertung"))}</a></h3>'
                f'<p>{stars(r["rating"])} <span class="badge badge-{esc(r.get("verification", "organisch"))}">{esc(r.get("verification", "organisch").capitalize())}</span></p>'
                f'<p>{esc(truncate(r.get("text", ""), 160))}</p></article>' for co, r in recent)
            rec_html = f'<div class="cards three">{rec_html}</div>'
        else:
            rec_html = self.empty_reviews("Noch keine Bewertungen – Profil beanspruchen",
                                          "Das Portal startet gerade. Unternehmen können ihr Profil kostenlos beanspruchen "
                                          "und ihre Kundinnen und Kunden zur Bewertung einladen. Wir veröffentlichen keine "
                                          "erfundenen oder gekauften Bewertungen – auch nicht zum Start.")
        cats = "".join(
            f'<section class="tile">{self.media("img/kategorien/" + s["slug"])}<div class="tile-body">'
            f'<h3><a href="/kategorie/{s["slug"]}/">{esc(s["name"])}</a></h3><p>{esc(s["description"])}</p>'
            f'<a class="more" href="/kategorie/{s["slug"]}/">Anbieter ansehen →</a></div></section>' for s in services)
        guides = [a for a in self.articles if a["ressort"] == "ratgeber"][:3]
        if guides:
            guide_html = f'<div class="cards three">{"".join(self.article_card(a, show_media=False) for a in guides)}</div>'
        else:
            guide_html = '<p class="empty">Die ersten Ratgeber erscheinen in Kürze.</p>'
        trust = ('<ul class="trust-points">'
                 '<li><strong>Herkunft sichtbar</strong>Jede Bewertung trägt ein Label: verifiziert, eingeladen oder organisch. '
                 '<a href="/so-funktionieren-bewertungen/">So prüfen wir</a></li>'
                 '<li><strong>Zahlung ohne Einfluss</strong>Bezahlpakete ändern weder Score noch Sortierung noch Sichtbarkeit. '
                 '<a href="/score-methodik/">Score-Methodik</a></li>'
                 '<li><strong>Melden statt Löschen gegen Geld</strong>Unzulässige Inhalte können gemeldet werden; wir entscheiden begründet. '
                 '<a href="/melden/">Inhalt melden</a></li></ul>')
        body = (f'<section class="search-hero"><div><h1>{esc(c["name"])}</h1><p class="lead"><strong>{esc(c["claim"])}</strong> '
                f'{esc(c["description"])}</p>'
                f'<form class="search-form" action="/suche/" method="get" role="search">'
                f'<label class="visually-hidden" for="hero-q">Firma, Leistung oder Ort</label>'
                f'<input id="hero-q" type="search" name="q" placeholder="Firma, Leistung oder Ort">'
                f'<button class="btn" type="submit">Suchen</button></form></div>{self.media("img/hero", "media-wide")}</section>'
                f'<h2>Kategorien</h2><div class="tiles">{cats}</div>'
                f'<h2>Neueste Bewertungen</h2>{rec_html}{self.ad("home_top", bool(recent))}'
                f'<h2>Transparenz</h2>{trust}'
                f'<h2>Ratgeber</h2>{guide_html}'
                f'<section class="cta"><h2>Für IT-Dienstleister</h2><p>Profil kostenlos beanspruchen, Daten pflegen und auf Bewertungen antworten.</p>'
                f'<a class="btn" href="/fuer-unternehmen/">Profil beanspruchen</a></section>{self.newsletter_box()}')
        website_ld = {"@context": "https://schema.org", "@type": "WebSite", "name": c["name"], "url": self.base + "/",
                      "inLanguage": "de-DE", "potentialAction": {"@type": "SearchAction",
                      "target": self.url("/suche/?q={search_term_string}"), "query-input": "required name=search_term_string"}}
        self.render("/", c["name"], c["description"], body, jsonld=[website_ld, self.org_ld()],
                    full_title=f"{c['name']} – {c['claim']}", body_class="home")
        # Kategorien
        crumb_html, crumb_ld = self.breadcrumbs([("Kategorien", None)])
        lis = "".join(f'<li><a href="/kategorie/{s["slug"]}/">{esc(s["name"])}</a> – {esc(s["description"])}</li>' for s in services)
        self.render("/kategorien/", "Kategorien", f"Alle Leistungskategorien auf {c['name']}.",
                    f'{crumb_html}<header class="page-head"><h1>Kategorien</h1></header><ul>{lis}</ul>',
                    jsonld=[crumb_ld], search={"text": "Alle Leistungskategorien", "section": "Kategorien"})
        for s in services:
            cos = [co for co in self.companies if s["slug"] in co.get("services", [])]
            cos.sort(key=lambda co: (-(co["stats"]["score"] or 0), co["name"]))
            crumb_html, crumb_ld = self.breadcrumbs([("Kategorien", "/kategorien/"), (s["name"], None)])
            if cos:
                lst = "".join(self.company_card(co) for co in cos)
                lst = f'<div class="cards">{lst}</div>'
            else:
                lst = self.empty_reviews(f"Noch keine Anbieter in „{s['name']}“",
                                         "Sie bieten diese Leistung an? Beanspruchen Sie Ihr Profil kostenlos.")
            note = ('<p class="meta">Sortierung nach Score (siehe <a href="/score-methodik/">Score-Methodik</a>). '
                    'Bezahlpakete haben keinen Einfluss auf die Reihenfolge.</p>')
            self.render(f"/kategorie/{s['slug']}/", f"{s['name']}: Anbieter und Erfahrungen",
                        s.get("intro") or s["description"],
                        f'{crumb_html}<header class="page-head"><h1>{esc(s["name"])}</h1><p class="lead">{esc(s.get("intro") or s["description"])}</p></header>{note}{lst}',
                        jsonld=[crumb_ld], noindex=not cos, search={"text": s["description"], "section": "Kategorie"})
        # Ratgeber
        guides_all = [a for a in self.articles if a["ressort"] == "ratgeber"]
        self.list_page("/ratgeber/", "Ratgeber", rv.get("guide_intro", "Ratgeber rund um die Auswahl von Dienstleistern."),
                       guides_all, empty_text="Die ersten Ratgeber erscheinen in Kürze.")
        for a in guides_all:
            self.article_page(a)
        for co in self.companies:
            self.review_company_page(co)

    def empty_reviews(self, title, text):
        return (f'<div class="empty-state">{self.media("img/empty/keine-bewertungen")}'
                f'<h2>{esc(title)}</h2><p>{esc(text)}</p>'
                f'<p><a class="btn" href="/fuer-unternehmen/">Profil beanspruchen</a> '
                f'<a class="btn btn-ghost" href="/so-funktionieren-bewertungen/">So funktionieren Bewertungen</a></p></div>')

    def company_card(self, co):
        st = co["stats"]
        score = (f'{stars(st["score"])} <strong>{de_number(st["score"])}</strong> · {st["count"]} Bewertungen'
                 if st["score"] is not None else "Noch keine Bewertungen")
        return (f'<article class="card tile"><div class="tile-body"><h3><a href="/firma/{co["slug"]}/">{esc(co["name"])}</a></h3>'
                f'<p class="meta">{esc(co.get("city", ""))}</p><p>{score}</p></div></article>')

    def review_company_page(self, co):
        c, rv = self.cfg, self.cfg["review"]
        st = co["stats"]
        crumb_html, crumb_ld = self.breadcrumbs([("Kategorien", "/kategorien/"), (co["name"], None)])
        badges = []
        if co.get("claimed"):
            badges.append('<span class="badge badge-verifiziert">Profil beansprucht</span>')
        if co.get("invites_actively"):
            badges.append('<span class="badge badge-eingeladen">lädt aktiv ein</span>')
        if co.get("reply_days"):
            badges.append(f'<span class="badge badge-organisch">antwortet meist in {int(co["reply_days"])} Tagen</span>')
        if st["count"]:
            total = st["count"]
            dist = "".join(
                f'<li><span>{s} Sterne</span><span class="bar"><span style="width:{(st["distribution"].get(s, 0) / total * 100):.0f}%"></span></span>'
                f'<span>{st["distribution"].get(s, 0)}</span></li>' for s in range(5, 0, -1))
            crit = "".join(
                f'<li><span>{esc(k["name"])}</span><span class="bar"><span style="width:{st["criteria"][k["key"]] / 5 * 100:.0f}%"></span></span>'
                f'<span>{de_number(st["criteria"][k["key"]])}</span></li>'
                for k in rv["criteria"] if k["key"] in st["criteria"])
            score_html = (f'<section class="score-block" aria-label="Bewertungsübersicht"><div>'
                          f'<p class="score-big">{de_number(st["score"])} <small>/ 5</small></p>{stars(st["score"])}'
                          f'<p class="meta">{total} Bewertung{"en" if total != 1 else ""} · <a href="/score-methodik/">So berechnen wir den Score</a></p></div>'
                          f'<div><h2 class="kicker">Verteilung</h2><ul class="bars">{dist}</ul></div>'
                          f'<div><h2 class="kicker">Teilkriterien</h2><ul class="bars">{crit}</ul></div></section>')
        else:
            score_html = self.empty_reviews("Noch keine Bewertungen – Profil beanspruchen",
                                            "Für dieses Unternehmen liegen noch keine Bewertungen vor.")
        summary = ""
        s = co.get("ai_summary") or {}
        if s.get("text") and (s.get("status") == "approved" or self.mode != "live"):
            summary = (f'<section class="ai-summary"><h2>Zusammenfassung der Bewertungen</h2><p>{esc(s["text"])}</p>'
                       f'<p class="meta">KI-generierte Zusammenfassung der veröffentlichten Bewertungen, redaktionell geprüft. '
                       f'Sie ersetzt nicht das Lesen der einzelnen Bewertungen.</p></section>')
        reviews = []
        for r in sorted(co["reviews"], key=lambda r: r.get("date", ""), reverse=True):
            v = r.get("verification", "organisch")
            label = next((x[1] for x in VERIFICATION if x[0] == v), v)
            extra = " · ".join(esc(x) for x in (r.get("service"), r.get("company_size"), r.get("contract")) if x)
            reply = ""
            if r.get("reply") and r["reply"].get("text"):
                reply = (f'<div class="reply"><p><strong>Antwort von {esc(co["name"])}</strong> · {de_date(content.parse_datetime(r["reply"].get("date")))}</p>'
                         f'<p>{esc(r["reply"]["text"])}</p></div>')
            reviews.append(
                f'<article class="review"><p>{stars(r["rating"])} <span class="badge badge-{esc(v)}">{esc(label)}</span> '
                f'<span class="meta">{de_date(content.parse_datetime(r.get("date")))}{" · " + extra if extra else ""}</span></p>'
                f'<h3>{esc(r.get("title", ""))}</h3><p>{esc(r.get("text", ""))}</p>'
                f'<p class="meta">{esc(r.get("author", "Kundin/Kunde"))} · <a href="/melden/">Bewertung melden</a></p>{reply}</article>')
        legend = "".join(f'<li><span class="badge badge-{k}">{n}</span> {esc(d)}</li>' for k, n, _, d in VERIFICATION)
        facts = [("Sitz", co.get("city")), ("Rechtsform", co.get("legal_form")), ("Register", co.get("register")),
                 ("Leistungen", ", ".join(x["name"] for x in rv["services"] if x["slug"] in co.get("services", [])))]
        dl = "".join(f"<dt>{k}</dt><dd>{esc(v)}</dd>" for k, v in facts if v)
        if co.get("website"):
            dl += f'<dt>Website</dt><dd><a href="{esc(co["website"])}" rel="noopener nofollow" target="_blank">{esc(co["website"])}</a></dd>'
        news = (f'<section class="box"><h2>Aktuelle Nachrichten</h2><p>Berichte zu diesem Unternehmen auf unserem Schwesterportal: '
                f'<a href="{esc(co["news_url"])}">{esc(co["news_url"])}</a></p></section>' if co.get("news_url") else "")
        claim = ("" if co.get("claimed") else
                 '<section class="cta"><h2>Ist das Ihr Unternehmen?</h2><p>Beanspruchen Sie das Profil kostenlos, pflegen Sie Ihre Daten '
                 'und antworten Sie auf Bewertungen.</p><a class="btn" href="/fuer-unternehmen/">Profil beanspruchen</a></section>')
        body = (f'{crumb_html}<header class="page-head"><p class="kicker">Firmenprofil</p><h1>{esc(co["name"])}</h1>'
                f'<p>{" ".join(badges)}</p><p class="lead">{esc(co.get("description", ""))}</p>'
                f'<p><a class="btn" href="/bewertung-schreiben/">Bewertung schreiben</a></p></header>'
                f'<div class="layout with-sidebar"><div>{score_html}{summary}{self.ad("profile", bool(st["count"]))}'
                f'<section aria-labelledby="rv-h"><h2 id="rv-h">Bewertungen</h2>{"".join(reviews) or "<p class=empty>Noch keine Bewertungen.</p>"}</section></div>'
                f'<aside class="sidebar"><section class="box"><h2>Herkunft der Bewertungen</h2><ul>{legend}</ul>'
                f'<p><a href="/so-funktionieren-bewertungen/">So prüfen wir Bewertungen</a></p></section>'
                f'<section class="box"><h2>Stammdaten</h2><dl class="facts">{dl}</dl></section>{news}{claim}</aside></div>')
        ld = {"@context": "https://schema.org", "@type": "Organization", "name": co["name"],
              "url": co.get("website") or self.url(f"/firma/{co['slug']}/")}
        if co.get("city"):
            ld["address"] = {"@type": "PostalAddress", "addressLocality": co["city"], "addressCountry": "DE"}
        if st["count"]:
            ld["aggregateRating"] = {"@type": "AggregateRating", "ratingValue": st["score"], "bestRating": 5,
                                     "worstRating": 1, "ratingCount": st["count"]}
            ld["review"] = [{"@type": "Review", "reviewRating": {"@type": "Rating", "ratingValue": r["rating"], "bestRating": 5},
                             "author": {"@type": "Person", "name": r.get("author", "Kunde")},
                             "datePublished": str(r.get("date", ""))[:10], "name": r.get("title", "")}
                            for r in co["reviews"][:10]]
        # Indexierungsschwelle: Profil erst mit ≥ 1 Bewertung indexieren
        self.render(f"/firma/{co['slug']}/", f"{co['name']}: Erfahrungen und Bewertungen",
                    co.get("description") or f"Kundenerfahrungen mit {co['name']}", body,
                    jsonld=[ld, crumb_ld], noindex=not st["count"],
                    search={"text": f"{co.get('city', '')} {co.get('description', '')}", "section": "Firmenprofil"})

    # ---------------- Betreiberseite
    def build_operator(self):
        c, op = self.cfg, self.net["operator"]
        cards = []
        for s in sorted((s for s in self.all_sites if s["type"] in ("news", "review") or s["type"] == "redirect"),
                        key=lambda s: (s.get("phase", 9), s["domain"])):
            if s["type"] == "redirect":
                target = s["redirect_to"]
                cards.append(f'<article class="card tile"><div class="tile-body"><p class="kicker">Weiterleitung</p>'
                             f'<h3>{esc(s.get("name", s["domain"]))}</h3><p>{esc(s.get("claim", ""))}</p>'
                             f'<p class="meta">{esc(s["domain"])} leitet derzeit auf <a href="{esc(target)}">{esc(target)}</a> weiter.</p></div></article>')
                continue
            status = ("online" if s.get("enabled") else f"in Vorbereitung (Phase {s.get('phase')})")
            name = (f'<a href="https://{esc(s["domain"])}/">{esc(s["name"])}</a>' if s.get("enabled") else esc(s["name"]))
            cards.append(f'<article class="card tile"><div class="tile-body"><p class="kicker">{TYPE_LABEL[s["type"]]} · {status}</p>'
                         f'<h3>{name}</h3><p><strong>{esc(s["claim"])}</strong></p><p>{esc(s["description"])}</p>'
                         f'<p class="meta">{esc(s["domain"])}</p></div></article>')
        body = (f'<section class="lead-story">{self.media("img/hero", "media-wide")}<div class="welcome">'
                f'<h1>{esc(self.net["brand"])}</h1><p><strong>{esc(c["claim"])}</strong></p><p>{esc(c["description"])}</p>'
                f'<p>{esc(self.net["brand"])} ist eine Marke der {esc(op["legal_name"])}. Alle Portale nennen den gemeinsamen Betreiber offen.</p></div></section>'
                f'<h2 id="portale">Unsere Portale</h2><div class="cards">{"".join(cards)}</div>'
                f'<h2>Unsere Grundsätze</h2><ul class="trust-points">'
                f'<li><strong>Unabhängig</strong>Redaktion und Bewertungen sind nicht käuflich. Kein Kunde kauft Berichterstattung, Löschungen oder bessere Bewertungen.</li>'
                f'<li><strong>Gekennzeichnet</strong>Werbung und bezahlte Inhalte sind immer als „Anzeige“ markiert und tauchen nie in redaktionellen Rankings auf.</li>'
                f'<li><strong>KI mit menschlicher Freigabe</strong>Entwürfe entstehen KI-gestützt aus belegten Quellen. Online geht nur, was ein Mensch geprüft und freigegeben hat.</li></ul>'
                f'<p><a href="/redaktionsgrundsaetze/">Alle Grundsätze lesen</a> · <a href="/kontakt/">Kontakt</a></p>')
        self.render("/", self.net["brand"], c["description"], body, jsonld=[self.org_ld()],
                    full_title=f"{self.net['brand']} – {c['claim']}", body_class="home")

    # ---------------- Rechts- und Vertrauensseiten
    def legal_vars(self):
        c, op, net = self.cfg, self.net["operator"], self.net
        sc = c.get("review", {}).get("score", {})
        vw = sc.get("verification_weights", {})
        portals = []
        for s in self.all_sites:
            if s["type"] == "redirect":
                portals.append(f"- **{s.get('name', s['domain'])}** ({s['domain']}) – derzeit Weiterleitung auf {s['redirect_to']}")
            elif s.get("enabled"):
                tag = " (dieses Portal)" if s["domain"] == self.domain else " (Schwesterportal)"
                portals.append(f"- **[{s['name']}](https://{s['domain']}/)**{tag} – {TYPE_LABEL[s['type']]}: {s['claim']}")
            else:
                portals.append(f"- **{s['name']}** ({s['domain']}) – {TYPE_LABEL[s['type']]}, in Vorbereitung (Phase {s.get('phase')})")
        criteria = "\n".join(f"- **{k['name']}**" + (f" – {k['hint']}" if k.get("hint") else "") for k in c.get("review", {}).get("criteria", []))
        services = "\n".join(f"- {s['name']}" for s in c.get("review", {}).get("services", []))
        packages = c.get("review", {}).get("packages") or net.get("packages", [])
        pk = "| Paket | Preis (monatlich, netto) | Leistungen |\n|---|---|---|\n" + "\n".join(
            f"| **{p['name']}** | {p['price']} | {p['features']} |" for p in packages)
        ressorts = "\n".join(f"- **{r['name']}** – {r['description']}" for r in c.get("ressorts", []))
        v = {
            "site_name": c["name"], "domain": self.domain, "base_url": self.base, "claim": c["claim"],
            "description": c["description"], "brand": net["brand"], "operator_name": op["legal_name"],
            "operator_name_short": op["legal_name"].replace(" i.G.", ""),
            "brand_line": op["brand_line"], "street": op["street"], "postal_city": op["postal_city"],
            "country": op["country"], "managing_director": op["managing_director"],
            "register_court": op["register_court"], "register_number": op["register_number"],
            "vat_id": op["vat_id"], "email": self.email_md(), "operator_email": self.email_md(op["email"]),
            "phone": op["phone"], "mstv_responsible": op["mstv_responsible"],
            "dpa_authority": op["dpa_authority"], "hosting_location": op.get("hosting_location", ""),
            "stand": de_date(self.now), "newsletter_name": c["newsletter"]["name"],
            "network_list": "\n".join(portals), "criteria_list": criteria, "services_list": services,
            "packages_table": pk, "ressort_list": ressorts, "region": c.get("region", ""),
            "type_label": TYPE_LABEL.get(self.type, ""), "ai_note": c.get("ai_note", net["ai_note"]),
            "score_prior_mean": de_number(sc.get("prior_mean", 3.5)), "score_prior_weight": de_number(sc.get("prior_weight", 3), 0),
            "score_half_life": str(sc.get("half_life_months", 12)),
            "weight_verified": de_number(vw.get("verifiziert", 1.2)), "weight_invited": de_number(vw.get("eingeladen", 1.0)),
            "weight_organic": de_number(vw.get("organisch", 1.0)),
            "dsa_contact": self.email_md(op.get("dsa_contact") or op["email"]),
            "subject_plural": c.get("review", {}).get("subject_plural", "Dienstleister"),
            "analytics_tool": (c.get("analytics") or {}).get("tool_name") or net.get("analytics_tool", "Umami"),
        }
        return v

    def legal_flags(self):
        return {"news": self.type == "news", "review": self.type == "review", "operator": self.type == "operator",
                "editorial": self.type in ("news", "review")}

    @staticmethod
    def apply_conditionals(text, flags):
        def repl(m):
            neg, flag, inner = m.group(1) == "!", m.group(2), m.group(3)
            return inner if bool(flags.get(flag)) != neg else ""
        prev = None
        while prev != text:
            prev = text
            text = re.sub(r"<!--if:(!?)(\w+)-->(.*?)<!--endif:\1\2-->", repl, text, flags=re.S)
        return text

    def build_legal(self):
        vars_ = self.legal_vars()
        flags = self.legal_flags()
        for slug in LEGAL_PAGES[self.type]:
            path = LEGAL_DIR / f"{slug}.md"
            meta, body = frontmatter.parse(path.read_text(encoding="utf-8"))
            body = self.apply_conditionals(body, flags)
            body = string.Template(body).safe_substitute(vars_)
            title = string.Template(meta.get("title", slug)).safe_substitute(vars_)
            desc = string.Template(meta.get("description", title)).safe_substitute(vars_)
            html = md.convert(body)
            extra = getattr(self, f"legal_extra_{slug.replace('-', '_')}", lambda: "")()
            note = ""
            if meta.get("draft_note"):
                note = f'<p class="draft-note">{esc(meta["draft_note"])}</p>'
            crumb_html, crumb_ld = self.breadcrumbs([(title, None)])
            page = (f'{crumb_html}<article class="legal"><h1>{esc(title)}</h1>{note}{html}{extra}'
                    f'<p class="meta">Stand: {de_date(self.now)}</p></article>')
            jsonld = [crumb_ld] + ([self.org_ld()] if slug == "ueber-uns" else [])
            noindex = bool(meta.get("noindex"))
            self.render(f"/{slug}/", title, desc, page, jsonld=jsonld, noindex=noindex,
                        search={"text": desc, "section": "Service"})

    def form(self, action, fields, submit, note=""):
        out = [f'<form method="post" action="{esc(action)}">']
        for name, label, kind, req in fields:
            r = " required" if req else ""
            fid = f"f-{name}"
            if kind == "textarea":
                out.append(f'<label for="{fid}">{esc(label)}</label><textarea id="{fid}" name="{name}" rows="6"{r}></textarea>')
            elif kind == "checkbox":
                out.append(f'<p><input type="checkbox" id="{fid}" name="{name}" value="1"{r}> <label for="{fid}" style="display:inline">{label}</label></p>')
            elif kind.startswith("select:"):
                opts = "".join(f"<option>{esc(o)}</option>" for o in kind[7:].split("|"))
                out.append(f'<label for="{fid}">{esc(label)}</label><select id="{fid}" name="{name}"{r}>{opts}</select>')
            else:
                out.append(f'<label for="{fid}">{esc(label)}</label><input id="{fid}" type="{kind}" name="{name}"{r}>')
        out.append(f'<p><button class="btn" type="submit">{esc(submit)}</button></p>')
        if note:
            out.append(f'<p class="form-note">{note}</p>')
        out.append("</form>")
        return "".join(out)

    def form_or_notice(self, key, fields, submit, what):
        action = (self.cfg.get("forms") or {}).get(key)
        if action:
            return self.form(action, fields, submit, 'Mit dem Absenden akzeptieren Sie die <a href="/datenschutz/">Datenschutzerklärung</a>.')
        return (f'<div class="box"><p><strong>Das Online-Formular für {esc(what)} wird gerade eingerichtet.</strong> '
                f'Bis dahin erreichen Sie uns per E-Mail: {self.email_html()}</p></div>')

    def legal_extra_kontakt(self):
        return self.form_or_notice("contact_action", [
            ("name", "Name", "text", True), ("email", "E-Mail-Adresse", "email", True),
            ("subject", "Anliegen", "select:Allgemeine Anfrage|Hinweis an die Redaktion|Korrektur|Rechtliches Anliegen|Datenschutz", True),
            ("message", "Nachricht", "textarea", True)], "Nachricht senden", "Kontaktanfragen")

    def legal_extra_melden(self):
        return self.form_or_notice("report_action", [
            ("url", "Adresse (URL) des gemeldeten Inhalts", "url", True),
            ("reason", "Grund", "select:Rechtsverletzung (z. B. unwahre Tatsachenbehauptung, Beleidigung)|Verstoß gegen Bewertungsrichtlinien|Kein echter Kundenkontakt|Datenschutz|Sonstiges", True),
            ("explanation", "Begründung (bitte so konkret wie möglich)", "textarea", True),
            ("name", "Name", "text", True), ("email", "E-Mail-Adresse", "email", True),
            ("good_faith", "Ich bestätige, dass meine Angaben nach bestem Wissen richtig und vollständig sind.", "checkbox", True)],
            "Meldung absenden", "Meldungen")

    def legal_extra_bewertung_schreiben(self):
        crit = self.cfg["review"]["criteria"]
        fields = [("company", "Unternehmen (Name und Ort)", "text", True),
                  ("rating", "Gesamtbewertung", "select:5 Sterne|4 Sterne|3 Sterne|2 Sterne|1 Stern", True)]
        fields += [(f"c_{k['key']}", k["name"], "select:5|4|3|2|1|keine Angabe", False) for k in crit]
        fields += [("title", "Überschrift", "text", True), ("text", "Ihre Erfahrung", "textarea", True),
                   ("pseudonym", "Angezeigter Name (Initialen oder Pseudonym)", "text", True),
                   ("email", "E-Mail-Adresse (wird nicht veröffentlicht)", "email", True),
                   ("honest", "Ich versichere, dass ich selbst Kundin/Kunde des Unternehmens war, keine Gegenleistung für diese Bewertung erhalte und nicht mit dem Unternehmen verbunden bin.", "checkbox", True)]
        return self.form_or_notice("review_action", fields, "Bewertung einreichen", "Bewertungen")

    def legal_extra_fuer_unternehmen(self):
        return self.form_or_notice("claim_action", [
            ("company", "Unternehmen", "text", True), ("website", "Website", "url", True),
            ("name", "Ihr Name", "text", True), ("role", "Ihre Funktion im Unternehmen", "text", True),
            ("email", "Geschäftliche E-Mail-Adresse (Domain des Unternehmens)", "email", True)],
            "Profil beanspruchen", "die Profil-Beanspruchung")

    def legal_extra_korrekturen(self):
        items = []
        for a in self.articles:
            for x in a["corrections"]:
                items.append(f'<li><a href="{a["url"]}">{esc(a["title"])}</a>: {md.inline(str(x))}</li>')
        if not items:
            return '<h2>Bisherige Korrekturen</h2><p class="empty">Bisher wurden keine Korrekturen veröffentlicht.</p>'
        return f'<h2>Bisherige Korrekturen</h2><ul>{"".join(items)}</ul>'

    # ---------------- Suche, 404
    def build_search_page(self):
        crumb_html, crumb_ld = self.breadcrumbs([("Suche", None)])
        body = (f'{crumb_html}<header class="page-head"><h1>Suche</h1></header>'
                f'<form id="search-form" class="search-form" action="/suche/" method="get" role="search">'
                f'<label class="visually-hidden" for="q">Suchbegriff</label>'
                f'<input id="q" type="search" name="q" placeholder="{"Firma, Leistung oder Ort" if self.type == "review" else "Suchbegriff"}" autofocus>'
                f'<button class="btn" type="submit">Suchen</button></form>'
                f'<p id="search-status" class="meta" role="status" aria-live="polite"></p><ul id="search-results"></ul>'
                f'<noscript><p>Für die Suche wird JavaScript benötigt. Alternativ finden Sie alle Beiträge über die Navigation.</p></noscript>')
        self.render("/suche/", "Suche", f"Suche auf {self.cfg['name']}", body, jsonld=[crumb_ld], noindex=True)

    def build_404(self):
        body = ('<div class="empty-state"><h1>Seite nicht gefunden</h1><p>Diese Adresse gibt es (nicht mehr). '
                'Vielleicht hilft die Suche oder die Startseite weiter.</p><p><a class="btn" href="/">Zur Startseite</a> '
                + ('<a class="btn btn-ghost" href="/suche/">Suche</a>' if self.type != "operator" else "") + "</p></div>")
        self.render("/404.html", "Seite nicht gefunden", "Diese Seite wurde nicht gefunden.", body, noindex=True)
        self.pages = [p for p in self.pages if p["url"] != "/404.html"]

    # ---------------- SEO-Dateien
    def build_seo_files(self):
        live = self.mode == "live"
        idx = [p for p in self.pages if p["indexable"]]
        # robots.txt
        lines = ["# robots.txt – " + self.domain, "User-agent: *"]
        if live:
            lines += ["Allow: /", "", f"Sitemap: {self.url('/sitemap.xml')}"]
            if self.type == "news":
                lines.append(f"Sitemap: {self.url('/news-sitemap.xml')}")
        else:
            lines.append("Disallow: /")
        self.write("/robots.txt", "\n".join(lines) + "\n")
        # sitemap.xml
        urls = "".join(f"<url><loc>{sax.escape(self.url(p['url']))}</loc><lastmod>{p['lastmod'].date().isoformat()}</lastmod></url>"
                       for p in sorted(idx, key=lambda p: p["url"]))
        self.write("/sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
                   f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
        # Google-News-Sitemap: Nachrichten der letzten 48 Stunden
        if self.type == "news":
            recent = [a for a in self.articles if a["kind"] == "news" and not a["noindex"]
                      and (self.now - a["date"]).total_seconds() <= 48 * 3600]
            items = "".join(
                f"<url><loc>{sax.escape(self.url(a['url']))}</loc><news:news><news:publication>"
                f"<news:name>{sax.escape(self.cfg['name'])}</news:name><news:language>de</news:language></news:publication>"
                f"<news:publication_date>{a['date'].isoformat()}</news:publication_date>"
                f"<news:title>{sax.escape(a['title'])}</news:title></news:news></url>" for a in recent)
            self.write("/news-sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
                       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                       f'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">{items}</urlset>\n')
        # RSS
        if self.type in ("news", "review"):
            items = "".join(
                f"<item><title>{sax.escape(a['title'])}</title><link>{sax.escape(self.url(a['url']))}</link>"
                f"<guid isPermaLink=\"true\">{sax.escape(self.url(a['url']))}</guid>"
                f"<pubDate>{rfc822(a['date'])}</pubDate><category>{sax.escape(a['ressort_name'])}</category>"
                f"<description>{sax.escape(a['teaser'])}</description></item>"
                for a in self.articles[:30] if not a["noindex"])
            self.write("/feed.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
                       '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>'
                       f"<title>{sax.escape(self.cfg['name'])}</title><link>{self.base}/</link>"
                       f"<description>{sax.escape(self.cfg['claim'])}</description><language>de-de</language>"
                       f'<atom:link href="{self.url("/feed.xml")}" rel="self" type="application/rss+xml"/>'
                       f"<lastBuildDate>{rfc822(self.now)}</lastBuildDate>{items}</channel></rss>\n")
        # ads.txt
        client = self.cfg.get("adsense_client_id", "")
        # Ohne AdSense-Freigabe leere ads.txt (keine Platzhalter-ID öffentlich ausliefern)
        self.write("/ads.txt", f"google.com, {client.replace('ca-', '')}, DIRECT, f08c47fec0942fa0\n" if client else "")
        # Suchindex
        if self.type != "operator":
            self.write("/search-index.json", json.dumps(self.search, ensure_ascii=False, separators=(",", ":")))

    # ------------------------------------------------------------ Bericht
    def placeholders_in_output(self):
        found = set()
        for f in self.out.rglob("*.html"):
            for m in PLACEHOLDER_RE.finditer(f.read_text(encoding="utf-8")):
                found.add(m.group(0))
        return sorted(found)
