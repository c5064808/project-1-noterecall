from __future__ import annotations

import sys
import time
from pathlib import Path

# `streamlit run noterecall/app.py` puts this file's own directory on the path, not the
# project root, so the package imports below would fail without this.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import streamlit as st
except ImportError:
    raise SystemExit(
        "streamlit is not installed. Run 'pip install streamlit', then "
        "'streamlit run noterecall/app.py'."
    )

from noterecall.chunking import chunk_notes
from noterecall.cli import overlap_for
from noterecall.config import load_config
from noterecall.embedding import build_embedder
from noterecall.index import build_index, namespace_for
from noterecall.keyword import BM25Search
from noterecall.notes import load_notes
from noterecall.search import SemanticSearch, reciprocal_rank_fusion

CHUNK_SIZES = (128, 256, 512)
MODES = ("Semantic", "Keyword", "Hybrid")
SNIPPET_WIDTH = 600


@st.cache_resource
def get_embedder(backend: str, model: str):
    return build_embedder(load_config(embedding_backend=backend, embedding_model=model))


@st.cache_resource
def get_index(backend: str):
    return build_index(load_config(index_backend=backend))


@st.cache_data
def get_chunks(notes_dir: str, size: int, overlap: int):
    return chunk_notes(load_notes(Path(notes_dir)), size, overlap)


def run_search(cfg, query: str, mode: str, top_k: int, size: int):
    namespace = namespace_for(size)
    runs = []
    if mode in ("Semantic", "Hybrid"):
        embedder = get_embedder(cfg.embedding_backend, cfg.embedding_model)
        searcher = SemanticSearch(get_index(cfg.index_backend), embedder, namespace)
        runs.append(searcher.search(query, top_k=top_k))
    if mode in ("Keyword", "Hybrid"):
        chunks = get_chunks(str(cfg.notes_dir), size, overlap_for(size, cfg))
        runs.append(BM25Search.from_chunks(chunks).search(query, top_k=top_k))

    if len(runs) > 1:
        return reciprocal_rank_fusion(runs)[:top_k]
    return runs[0]


def main() -> None:
    st.set_page_config(page_title="NoteRecall", layout="centered")
    cfg = load_config()

    st.sidebar.header("Setup")
    st.sidebar.write(f"Notes: {cfg.notes_dir}")
    st.sidebar.write(f"Index backend: {cfg.index_backend}")
    st.sidebar.write(f"Embeddings: {cfg.embedding_backend}")
    st.sidebar.write(f"Model: {cfg.embedding_model}")
    st.sidebar.caption(
        "Every result is a verbatim passage from the notes. Nothing here is generated."
    )

    st.title("NoteRecall")
    query = st.text_input("Search your notes", placeholder="how does chunk size affect recall")
    mode = st.radio("Mode", MODES, horizontal=True)
    top_k = st.slider("Results", min_value=1, max_value=10, value=cfg.top_k)
    size = st.selectbox(
        "Chunk size",
        CHUNK_SIZES,
        index=CHUNK_SIZES.index(cfg.chunk_size) if cfg.chunk_size in CHUNK_SIZES else 1,
    )

    if not query:
        st.caption("Build an index first with: python -m noterecall index --chunk-size 256")
        return

    started = time.perf_counter()
    try:
        hits = run_search(cfg, query, mode, top_k, size)
    except FileNotFoundError as exc:
        st.error(str(exc))
        return
    elapsed_ms = (time.perf_counter() - started) * 1000

    st.sidebar.metric("Last search", f"{elapsed_ms:.0f} ms")
    if not hits:
        st.info("No matches. Keyword search needs a term that appears in the notes.")
        return

    for rank, hit in enumerate(hits, start=1):
        with st.expander(f"{rank}. {hit.title} ({hit.score:.3f})", expanded=rank == 1):
            st.caption(hit.note_id)
            st.write(hit.snippet(query, width=SNIPPET_WIDTH))


if __name__ == "__main__":
    main()
