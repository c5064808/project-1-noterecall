from __future__ import annotations

from noterecall.config import Config
from noterecall.index.base import (
    METADATA_TEXT_LIMIT,
    Match,
    VectorIndex,
    chunk_metadata,
    namespace_for,
)
from noterecall.index.local_index import LocalIndex

__all__ = [
    "METADATA_TEXT_LIMIT",
    "LocalIndex",
    "Match",
    "VectorIndex",
    "build_index",
    "chunk_metadata",
    "namespace_for",
]


def build_index(cfg: Config) -> VectorIndex:
    if cfg.index_backend == "local":
        return LocalIndex(cfg.local_index_dir)
    if cfg.index_backend == "pinecone":
        # Imported here so the package still works without the pinecone dependency.
        from noterecall.index.pinecone_index import PineconeIndex

        return PineconeIndex(
            cfg.pinecone_api_key,
            cfg.pinecone_index_name,
            cfg.pinecone_cloud,
            cfg.pinecone_region,
        )
    raise ValueError(f"unknown index backend {cfg.index_backend!r}; expected 'local' or 'pinecone'")
