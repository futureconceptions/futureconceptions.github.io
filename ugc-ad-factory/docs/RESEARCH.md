# Evidence-backed product research (SID-2-style search swarm)

The Product Researcher no longer reads one page and summarises it. It runs an **agentic search swarm** over a small corpus, then lets the model extract claims **only from passages the agents retrieved**. It then **verifies every quoted claim against the source text**.

The search design follows the *SID-2 Technical Report: Scaling Search Swarms* (SID AI, 2026) — <https://www.sid.ai/research/sid-2-technical-report>, read on 2026-11-19.

## What was taken from the report, and what was not

SID-2 is a reinforcement-learning-trained search model. SID sells it through its own API (platform.sid.ai). The report describes the harness and swarm protocol but links no code or weights.

Here, the **harness and swarm protocol were re-implemented from the report's text**. The *policy* driving them is our configured LLM (Claude) or, offline, a deterministic facet-search policy. **No SID code or model is used.** Without SID's RL training, the quality of the search decisions depends on the LLM policy, not on SID-2.

| Report section | What the report says | Implementation |
|---|---|---|
| Harness | Snippets are the "highest-scoring window" of a fixed-size sliding window scored "with BM25 over unigrams and bigrams" | `research/bm25.py` (`BM25Index.best_window`, step = size/4, word-boundary snap) |
| Harness | The model "controls both the number of snippets returned (`limit`) and the size of each snippet (`snippet_size`)" | `search(query, limit, snippet_size)` |
| Harness | Each snippet "carries a reference `id#start:end`"; redundant text "is replaced with a marker, such as `[seen: "#120:480"]`"; reads "are served from the cache" | `AgentView._render` / `read` in `research/harness.py` |
| Harness | "each document receives a new ID when it first appears in an episode" | `assign_episode_ids` (d1, d2, …) |
| Harness | The episode ends by reporting "a ranked list of document IDs once it has enough context… or is confident that sufficient context does not exist" | `report_helpful_ids`; unknown IDs are dropped |
| Multi-agent harness design | Every agent can call the search tools, `fork`, `message`, `wait`, `list`, `report_helpful_ids`; inbox messages "are appended to the result of its next tool call"; reports "are fused with RRF" | `research/swarm.py`; RRF with k = 60 |
| Simulated-latency request scheduling | Agents that run ahead wait for the others, so they stay in sync | Lock-step rounds: every active agent takes one turn per round |
| Metric Steering | Objectives NDCG (comprehensive), F1 (precise), Recall@k (exactly k) | `research_metric` setting changes instructions and caps Recall@k reports. **Note:** the report states that metric steering "is not just prompting" (base models move ≤ 0.05 when only prompted). Ours is prompt-level, so expect a weaker effect than SID-2. |
| Reasoning effort | Low / medium / high trade quality against latency; the evaluation used a 10-turn limit | `research_effort`: 3 / 6 / 10 turns per agent. An agent that hits the limit is force-reported, so the episode always yields results. |
| Search parallelizes well | Breadth (many small agents) tends to beat depth for search | Default 3 agents (configurable 1–12). The coordinator forks facet helpers. |
| Not reproduced | RL training, the analytic latency model, proposer–solver self-play, entropy stabilisation, and the infrastructure sections | — |

## Claims must be backed by research

1. **Corpus.** The corpus is assembled from four sources:
   * the user's description;
   * the product page;
   * up to `research_max_pages` informative pages on the **same site**, such as specs, FAQ, materials, warranty or shipping. Login, cart, privacy and legal pages are skipped. Each page passes **robots.txt** and **SSRF** checks.
   * the brand guidelines.
2. **Search.** The swarm searches the corpus. The evidence pack is the set of passages the agents actually saw, in fused rank order; small corpora also include unranked documents last.
3. **Extraction.** Claim extraction receives only the evidence pack. Each claim must copy its supporting sentence verbatim into `evidence` and cite `source_ref` (`d2#120:480`).
4. **Verification** (`research/evidence.py`). The quote is located in the source text with whitespace and case normalised. The stored reference is rewritten to the **exact character span**, and the source URL is attached.
5. **Rejection.** Claims whose quote is not found are **removed**. They are listed as `UNVERIFIED (no source text): …` under `claims_to_avoid`.
6. **Downstream use.** The strategist may only use verified claims. Its existing `validate_concept` check flags any concept that cites a claim outside this list.

The project's **Research** tab shows each claim with its quote, span and source link, plus the searched corpus and the swarm summary. The full search trace is in `product.research.search.trace`.

## Settings (advanced mode, or the API)

| Field | Default | Meaning |
|---|---|---|
| `research_agents` | 3 | Swarm size (1 = single agent) |
| `research_effort` | `medium` | Turn limit per agent: 3 / 6 / 10 |
| `research_metric` | `ndcg` | `ndcg`, `f1` or `recall_at_k` |
| `research_max_pages` | 6 | Same-site pages fetched, including the product page |

**Cost.** With `LLM_PROVIDER=anthropic`, each agent turn is one structured LLM call, so the default (3 agents × up to 6 turns) is at most 18 calls per project. LLM spend appears under `llm:research` in usage.
