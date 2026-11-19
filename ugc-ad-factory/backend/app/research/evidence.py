"""Evidence packs and citation verification ("back everything with research").

Every claim the pipeline may use must cite a passage `dN#start:end` and quote
text that literally exists in that source document. Claims that fail
verification are removed and recorded, never silently kept."""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.research.harness import Corpus

_WS = re.compile(r"\s+")


def _norm(s: str) -> str:
    return _WS.sub(" ", s.replace(" ", " ")).strip().lower().strip(" .;:,!?\"'“”„")


@dataclass
class Passage:
    ref: str
    doc_id: str
    start: int
    end: int
    text: str
    url: str | None
    title: str


def merge_ranges(rngs: list[tuple[int, int]], gap: int = 40) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for a, b in sorted(rngs):
        if out and a <= out[-1][1] + gap:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def build_pack(corpus: Corpus, fused: list[tuple[str, float]], shown: dict[str, list[tuple[int, int]]],
               max_docs: int = 8, max_chars: int = 14000) -> list[Passage]:
    """Passages the agents actually saw, for the top fused documents, in rank order."""
    docs = corpus.by_id()
    pack, total = [], 0
    ranked = [d for d, _ in fused[:max_docs]]
    # Small corpora: unranked documents follow the ranked ones, so a lexical
    # miss never silently drops a sourced fact (they keep their low rank).
    ranked += [d.id for d in corpus.docs if d.id not in ranked][: max(0, max_docs - len(ranked))]
    for doc_id in ranked:
        d = docs[doc_id]
        for a, b in merge_ranges(shown.get(doc_id, [])) or [(0, min(len(d.text), 1500))]:
            t = d.text[a:b]
            if total + len(t) > max_chars:
                return pack
            pack.append(Passage(f"{doc_id}#{a}:{b}", doc_id, a, b, t, d.url, d.title))
            total += len(t)
    return pack


def locate(corpus: Corpus, quote: str, ref: str | None) -> tuple[str, int, int] | None:
    """Find `quote` in the cited document (or, failing that, anywhere in the
    corpus). Returns (doc_id, start, end) of the literal occurrence."""
    q = _norm(quote)
    if len(q) < 8:
        return None
    docs = corpus.by_id()
    order = []
    if ref:
        d = ref.split("#")[0]
        if d in docs:
            order.append(d)
    order += [d for d in docs if d not in order]
    for d in order:
        text = docs[d].text
        # map normalised text back to original offsets
        norm_chars, idx_map = [], []
        prev_space = False
        for i, ch in enumerate(text):
            c = " " if ch.isspace() or ch == " " else ch.lower()
            if c == " " and prev_space:
                continue
            prev_space = c == " "
            norm_chars.append(c)
            idx_map.append(i)
        hay = "".join(norm_chars)
        pos = hay.find(q)
        if pos >= 0:
            return d, idx_map[pos], idx_map[pos + len(q) - 1] + 1
    return None


def verify_claims(corpus: Corpus, claims: list[dict]) -> tuple[list[dict], list[dict]]:
    """Each claim: {claim, evidence, source_ref?}. Returns (verified, rejected)
    with exact refs and source URLs filled in."""
    docs = corpus.by_id()
    ok, bad = [], []
    for c in claims:
        hit = locate(corpus, c.get("evidence") or "", c.get("source_ref"))
        if not hit:
            bad.append({**c, "reason": "evidence quote not found in any source document"})
            continue
        d, s, e = hit
        doc = docs[d]
        ok.append({**c, "source_ref": f"{d}#{s}:{e}", "source_url": doc.url, "source": doc.source,
                   "evidence": doc.text[s:e]})
    return ok, bad
