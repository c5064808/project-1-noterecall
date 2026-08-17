from __future__ import annotations

import os
from dataclasses import dataclass, fields, replace
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_NOTES_DIR = PROJECT_ROOT / "data" / "notes"
DEFAULT_LOCAL_INDEX_DIR = PROJECT_ROOT / ".index"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_INDEX_NAME = "noterecall"
DEFAULT_CHUNK_SIZE = 256
DEFAULT_CHUNK_OVERLAP = 32
DEFAULT_TOP_K = 5

PATH_FIELDS = ("notes_dir", "local_index_dir")


@dataclass(frozen=True)
class Config:
    notes_dir: Path
    index_backend: str
    embedding_backend: str
    embedding_model: str
    pinecone_api_key: str | None
    pinecone_index_name: str
    pinecone_cloud: str
    pinecone_region: str
    local_index_dir: Path
    chunk_size: int
    chunk_overlap: int
    top_k: int


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) > 1 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def load_config(**overrides) -> Config:
    """Build the settings from .env, then the environment, then keyword overrides."""
    env = {**_read_env_file(PROJECT_ROOT / ".env"), **os.environ}

    api_key = env.get("PINECONE_API_KEY") or None
    cfg = Config(
        notes_dir=_as_path(env.get("NOTES_DIR"), DEFAULT_NOTES_DIR),
        index_backend=env.get("INDEX_BACKEND") or ("pinecone" if api_key else "local"),
        embedding_backend=env.get("EMBEDDING_BACKEND", "sentence-transformers"),
        embedding_model=env.get("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
        pinecone_api_key=api_key,
        pinecone_index_name=env.get("PINECONE_INDEX", DEFAULT_INDEX_NAME),
        pinecone_cloud=env.get("PINECONE_CLOUD", "aws"),
        pinecone_region=env.get("PINECONE_REGION", "us-east-1"),
        local_index_dir=_as_path(env.get("LOCAL_INDEX_DIR"), DEFAULT_LOCAL_INDEX_DIR),
        chunk_size=int(env.get("CHUNK_SIZE", DEFAULT_CHUNK_SIZE)),
        chunk_overlap=int(env.get("CHUNK_OVERLAP", DEFAULT_CHUNK_OVERLAP)),
        top_k=int(env.get("TOP_K", DEFAULT_TOP_K)),
    )

    # None overrides are dropped so the CLI can forward unset argparse values as they are.
    supplied = {key: value for key, value in overrides.items() if value is not None}
    unknown = sorted(set(supplied) - {f.name for f in fields(Config)})
    if unknown:
        raise TypeError(f"unknown config override(s): {', '.join(unknown)}")
    for key in PATH_FIELDS:
        if key in supplied:
            supplied[key] = Path(supplied[key]).expanduser()
    return replace(cfg, **supplied)


def _as_path(value: str | None, default: Path) -> Path:
    """Resolve a configured path; relative values are read as relative to the project root."""
    if not value:
        return default
    path = Path(value).expanduser()
    return path if path.is_absolute() else (PROJECT_ROOT / path)
