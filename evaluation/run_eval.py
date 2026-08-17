"""Run the gold set through semantic and keyword search at several chunk sizes."""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
import textwrap
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from pathlib import Path

from evaluation.goldset import CATEGORIES, GoldQuery, load_goldset
from evaluation.metrics import ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank
from noterecall.chunking import chunk_notes
from noterecall.cli import index_chunks, overlap_for
from noterecall.config import load_config
from noterecall.embedding import build_embedder
from noterecall.index import build_index, namespace_for
from noterecall.keyword import BM25Search
from noterecall.notes import load_notes
from noterecall.search import SemanticSearch

DEFAULT_GOLDSET = Path(__file__).resolve().parent / "goldset.yaml"
DEFAULT_CHUNK_SIZES = (128, 256, 512)
METHODS = ("semantic", "keyword")

# Relevance is judged per note, so the ranking is deduplicated by note before scoring. We
# ask for more chunks than we need because several of them usually come from one note.
FETCH_MULTIPLIER = 4
WARMUP_QUERIES = 5
TIMED_REPEATS = 3

# Width the hand-written prose in this file is wrapped to, matched by the generated sentence.
SUMMARY_WRAP = 88

PREAMBLE = """\
Corpus: {notes} notes. Gold set: {queries} queries, judged at note level. Cutoff k = {k}.
Embeddings: {embedder}.

Index: the local exact-cosine backend, so retrieval quality here is the ceiling an
approximate index would be trying to reach, and the latencies are not comparable with a
hosted service over the network. The index size column is the vector index; the BM25 model
is rebuilt in memory and stores nothing on disk. Each query is timed as the fastest of
three identical runs, taken after a short warm-up.
"""

READING = """\
Recall@k is the primary metric: most queries have one or two relevant notes, so it answers
the question a user actually asks, which is whether the note they wanted is on the first
screen. P@{k} is capped by the number of relevant notes a query has, so it looks low by
construction and only the comparison between rows means anything. The win counts matter as
much as the means: thirty queries is a small sample and a couple of large per-query margins
can carry an average on their own.
"""

BY_CATEGORY = """\
Every gold query is labelled paraphrase, exact-token or lookup in goldset.yaml, and this is
the split the proposal set out to test. The aggregate table above is close to a tie, so it
is this breakdown rather than the means that answers the research question. The counts are
small once thirty queries are cut three ways, so read the direction of each row rather than
the third decimal place. Chunk size {size} is shown because it has the best semantic recall.
"""


@dataclass(frozen=True)
class QueryResult:
    chunk_size: int
    method: str
    query_id: str
    query: str
    precision: float
    recall: float
    reciprocal_rank: float
    ndcg: float
    latency_ms: float
    top_note: str


@dataclass(frozen=True)
class MethodSummary:
    chunk_size: int
    method: str
    chunks: int
    queries: int
    precision: float
    recall: float
    mrr: float
    ndcg: float
    median_latency_ms: float
    p95_latency_ms: float
    index_size_mb: float


@dataclass(frozen=True)
class CategorySummary:
    chunk_size: int
    method: str
    category: str
    queries: int
    precision: float
    recall: float
    mrr: float
    ndcg: float


def ranked_note_ids(searcher, query: str, top_k: int) -> tuple[list[str], float]:
    # Timed as the fastest of a few identical runs. A single measurement on a laptop picks
    # up whatever else the scheduler was doing, and the number we want is the cost of the
    # search rather than the cost of the search plus an unlucky moment.
    latency_ms = float("inf")
    for _ in range(TIMED_REPEATS):
        started = time.perf_counter()
        hits = searcher.search(query, top_k=top_k * FETCH_MULTIPLIER)
        latency_ms = min(latency_ms, (time.perf_counter() - started) * 1000)

    ordered: list[str] = []
    for hit in hits:
        if hit.note_id not in ordered:
            ordered.append(hit.note_id)
    return ordered[:top_k], latency_ms


def evaluate_method(searcher, method: str, size: int, gold: Sequence[GoldQuery],
                    top_k: int) -> list[QueryResult]:
    # The first call pays for lazy imports and warm caches, which would land entirely on
    # whichever query happens to come first.
    for query in gold[:WARMUP_QUERIES]:
        searcher.search(query.query, top_k=top_k)

    results = []
    for query in gold:
        ranked, latency_ms = ranked_note_ids(searcher, query.query, top_k)
        relevant = set(query.relevant_notes)
        results.append(
            QueryResult(
                chunk_size=size,
                method=method,
                query_id=query.query_id,
                query=query.query,
                precision=precision_at_k(ranked, relevant, top_k),
                recall=recall_at_k(ranked, relevant, top_k),
                reciprocal_rank=reciprocal_rank(ranked, relevant, top_k),
                ndcg=ndcg_at_k(ranked, relevant, top_k),
                latency_ms=latency_ms,
                top_note=ranked[0] if ranked else "",
            )
        )
    return results


def summarise(results: Sequence[QueryResult], chunks: int, index_size_mb: float) -> MethodSummary:
    latencies = [r.latency_ms for r in results]
    return MethodSummary(
        chunk_size=results[0].chunk_size,
        method=results[0].method,
        chunks=chunks,
        queries=len(results),
        precision=statistics.fmean(r.precision for r in results),
        recall=statistics.fmean(r.recall for r in results),
        mrr=statistics.fmean(r.reciprocal_rank for r in results),
        ndcg=statistics.fmean(r.ndcg for r in results),
        median_latency_ms=statistics.median(latencies),
        p95_latency_ms=percentile(latencies, 0.95),
        index_size_mb=index_size_mb,
    )


def summarise_by_category(results: Sequence[QueryResult],
                          categories: Mapping[str, str]) -> list[CategorySummary]:
    """Mean of each metric over the queries of one category, per chunk size and method."""
    rows = []
    for size in sorted({r.chunk_size for r in results}):
        for method in METHODS:
            for category in CATEGORIES:
                group = [r for r in results if r.chunk_size == size and r.method == method
                         and categories[r.query_id] == category]
                if not group:
                    continue
                rows.append(
                    CategorySummary(
                        chunk_size=size,
                        method=method,
                        category=category,
                        queries=len(group),
                        precision=statistics.fmean(r.precision for r in group),
                        recall=statistics.fmean(r.recall for r in group),
                        mrr=statistics.fmean(r.reciprocal_rank for r in group),
                        ndcg=statistics.fmean(r.ndcg for r in group),
                    )
                )
    return rows


def best_chunk_size(summaries: Sequence[MethodSummary]) -> int:
    """The chunk size the report leads on: the one with the best semantic recall."""
    best = max((s for s in summaries if s.method == "semantic"), key=lambda s: s.recall)
    return best.chunk_size


def percentile(values: Sequence[float], fraction: float) -> float:
    """Nearest-rank percentile. Interpolating over thirty samples would be false precision."""
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(fraction * (len(ordered) - 1)))]


def namespace_size_mb(directory: Path, namespace: str) -> float:
    files = [p for p in directory.rglob("*") if p.is_file() and namespace in p.name]
    return sum(p.stat().st_size for p in files) / (1024 * 1024)


def write_csv(path: Path, rows: Sequence, columns: Sequence[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for row in rows:
            writer.writerow(
                [round(v, 4) if isinstance(v, float) else v
                 for v in (getattr(row, column) for column in columns)]
            )


def summary_table(summaries: Sequence[MethodSummary]) -> str:
    header = ["chunk", "method", "chunks", "P@k", "R@k", "MRR", "nDCG@k",
              "median ms", "p95 ms", "index MB"]
    rows = [
        [str(s.chunk_size), s.method, str(s.chunks), f"{s.precision:.3f}", f"{s.recall:.3f}",
         f"{s.mrr:.3f}", f"{s.ndcg:.3f}", f"{s.median_latency_ms:.1f}",
         f"{s.p95_latency_ms:.1f}", f"{s.index_size_mb:.2f}"]
        for s in summaries
    ]
    return markdown_table(header, rows)


def markdown_table(header: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    widths = [max(len(cell) for cell in column) for column in zip(header, *rows)]

    def render(cells: Sequence[str]) -> str:
        return "| " + " | ".join(cell.ljust(w) for cell, w in zip(cells, widths)) + " |"

    separator = "|" + "|".join("-" * (width + 2) for width in widths) + "|"
    return "\n".join([render(header), separator, *(render(row) for row in rows)])


def category_table(rows: Sequence[CategorySummary]) -> str:
    header = ["category", "method", "n", "P@k", "R@k", "MRR", "nDCG@k"]
    ordered = [r for category in CATEGORIES for method in METHODS
               for r in rows if r.category == category and r.method == method]
    body = [
        [r.category, r.method, str(r.queries), f"{r.precision:.3f}", f"{r.recall:.3f}",
         f"{r.mrr:.3f}", f"{r.ndcg:.3f}"]
        for r in ordered
    ]
    return markdown_table(header, body)


def category_leads(rows: Sequence[CategorySummary], size: int) -> str:
    """One sentence naming the leading method on each category, on MRR, with the margin."""
    clauses = []
    for category in CATEGORIES:
        pair = {r.method: r for r in rows if r.category == category}
        if len(pair) != len(METHODS):
            continue
        gap = pair["semantic"].mrr - pair["keyword"].mrr
        if abs(gap) < 0.0005:
            clauses.append(f"the two are level on {category} queries")
        else:
            leader = "semantic" if gap > 0 else "keyword"
            clauses.append(f"{leader} leads on {category} queries by "
                           f"{abs(gap):.3f} MRR")
    if len(clauses) > 1:
        clauses[-1] = f"and {clauses[-1]}"
    sentence = f"At chunk size {size}, " + ", ".join(clauses) + "."
    return textwrap.fill(sentence, width=SUMMARY_WRAP)


def win_counts(results: Sequence[QueryResult], size: int) -> tuple[int, int, int]:
    """Per-query wins for semantic against keyword on reciprocal rank, at one chunk size."""
    scores = {(r.method, r.query_id): r.reciprocal_rank for r in results if r.chunk_size == size}
    pairs = [(rank, scores[("keyword", query_id)])
             for (method, query_id), rank in scores.items() if method == "semantic"]
    return (sum(s > k for s, k in pairs), sum(s < k for s, k in pairs),
            sum(s == k for s, k in pairs))


def write_summary(path: Path, summaries: Sequence[MethodSummary], results: Sequence[QueryResult],
                  by_category: Sequence[CategorySummary], top_k: int, notes: int,
                  embedder_name: str) -> str:
    wins = markdown_table(
        ["chunk", "semantic wins", "keyword wins", "tied"],
        [[str(size), *(str(count) for count in win_counts(results, size))]
         for size in sorted({s.chunk_size for s in summaries})],
    )
    size = best_chunk_size(summaries)
    best_rows = [r for r in by_category if r.chunk_size == size]
    text = "\n".join([
        "# Evaluation summary",
        "",
        PREAMBLE.format(notes=notes, queries=summaries[0].queries, k=top_k,
                        embedder=embedder_name),
        summary_table(summaries),
        "",
        "## Per-query wins (reciprocal rank, semantic against keyword)",
        "",
        wins,
        "",
        "## By query type",
        "",
        BY_CATEGORY.format(size=size),
        category_table(best_rows),
        "",
        category_leads(best_rows, size),
        "",
        "## Reading this",
        "",
        READING.format(k=top_k),
        "Regenerate with: make eval",
    ]) + "\n"
    path.write_text(text, encoding="utf-8")
    return text


def write_figures(directory: Path, summaries: Sequence[MethodSummary],
                  by_category: Sequence[CategorySummary]) -> None:
    import matplotlib

    matplotlib.use("Agg")  # written from a terminal, no display attached
    import matplotlib.pyplot as plt

    directory.mkdir(parents=True, exist_ok=True)
    sizes = sorted({s.chunk_size for s in summaries})

    figure, axes = plt.subplots(figsize=(7, 4.5))
    plotted = []
    for method in METHODS:
        for metric, style in (("recall", "-o"), ("ndcg", "--s")):
            values = [getattr(s, metric) for s in summaries if s.method == method]
            plotted.extend(values)
            axes.plot(sizes, values, style, label=f"{method} {metric}")
    axes.set_xticks(sizes)
    axes.set_xlabel("chunk size (whitespace tokens)")
    axes.set_ylabel("score")
    # The differences are a few points, so a full 0-1 axis would show four flat lines. The
    # bar chart below keeps its zero baseline, where a truncated axis would mislead.
    axes.set_ylim(max(0.0, min(plotted) - 0.05), min(1.0, max(plotted) + 0.05))
    axes.set_title("Retrieval quality against chunk size")
    axes.legend()
    axes.grid(True, alpha=0.3)
    figure.tight_layout()
    figure.savefig(directory / "metrics_by_chunk_size.png", dpi=150)
    plt.close(figure)

    best_size = best_chunk_size(summaries)
    metrics = ("precision", "recall", "mrr", "ndcg")
    labels = ("P@k", "R@k", "MRR", "nDCG@k")
    positions = range(len(metrics))
    width = 0.38

    figure, axes = plt.subplots(figsize=(7, 4.5))
    for offset, method in zip((-width / 2, width / 2), METHODS):
        row = next(s for s in summaries if s.method == method and s.chunk_size == best_size)
        axes.bar([p + offset for p in positions], [getattr(row, m) for m in metrics],
                 width, label=method)
    axes.set_xticks(list(positions))
    axes.set_xticklabels(labels)
    axes.set_ylabel("score")
    axes.set_ylim(0, 1)
    axes.set_title(f"Semantic against keyword at chunk size {best_size}")
    axes.legend()
    axes.grid(True, axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(directory / "method_comparison.png", dpi=150)
    plt.close(figure)

    best_rows = [r for r in by_category if r.chunk_size == best_size]
    categories = [c for c in CATEGORIES if any(r.category == c for r in best_rows)]
    positions = range(len(categories))

    figure, axes = plt.subplots(figsize=(7, 4.5))
    for offset, method in zip((-width / 2, width / 2), METHODS):
        scores = [next(r.mrr for r in best_rows if r.category == c and r.method == method)
                  for c in categories]
        axes.bar([p + offset for p in positions], scores, width, label=method)
    counts = {r.category: r.queries for r in best_rows}
    axes.set_xticks(list(positions))
    axes.set_xticklabels([f"{c}\n(n = {counts[c]})" for c in categories])
    axes.set_ylabel("MRR")
    axes.set_ylim(0, 1)
    axes.set_title(f"MRR by query type at chunk size {best_size}")
    axes.legend()
    axes.grid(True, axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(directory / "method_by_category.png", dpi=150)
    plt.close(figure)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="evaluation.run_eval",
        description="Score semantic and keyword retrieval against the gold set.",
    )
    parser.add_argument("--notes-dir")
    parser.add_argument("--goldset", type=Path, default=DEFAULT_GOLDSET)
    parser.add_argument("--chunk-sizes", type=int, nargs="+", default=list(DEFAULT_CHUNK_SIZES))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--out", type=Path, default=Path("results"))
    args = parser.parse_args(argv)

    cfg = load_config(notes_dir=args.notes_dir, index_backend="local")
    notes = load_notes(cfg.notes_dir)
    if not notes:
        print(f"No markdown notes found in {cfg.notes_dir}", file=sys.stderr)
        return 1
    try:
        gold = load_goldset(args.goldset, {note.note_id for note in notes})
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1

    print(f"{len(notes)} notes, {len(gold)} gold queries, k = {args.top_k}")
    embedder = build_embedder(cfg)
    index = build_index(cfg)
    index.ensure_ready(embedder.dimension)

    results: list[QueryResult] = []
    summaries: list[MethodSummary] = []
    for size in args.chunk_sizes:
        namespace = namespace_for(size)
        chunks = chunk_notes(notes, size, overlap_for(size, cfg))
        index.clear(namespace)
        encode_seconds, _ = index_chunks(index, embedder, chunks, namespace)
        print(f"{namespace}: {len(chunks)} chunks embedded in {encode_seconds:.1f}s")

        searchers = {
            "semantic": SemanticSearch(index, embedder, namespace),
            "keyword": BM25Search.from_chunks(chunks),
        }
        size_mb = namespace_size_mb(cfg.local_index_dir, namespace)
        for method in METHODS:
            method_results = evaluate_method(searchers[method], method, size, gold, args.top_k)
            results.extend(method_results)
            summaries.append(summarise(method_results, len(chunks), size_mb))

    by_category = summarise_by_category(results, {q.query_id: q.category for q in gold})

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "metrics.csv", summaries, [f.name for f in fields(MethodSummary)])
    write_csv(args.out / "metrics_by_category.csv", by_category,
              [f.name for f in fields(CategorySummary)])
    write_csv(args.out / "per_query.csv", results, [f.name for f in fields(QueryResult)])
    text = write_summary(args.out / "summary.md", summaries, results, by_category, args.top_k,
                         len(notes), embedder.name)
    write_figures(args.out / "figures", summaries, by_category)

    print()
    print(text)
    print(f"Written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
