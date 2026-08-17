"""Load and validate the hand-written gold set."""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path

import yaml

REQUIRED_FIELDS = ("id", "query", "relevant_notes", "category")

# The three kinds of query the report splits its results on. Defined in goldset.yaml.
CATEGORIES = ("paraphrase", "exact-token", "lookup")


@dataclass(frozen=True)
class GoldQuery:
    query_id: str
    query: str
    relevant_notes: tuple[str, ...]
    category: str
    comment: str


def load_goldset(path: Path, known_note_ids: Collection[str] | None = None) -> list[GoldQuery]:
    """Read goldset.yaml, checking the judgements point at notes that exist.

    `known_note_ids` is the set of note ids in the corpus. Passing it is what turns a stale
    gold set into an error at startup rather than a silently deflated recall figure.
    """
    with path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    entries = raw.get("queries") if isinstance(raw, dict) else None
    if not entries:
        raise ValueError(f"{path} has no queries")

    queries = []
    seen: set[str] = set()
    for entry in entries:
        missing_fields = [field for field in REQUIRED_FIELDS if not entry.get(field)]
        if missing_fields:
            raise ValueError(f"{path}: entry {entry!r} is missing {', '.join(missing_fields)}")
        query_id = str(entry["id"])
        if query_id in seen:
            raise ValueError(f"{path}: duplicate query id {query_id}")
        seen.add(query_id)
        category = str(entry["category"]).strip()
        if category not in CATEGORIES:
            raise ValueError(
                f"{path}: query {query_id} has category {category!r}, "
                f"expected one of {', '.join(CATEGORIES)}"
            )
        queries.append(
            GoldQuery(
                query_id=query_id,
                query=entry["query"].strip(),
                relevant_notes=tuple(entry["relevant_notes"]),
                category=category,
                comment=str(entry.get("note", "")).strip(),
            )
        )

    if known_note_ids is not None:
        unknown = sorted(
            f"{q.query_id} -> {note_id}"
            for q in queries
            for note_id in q.relevant_notes
            if note_id not in known_note_ids
        )
        if unknown:
            raise ValueError(
                f"{path} judges notes that are not in the corpus:\n  " + "\n  ".join(unknown)
            )

    return queries
