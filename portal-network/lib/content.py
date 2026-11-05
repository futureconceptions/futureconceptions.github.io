"""Inhalte laden: Artikel (Markdown + Front Matter), Firmen und Personen (JSON).

Freigabe-Regel: Nur Einträge mit ``status: approved`` werden gerendert.
Alles andere (draft, queued, rejected, …) ist Eingabe für den späteren
Telegram-Freigabe-Workflow und erscheint nie auf der Website – außer im
ausdrücklichen Vorschau-Build (``build.py --drafts``), der auf noindex steht.
"""
import json
import math
import pathlib

from . import frontmatter, md
from .util import now, parse_datetime, slugify, strip_tags, truncate

APPROVED = "approved"


class ContentError(Exception):
    pass


def _visible(status, include_drafts):
    return status == APPROVED or (include_drafts and status == "draft")


def load_articles(dirs, site, include_drafts=False):
    ressorts = {r["slug"]: r for r in site.get("ressorts", [])}
    if site["type"] == "review":
        ressorts.setdefault("ratgeber", {"slug": "ratgeber", "name": "Ratgeber"})
    articles, drafts = [], 0
    current = now()
    for d in dirs:
        for path in sorted(pathlib.Path(d).glob("*.md")):
            meta, body = frontmatter.parse(path.read_text(encoding="utf-8"))
            status = str(meta.get("status", "draft")).strip()
            if status != APPROVED:
                drafts += 1
            if not _visible(status, include_drafts):
                continue
            for k in ("title", "ressort"):
                if not meta.get(k):
                    raise ContentError(f"{path}: Pflichtfeld '{k}' fehlt")
            if meta["ressort"] not in ressorts:
                raise ContentError(f"{path}: Ressort {meta['ressort']!r} ist in site.json nicht definiert")
            date = parse_datetime(meta.get("date")) or current
            if status == APPROVED and date > current:
                continue  # geplante Veröffentlichung
            slug = meta.get("slug") or slugify(path.stem)
            kind = meta.get("kind") or ("ratgeber" if meta["ressort"] == "ratgeber" else "news")
            if kind == "ratgeber":
                url = f"/{meta['ressort']}/{slug}/"
            else:
                url = f"/{meta['ressort']}/{date:%Y}/{date:%m}/{slug}/"
            html = md.convert(body)
            sources = []
            for s in meta.get("sources") or []:
                text, _, link = str(s).partition("|")
                sources.append({"text": text.strip(), "url": link.strip()})
            words = md.word_count(body)
            articles.append({
                "path": str(path), "status": status, "title": meta["title"], "slug": slug,
                "ressort": meta["ressort"], "ressort_name": ressorts[meta["ressort"]]["name"],
                "kind": kind, "date": date, "updated": parse_datetime(meta.get("updated")),
                "author": meta.get("author") or site.get("default_author", "Redaktion"),
                "teaser": meta.get("teaser") or truncate(strip_tags(html), 180),
                "image": meta.get("image", ""), "image_alt": meta.get("image_alt", ""),
                "region": meta.get("region", ""), "tags": meta.get("tags") or [],
                "featured": bool(meta.get("featured")), "sources": sources,
                "corrections": meta.get("corrections") or [],
                "companies": meta.get("companies") or [], "people": meta.get("people") or [],
                "needs_fact_check": bool(meta.get("needs_fact_check")),
                "noindex": bool(meta.get("noindex")),
                "html": html, "words": words, "url": url,
                "reading_min": max(1, math.ceil(words / 200)),
            })
    articles.sort(key=lambda a: a["date"], reverse=True)
    return articles, drafts


def load_json_items(dirs, include_drafts=False):
    items, drafts = [], 0
    for d in dirs:
        for path in sorted(pathlib.Path(d).glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                raise ContentError(f"{path}: ungültiges JSON ({e})") from e
            status = data.get("status", "draft")
            if status != APPROVED:
                drafts += 1
            if not _visible(status, include_drafts):
                continue
            if not data.get("name"):
                raise ContentError(f"{path}: Pflichtfeld 'name' fehlt")
            data.setdefault("slug", slugify(data["name"]))
            data["_path"] = str(path)
            items.append(data)
    items.sort(key=lambda x: x["name"].lower())
    return items, drafts


# ---------------------------------------------------------------- Score-Methodik

def review_weight(review, score_cfg, today):
    """Gewicht einer Bewertung: Aktualität (Halbwertszeit) × Verifizierungsstufe."""
    date = parse_datetime(review.get("date")) or today
    age_days = max(0.0, (today - date).total_seconds() / 86400)
    half_life_days = score_cfg["half_life_months"] * 30.4375
    recency = 0.5 ** (age_days / half_life_days)
    level = score_cfg["verification_weights"].get(review.get("verification", "organisch"), 1.0)
    return recency * level


def compute_score(reviews, score_cfg, today=None):
    """Bayes-geglätteter, gewichteter Mittelwert (siehe Seite Score-Methodik)."""
    today = today or now()
    m, prior = score_cfg["prior_weight"], score_cfg["prior_mean"]
    num, den = m * prior, m
    crit_sum, crit_w = {}, {}
    dist = {s: 0 for s in range(5, 0, -1)}
    for r in reviews:
        w = review_weight(r, score_cfg, today)
        rating = int(r["rating"])
        num += w * rating
        den += w
        dist[rating] = dist.get(rating, 0) + 1
        for key, val in (r.get("criteria") or {}).items():
            crit_sum[key] = crit_sum.get(key, 0) + w * float(val)
            crit_w[key] = crit_w.get(key, 0) + w
    criteria = {k: crit_sum[k] / crit_w[k] for k in crit_sum if crit_w[k] > 0}
    return {
        "score": round(num / den, 1) if reviews else None,
        "count": len(reviews),
        "distribution": dist,
        "criteria": criteria,
    }
