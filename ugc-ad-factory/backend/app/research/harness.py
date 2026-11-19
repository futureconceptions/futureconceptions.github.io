"""Search harness and multi-agent swarm, implemented from the description in
the SID-2 technical report (SID AI, 2026,
https://www.sid.ai/research/sid-2-technical-report). No SID code or weights
are used: SID-2 is an RL-trained model offered via SID's API; here the policy
is our configured LLM (or a deterministic heuristic policy).

Report features reproduced (section in brackets):
* Snippets: BM25 (unigram+bigram) best sliding window per document; the agent
  chooses `limit` and `snippet_size` [Harness].
* Every snippet carries a reference `id#start:end`; the harness caches every
  surfaced document and tracks seen character ranges; redundant text is
  replaced by a marker like `[seen: "#120:480"]` [Harness].
* `read` expands a snippet from the cache, no backend round trip [Harness].
* Documents get per-episode IDs, never storage/database IDs [Harness].
* The episode ends when the agent reports a ranked list of helpful IDs, or
  when it is confident sufficient context does not exist [Harness].
* Metric Steering: the retrieval objective (NDCG / F1 / Recall@k) is an
  explicit parameter that changes search breadth and reporting [Metric
  Steering].
* Reasoning effort low/medium/high bounds the number of turns [Reasoning
  effort]; the report's evaluation used a 10-turn limit [Results].
* Swarm tools: fork, message, wait, list, report_helpful_ids; inbox messages
  are appended to the result of the recipient's next tool call; results of all
  reports are fused with Reciprocal Rank Fusion [Multi-agent harness design].
* Agents advance in lock-step so none runs ahead of the others, mirroring the
  report's simulated-latency scheduling (an agent >2 s of simulated latency
  ahead waits) [Simulated-latency request scheduling].
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from app.research.bm25 import BM25Index

Metric = Literal["ndcg", "f1", "recall_at_k"]
Effort = Literal["low", "medium", "high"]
MAX_TURNS = {"low": 3, "medium": 6, "high": 10}
RRF_K = 60  # standard RRF constant (Cormack et al., 2009)

METRIC_GUIDANCE = {
    "ndcg": "Objective NDCG: be comprehensive; reporting extra relevant background documents is not penalised. "
            "Rank the most relevant first.",
    "f1": "Objective F1: be precise; report only documents that are clearly needed. Non-critical documents are "
          "penalised.",
    "recall_at_k": "Objective Recall@{k}: report exactly {k} documents, most relevant first.",
}


@dataclass
class Doc:
    id: str           # per-episode id, e.g. "d3"
    text: str
    title: str = ""
    url: str | None = None
    source: str = "product_page"  # product_page | site_page | user_description | brand_guidelines


@dataclass
class Corpus:
    docs: list[Doc]

    def by_id(self) -> dict[str, Doc]:
        return {d.id: d for d in self.docs}


def assign_episode_ids(raw: list[Doc]) -> Corpus:
    """Per-episode IDs (d1, d2, ...) so the policy never sees storage IDs."""
    return Corpus([Doc(id=f"d{i + 1}", text=d.text, title=d.title, url=d.url, source=d.source)
                   for i, d in enumerate(raw)])


_REF = re.compile(r"^(d\d+)(?:#(\d+):(\d+))?$")


class Episode:
    """Shared document cache + seen-range bookkeeping for one research episode."""

    def __init__(self, corpus: Corpus, metric: Metric = "ndcg", k: int = 10):
        self.corpus = corpus
        self.docs = corpus.by_id()
        self.index = BM25Index({d.id: d.text for d in corpus.docs})
        self.metric = metric
        self.k = k

    def guidance(self) -> str:
        return METRIC_GUIDANCE[self.metric].format(k=self.k)


class AgentView:
    """One agent's tools. Seen ranges are per agent (each agent has its own
    context window); the document cache is shared by the episode."""

    def __init__(self, episode: Episode, name: str):
        self.ep = episode
        self.name = name
        self.seen: dict[str, list[tuple[int, int]]] = {}
        self.shown: dict[str, list[tuple[int, int]]] = {}  # ranges actually shown (evidence)
        self.inbox: list[str] = []
        self.reported: list[str] | None = None
        self.transcript: list[str] = []

    # --------------------------------------------------------------- tools
    def search(self, query: str, limit: int = 5, snippet_size: int = 400) -> str:
        limit = max(1, min(int(limit or 5), 20))
        snippet_size = max(120, min(int(snippet_size or 400), 2000))
        hits = self.ep.index.search(query, snippet_size, limit)
        if not hits:
            return self._deliver(f'search("{query}") -> no results')
        lines = [f'search("{query}") -> {len(hits)} result(s)']
        for doc_id, w in hits:
            d = self.ep.docs[doc_id]
            lines.append(f"[{doc_id}#{w.start}:{w.end}] {d.title[:80]}\n{self._render(doc_id, w.start, w.end)}")
        return self._deliver("\n".join(lines))

    def read(self, ref: str, expand: int = 600) -> str:
        m = _REF.match((ref or "").strip())
        if not m or m.group(1) not in self.ep.docs:
            return self._deliver(f"read({ref}) -> unknown reference; use an id like d2 or d2#100:500")
        doc_id = m.group(1)
        text = self.ep.docs[doc_id].text
        if m.group(2) is not None:
            s, e = int(m.group(2)), int(m.group(3))
            s, e = max(0, s - expand), min(len(text), e + expand)
        else:
            s, e = 0, min(len(text), 4000)
        return self._deliver(f"read({doc_id}#{s}:{e})\n{self._render(doc_id, s, e)}")

    def list_docs(self) -> str:
        return self._deliver("\n".join(f"{d.id}: {d.title[:80]} ({d.source}, {len(d.text)} chars)"
                                       for d in self.ep.corpus.docs))

    def report(self, ids: list[str]) -> str:
        valid = [i for i in ids if i in self.ep.docs]
        seen_order = list(dict.fromkeys(valid))
        if self.ep.metric == "recall_at_k":
            seen_order = seen_order[: self.ep.k]
        self.reported = seen_order
        return f"reported {seen_order}"

    # --------------------------------------------------------------- internals
    def _render(self, doc_id: str, s: int, e: int) -> str:
        """Return text[s:e] with already-seen sub-ranges replaced by markers."""
        text = self.ep.docs[doc_id].text
        parts, cur = [], s
        for a, b in sorted(self.seen.get(doc_id, [])):
            a, b = max(a, s), min(b, e)
            if a >= b:
                continue
            if a > cur:
                parts.append(text[cur:a])
                self._mark(doc_id, cur, a)
            parts.append(f'[seen: "#{a}:{b}"]')
            cur = max(cur, b)
        if cur < e:
            parts.append(text[cur:e])
            self._mark(doc_id, cur, e)
        return "".join(parts).strip()

    def _mark(self, doc_id: str, a: int, b: int) -> None:
        self.shown.setdefault(doc_id, []).append((a, b))
        rng = sorted(self.seen.get(doc_id, []) + [(a, b)])
        merged = [rng[0]]
        for x, y in rng[1:]:
            if x <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], y))
            else:
                merged.append((x, y))
        self.seen[doc_id] = merged

    def _deliver(self, result: str) -> str:
        """Inbox messages are appended to the result of the next tool call."""
        if self.inbox:
            result += "\n\nINBOX:\n" + "\n".join(self.inbox)
            self.inbox.clear()
        self.transcript.append(result)
        return result


def rrf(rankings: list[list[str]], k: int = RRF_K) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking, start=1):
            scores[doc] = scores.get(doc, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


@dataclass
class SwarmResult:
    fused: list[tuple[str, float]]
    reports: dict[str, list[str]]
    turns: dict[str, int]
    messages: int
    evidence: dict[str, list[tuple[int, int]]] = field(default_factory=dict)  # ranges shown per doc
    trace: list[dict] = field(default_factory=list)
