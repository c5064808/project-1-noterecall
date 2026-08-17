from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, replace

from noterecall.embedding import Embedder
from noterecall.index.base import Match, VectorIndex

TERM_RE = re.compile(r"[a-z0-9_]+")
RRF_K = 60


@dataclass(frozen=True)
class SearchHit:
    chunk_id: str
    note_id: str
    title: str
    score: float
    text: str

    def snippet(self, query: str, width: int = 240) -> str:
        """A single-line window of the chunk, centred on the first query term that occurs."""
        text = " ".join(self.text.split())
        if len(text) <= width:
            return text

        lowered = text.lower()
        start = 0
        for term in TERM_RE.findall(query.lower()):
            found = lowered.find(term)
            if found != -1:
                start = max(0, min(found - width // 3, len(text) - width))
                break

        window = text[start:start + width].strip()
        prefix = "..." if start > 0 else ""
        suffix = "..." if start + width < len(text) else ""
        return f"{prefix}{window}{suffix}"


class SemanticSearch:
    def __init__(self, index: VectorIndex, embedder: Embedder, namespace: str):
        self.index = index
        self.embedder = embedder
        self.namespace = namespace

    def search(self, query: str, top_k: int = 5) -> list[SearchHit]:
        vector = self.embedder.encode_query(query)
        matches = self.index.query(vector, top_k, self.namespace)
        return [hit_from_match(match) for match in matches]


def hit_from_match(match: Match) -> SearchHit:
    metadata = match.metadata
    return SearchHit(
        chunk_id=match.chunk_id,
        note_id=metadata.get("note_id", ""),
        title=metadata.get("title", ""),
        score=match.score,
        text=metadata.get("text", ""),
    )


def reciprocal_rank_fusion(runs: Sequence[Sequence[SearchHit]], k: int = RRF_K) -> list[SearchHit]:
    """Merge ranked lists by summing 1/(k + rank), so agreement matters more than raw score."""
    scores: dict[str, float] = {}
    hits: dict[str, SearchHit] = {}
    for run in runs:
        for rank, hit in enumerate(run, start=1):
            scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + 1.0 / (k + rank)
            hits.setdefault(hit.chunk_id, hit)

    order = sorted(scores, key=lambda chunk_id: (-scores[chunk_id], chunk_id))
    return [replace(hits[chunk_id], score=scores[chunk_id]) for chunk_id in order]
