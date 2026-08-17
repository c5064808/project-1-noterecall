from __future__ import annotations

import argparse
import sys
import time

from noterecall.chunking import chunk_notes
from noterecall.config import Config, load_config
from noterecall.embedding import build_embedder
from noterecall.index import build_index, chunk_metadata, namespace_for
from noterecall.keyword import BM25Search
from noterecall.notes import load_notes
from noterecall.search import SemanticSearch, reciprocal_rank_fusion

SNIPPET_WIDTH = 240
MODES = ("semantic", "keyword", "hybrid")
REPORTED_CHUNK_SIZES = (128, 256, 512)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="noterecall",
        description="Search a folder of markdown notes by meaning or by keyword.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    index = sub.add_parser("index", help="chunk, embed and store the notes")
    index.add_argument("--notes-dir")
    # append with no default, because argparse appends to a default list instead of
    # replacing it; the configured chunk size is substituted afterwards.
    index.add_argument("--chunk-size", type=int, action="append")
    index.add_argument("--backend", choices=("local", "pinecone"))
    index.add_argument("--rebuild", action="store_true", help="empty the namespace first")

    search = sub.add_parser("search", help="run a query against an existing index")
    search.add_argument("query")
    search.add_argument("--mode", choices=MODES, default="semantic")
    search.add_argument("--top-k", type=int)
    search.add_argument("--chunk-size", type=int)

    sub.add_parser("stats", help="show what is currently indexed")
    return parser


def overlap_for(size: int, cfg: Config) -> int:
    """Scale the configured overlap with the window, so chunk size is the only variable."""
    return round(size * cfg.chunk_overlap / cfg.chunk_size)


def index_chunks(index, embedder, chunks, namespace: str) -> tuple[float, float]:
    """Embed the chunks and upsert them under `namespace`. Returns (encode, upsert) seconds."""
    started = time.perf_counter()
    vectors = embedder.encode_documents([chunk.text for chunk in chunks])
    encode_seconds = time.perf_counter() - started

    started = time.perf_counter()
    index.upsert(
        [chunk.chunk_id for chunk in chunks],
        vectors,
        [chunk_metadata(chunk) for chunk in chunks],
        namespace,
    )
    return encode_seconds, time.perf_counter() - started


def cmd_index(args) -> int:
    cfg = load_config(notes_dir=args.notes_dir, index_backend=args.backend)
    notes = load_notes(cfg.notes_dir)
    if not notes:
        return fail(f"No markdown notes found in {cfg.notes_dir}")

    print(f"Loaded {len(notes)} notes from {cfg.notes_dir}")
    embedder = build_embedder(cfg)
    index = build_index(cfg)
    index.ensure_ready(embedder.dimension)
    print(f"Embedding with {embedder.name} ({embedder.dimension} dimensions) "
          f"into the {index.name} index")

    for size in args.chunk_size or [cfg.chunk_size]:
        namespace = namespace_for(size)
        if args.rebuild:
            index.clear(namespace)
        chunks = chunk_notes(notes, size, overlap_for(size, cfg))
        encode_seconds, upsert_seconds = index_chunks(index, embedder, chunks, namespace)
        print(f"{namespace}: {len(chunks)} chunks, embedded in {encode_seconds:.1f}s, "
              f"stored in {upsert_seconds:.1f}s")

    print("\nIndex stats")
    print_stats(index.stats())
    return 0


def cmd_search(args) -> int:
    cfg = load_config(top_k=args.top_k, chunk_size=args.chunk_size)
    namespace = namespace_for(cfg.chunk_size)

    runs = []
    if args.mode in ("semantic", "hybrid"):
        index = build_index(cfg)
        searcher = SemanticSearch(index, build_embedder(cfg), namespace)
        try:
            runs.append(searcher.search(args.query, top_k=cfg.top_k))
        except FileNotFoundError as exc:
            return fail(str(exc))

    if args.mode in ("keyword", "hybrid"):
        notes = load_notes(cfg.notes_dir)
        if not notes:
            return fail(f"No markdown notes found in {cfg.notes_dir}")
        chunks = chunk_notes(notes, cfg.chunk_size, overlap_for(cfg.chunk_size, cfg))
        runs.append(BM25Search.from_chunks(chunks).search(args.query, top_k=cfg.top_k))

    hits = reciprocal_rank_fusion(runs)[:cfg.top_k] if len(runs) > 1 else runs[0]
    if not hits:
        return fail(f"No matches for {args.query!r} in {namespace}")

    print(f"{args.mode} search over {namespace}, top {len(hits)}\n")
    for rank, hit in enumerate(hits, start=1):
        print(f"{rank:>2}  {hit.score:6.3f}  {hit.title}  ({hit.note_id})")
        print(f"          {hit.snippet(args.query, width=SNIPPET_WIDTH)}\n")
    return 0


def cmd_stats(args) -> int:
    cfg = load_config()
    notes = load_notes(cfg.notes_dir)
    print(f"Notes in {cfg.notes_dir}: {len(notes)}")
    for size in REPORTED_CHUNK_SIZES:
        chunks = chunk_notes(notes, size, overlap_for(size, cfg))
        print(f"  {namespace_for(size)}: {len(chunks)} chunks if indexed")
    print()
    print_stats(build_index(cfg).stats())
    return 0


def print_stats(stats: dict) -> None:
    namespaces = stats.get("namespaces") or {}
    for key, value in stats.items():
        if key != "namespaces":
            print(f"  {key}: {value}")
    for name, detail in sorted(namespaces.items()):
        if isinstance(detail, dict):
            detail = ", ".join(f"{k}={v}" for k, v in detail.items())
        print(f"    {name}: {detail}")
    if not namespaces:
        print("    nothing indexed yet")


def fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "index":
        return cmd_index(args)
    if args.command == "search":
        return cmd_search(args)
    return cmd_stats(args)


if __name__ == "__main__":
    sys.exit(main())
