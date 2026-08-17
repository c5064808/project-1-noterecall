from __future__ import annotations

from pathlib import Path

import pytest

from noterecall.chunking import MIN_CHUNK_TOKENS, chunk_note, chunk_notes
from noterecall.notes import Note


def make_note(token_count: int, note_id: str = "python/loops.md", title: str = "Loops") -> Note:
    words = " ".join(f"w{i}" for i in range(token_count))
    return Note(note_id=note_id, path=Path(note_id), title=title, text=words, tags=[])


def body_of(chunk) -> list[str]:
    return chunk.text.split("\n\n", 1)[1].split()


def test_a_note_shorter_than_the_window_becomes_one_chunk():
    chunks = chunk_note(make_note(30), size=64, overlap=8)

    assert len(chunks) == 1
    assert chunks[0].chunk_id == "python/loops.md#0"
    assert (chunks[0].token_start, chunks[0].token_end) == (0, 30)


def test_overlap_carries_tokens_between_chunks():
    chunks = chunk_note(make_note(100), size=40, overlap=10)

    assert [(c.token_start, c.token_end) for c in chunks] == [(0, 40), (30, 70), (60, 100)]
    assert body_of(chunks[0])[-10:] == body_of(chunks[1])[:10]
    assert body_of(chunks[1])[-10:] == body_of(chunks[2])[:10]


def test_a_short_trailing_window_is_dropped():
    # 80 tokens with step 30 leaves a final window of 20, which is below the minimum.
    chunks = chunk_note(make_note(80), size=40, overlap=10)

    assert len(chunks) == 2
    assert chunks[-1].token_end == 70
    assert all(len(body_of(chunk)) >= MIN_CHUNK_TOKENS for chunk in chunks)


def test_a_short_note_is_kept_even_below_the_minimum():
    chunks = chunk_note(make_note(MIN_CHUNK_TOKENS - 5), size=40, overlap=10)

    assert len(chunks) == 1


def test_overlap_at_least_as_large_as_the_window_is_rejected():
    with pytest.raises(ValueError):
        chunk_note(make_note(100), size=40, overlap=40)


def test_the_title_is_prepended_to_every_chunk():
    chunks = chunk_note(make_note(100, title="Nested Loops"), size=40, overlap=10)

    assert len(chunks) == 3
    assert all(chunk.text.startswith("Nested Loops\n\n") for chunk in chunks)


def test_ordinals_restart_for_each_note():
    notes = [make_note(100, "a.md"), make_note(100, "b.md")]

    chunks = chunk_notes(notes, size=40, overlap=10)

    assert [c.chunk_id for c in chunks if c.note_id == "b.md"] == ["b.md#0", "b.md#1", "b.md#2"]
    assert len({c.chunk_id for c in chunks}) == len(chunks)
