from __future__ import annotations

import re
import sys
import zlib
from collections.abc import Sequence
from typing import Protocol

import numpy as np

from noterecall.config import Config

HASHING_DIMENSION = 384
TOKEN_RE = re.compile(r"[a-z0-9_]+")

PROGRESS_THRESHOLD = 500
PROGRESS_EVERY_N_BATCHES = 10


class Embedder(Protocol):
    name: str
    dimension: int

    def encode_documents(self, texts: Sequence[str], batch_size: int = 64) -> np.ndarray: ...

    def encode_query(self, text: str) -> np.ndarray: ...


class SentenceTransformerEmbedder:
    """Wraps a sentence-transformers model and returns L2-normalised float32 vectors."""

    def __init__(self, model_name: str):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed. Run 'pip install -r requirements.txt', "
                "or set EMBEDDING_BACKEND=hashing for an offline smoke test."
            ) from exc

        self.name = model_name
        self._model = SentenceTransformer(model_name)
        # Renamed in sentence-transformers 5; the old name still works but warns.
        read_dimension = getattr(
            self._model, "get_embedding_dimension", self._model.get_sentence_embedding_dimension
        )
        self.dimension = int(read_dimension())

    def encode_documents(self, texts: Sequence[str], batch_size: int = 64) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dimension), dtype=np.float32)

        report = len(texts) > PROGRESS_THRESHOLD
        batches = []
        for number, start in enumerate(range(0, len(texts), batch_size), start=1):
            batch = list(texts[start:start + batch_size])
            batches.append(
                self._model.encode(
                    batch,
                    batch_size=batch_size,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                )
            )
            if report and number % PROGRESS_EVERY_N_BATCHES == 0:
                done = min(start + batch_size, len(texts))
                print(f"encoded {done}/{len(texts)} texts", file=sys.stderr)
        return np.vstack(batches).astype(np.float32, copy=False)

    def encode_query(self, text: str) -> np.ndarray:
        vector = self._model.encode(
            text, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False
        )
        return vector.astype(np.float32, copy=False)


class HashingEmbedder:
    """Hashed bag of unigrams and bigrams. No model download, no network, no semantics."""

    name = "hashing"

    def __init__(self, dimension: int = HASHING_DIMENSION):
        self.dimension = dimension

    def encode_documents(self, texts: Sequence[str], batch_size: int = 64) -> np.ndarray:
        vectors = np.zeros((len(texts), self.dimension), dtype=np.float32)
        for row, text in enumerate(texts):
            self._fill(vectors[row], text)
        return vectors

    def encode_query(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimension, dtype=np.float32)
        self._fill(vector, text)
        return vector

    def _fill(self, row: np.ndarray, text: str) -> None:
        tokens = TOKEN_RE.findall(text.lower())
        features = tokens + [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]
        for feature in features:
            digest = zlib.crc32(feature.encode("utf-8"))
            # Signed hashing: the low bit picks the sign so colliding features tend to
            # cancel rather than pile up as spurious similarity.
            sign = 1.0 if digest & 1 else -1.0
            row[(digest >> 1) % self.dimension] += sign

        norm = float(np.linalg.norm(row))
        if norm:
            row /= norm


def build_embedder(cfg: Config) -> Embedder:
    if cfg.embedding_backend == "hashing":
        return HashingEmbedder()
    if cfg.embedding_backend == "sentence-transformers":
        return SentenceTransformerEmbedder(cfg.embedding_model)
    raise ValueError(
        f"unknown embedding backend {cfg.embedding_backend!r}; "
        "expected 'sentence-transformers' or 'hashing'"
    )
