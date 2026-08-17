from __future__ import annotations

import time
from collections.abc import Sequence

import numpy as np

from noterecall.index.base import Match

UPSERT_BATCH = 100
READY_TIMEOUT_SECONDS = 120
READY_POLL_SECONDS = 2.0


class PineconeIndex:
    """Serverless Pinecone index, cosine metric, one namespace per chunk size."""

    name = "pinecone"

    def __init__(self, api_key: str | None, index_name: str, cloud: str, region: str):
        if not api_key:
            raise RuntimeError(
                "PINECONE_API_KEY is not set. Add it to .env, or use INDEX_BACKEND=local "
                "to keep everything on this machine."
            )
        try:
            from pinecone import Pinecone, ServerlessSpec
        except ImportError as exc:
            raise RuntimeError(
                "the pinecone package is not installed. Run 'pip install -r requirements.txt', "
                "or use INDEX_BACKEND=local."
            ) from exc

        self.index_name = index_name
        self._spec = ServerlessSpec(cloud=cloud, region=region)
        self._client = Pinecone(api_key=api_key)
        self._index = None

    def ensure_ready(self, dimension: int) -> None:
        if not self._client.has_index(self.index_name):
            self._client.create_index(
                name=self.index_name,
                dimension=dimension,
                metric="cosine",
                spec=self._spec,
            )

        deadline = time.monotonic() + READY_TIMEOUT_SECONDS
        while not self._client.describe_index(self.index_name).status["ready"]:
            if time.monotonic() > deadline:
                raise TimeoutError(
                    f"Pinecone index '{self.index_name}' was not ready after "
                    f"{READY_TIMEOUT_SECONDS}s"
                )
            time.sleep(READY_POLL_SECONDS)
        self._index = self._client.Index(self.index_name)

    def upsert(
        self,
        ids: Sequence[str],
        vectors: np.ndarray,
        metadatas: Sequence[dict],
        namespace: str,
    ) -> int:
        records = [
            {"id": chunk_id, "values": [float(x) for x in vector], "metadata": dict(metadata)}
            for chunk_id, vector, metadata in zip(ids, vectors, metadatas)
        ]
        for start in range(0, len(records), UPSERT_BATCH):
            self._handle().upsert(vectors=records[start:start + UPSERT_BATCH], namespace=namespace)
        return len(records)

    def query(self, vector: np.ndarray, top_k: int, namespace: str) -> list[Match]:
        response = self._handle().query(
            vector=[float(x) for x in np.asarray(vector).ravel()],
            top_k=top_k,
            namespace=namespace,
            include_metadata=True,
        )
        return [
            Match(match["id"], float(match["score"]), dict(match.get("metadata") or {}))
            for match in response["matches"]
        ]

    def clear(self, namespace: str) -> None:
        try:
            self._handle().delete(delete_all=True, namespace=namespace)
        except Exception:
            # Deleting a namespace that was never written is a 404 from the API; for our
            # purposes an absent namespace is already clear.
            pass

    def stats(self) -> dict:
        raw = self._handle().describe_index_stats()
        namespaces = {
            name: {"vector_count": int(values["vector_count"])}
            for name, values in (raw.get("namespaces") or {}).items()
        }
        return {
            "backend": self.name,
            "index_name": self.index_name,
            "dimension": int(raw.get("dimension", 0)),
            "namespaces": namespaces,
            "total_vector_count": int(raw.get("total_vector_count", 0)),
        }

    def _handle(self):
        if self._index is None:
            self._index = self._client.Index(self.index_name)
        return self._index
