"""BM25 over unigrams + bigrams, and best-window snippet selection.

Implements the snippet rule from the SID-2 technical report (§"Harness"):
"we slide a fixed-size window over the document, score each position against
the query with BM25 over unigrams and bigrams, and return only the
highest-scoring window." (https://www.sid.ai/research/sid-2-technical-report)
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

_TOKEN = re.compile(r"[\wäöüß]+", re.IGNORECASE)
STOP = {"the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "it", "with", "this", "that",
        "der", "die", "das", "und", "oder", "ist", "mit", "für", "ein", "eine", "zu", "in", "den", "von"}

K1, B = 1.2, 0.75


def tokens_with_offsets(text: str) -> list[tuple[str, int, int]]:
    return [(m.group(0).lower(), m.start(), m.end()) for m in _TOKEN.finditer(text)]


def terms(text: str) -> list[str]:
    """Unigrams (stopwords dropped) + bigrams (stopwords kept, so phrases match)."""
    toks = [t for t, _, _ in tokens_with_offsets(text)]
    uni = [t for t in toks if t not in STOP]
    bi = [f"{a} {b}" for a, b in zip(toks, toks[1:])]
    return uni + bi


@dataclass
class Window:
    start: int
    end: int
    score: float


class BM25Index:
    def __init__(self, docs: dict[str, str]):
        self.docs = docs
        self.tf = {d: Counter(terms(t)) for d, t in docs.items()}
        self.len = {d: sum(c.values()) for d, c in self.tf.items()}
        self.avglen = (sum(self.len.values()) / len(self.len)) if self.len else 1.0
        df: Counter = Counter()
        for c in self.tf.values():
            df.update(c.keys())
        n = max(1, len(docs))
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def _bm25(self, q: list[str], tf: Counter, length: int, avglen: float) -> float:
        s = 0.0
        for t in set(q):
            f = tf.get(t, 0)
            if not f:
                continue
            idf = self.idf.get(t, math.log(1 + (len(self.docs) + 0.5) / 0.5))
            s += idf * f * (K1 + 1) / (f + K1 * (1 - B + B * length / max(1.0, avglen)))
        return s

    def best_window(self, doc_id: str, query: str, size: int) -> Window:
        """Slide a fixed-size char window (step = size/4) and return the
        BM25-best one, snapped to word boundaries."""
        text = self.docs[doc_id]
        q = terms(query)
        if len(text) <= size:
            return Window(0, len(text), self._bm25(q, Counter(terms(text)), len(terms(text)) or 1, len(terms(text)) or 1))
        step = max(1, size // 4)
        best = Window(0, size, -1.0)
        avg = max(1.0, len(terms(text[:size])))
        for start in range(0, max(1, len(text) - size) + step, step):
            start = min(start, len(text) - size)
            w = text[start:start + size]
            wt = Counter(terms(w))
            sc = self._bm25(q, wt, sum(wt.values()) or 1, avg)
            if sc > best.score:
                best = Window(start, start + size, sc)
            if start >= len(text) - size:
                break
        return snap(text, best)

    def search(self, query: str, size: int, limit: int, allowed: set[str] | None = None) -> list[Window | tuple]:
        """Rank documents by their best window (passage-level BM25)."""
        out = []
        for d in self.docs:
            if allowed is not None and d not in allowed:
                continue
            w = self.best_window(d, query, size)
            if w.score > 0:
                out.append((d, w))
        out.sort(key=lambda x: x[1].score, reverse=True)
        return out[:limit]


def snap(text: str, w: Window) -> Window:
    s, e = w.start, w.end
    while s > 0 and s > w.start - 40 and not text[s - 1].isspace():
        s -= 1
    while e < len(text) and e < w.end + 40 and not text[e].isspace():
        e += 1
    return Window(s, min(e, len(text)), w.score)
