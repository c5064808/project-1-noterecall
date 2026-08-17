# NoteRecall

Semantic search over a folder of markdown notes, with a BM25 keyword search over the same
material as the comparison baseline. Module 55-710603 group project, project 1.

## What it does

You point it at a directory of markdown files. It splits each note into overlapping
chunks, embeds every chunk with a sentence-transformer, and stores the vectors in Pinecone
or in a local index on disk. When you search, your query is embedded the same way and the
index returns the nearest chunks.

There is no language model anywhere in this project and nothing is ever generated. Every
result you see is a verbatim span of your own notes, printed with the note it came from.
That is the point: a tool that only ever quotes cannot invent an answer, so there is no
faithfulness problem to evaluate and no way for it to state something you never wrote.

The code exists to answer two questions with numbers:

1. Does semantic search beat BM25 keyword search on the same set of queries?
2. How much does chunk size (128, 256 or 512 tokens) change the quality of the results?

Both are answered by `evaluation/run_eval.py`, and the answers on the demo corpus are in
`results/summary.md`.

## How it works

1. **Load.** Every `.md` and `.markdown` file under the notes directory is read
   recursively. YAML front matter is stripped, tags are kept, the first H1 becomes the
   note title, and `README.md` files are skipped.
2. **Chunk.** Each note is cut into windows of N whitespace tokens with an overlap carried
   forward, so a sentence that straddles a boundary still appears whole somewhere. The
   note title is prepended to every chunk before it is embedded. That is deliberate: most
   notes name their subject only in the heading, and without it the second and third chunk
   of a note have no idea what document they belong to.
3. **Embed.** Chunks go through `sentence-transformers/all-MiniLM-L6-v2`, which returns
   384-dimensional vectors, L2-normalised so that a dot product is the cosine similarity.
4. **Index.** Vectors are upserted into Pinecone or into the local numpy index, in a
   namespace named after the chunk size (`chunk128`, `chunk256`, `chunk512`). Each vector
   carries the note id, title, ordinal and the chunk text as metadata.
5. **Search.** The query is embedded with the same model and the index returns the k
   nearest chunks by cosine similarity.
6. **Show.** Results are printed as rank, score, note title, note id and a snippet of the
   original text. Nothing is summarised, rewritten or generated.

The BM25 baseline runs over exactly the same chunks, so the only thing that differs
between the two arms of the comparison is how a match is scored.

## Install

Python 3.10 or newer; developed on 3.12.

    python3 -m venv .venv
    source .venv/bin/activate
    make install

That pulls in torch through sentence-transformers, which is a large download on a slow
connection. The first index or search also downloads about 80MB of model weights into
`~/.cache/huggingface`; after that everything runs offline.

If you cannot install sentence-transformers at all, set `EMBEDDING_BACKEND=hashing`. That
uses a hashed bag of unigrams and bigrams with no model and no network. It is a smoke test
so the CLI runs end to end, it has no semantics whatsoever, and no result from it should
be reported.

## Configure

Every setting has a default, so the project runs with no configuration at all. Settings
are read from a `.env` file in the project root if there is one, then from environment
variables, then from command line flags. Copy `.env.example` to `.env` to change anything.

| Variable | Default | What it does |
|---|---|---|
| `NOTES_DIR` | `data/notes` | Folder of markdown notes to index |
| `INDEX_BACKEND` | `local`, or `pinecone` if an API key is set | Where the vectors live |
| `EMBEDDING_BACKEND` | `sentence-transformers` | `sentence-transformers` or `hashing` |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Any sentence-transformers model |
| `PINECONE_API_KEY` | unset | Needed only for the Pinecone backend |
| `PINECONE_INDEX` | `noterecall` | Name of the serverless index |
| `PINECONE_CLOUD` | `aws` | Cloud for a new serverless index |
| `PINECONE_REGION` | `us-east-1` | Region for a new serverless index |
| `LOCAL_INDEX_DIR` | `.index` | Where the local backend writes its files |
| `CHUNK_SIZE` | `256` | Window size in whitespace tokens |
| `CHUNK_OVERLAP` | `32` | Tokens carried from one window into the next |
| `TOP_K` | `5` | Default number of results |

`CHUNK_OVERLAP` is interpreted as a proportion of `CHUNK_SIZE`. When you index at another
size the overlap scales with it, so indexing at 128 with the defaults gives an overlap of
16. Keeping the ratio fixed means the chunk size experiment varies one thing rather than
two.

## Index

    python -m noterecall index
    python -m noterecall index --chunk-size 128 --chunk-size 256 --chunk-size 512 --rebuild

`--chunk-size` may be repeated and each size lands in its own namespace, which is how all
three variants coexist. `--rebuild` empties the namespace first; without it the upsert
overwrites matching chunk ids and leaves anything else in place, which is what you want
after editing a few notes and what you do not want after deleting some. `--notes-dir` and
`--backend` override the configuration for one run.

On the 33-note demo corpus this takes a few seconds:

    Loaded 33 notes from .../data/notes
    Embedding with sentence-transformers/all-MiniLM-L6-v2 (384 dimensions) into the local index
    chunk256: 65 chunks, embedded in 0.2s, stored in 0.0s

`make index` builds all three sizes at once. `python -m noterecall stats` prints what is
currently indexed and how many chunks each size would produce.

## Search

    python -m noterecall search "how does approximate nearest neighbour search work"
    python -m noterecall search "externally-managed-environment" --mode keyword
    python -m noterecall search "how do I time the search loop" --mode hybrid --top-k 3

`--mode` is `semantic` (the default), `keyword` for BM25, or `hybrid`, which merges the two
rankings with reciprocal rank fusion. Hybrid is a secondary result rather than one of the
two methods being compared: it exists so the report can say what a practical system would
actually do. `--chunk-size` picks which namespace to search and defaults to 256.

Output is rank, score, note title, note id and a snippet centred on the first query term
that appears in the chunk. Scores are cosine similarities in semantic mode and raw BM25
scores in keyword mode, so they are not comparable across modes.

Keyword mode builds its BM25 model from the notes at query time rather than reading the
vector index, so it needs `NOTES_DIR` to be correct but does not need an index to exist.

## The Streamlit app

    make app

or `streamlit run noterecall/app.py`. A search box, a mode radio, a top-k slider and a
chunk size selector, with results as expandable blocks. The sidebar shows which backend
and model are live and the latency of the last search. It reads the same index the CLI
writes, so build one first.

## Evaluation

    make eval

which is `python -m evaluation.run_eval --chunk-sizes 128 256 512 --top-k 5`. It takes
well under a minute on the demo corpus and needs no network.

`evaluation/goldset.yaml` holds 30 queries, each with the notes that should be returned
and a sentence explaining the judgement. Roughly ten are paraphrases sharing little
vocabulary with the note that answers them, seven are rare exact tokens such as an error
string or a citation key, and the rest are ordinary lookups. For each chunk size the
harness rebuilds the index, runs every query through both methods, and writes:

- `results/metrics.csv`, one row per chunk size and method;
- `results/per_query.csv`, one row per query, which is where you look to find out *which*
  queries a method lost;
- `results/summary.md`, the table a human reads;
- `results/figures/`, two plots.

Relevance is judged at note level, not chunk level, so the ranked list is deduplicated by
note before it is scored: five chunks from one note count once. Because deduplication
shrinks the list, the harness asks the index for four times k chunks and keeps the first k
distinct notes.

Latency is the fastest of three identical runs per query, taken after a short warm-up. A
single measurement on a laptop mostly records what else the machine was doing at the time,
and one unlucky query was enough to move the p95 by an order of magnitude before this was
fixed.

### How to read the results

Recall@5 is the primary metric, chosen before the numbers were looked at. Most queries
have one or two relevant notes, so recall answers the question a user actually cares
about: is the note I wanted on the first screen. Precision@5 is capped by the number of
relevant notes a query has, so a query with one right answer can never score above 0.2 and
the absolute value means very little; only the comparison between rows does. MRR reports
how often the first result was right, and nDCG@5 rewards putting the relevant notes higher
up.

The per-query win counts under the table matter as much as the means. Thirty queries is a
small sample and two or three large per-query margins can carry an average on their own.

On the demo corpus the two methods come out close overall, and that is the honest finding
rather than a disappointing one. Splitting the gold set by query type says more than the
overall mean does, and `results/metrics_by_category.csv` has the full breakdown. The gap
widens as the chunk gets larger: on the ten paraphrase queries semantic search leads BM25
by 0.038 MRR at chunk size 256 (0.783 against 0.745) and by 0.175 at 512 (0.875 against
0.700). There are one to three queries, depending on chunk size, where BM25 finds nothing
relevant at all, because the note that answers the question shares no words with it. On the
eight exact-token queries BM25 scores a perfect 1.0 at every chunk size against semantic's
0.85 to 0.94, and it is far faster: a median well under a tenth of a millisecond against
about three, because it never runs a transformer over the query. Semantic search never came
back with nothing relevant on this gold set and BM25 sometimes did, which is the difference
a user would actually feel.

Neither method dominates on the aggregate, which is roughly what the BEIR results would
predict for a corpus that looks nothing like anyone's training data.

The chunk size result comes with a caveat that belongs in the discussion: the demo notes
are 250 to 350 words each, so at 512 tokens almost every note becomes a single chunk and
that row is really measuring whole-note indexing rather than a chunk size. On a corpus of
longer documents the comparison would look different.

## Using Pinecone instead of the local index

    export PINECONE_API_KEY=...
    python -m noterecall index --backend pinecone --rebuild
    python -m noterecall search "chunk size trade-off"

`INDEX_BACKEND` defaults to `pinecone` as soon as an API key is present, so exporting the
key is usually enough. A serverless index with the cosine metric is created if it does not
exist and the client waits for it to become ready. Vectors are upserted in batches of 100,
and the chunk text stored alongside each vector is truncated to 1500 characters because
Pinecone caps per-vector metadata.

The local backend is not a fallback we were forced into. The notes this tool is built for
are personal, and being able to run the whole thing with no account and no network is part
of the privacy argument in the proposal. It is also what the ethics approval assumed. Do
be aware of the trade: with Pinecone, text derived from your notes leaves your machine.

One thing the local backend is not is approximate. It scores every vector with a single
matrix multiply and returns the true top k, which makes it a correctness reference rather
than a speed comparison. Timing it against Pinecone would mostly measure the round trip to
us-east-1.

## Using your own notes

    NOTES_DIR=~/Documents/vault python -m noterecall index --rebuild
    NOTES_DIR=~/Documents/vault python -m noterecall search "that thing about batch sizes"

Nothing about the demo corpus is special; it is committed so the project runs out of the
box. The gold set, however, was written against it, and `run_eval.py` refuses to start if
the judgements name notes that do not exist. To evaluate on your own vault you have to
write your own `goldset.yaml`, which is a couple of hours of work and the only honest way
to get numbers you can quote.

## Limitations

Chunks are counted in whitespace tokens, which only approximates the model's word-piece
tokeniser. Technical prose expands by roughly a third under word-piece, so a 512-token
chunk comfortably exceeds MiniLM's 256 word-piece limit and its tail is silently
truncated. The 512 row of the results table is therefore not quite the experiment it looks
like.

Chunking loses context that crosses a boundary. A question whose answer is spread over two
paragraphs may not be satisfied well by any single chunk, and the overlap only patches the
seam rather than fixing the problem.

The gold set is thirty queries written by one of us after reading the corpus, with binary
judgements and no second annotator, so there is no inter-annotator agreement to report.
Knowing what was in the notes made it easy to write queries that are answerable, and real
users search for things that are not there at all. That behaviour is untested here.

Thirty queries is enough to see the direction of a difference and not enough to trust its
size. The evaluation reports no confidence intervals or significance tests; the win counts
are there instead, and any claim in the report should be phrased accordingly.

The corpus is 33 short notes on a narrow technical subject, which makes the top five
results about fifteen percent of the whole collection. Both methods score high partly for
that reason, and neither number should be read as what the tool would do over a vault of
several thousand notes.
