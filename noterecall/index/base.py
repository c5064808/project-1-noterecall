from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from noterecall.chunking import Chunk

# Pinecone caps the metadata attached to a vector, so the stored copy of the chunk text is
# clipped. It is only used to render results; the full text is always in the note itself.
METADATA_TEXT_LIMIT = 1500


@dataclass(frozen=True)
class Match:
    chunk_id: str
    score: float
    metadata: dict


class VectorIndex(Protocol):
    name: str

    def ensure_ready(self, dimension: int) -> None: ...

    def upsert(
        self,
        ids: Sequence[str],
        vectors: np.ndarray,
        metadatas: Sequence[dict],
        namespace: str,
    ) -> int: ...

    def query(self, vector: np.ndarray, top_k: int, namespace: str) -> list[Match]: ...

    def clear(self, namespace: str) -> None: ...

    def stats(self) -> dict: ...


def namespace_for(chunk_size: int) -> str:
    """One namespace per chunk size, which is how the chunk-size experiment is kept apart."""
    return f"chunk{chunk_size}"


def chunk_metadata(chunk: Chunk) -> dict:
    return {
        "note_id": chunk.note_id,
        "title": chunk.title,
        "ordinal": chunk.ordinal,
        "text": chunk.text[:METADATA_TEXT_LIMIT],
    }
