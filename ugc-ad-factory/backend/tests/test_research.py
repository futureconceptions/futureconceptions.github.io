"""SID-2-style search harness, swarm and evidence verification."""
import socket

import httpx
import respx

from app.agents.researcher import ProductResearcher, build_corpus, crawl_site, extract_page
from app.providers.base import LLMUsage
from app.providers.llm import HeuristicLLM
from app.research.bm25 import BM25Index, terms
from app.research.evidence import build_pack, locate, verify_claims
from app.research.harness import AgentView, Corpus, Doc, Episode, assign_episode_ids, rrf
from app.research.swarm import AgentAction, Swarm

FILLER = "Lorem ipsum dolor sit amet consectetur. " * 30
DOCS = [
    Doc(id="", title="Specs", text=FILLER + "The bottle keeps drinks cold for 24 hours thanks to double-wall vacuum "
                                         "insulation. " + FILLER, source="product_page"),
    Doc(id="", title="Shipping", text="Free shipping in Germany. Returns accepted within 30 days. " + FILLER,
        source="site_page"),
    Doc(id="", title="Materials", text="Made from 18/8 stainless steel. The lid is leak-proof and BPA-free.",
        source="site_page"),
]


def corpus():
    return assign_episode_ids(DOCS)


def test_terms_include_bigrams_and_drop_stopwords():
    t = terms("keeps the drinks cold")
    assert "keeps" in t and "the" not in t and "keeps the" in t and "drinks cold" in t


def test_best_window_finds_relevant_passage_in_long_doc():
    c = corpus()
    idx = BM25Index({d.id: d.text for d in c.docs})
    w = idx.best_window("d1", "cold 24 hours insulation", 200)
    assert "24 hours" in c.docs[0].text[w.start:w.end]
    assert w.end - w.start < 300
    ranked = idx.search("stainless steel lid", 200, 3)
    assert ranked[0][0] == "d3"


def test_snippet_refs_seen_markers_and_cached_reads():
    view = AgentView(Episode(corpus()), "a1")
    out1 = view.search("cold 24 hours", limit=1, snippet_size=200)
    assert "[d1#" in out1 and "24 hours" in out1
    out2 = view.search("cold 24 hours vacuum", limit=1, snippet_size=200)
    body2 = out2.split("\n", 2)[2]
    assert '[seen: "#' in body2 and "24 hours" not in body2  # never shows the same text twice
    ref = out1.split("[", 1)[1].split("]", 1)[0]
    out3 = view.read(ref, expand=50)
    assert '[seen: "#' in out3  # the expansion only adds new text
    assert view.read("d99").startswith("read(d99) -> unknown reference")


def test_episode_ids_hide_storage_ids():
    c = assign_episode_ids([Doc(id="db-uuid-123", text="x y z", title="t")])
    assert c.docs[0].id == "d1"


def test_rrf_fusion():
    fused = rrf([["d1", "d2", "d3"], ["d2", "d1"], ["d2"]])
    assert [d for d, _ in fused] == ["d2", "d1", "d3"]


def test_inbox_messages_append_to_next_tool_result():
    view = AgentView(Episode(corpus()), "a2")
    view.inbox.append("from a1: try d3")
    out = view.list_docs()
    assert out.endswith("INBOX:\nfrom a1: try d3") and not view.inbox


def test_metric_steering_recall_at_k_caps_report():
    view = AgentView(Episode(corpus(), metric="recall_at_k", k=1), "a1")
    view.report(["d2", "d1", "d3", "bogus"])
    assert view.reported == ["d2"]
    assert "Recall@1" in Episode(corpus(), metric="recall_at_k", k=1).guidance()


def test_heuristic_swarm_forks_messages_and_fuses():
    res = Swarm(corpus(), llm=HeuristicLLM(), max_agents=3, effort="medium").run("AquaBottle")
    assert set(res.reports) == {"a1", "a2", "a3"}
    assert res.messages >= 1  # helpers send leads to the coordinator
    assert res.fused and all(d in {"d1", "d2", "d3"} for d, _ in res.fused)
    tools = {t["tool"] for t in res.trace}
    assert {"fork", "search", "message", "report_helpful_ids"} <= tools
    assert res.evidence  # ranges actually shown to agents


def test_single_agent_low_effort_respects_turn_limit():
    res = Swarm(corpus(), llm=HeuristicLLM(), max_agents=1, effort="low").run("bottle cold steel")
    assert res.turns["a1"] <= 3 and res.reports["a1"]


class ScriptedPolicy:
    """Stands in for an LLM policy: verifies the harness tool protocol."""
    name = "scripted"
    supports_vision = False

    def __init__(self):
        self.prompts = []

    def structured(self, *, system, prompt, schema, images=None, task="", fallback=None):
        self.prompts.append(prompt)
        me = prompt.split("You are agent ")[1].split(".")[0]
        n = sum(1 for p in self.prompts if p.startswith(f"You are agent {me}."))
        if me == "a1":
            plan = [AgentAction(reasoning="split", tool="fork", fork_names=["a2"], fork_tasks=["materials"]),
                    AgentAction(reasoning="look", tool="search", query="cold 24 hours", limit=2, snippet_size=200),
                    AgentAction(reasoning="wait", tool="wait"),
                    AgentAction(reasoning="done", tool="report_helpful_ids", ids=["d1", "d3", "d77"])]
        else:
            plan = [AgentAction(reasoning="look", tool="search", query="stainless steel leak-proof", limit=2),
                    AgentAction(reasoning="share", tool="message", to=["a1"], message="d3 has the materials"),
                    AgentAction(reasoning="done", tool="report_helpful_ids", ids=["d3"])]
        return plan[min(n, len(plan)) - 1], LLMUsage(input_tokens=10, output_tokens=5, model="scripted", cost_usd=0.001)


def test_llm_policy_protocol():
    pol = ScriptedPolicy()
    s = Swarm(corpus(), llm=pol, max_agents=2, effort="medium")
    res = s.run("AquaBottle facts")
    assert res.reports["a2"] == ["d3"] and res.reports["a1"] == ["d1", "d3"]  # invented id dropped
    assert res.fused[0][0] == "d3"
    assert res.messages == 1 and s.usage.input_tokens > 0
    assert any("INBOX" in p and "d3 has the materials" in p for p in pol.prompts)  # delivered on a1's next turn
    assert any("Objective NDCG" in p for p in pol.prompts)


def test_claim_verification_rejects_unsupported():
    c = corpus()
    ok, bad = verify_claims(c, [
        {"claim": "24h cold", "evidence": "keeps drinks cold for 24 hours", "source_ref": "d1#0:10"},
        {"claim": "lab tested", "evidence": "Independently lab tested by TÜV", "source_ref": "d1"},
        {"claim": "steel", "evidence": "made from 18/8   stainless steel", "source_ref": "d2"},  # wrong doc, ws
    ])
    assert [o["claim"] for o in ok] == ["24h cold", "steel"]
    assert ok[1]["source_ref"].startswith("d3#") and ok[1]["evidence"] == "Made from 18/8 stainless steel"
    d, s, e = locate(c, "keeps drinks cold for 24 hours", None)
    assert c.by_id()[d].text[s:e] == "keeps drinks cold for 24 hours"
    assert bad[0]["claim"] == "lab tested"


def test_build_pack_uses_seen_ranges_in_rank_order():
    c = corpus()
    pack = build_pack(c, [("d3", 1.0), ("d1", 0.5)], {"d1": [(10, 50)], "d3": [(0, 30)]})
    assert [p.doc_id for p in pack] == ["d3", "d1", "d2"] and pack[0].ref == "d3#0:30"  # unranked doc last


HOME = """<html><head><title>AquaBottle</title></head><body><h1>AquaBottle 750</h1>
<p>Keeps drinks cold for 24 hours.</p><a href="/faq">FAQ</a><a href="/cart">Cart</a>
<a href="/specs">Technical specs</a><a href="https://other.example.org/x">Partner</a></body></html>"""
SPECS = "<html><head><title>Specs</title></head><body><p>Capacity is 750 ml and weight is 350 g.</p></body></html>"
FAQ = "<html><head><title>FAQ</title></head><body><p>The lid is dishwasher safe on the top rack.</p></body></html>"


@respx.mock
def test_crawl_same_site_informative_pages(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda h, p, proto=None: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", p))])
    respx.get("https://shop.example.com/robots.txt").mock(return_value=httpx.Response(200, text="User-agent: *\nDisallow: /faq\n"))
    respx.get("https://shop.example.com/p").mock(return_value=httpx.Response(200, html=HOME))
    respx.get("https://shop.example.com/specs").mock(return_value=httpx.Response(200, html=SPECS))
    faq = respx.get("https://shop.example.com/faq").mock(return_value=httpx.Response(200, html=FAQ))
    pages = crawl_site("https://shop.example.com/p", max_pages=5)
    assert [p.title for p in pages] == ["AquaBottle", "Specs"]  # cart skipped, faq robots-blocked, offsite ignored
    assert not faq.called
    c = build_corpus("Great bottle for commuters.", None, pages, "https://shop.example.com/p")
    assert [d.source for d in c.docs] == ["user_description", "product_page", "site_page"]

    research, _, _ = ProductResearcher(HeuristicLLM()).run(
        url="https://shop.example.com/p", name="AquaBottle", brand=None, description="Great bottle for commuters.",
        audience=None, language="en")
    assert research.supported_claims, "expected verified claims"
    by_text = {d["id"]: d for d in research.sources}
    for cl in research.supported_claims:
        doc_id, rng = cl.source_ref.split("#")
        s, e = map(int, rng.split(":"))
        assert doc_id in by_text and e > s  # every claim cites an exact span
    assert any("750 ml" in cl.evidence for cl in research.supported_claims)  # found on a crawled sub-page
    assert research.search["agents"] == 3 and "sid.ai" in research.search["method"]


def test_extract_page_collects_same_host_links():
    pg = extract_page(HOME, base_url="https://shop.example.com/p")
    urls = [u for u, _ in pg.links]
    assert "https://shop.example.com/specs" in urls and all("other.example.org" not in u for u in urls)
