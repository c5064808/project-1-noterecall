from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from noterecall.index.base import Match


@dataclass
class _Shard:
    ids: list[str] = field(default_factory=list)
    metadatas: list[dict] = field(default_factory=list)
    vectors: np.ndarray | None = None


class LocalIndex:
    """Exact cosine search over a numpy matrix, one matrix and JSON sidecar per namespace.

    This is a correctness reference rather than a speed comparison: it scores every vector
    instead of approximating, so it is slower than Pinecone but always returns the true
    top k.
    """

    name = "local"

    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self._shards: dict[str, _Shard] = {}

    def ensure_ready(self, dimension: int) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)

    def upsert(
        self,
        ids: Sequence[str],
        vectors: np.ndarray,
        metadatas: Sequence[dict],
        namespace: str,
    ) -> int:
        if len(ids) != len(vectors) or len(ids) != len(metadatas):
            raise ValueError("ids, vectors and metadatas must be the same length")
        if not ids:
            return 0

        shard = self._load(namespace)
        position = {chunk_id: i for i, chunk_id in enumerate(shard.ids)}
        rows = [] if shard.vectors is None else [shard.vectors]
        for chunk_id, vector, metadata in zip(ids, vectors, metadatas):
            existing = position.get(chunk_id)
            if existing is None:
                position[chunk_id] = len(shard.ids)
                shard.ids.append(chunk_id)
                shard.metadatas.append(dict(metadata))
                rows.append(np.asarray(vector, dtype=np.float32).reshape(1, -1))
            else:
                shard.metadatas[existing] = dict(metadata)
                shard.vectors[existing] = vector

        shard.vectors = np.vstack(rows).astype(np.float32, copy=False)
        self.directory.mkdir(parents=True, exist_ok=True)
        np.save(self._vectors_path(namespace), shard.vectors)
        self._meta_path(namespace).write_text(
            json.dumps({"ids": shard.ids, "metadatas": shard.metadatas}, indent=1),
            encoding="utf-8",
        )
        return len(ids)

    def query(self, vector: np.ndarray, top_k: int, namespace: str) -> list[Match]:
        shard = self._load(namespace)
        if shard.vectors is None or not shard.ids:
            raise FileNotFoundError(
                f"no local index for namespace '{namespace}' in {self.directory}; "
                "build it first with 'python -m noterecall index'"
            )

        # Both sides are L2-normalised, so the dot product is the cosine similarity.
        scores = shard.vectors @ np.asarray(vector, dtype=np.float32)
        top_k = min(top_k, len(scores))
        best = np.argpartition(-scores, top_k - 1)[:top_k]
        best = best[np.argsort(-scores[best], kind="stable")]
        return [Match(shard.ids[i], float(scores[i]), shard.metadatas[i]) for i in best]

    def clear(self, namespace: str) -> None:
        self._shards.pop(namespace, None)
        self._vectors_path(namespace).unlink(missing_ok=True)
        self._meta_path(namespace).unlink(missing_ok=True)

    def stats(self) -> dict:
        namespaces = {}
        for path in sorted(self.directory.glob("*.npy")):
            shard = self._load(path.stem)
            if shard.vectors is None:
                continue
            namespaces[path.stem] = {
                "vector_count": len(shard.ids),
                "dimension": int(shard.vectors.shape[1]),
                "size_mb": round(path.stat().st_size / (1024 * 1024), 3),
            }
        return {
            "backend": self.name,
            "directory": str(self.directory),
            "namespaces": namespaces,
            "total_vector_count": sum(ns["vector_count"] for ns in namespaces.values()),
        }

    def _load(self, namespace: str) -> _Shard:
        if namespace in self._shards:
            return self._shards[namespace]

        shard = _Shard()
        vectors_path = self._vectors_path(namespace)
        meta_path = self._meta_path(namespace)
        if vectors_path.is_file() and meta_path.is_file():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            shard.ids = meta["ids"]
            shard.metadatas = meta["metadatas"]
            shard.vectors = np.load(vectors_path).astype(np.float32, copy=False)
        self._shards[namespace] = shard
        return shard

    def _vectors_path(self, namespace: str) -> Path:
        return self.directory / f"{namespace}.npy"

    def _meta_path(self, namespace: str) -> Path:
        return self.directory / f"{namespace}.json"
