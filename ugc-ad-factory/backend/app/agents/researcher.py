"""Agent 1 - Product Researcher."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup

from app.agents import prompts as P
from app.agents.schemas import ProductResearch, SupportedClaim
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


def extract_page(html: str, max_chars: int = 15000) -> PageExtract:
    soup = BeautifulSoup(html, "html.parser")
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
                       text=text, meta=meta)


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
    return extract_page(res.content.decode("utf-8", "ignore"))


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


class ProductResearcher:
    def __init__(self, llm):
        self.llm = llm

    def run(self, *, url: str | None, name: str | None, brand: str | None, description: str | None,
            audience: str | None, language: str, image_count: int = 0,
            page: PageExtract | None = None) -> tuple[ProductResearch, PageExtract | None, LLMUsage]:
        if url and page is None:
            page = fetch_product_page(url)
        sources = []
        if description:
            sources.append(f"USER DESCRIPTION:\n{description}")
        if page and page.status == "ok":
            sources.append(f"PRODUCT PAGE ({url})\nTITLE: {page.title}\nMETA: {json.dumps(page.meta)[:3000]}\n"
                           f"TEXT:\n{page.text}")
        elif page:
            sources.append(f"(Product page not used: {page.status} {page.error or ''})")
        prompt = (f"Product name hint: {name or 'unknown'}\nBrand: {brand or 'unknown'}\n"
                  f"Target audience hint: {audience or 'not specified'}\nOutput language for fields: {language}\n"
                  f"User uploaded {image_count} product image(s).\n\n" + "\n\n".join(sources))
        research, usage = self.llm.structured(
            system=P.RESEARCH_SYSTEM, prompt=prompt, schema=ProductResearch, task="product_research",
            fallback=lambda: heuristic_research(name, brand, description, page, audience, language))
        research.language = language
        if brand and not research.brand:
            research.brand = brand
        return research, page, usage
