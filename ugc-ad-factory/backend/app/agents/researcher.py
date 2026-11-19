"""Agent 1 - Product Researcher."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.agents import prompts as P
from app.agents.schemas import ProductResearch, ResearchRecord, SupportedClaim
from app.research.evidence import Passage, build_pack, verify_claims
from app.research.harness import Corpus, Doc, assign_episode_ids
from app.research.swarm import Swarm
from app.providers.base import LLMUsage
from app.services.safe_fetch import FetchError, UnsafeURLError, robots_allows, safe_get


@dataclass
class PageExtract:
    status: str  # ok|robots_disallowed|error|skipped|not_html
    title: str | None = None
    description: str | None = None
    text: str = ""
    meta: dict = field(default_factory=dict)
    error: str | None = None
    links: list[tuple[str, str]] = field(default_factory=list)  # (absolute url, anchor text), same host
    url: str | None = None


def extract_page(html: str, max_chars: int = 15000, base_url: str | None = None) -> PageExtract:
    soup = BeautifulSoup(html, "html.parser")
    links: list[tuple[str, str]] = []
    if base_url:
        host = urlparse(base_url).netloc
        for a in soup.find_all("a", href=True):
            u = urljoin(base_url, a["href"]).split("#")[0]
            if urlparse(u).netloc == host and urlparse(u).scheme in ("http", "https") and u != base_url:
                links.append((u, a.get_text(" ", strip=True)[:80]))
    meta: dict = {}
    for m in soup.find_all("meta"):
        key = m.get("property") or m.get("name")
        if key and m.get("content") and (key.startswith("og:") or key in (
                "description", "keywords", "twitter:title", "twitter:description", "product:price:amount",
                "product:price:currency")):
            meta[key] = m["content"][:500]
    jsonld = []
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string or "")
        except (ValueError, TypeError):
            continue
        items = data if isinstance(data, list) else data.get("@graph", [data]) if isinstance(data, dict) else []
        for it in items:
            if isinstance(it, dict) and str(it.get("@type", "")).lower() in ("product", "['product']"):
                jsonld.append({k: it.get(k) for k in ("name", "brand", "description", "offers", "sku")
                               if it.get(k)})
    if jsonld:
        meta["jsonld_product"] = jsonld[:3]
    for t in soup(["script", "style", "noscript", "svg", "nav", "footer", "form", "iframe"]):
        t.decompose()
    title = soup.title.get_text(strip=True) if soup.title else None
    blocks = []
    for el in soup.find_all(["h1", "h2", "h3", "p", "li", "td"]):
        txt = el.get_text(" ", strip=True)
        if 3 <= len(txt.split()) <= 120:
            blocks.append(txt)
    seen, uniq = set(), []
    for b in blocks:
        if b not in seen:
            seen.add(b)
            uniq.append(b)
    text = "\n".join(uniq)[:max_chars]
    return PageExtract(status="ok", title=title, description=meta.get("description") or meta.get("og:description"),
                       text=text, meta=meta, links=list(dict.fromkeys(links))[:200], url=base_url)


def fetch_product_page(url: str) -> PageExtract:
    try:
        if not robots_allows(url):
            return PageExtract(status="robots_disallowed",
                               error="robots.txt disallows fetching this page; using the description only")
        res = safe_get(url)
    except (UnsafeURLError, FetchError) as e:
        return PageExtract(status="error", error=str(e))
    except Exception as e:  # noqa: BLE001 - network errors are non-fatal for research
        return PageExtract(status="error", error=f"fetch failed: {e}")
    if res.status_code >= 400:
        return PageExtract(status="error", error=f"HTTP {res.status_code}")
    if "html" not in res.content_type.lower():
        return PageExtract(status="not_html", error=f"unsupported content type {res.content_type}")
    return extract_page(res.content.decode("utf-8", "ignore"), base_url=res.url)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text or "")
    return [p.strip(" -•*\t") for p in parts if 3 <= len(p.split()) <= 30]


def heuristic_research(name: str | None, brand: str | None, description: str | None,
                       page: PageExtract | None, audience: str | None, language: str) -> ProductResearch:
    """Deterministic, conservative extraction used without an LLM: every claim
    is a verbatim sentence from the sources."""
    src_desc = _sentences(description or "")
    src_page = _sentences(page.text if page and page.status == "ok" else "")
    product_name = (name or (page.title.split("|")[0].split(" - ")[0].strip() if page and page.title else None)
                    or brand or ("das Produkt" if language == "de" else "the product"))
    claims = [SupportedClaim(claim=s, evidence=s, source="user_description") for s in src_desc[:6]]
    claims += [SupportedClaim(claim=s, evidence=s, source="product_page") for s in src_page[:6]]
    features = [c.claim for c in claims][:6] or [f"{product_name}"]
    return ProductResearch(
        product_name=product_name, brand=brand, category="consumer product",
        summary=(description or (page.description if page else "") or product_name)[:600],
        features=features, benefits=features[:3],
        target_audience=[audience] if audience else ["people who would use this product day to day"],
        customer_problems=[], differentiators=[], supported_claims=claims,
        claims_to_avoid=["health, income or guaranteed-result claims not stated in the sources"],
        potential_objections=["Is it worth the price?", "Will it work for me?"],
        price=(page.meta.get("product:price:amount") if page else None),
        before_after_supported=False, language=language)


# Pages on the same site that usually hold verifiable product facts.
LINK_PRIORITY = ["spec", "technical", "detail", "feature", "faq", "ingredient", "material", "size", "warranty",
                 "garantie", "shipping", "versand", "return", "rückgabe", "about", "über", "how", "anleitung",
                 "datenblatt", "produkt", "product"]
SKIP_LINK = ["login", "account", "cart", "warenkorb", "checkout", "privacy", "datenschutz", "impressum",
             "imprint", "terms", "agb", "cookie", "career", "jobs", "javascript:", "mailto:", "tel:"]


def crawl_site(url: str, max_pages: int = 6, first: PageExtract | None = None,
               fetch=fetch_product_page) -> list[PageExtract]:
    """Product page + up to `max_pages-1` informative same-host pages.
    Every page passes robots.txt and SSRF checks (fetch_product_page)."""
    first = first or fetch(url)
    pages = [first]
    if first.status != "ok" or max_pages <= 1:
        return pages

    def prio(link: tuple[str, str]) -> int:
        hay = (link[0] + " " + link[1]).lower()
        for i, kw in enumerate(LINK_PRIORITY):
            if kw in hay:
                return i
        return len(LINK_PRIORITY)

    cands = [l for l in first.links if not any(k in l[0].lower() for k in SKIP_LINK)]
    cands = [l for l in sorted(cands, key=prio) if prio(l) < len(LINK_PRIORITY)]
    for link, _ in cands:
        if len(pages) >= max_pages:
            break
        pg = fetch(link)
        if pg.status == "ok" and pg.text:
            pg.url = pg.url or link
            pages.append(pg)
    return pages


def build_corpus(description: str | None, brand_guidelines: str | None, pages: list[PageExtract],
                 page_url: str | None) -> Corpus:
    raw: list[Doc] = []
    if description:
        raw.append(Doc(id="", text=description, title="User product description", source="user_description"))
    for i, pg in enumerate(pages):
        if pg.status != "ok" or not pg.text:
            continue
        meta_lines = []
        if pg.description:
            meta_lines.append(pg.description)
        for item in pg.meta.get("jsonld_product", []) or []:
            offers = item.get("offers")
            if isinstance(offers, dict) and offers.get("price"):
                meta_lines.append(f"Price: {offers.get('price')} {offers.get('priceCurrency', '')}".strip())
        text = "\n".join(([pg.title] if pg.title else []) + meta_lines + [pg.text])
        raw.append(Doc(id="", text=text, title=pg.title or (pg.url or ""), url=pg.url or page_url,
                       source="product_page" if i == 0 else "site_page"))
    if brand_guidelines:
        raw.append(Doc(id="", text=brand_guidelines, title="Brand guidelines", source="brand_guidelines"))
    return assign_episode_ids(raw)


def heuristic_claims(pack: list[Passage], limit: int = 12) -> list[dict]:
    """Offline mode: verbatim sentences from the retrieved passages."""
    out, seen = [], set()
    for p in pack:
        for sent in _sentences(p.text):
            key = sent.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append({"claim": sent, "evidence": sent, "source_ref": p.ref, "source": "retrieved"})
            if len(out) >= limit:
                return out
    return out


class ProductResearcher:
    """Agentic research (SID-2-style swarm search, see app/research) followed by
    claim extraction that must quote retrieved evidence; every claim is then
    verified against the source text. Unverifiable claims are dropped."""

    def __init__(self, llm):
        self.llm = llm

    def run(self, *, url: str | None, name: str | None, brand: str | None, description: str | None,
            audience: str | None, language: str, image_count: int = 0, page: PageExtract | None = None,
            brand_guidelines: str | None = None, agents: int = 3, effort: str = "medium",
            metric: str = "ndcg", max_pages: int = 6) -> tuple[ProductResearch, PageExtract | None, LLMUsage]:
        pages: list[PageExtract] = []
        if url:
            pages = crawl_site(url, max_pages=max_pages, first=page)
            page = pages[0]
        corpus = build_corpus(description, brand_guidelines, pages, url)
        task = (f"Find verifiable facts about the product {name or brand or ''} for an advert: what it is, "
                "features, benefits, price, materials, who it is for, problems it solves, guarantees, "
                "and any limitations or caveats.").replace("  ", " ")
        swarm_result, pack = None, []
        usage = LLMUsage(model="heuristic")
        if corpus.docs:
            swarm = Swarm(corpus, llm=self.llm, metric=metric, effort=effort, max_agents=agents)
            swarm_result = swarm.run(task)
            usage = swarm.usage
            pack = build_pack(corpus, swarm_result.fused, swarm_result.evidence)

        evidence_txt = "\n\n".join(f"[{p.ref}] ({p.title[:60]}{', ' + p.url if p.url else ''})\n{p.text}" for p in pack)
        page_note = f"(Product page not used: {page.status} {page.error or ''})" if (page and page.status != "ok") else ""
        prompt = (f"Product name hint: {name or 'unknown'}\nBrand: {brand or 'unknown'}\n"
                  f"Target audience hint: {audience or 'not specified'}\nOutput language for fields: {language}\n"
                  f"User uploaded {image_count} product image(s). {page_note}\n\n"
                  "EVIDENCE PASSAGES retrieved by the search agents. Use ONLY these. For every supported claim, "
                  "copy the exact supporting sentence into `evidence` (verbatim, it will be checked) and put the "
                  "passage reference (e.g. d2#120:480) into `source_ref`.\n\n" + (evidence_txt or "(no evidence found)"))

        def fallback():
            r = heuristic_research(name, brand, description, page, audience, language)
            r.supported_claims = [SupportedClaim(**{k: v for k, v in c.items() if k in SupportedClaim.model_fields})
                                  for c in heuristic_claims(pack)]
            r.features = [c.claim for c in r.supported_claims][:6] or r.features
            r.benefits = r.features[:3]
            return r

        research, u2 = self.llm.structured(system=P.RESEARCH_SYSTEM, prompt=prompt, schema=ProductResearch,
                                           task="product_research", fallback=fallback)
        usage.input_tokens += u2.input_tokens
        usage.output_tokens += u2.output_tokens
        usage.cost_usd += u2.cost_usd
        if u2.model != "heuristic":
            usage.model = u2.model

        verified, rejected = verify_claims(corpus, [c.model_dump() for c in research.supported_claims])
        research.supported_claims = [SupportedClaim(**{k: v for k, v in c.items() if k in SupportedClaim.model_fields})
                                     for c in verified]
        research.claims_to_avoid = list(research.claims_to_avoid) + [
            f"UNVERIFIED (no source text): {c.get('claim')}" for c in rejected]
        research.language = language
        if brand and not research.brand:
            research.brand = brand
        research = ResearchRecord(**research.model_dump())
        research.sources = [{"id": d.id, "title": d.title, "url": d.url, "source": d.source, "chars": len(d.text)}
                            for d in corpus.docs]
        if swarm_result:
            research.search = {
                "method": "SID-2-style search swarm (https://www.sid.ai/research/sid-2-technical-report)",
                "metric": metric, "effort": effort, "agents": len(swarm_result.reports),
                "turns": swarm_result.turns, "messages": swarm_result.messages,
                "fused_ranking": [[d, round(s, 4)] for d, s in swarm_result.fused],
                "rejected_claims": len(rejected), "trace": swarm_result.trace[:80]}
        return research, page, usage
