from __future__ import annotations

import re
from collections.abc import Sequence

from noterecall.chunking import Chunk
from noterecall.search import SearchHit

TOKEN_RE = re.compile(r"[a-z0-9_]+")

# Deliberately short. A long stopword list would strip terms such as "not" or "over" that
# carry meaning in technical notes.
STOPWORDS = frozenset(
    """
    a an and are as at be by for from in into is it its of on or that the their then
    there these this to was were what when which with
    """.split()
)


def tokenise(text: str) -> list[str]:
    return [token for token in TOKEN_RE.findall(text.lower()) if token not in STOPWORDS]


class BM25Search:
    """BM25 keyword baseline over the same chunks the vector index holds."""

    def __init__(self, chunks: Sequence[Chunk], model):
        self.chunks = list(chunks)
        self._model = model

    @classmethod
    def from_chunks(cls, chunks: Sequence[Chunk]) -> "BM25Search":
        try:
            from rank_bm25 import BM25Okapi
        except ImportError as exc:
            raise RuntimeError(
                "rank-bm25 is not installed. Run 'pip install -r requirements.txt'."
            ) from exc

        if not chunks:
            raise ValueError("cannot build a BM25 index from an empty corpus")
        return cls(chunks, BM25Okapi([tokenise(chunk.text) for chunk in chunks]))

    def search(self, query: str, top_k: int = 5) -> list[SearchHit]:
        terms = tokenise(query)
        if not terms:
            return []

        scores = self._model.get_scores(terms)
        ranked = sorted(range(len(scores)), key=lambda i: (-scores[i], self.chunks[i].chunk_id))
        hits = []
        for i in ranked[:top_k]:
            if scores[i] <= 0:
                break
            chunk = self.chunks[i]
            hits.append(
                SearchHit(
                    chunk_id=chunk.chunk_id,
                    note_id=chunk.note_id,
                    title=chunk.title,
                    score=float(scores[i]),
                    text=chunk.text,
                )
            )
        return hits
