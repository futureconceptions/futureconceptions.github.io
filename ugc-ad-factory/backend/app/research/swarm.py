"""Search swarm runner (SID-2 Swarm-style harness, see harness.py docstring).

Every agent can: search, read, fork, message, wait, list, report_helpful_ids.
Agents act in lock-step rounds. Final rankings are fused with RRF.
The policy is the configured LLM (structured action per turn); without an
LLM a deterministic facet-search policy is used."""
from __future__ import annotations

import copy
import re
from typing import Literal

from pydantic import BaseModel, Field

from app.providers.base import LLMUsage
from app.research.harness import (MAX_TURNS, AgentView, Corpus, Effort, Episode, Metric, SwarmResult, rrf)

Tool = Literal["search", "read", "fork", "message", "wait", "list", "report_helpful_ids"]

PRODUCT_FACETS = [
    "features specifications what it does capacity size weight dimensions",
    "benefits results outcome",
    "price cost offer discount",
    "materials ingredients made of steel plastic cotton",
    "who it is for audience use case",
    "problem it solves pain",
    "warranty returns shipping guarantee",
    "how to use instructions",
    "limitations concerns not suitable",
    "certified tested proven study",
]


class AgentAction(BaseModel):
    reasoning: str = Field(description="One or two sentences on why this action")
    tool: Tool
    query: str | None = None
    limit: int | None = None
    snippet_size: int | None = None
    ref: str | None = Field(default=None, description="read: d3 or d3#120:480")
    fork_names: list[str] | None = None
    fork_tasks: list[str] | None = Field(default=None, description="One sub-task per forked agent")
    to: list[str] | None = None
    message: str | None = None
    ids: list[str] | None = Field(default=None, description="report_helpful_ids: ranked document ids")


SYSTEM = """You are a retrieval agent in a search swarm. Find the documents in the corpus that contain the
evidence needed for the task. Tools (call exactly one per turn):
- search(query, limit 1-20, snippet_size 120-2000): BM25 search; each result shows the best-matching snippet
  as [d3#start:end]. Text you already saw is replaced by [seen: "#a:b"].
- read(ref): expand a snippet (e.g. d3#120:480) or open a document (d3).
- fork(fork_names, fork_tasks): spawn helper agents that inherit your context, one sub-task each.
- message(to, message): send findings (e.g. promising document ids) to other agents' inboxes.
- wait: pause until a message arrives.
- list: list agents and their status.
- report_helpful_ids(ids): END your part and report the most helpful documents, most relevant first.
Rules: never invent document ids; report as soon as you have enough evidence or you are confident the corpus
does not contain it; prefer reformulating queries over re-reading the same text."""


class _Agent:
    def __init__(self, view: AgentView, task: str, facet_queries: list[str]):
        self.view = view
        self.task = task
        self.turns = 0
        self.waiting = False
        self.facets = facet_queries
        self.scores: dict[str, float] = {}

    @property
    def done(self) -> bool:
        return self.view.reported is not None


class Swarm:
    def __init__(self, corpus: Corpus, *, llm=None, metric: Metric = "ndcg", effort: Effort = "medium",
                 max_agents: int = 3, k: int = 10):
        self.ep = Episode(corpus, metric, k)
        self.llm = llm if (llm is not None and getattr(llm, "name", "") != "heuristic") else None
        self.effort = effort
        self.max_turns = MAX_TURNS[effort]
        self.max_agents = max(1, max_agents)
        self.agents: dict[str, _Agent] = {}
        self.messages = 0
        self.trace: list[dict] = []
        self.usage = LLMUsage(model="heuristic")

    # ----------------------------------------------------------------- run
    def run(self, task: str, facets: list[str] | None = None) -> SwarmResult:
        facets = facets or PRODUCT_FACETS
        self.agents["a1"] = _Agent(AgentView(self.ep, "a1"), task, facets)
        for _round in range(self.max_turns + 2):
            active = [a for a in self.agents.values() if not a.done]
            if not active:
                break
            for agent in list(active):  # lock-step: everyone advances one turn per round
                if agent.done:
                    continue
                if agent.waiting and not agent.view.inbox and any(not a.done and not a.waiting
                                                                   for a in self.agents.values() if a is not agent):
                    continue
                if agent.waiting:
                    agent.waiting = False
                    # wake-up: the inbox is delivered as the result of the wait call
                    agent.view._deliver("wait -> " + ("message(s) received" if agent.view.inbox else
                                                     "all other agents are idle or finished"))
                if agent.turns >= self.max_turns:
                    self._force_report(agent)
                    continue
                agent.turns += 1
                action = self._decide(agent)
                self._apply(agent, action)
        for a in self.agents.values():
            if not a.done:
                self._force_report(a)
        reports = {n: a.view.reported or [] for n, a in self.agents.items()}
        fused = rrf([r for r in reports.values() if r])
        evidence: dict[str, list[tuple[int, int]]] = {}
        for a in self.agents.values():
            for d, rngs in a.view.shown.items():
                evidence.setdefault(d, []).extend(rngs)
        return SwarmResult(fused=fused, reports=reports, turns={n: a.turns for n, a in self.agents.items()},
                           messages=self.messages, evidence=evidence, trace=self.trace)

    # ----------------------------------------------------------------- policy
    def _decide(self, agent: _Agent) -> AgentAction:
        if self.llm is None:
            return self._heuristic(agent)
        others = ", ".join(f"{n}({'done' if a.done else 'active'})" for n, a in self.agents.items() if a is not agent)
        history = "\n---\n".join(agent.view.transcript[-10:])[-12000:]
        prompt = (f"You are agent {agent.view.name}. TASK: {agent.task}\n{self.ep.guidance()}\n"
                  f"Turn {agent.turns} of {self.max_turns}. Other agents: {others or 'none'}. "
                  f"You may fork up to {self.max_agents - len(self.agents)} more agent(s).\n"
                  f"Corpus: {len(self.ep.corpus.docs)} documents.\n\nOBSERVATIONS SO FAR:\n{history or '(none yet)'}")
        try:
            action, usage = self.llm.structured(system=SYSTEM, prompt=prompt, schema=AgentAction, task="search_agent")
        except Exception as e:  # noqa: BLE001 - a failing policy call must not lose the episode
            self.trace.append({"agent": agent.view.name, "error": str(e)[:200]})
            return self._heuristic(agent)
        self.usage.input_tokens += usage.input_tokens
        self.usage.output_tokens += usage.output_tokens
        self.usage.cost_usd += usage.cost_usd
        self.usage.model = usage.model
        return action

    def _heuristic(self, agent: _Agent) -> AgentAction:
        name = agent.view.name
        if name == "a1" and agent.turns == 1 and self.max_agents > 1:
            n = min(self.max_agents - 1, len(agent.facets))
            groups = [agent.facets[i::n] for i in range(n)]
            return AgentAction(reasoning="split facets across helpers", tool="fork",
                               fork_names=[f"a{i + 2}" for i in range(n)],
                               fork_tasks=[" | ".join(g) for g in groups])
        queue = ([agent.task] + agent.facets) if self.max_agents == 1 else (agent.facets if name != "a1" else [agent.task])
        idx = agent.turns - (2 if name == "a1" and self.max_agents > 1 else 1)
        if 0 <= idx < len(queue) and agent.turns < self.max_turns:
            return AgentAction(reasoning="facet search", tool="search", query=f"{queue[idx]} {agent.task}"[:300],
                               limit=5, snippet_size=400)
        helpers_active = [n for n, a in self.agents.items() if n != name and not a.done]
        if name == "a1" and helpers_active and agent.turns < self.max_turns:
            return AgentAction(reasoning="wait for helper findings", tool="wait")
        ranked = sorted(agent.scores, key=agent.scores.get, reverse=True)
        if ranked and name != "a1" and not getattr(agent, "_sent", False):
            agent._sent = True  # type: ignore[attr-defined]
            return AgentAction(reasoning="share best leads", tool="message", to=["a1"],
                               message=f"{name} top documents: {', '.join(ranked[:3])}")
        return AgentAction(reasoning="enough evidence", tool="report_helpful_ids", ids=ranked)

    # ----------------------------------------------------------------- tools
    def _apply(self, agent: _Agent, act: AgentAction) -> None:
        v = agent.view
        entry = {"agent": v.name, "turn": agent.turns, "tool": act.tool}
        if act.tool == "search" and act.query:
            entry["query"] = act.query
            hits = self.ep.index.search(act.query, max(120, min(act.snippet_size or 400, 2000)),
                                        max(1, min(act.limit or 5, 20)))
            for rank, (d, w) in enumerate(hits):
                agent.scores[d] = agent.scores.get(d, 0) + w.score / (1 + rank)
            v.search(act.query, act.limit or 5, act.snippet_size or 400)
        elif act.tool == "read" and act.ref:
            entry["ref"] = act.ref
            v.read(act.ref)
            d = act.ref.split("#")[0]
            if d in self.ep.docs:
                agent.scores[d] = agent.scores.get(d, 0) + 0.5
        elif act.tool == "fork":
            names = list(act.fork_names or [])
            tasks = list(act.fork_tasks or [])
            made = []
            for i, n in enumerate(names):
                if len(self.agents) >= self.max_agents or not n or n in self.agents:
                    continue
                child = AgentView(self.ep, n)
                child.seen = copy.deepcopy(v.seen)          # forked context
                child.transcript = list(v.transcript)
                sub = tasks[i] if i < len(tasks) else agent.task
                self.agents[n] = _Agent(child, f"{agent.task} — focus: {sub}",
                                        [s.strip() for s in sub.split("|") if s.strip()] or agent.facets)
                made.append(n)
            entry["forked"] = made
            v._deliver(f"forked {made}" if made else "fork refused: agent limit reached")
        elif act.tool == "message":
            delivered = []
            for n in act.to or []:
                tgt = self.agents.get(n)
                if tgt and not tgt.done:
                    tgt.view.inbox.append(f"from {v.name}: {act.message or ''}"[:1500])
                    delivered.append(n)
                    # leads named in a message count as soft evidence for the recipient's fallback ranking
                    for rank, d in enumerate(re.findall(r"\bd\d+\b", act.message or "")):
                        if d in self.ep.docs:
                            tgt.scores[d] = tgt.scores.get(d, 0) + 1.0 / (1 + rank)
            self.messages += len(delivered)
            missed = [n for n in act.to or [] if n not in delivered]
            entry["to"] = delivered
            v._deliver(f"message delivered to {delivered}" + (f"; not delivered to {missed} (finished or unknown)"
                                                             if missed else ""))
        elif act.tool == "wait":
            agent.waiting = True
        elif act.tool == "list":
            v._deliver("\n".join(f"{n}: {'reported' if a.done else 'active'}" for n, a in self.agents.items()))
        elif act.tool == "report_helpful_ids":
            ids = act.ids or sorted(agent.scores, key=agent.scores.get, reverse=True)
            v.report(ids)
            entry["ids"] = v.reported
        else:
            v._deliver(f"invalid action {act.tool}: missing arguments")
        self.trace.append(entry)

    def _force_report(self, agent: _Agent) -> None:
        """Turn limit reached: report what was found so the episode still yields results."""
        agent.view.report(sorted(agent.scores, key=agent.scores.get, reverse=True))
        self.trace.append({"agent": agent.view.name, "tool": "report_helpful_ids", "forced": True,
                           "ids": agent.view.reported})
