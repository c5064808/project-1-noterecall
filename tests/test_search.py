from __future__ import annotations

from pathlib import Path

import pytest

from noterecall.chunking import chunk_notes
from noterecall.embedding import HashingEmbedder
from noterecall.index.base import chunk_metadata, namespace_for
from noterecall.index.local_index import LocalIndex
from noterecall.keyword import BM25Search
from noterecall.notes import Note
from noterecall.search import SemanticSearch, reciprocal_rank_fusion

CHUNK_SIZE = 128
CHUNK_OVERLAP = 16

CORPUS = {
    "retrieval/ann-search.md": (
        "Approximate nearest neighbour search",
        """
        Exact nearest neighbour search compares the query against every stored vector, so
        the cost grows with the size of the collection. Approximate nearest neighbour
        search gives up the guarantee of finding the true closest vector and in exchange
        answers in roughly logarithmic time. HNSW builds a layered proximity graph and
        walks it greedily from a coarse layer down to a fine one. The parameter that
        matters is the number of neighbours kept per node: raise it and recall improves
        while the graph gets larger and slower to search. Recall against the exact result
        is the honest way to report quality, because a fast index that returns the wrong
        neighbours is not faster in any useful sense.
        """,
    ),
    "retrieval/vector-databases.md": (
        "Vector databases",
        """
        A vector database stores embeddings next to a small amount of metadata and serves
        similarity queries over them. The operations are upsert, query and delete, and most
        services partition the data into namespaces so unrelated collections can live in one
        index. Cosine similarity is the usual metric for sentence embeddings, and if the
        vectors are already unit length the cosine is just a dot product. Metadata is kept
        small on purpose since it travels back with every result.
        """,
    ),
    "python/pandas-timeseries.md": (
        "Pandas time series joins",
        """
        Joining two time series on an exact timestamp almost never works because the clocks
        differ by a few milliseconds. The answer is merge_asof, which pairs each row on the
        left with the most recent row on the right at or before it. Both frames must be
        sorted on the join column first or merge_asof raises straight away. The tolerance
        keyword bounds how far back it will look, so a tolerance of one minute leaves a
        missing value rather than pairing a row with a reading from an hour earlier. There
        is a direction keyword too, forward or nearest instead of the default backward.
        TODO: check whether merge_asof still needs the by column to be of the same dtype on
        both sides, it bit me last week and I never wrote down the fix.
        """,
    ),
    "python/functions-and-arguments.md": (
        "Function arguments and call frames",
        """
        Every call pushes a frame, and the traceback you see is just those frames printed
        from the outside in. A positional argument is bound by position, a keyword argument
        by name, and anything after a bare star must be passed by keyword. A mutable default
        argument is shared between calls, which is the classic way to get a list that
        quietly grows. When I read an unfamiliar function I look at the argument list first
        and work out which of them the caller actually has to supply.
        """,
    ),
}


def build_notes() -> list[Note]:
    return [
        Note(note_id=note_id, path=Path(note_id), title=title, text=" ".join(body.split()), tags=[])
        for note_id, (title, body) in CORPUS.items()
    ]


def build_search(tmp_path: Path) -> tuple[SemanticSearch, BM25Search]:
    notes = build_notes()
    chunks = chunk_notes(notes, CHUNK_SIZE, CHUNK_OVERLAP)
    embedder = HashingEmbedder()
    namespace = namespace_for(CHUNK_SIZE)

    index = LocalIndex(tmp_path / "index")
    index.ensure_ready(embedder.dimension)
    index.upsert(
        [chunk.chunk_id for chunk in chunks],
        embedder.encode_documents([chunk.text for chunk in chunks]),
        [chunk_metadata(chunk) for chunk in chunks],
        namespace,
    )
    return SemanticSearch(index, embedder, namespace), BM25Search.from_chunks(chunks)


def test_semantic_search_returns_the_note_that_shares_the_query_vocabulary(tmp_path):
    semantic, _ = build_search(tmp_path)

    hits = semantic.search("approximate nearest neighbour graph recall", top_k=3)

    assert hits[0].note_id == "retrieval/ann-search.md"
    assert hits[0].score > hits[-1].score


def test_bm25_finds_a_rare_exact_token_that_the_hashing_embedder_misses(tmp_path):
    semantic, keyword = build_search(tmp_path)
    query = "why is merge_asof in the traceback frames"

    keyword_hits = keyword.search(query, top_k=3)
    semantic_hits = semantic.search(query, top_k=3)

    # BM25 weights merge_asof by how rare it is, so one occurrence outranks a note that
    # matches the ordinary words. The hashing fallback has no such weighting and follows
    # the common words to the note about calls and frames instead.
    assert keyword_hits[0].note_id == "python/pandas-timeseries.md"
    assert semantic_hits[0].note_id == "python/functions-and-arguments.md"


def test_hybrid_fusion_promotes_the_note_both_methods_agree_on(tmp_path):
    semantic, keyword = build_search(tmp_path)
    query = "how does a vector database keep collections apart in one index"

    runs = [semantic.search(query, top_k=3), keyword.search(query, top_k=3)]
    fused = reciprocal_rank_fusion(runs)

    assert fused[0].note_id == "retrieval/vector-databases.md"
    assert [hit.score for hit in fused] == sorted((hit.score for hit in fused), reverse=True)


def test_querying_a_namespace_that_was_never_built_fails_with_a_clear_message(tmp_path):
    semantic, _ = build_search(tmp_path)
    semantic.namespace = namespace_for(512)

    with pytest.raises(FileNotFoundError, match="chunk512"):
        semantic.search("anything at all")


def test_the_snippet_is_centred_on_the_first_query_term_that_occurs(tmp_path):
    _, keyword = build_search(tmp_path)

    hit = keyword.search("tolerance", top_k=1)[0]
    snippet = hit.snippet("tolerance", width=80)

    assert "tolerance" in snippet
    assert len(snippet) <= 86
    assert "\n" not in snippet
