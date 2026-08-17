from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from noterecall.notes import Note

MIN_CHUNK_TOKENS = 24


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    note_id: str
    title: str
    ordinal: int
    text: str
    token_start: int
    token_end: int


def chunk_note(note: Note, size: int, overlap: int) -> list[Chunk]:
    """Split one note into overlapping token windows.

    Tokens are whitespace-separated words, which only approximates the model tokeniser.
    `token_start` and `token_end` index the note body, not the prepended title.
    """
    if overlap >= size:
        raise ValueError(f"chunk overlap ({overlap}) must be smaller than chunk size ({size})")

    tokens = note.text.split()
    if not tokens:
        return []

    step = size - overlap
    chunks: list[Chunk] = []
    for start in range(0, len(tokens), step):
        window = tokens[start:start + size]
        if len(window) < MIN_CHUNK_TOKENS and chunks:
            break
        ordinal = len(chunks)
        chunks.append(
            Chunk(
                chunk_id=f"{note.note_id}#{ordinal}",
                note_id=note.note_id,
                title=note.title,
                ordinal=ordinal,
                # The title goes into the embedded text: most notes name their topic only
                # in the heading, so later chunks are otherwise stripped of their context.
                text=f"{note.title}\n\n{' '.join(window)}",
                token_start=start,
                token_end=start + len(window),
            )
        )
        if start + len(window) >= len(tokens):
            break
    return chunks


def chunk_notes(notes: Sequence[Note], size: int, overlap: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    for note in notes:
        chunks.extend(chunk_note(note, size, overlap))
    return chunks
